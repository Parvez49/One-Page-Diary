# Scaling — Replication, Partitioning, Sharding

> Tune first: **[performance.md](performance.md)** · System design context:
> **[../SDLC/system_design.md](../SDLC/system_design.md)**

---

## 1. The order of escalation ⭐⭐

**Each step is an order of magnitude more complexity. Do them in order, and say so.**

```
1. Fix queries & indexes        ⭐⭐ usually the entire problem
2. Connection pooling           PgBouncer — cheap, big win
3. Cache (Redis)                remove reads from the DB entirely
4. Vertical scaling             ⭐ bigger box — boring, effective, buys years
5. Read replicas                ⭐ scale READS; ⚠️ replication lag appears
6. Partitioning                 one DB, many physical tables
7. Sharding                     ⚠️⚠️ many DBs — the point of no return
8. Different datastore          the right tool for that workload
```

⭐⭐ **"Just scale vertically" is a legitimate and often correct senior answer.** A single
modern Postgres box handles tens of thousands of transactions per second and terabytes of data.
Most teams that shard didn't need to — they needed an index. Reaching for sharding early is the
architectural equivalent of premature optimisation, and interviewers are listening for whether
you know that.

---

## 2. Replication ⭐⭐

**One primary accepts writes; replicas copy its stream and serve reads.**

```
        writes
          ↓
     ┌─────────┐   WAL stream   ┌──────────┐
     │ PRIMARY │ ─────────────▶ │ REPLICA  │ ← reads
     └─────────┘ ─────────────▶ │ REPLICA  │ ← reads
                                └──────────┘
```

| | **Async replication** | **Sync replication** |
|---|---|---|
| Commit waits for replica | ❌ no | ⭐ yes |
| Write latency | ⭐ fast | ⚠️ slower (network round trip) |
| Data loss on primary failure | ⚠️ **possible** (unreplicated commits) | ⭐ none |
| Default | ⭐ almost everywhere | used for critical data |

⭐ **Semi-sync / quorum** (`synchronous_commit = remote_apply`, or "wait for 1 of 3") is the
usual compromise: durability without waiting on every replica.

⚠️⚠️ **Replication lag is the defining problem of read replicas** — and the interview question:

> A user updates their profile (goes to the **primary**), is redirected, and the next page reads
> from a **replica** that's 200 ms behind — **their own change has vanished.** This is a
> read-your-own-writes violation and it *will* happen in production.

⭐ **Mitigations, in order of preference:**
1. **Read-your-writes routing** — send a user to the primary for a short window after they
   write (session-sticky, or a "last write timestamp" cookie).
2. **Route by query intent** — reports and analytics to replicas; anything the user just changed
   to the primary.
3. **Monitor lag** and remove a replica from rotation when it exceeds a threshold.
4. ⚠️ Don't blanket-route "all reads to replicas" and hope.

⭐ **Read replicas scale reads, not writes.** Every replica still applies **every** write, so
they don't reduce write load at all — they add to it. If writes are the bottleneck, replication
is the wrong tool; that's what sharding addresses.

**Other uses:** high availability (promote a replica on failure — with automated failover via
Patroni/Orchestrator), zero-downtime major upgrades, and geographically local reads.

⚠️ **Failover is not free** — you need fencing to avoid **split brain** (two primaries accepting
writes). Manual failover is a real outage; automatic failover is a real complexity.

---

## 3. Partitioning ⭐

**One logical table split into physical pieces, inside a single database.**

```sql
CREATE TABLE events (id BIGSERIAL, created_at TIMESTAMPTZ NOT NULL, ...)
PARTITION BY RANGE (created_at);

CREATE TABLE events_2024_01 PARTITION OF events
  FOR VALUES FROM ('2024-01-01') TO ('2024-02-01');
```

| Strategy | Use |
|---|---|
| **Range** | ⭐ time-series — logs, events, orders by month |
| **List** | discrete values — region, tenant, country |
| **Hash** | even distribution when there's no natural range key |

⭐⭐ **The two real wins:**

1. **Partition pruning** — `WHERE created_at >= '2024-06-01'` scans *one* partition instead of
   the whole table. Indexes stay small enough to sit in memory.
2. **`DROP TABLE events_2023_01` is instant.** Deleting a month of data from a 10-billion-row
   table is otherwise hours of `DELETE`, WAL, bloat, and vacuum
   ([performance.md](performance.md)). This alone justifies partitioning for retention-based
   data.

⚠️ **Partitioning is not automatic performance.** A query with no partition key filter now scans
**every** partition. And the partition key must be in the primary key / unique constraints,
which constrains your schema.

⚠️ Too many partitions (thousands) slows planning. Automate creation/retention with
`pg_partman`.

⭐ **Partitioning ≠ sharding**: partitioning is *one* database (one connection, joins and
transactions work normally); sharding is *many* databases. Partitioning buys most of the
manageability benefit at a fraction of the cost.

---

## 4. Sharding ⚠️⚠️

**Splitting data across multiple independent databases.** The only way to scale **writes**
horizontally — and the point at which you give up much of what a relational database provides.

```
   shard key = user_id
   ┌──────────┐  ┌──────────┐  ┌──────────┐
   │ Shard 1  │  │ Shard 2  │  │ Shard 3  │
   │ users    │  │ users    │  │ users    │
   │ 1-1M     │  │ 1M-2M    │  │ 2M-3M    │
   └──────────┘  └──────────┘  └──────────┘
```

| Strategy | Trade-off |
|---|---|
| **Range** (id 1–1M) | ⭐ simple, range queries work; ⚠️ **hotspots** — newest shard gets all writes |
| **Hash** (`hash(id) % N`) | ⭐ even distribution; ⚠️ **resharding rewrites everything** |
| ⭐ **Consistent hashing** | only `1/N` of keys move when adding a shard |
| **Directory/lookup** | ⭐ flexible, supports rebalancing; ⚠️ the lookup service is a SPOF |
| **Geographic / tenant** | ⭐ data residency, natural isolation; ⚠️ uneven sizes |

⭐⭐ **Choosing the shard key is the entire decision, and it's irreversible.** The right key
makes almost every query single-shard; the wrong one makes everything a scatter-gather. For a
SaaS product, `tenant_id` is usually right — one customer's data lives together, so their
queries touch one shard.

⚠️⚠️ **What you lose when you shard:**

- **Cross-shard joins** — gone. Join in the application, or denormalise.
- **Cross-shard transactions** — no ACID. Sagas and eventual consistency
  ([transactions.md §8](transactions.md)).
- **Global uniqueness / auto-increment** — needs UUIDs or a coordinator (Snowflake ids).
- **Cross-shard aggregates** (`COUNT(*)` across all users) — scatter-gather, or a
  separate analytics store.
- **Rebalancing** — moving data live, without downtime, is genuinely hard.
- **Operations** — N databases to back up, monitor, upgrade, and fail over.

⭐ **The honest answer: shard last.** Vertical scaling, read replicas, caching, and partitioning
cover most needs. Shard when a single primary can't absorb the **write** volume or the working
set no longer fits — and consider a distributed SQL database (**CockroachDB**, **YugabyteDB**,
**Vitess**, **Citus**) which handles sharding for you while keeping SQL and transactions.

---

## 5. CAP and consistency ⭐⭐

**In a distributed system, a network *partition* is inevitable. When one happens you must
choose:**

```
C — Consistency     every read sees the latest write
A — Availability    every request gets a response
P — Partition tolerance   ⭐ NOT optional in a real network
```

⭐⭐ **CAP is really "CP or AP", because P is mandatory.** "Pick two" is the popular phrasing and
it misleads — you don't get to give up partition tolerance on a real network.

| Choice | Behaviour during a partition | Examples |
|---|---|---|
| **CP** | ⭐ refuse requests rather than serve stale/divergent data | Postgres w/ sync replication, MongoDB, HBase, etcd |
| **AP** | ⭐ stay up, reconcile later (eventual consistency) | Cassandra, DynamoDB, Riak |

⭐ **PACELC is the better model, and worth naming:** *if there's a **P**artition, choose
**A** or **C**; **E**lse (normal operation), choose **L**atency or **C**onsistency.* It captures
the trade you make every day, not just during failures — a synchronous replica costs latency
even when nothing is broken.

**Consistency models:** strong · **read-your-writes** (⭐ the one users actually notice) ·
monotonic reads · **eventual**.

⭐ **BASE** (Basically Available, Soft state, Eventual consistency) is the NoSQL counterpoint to
ACID — see [nosql.md](nosql.md).

---

## 6. Other scaling levers

- ⭐ **CQRS** — separate the write model from read models/projections; the read side can be
  denormalised and independently scaled
  ([../SDLC/architecture.md](../SDLC/architecture.md)).
- ⭐ **Separate OLAP from OLTP** — ETL into a columnar warehouse so analytics stop competing
  with transactions ([normalization.md §5](normalization.md)).
- **Archive cold data** — a table where 95% of rows are never read is mostly wasted cache.
- **Queue writes** — absorb spikes with a durable queue instead of scaling for peak.
- **Right tool per workload** — Redis for sessions/counters, Elasticsearch for search, a
  time-series DB for metrics, object storage for blobs ([nosql.md](nosql.md)).

⚠️ **Storing large blobs (images, PDFs) in the database** bloats backups, buffer cache, and
replication for no benefit. Store them in object storage and keep the URL in a column.

---

## 7. Interview points

- **How would you scale a database? ⭐⭐** In order: fix queries/indexes → pool connections →
  cache → **scale vertically** → read replicas → partition → shard. Each step is far more
  complexity than the last.
- **Is vertical scaling a valid answer? ⭐** Yes — a single modern box handles far more than most
  teams assume; premature sharding is a common architectural mistake.
- **What do read replicas scale, and what don't they? ⭐⭐** Reads. Every replica applies every
  write, so they don't help write throughput at all.
- **What is replication lag, and what breaks? ⭐⭐** Replicas trail the primary — a user can fail
  to see their **own write**. Fix with read-your-writes routing to the primary after a write.
- **Sync vs async replication?** No data loss but slower commits vs fast commits with possible
  loss on failover.
- **Partitioning vs sharding? ⭐⭐** Many physical tables in **one** database (joins,
  transactions, one connection) vs data split across **many** databases.
- **Why partition? ⭐** Partition pruning keeps scans and indexes small, and dropping old data
  becomes an instant `DROP TABLE` instead of a massive `DELETE`.
- **How do you choose a shard key? ⭐⭐** So that most queries hit one shard — often `tenant_id`.
  It's effectively irreversible.
- **What do you lose by sharding?** Cross-shard joins, transactions, global uniqueness, cheap
  aggregates — plus operational multiplication.
- **Explain CAP. ⭐⭐** Under a network partition, choose consistency or availability —
  partition tolerance isn't optional. **PACELC** adds the everyday latency-vs-consistency trade.
- **What is eventual consistency, and where is it unacceptable?** Replicas converge over time —
  fine for feeds and counts, not for account balances or inventory.
- **When would you use a distributed SQL database?** When you need horizontal write scaling but
  want to keep SQL and transactions — CockroachDB, Vitess, Citus.
