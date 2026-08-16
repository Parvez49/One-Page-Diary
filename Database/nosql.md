# NoSQL

> CAP & distribution: **[scaling.md §5](scaling.md)** · Search engine: **[elasticsearch.md](elasticsearch.md)**

---

## 1. What NoSQL actually means ⭐

**"Not only SQL"** — non-relational stores that trade fixed schemas and joins for **horizontal
scalability, flexible data models, and specific access patterns**.

⭐ **The honest framing: NoSQL isn't "newer SQL", it's a different set of trade-offs.** You give
up joins, referential integrity, and (often) multi-record ACID to get easy sharding and a data
model shaped like your access pattern. That's a *choice*, not an upgrade.

| Type | Model | Examples | Best for |
|---|---|---|---|
| **Document** | JSON-like documents | ⭐ MongoDB, Couchbase, DynamoDB | content, catalogues, evolving schemas |
| **Key–value** | key → blob | ⭐ **Redis**, Memcached, DynamoDB | cache, sessions, counters, rate limits |
| **Wide-column** | rows with dynamic columns | ⭐ Cassandra, HBase, ScyllaDB | huge write volume, time-series |
| **Graph** | nodes + edges | ⭐ Neo4j, Neptune | social graphs, recommendations, fraud rings |
| **Search** | inverted index | ⭐ Elasticsearch, OpenSearch | full-text, faceted search, log analytics |
| **Time-series** | timestamped metrics | InfluxDB, TimescaleDB, Prometheus | monitoring, IoT |

---

## 2. SQL vs NoSQL ⭐⭐

| | **Relational** | **NoSQL** |
|---|---|---|
| Schema | ⭐ enforced, migrations | ⚠️ flexible — **the schema moves into your application** |
| Joins | ⭐ native, optimised | ⚠️ application-side or denormalised |
| Transactions | ⭐ ACID across tables | often single-document only |
| Scaling | vertical + read replicas; ⚠️ sharding is hard | ⭐ **horizontal by design** |
| Consistency | ⭐ strong | often eventual (tunable) |
| Query | ⭐ declarative SQL, ad-hoc | ⚠️ shaped by the access pattern you designed for |

⭐⭐ **"Schemaless" is a misconception worth correcting out loud.** The schema still exists —
it's just enforced by application code instead of the database, and different versions of it
coexist in the same collection. That's genuinely useful during rapid iteration and genuinely
painful three years later when six document shapes are in production and nothing validates them.

⭐ **Modern convergence blurs the line:** Postgres has `JSONB` with GIN indexes (a competent
document store), MongoDB added multi-document ACID transactions, and distributed SQL
(CockroachDB, Vitess) scales horizontally. "SQL can't scale / NoSQL can't do transactions" is
outdated on both sides.

⭐⭐ **The decision rule to state:**

> *"Default to Postgres. It handles relational data, JSON documents, full-text search, and
> geospatial queries competently, and it gives you ACID and ad-hoc queries for free. Reach for a
> specialised store when you have a specific access pattern it serves dramatically better —
> Redis for sub-millisecond key lookups, Cassandra for enormous write throughput, Elasticsearch
> for relevance-ranked search, Neo4j for deep graph traversal."*

---

## 3. Document stores — MongoDB ⭐

```json
{
  "_id": "123",
  "name": "Parvez",
  "orders": [                          // ⭐ EMBEDDED — one read gets everything
    { "id": 1, "amount": 500 },
    { "id": 2, "amount": 900 }
  ],
  "user_id": 1                         // ⚠️ looks like an FK — Mongo does NOT enforce it
}
```

⭐⭐ **Embed vs reference is *the* MongoDB design decision:**

| Embed when | Reference when |
|---|---|
| ⭐ data is read together | ⭐ data is read independently |
| the child doesn't exist alone (order lines) | the child is shared (users, products) |
| the array is **bounded** | ⚠️ unbounded growth (comments, events) |
| updates are infrequent | the child changes often and is duplicated widely |

⚠️⚠️ **The unbounded-array trap:** embedding comments in a post works until a post has 50,000
comments and hits the **16 MB document limit** — and every read of the post transfers the whole
array. Reference anything that grows without limit.

⚠️ **No foreign keys means no referential integrity.** An order can reference a deleted user and
nothing complains. Your application owns every invariant the database used to enforce.

**Modelling:** design around your **queries**, not your entities — the opposite instinct to
normalisation. Duplication is normal and expected; you pay for it on writes.

⭐ **When MongoDB is the wrong choice:** strong relationships between entities, multi-entity
transactional invariants, and ad-hoc analytical queries. If "an order must always belong to a
valid user" is a business rule you can't violate, a relational database enforces it and Mongo
doesn't.

---

## 4. Key–value — Redis ⭐

**In-memory, single-threaded, sub-millisecond.** More a data-structure server than a plain
key–value store.

```
STRING   SET user:123 '{"name":"P"}'  EX 3600   ⭐ cache with TTL
HASH     HSET user:123 name P age 25              partial updates
LIST     LPUSH queue job1                         simple queue
SET      SADD online:users 123                    ⭐ unique membership
ZSET     ZADD leaderboard 500 user:123            ⭐⭐ sorted set — leaderboards, rate limits
BITMAP   SETBIT active:2024-01-15 123 1           daily-active users, cheaply
HLL      PFADD visitors user123                   ⭐ approximate unique counts, 12 KB
STREAM   XADD events * type click                 append-only log with consumer groups
```

⭐ **Use for:** caching, sessions, rate limiting (`INCR` + `EXPIRE`), leaderboards, distributed
locks, pub/sub, queues, and real-time counters.

⚠️⚠️ **Redis is memory-bound and mostly single-threaded.** Consequences: one slow command blocks
everything (⚠️ **never run `KEYS *` in production** — use `SCAN`), and your dataset must fit in
RAM plus room for the fork during persistence.

⚠️ **Persistence is optional and not free.** RDB snapshots lose everything since the last
snapshot; AOF is durable but slower. ⭐ **Redis-as-a-cache and Redis-as-a-database are different
configurations** — using an ephemeral cache as a task broker means silently losing jobs
([../Web/Django/async_tasks.md](../Web/Django/async_tasks.md)).

⭐ **Set an eviction policy** (`allkeys-lru`) for cache use, or writes fail when memory fills.

---

## 5. Wide-column — Cassandra ⭐

**Built for enormous write throughput and multi-datacenter availability.** No single primary —
every node accepts writes.

⭐⭐ **Cassandra's defining rule: you design tables *per query*.** There are no joins and no
ad-hoc queries; the partition key determines which node holds the data, and you cannot filter
efficiently on anything else. It's normal to store the same data in three tables shaped for
three queries.

```
PRIMARY KEY ((user_id), created_at)    ⭐ partition key + clustering key
             └ which node             └ sort order within the partition
```

⚠️ **Bad partition keys are the failure mode**: a low-cardinality key creates hotspots, and an
unbounded partition (all events for one user, forever) becomes a multi-GB row.

⭐ **Tunable consistency** — per query: `ONE`, `QUORUM`, `ALL`. `R + W > N` gives strong
consistency; lower values give speed. That dial is the practical expression of CAP
([scaling.md §5](scaling.md)).

⚠️ **Deletes create tombstones**, and heavy delete workloads degrade reads badly. Cassandra
suits append-mostly data.

---

## 6. Graph — Neo4j ⭐

**Nodes, relationships, and properties — relationships are first-class, stored as pointers.**

```cypher
MATCH (u:User)-[:FRIEND*2..3]->(f:User)     -- ⭐ friends-of-friends, 2-3 hops
WHERE u.id = 123 RETURN f
```

⭐⭐ **The argument for a graph database is *depth*.** A 2-hop query is a manageable SQL
self-join; a **variable-depth traversal** ("everyone connected to X within 6 hops", shortest
path, fraud-ring detection) is exponentially expensive in SQL and near-linear in a graph store,
because traversal follows physical pointers rather than performing an index lookup per hop.

⚠️ Graph databases are weaker at aggregate/analytical queries and add another system to operate.
For 1–2 hop relationships, a relational join is fine — recursive CTEs cover a lot
([sql.md](sql.md)).

---

## 7. Polyglot persistence & operations ⭐

⭐ **Using several stores for their strengths is normal at scale** — Postgres for
transactional truth, Redis for cache/sessions, Elasticsearch for search, S3 for blobs, a
warehouse for analytics.

⚠️⚠️ **Every extra datastore is a *synchronisation* problem**, not just an operational one:
data in Postgres and Elasticsearch will diverge, and you need CDC/outbox to keep them aligned
([transactions.md §8](transactions.md)). Two stores mean dual writes, dual failures, and
reconciliation jobs. Add one only when the benefit is decisive.

⭐ **The system of record must be unambiguous.** Derived stores (search index, cache, warehouse)
must be rebuildable from it.

**Backups — the point people forget:** MongoDB `mongodump`/`mongorestore`, Redis RDB/AOF files,
Cassandra snapshots. ⚠️ **An untested backup is not a backup** — schedule restore drills, and
verify that a NoSQL backup is *consistent* (a `mongodump` without `--oplog` on a live replica set
can capture a torn state).

---

## 8. Interview points

- **What does NoSQL mean, and what are the categories? ⭐** "Not only SQL" — document,
  key–value, wide-column, graph, search, time-series.
- **SQL or NoSQL — how do you choose? ⭐⭐** Default to Postgres for its versatility and ACID;
  choose a specialised store for a specific access pattern it serves dramatically better.
- **Is NoSQL schemaless? ⭐** No — the schema moves into application code, and multiple versions
  coexist in production without validation.
- **When is MongoDB a bad fit? ⭐** Strong relationships, multi-entity transactional invariants,
  and ad-hoc analytics — it won't enforce that an order belongs to a valid user.
- **Embed or reference in MongoDB? ⭐⭐** Embed bounded data read together; reference shared or
  unbounded data — an unbounded embedded array eventually hits the 16 MB limit.
- **Why is Redis fast, and what's the constraint?** In-memory and mostly single-threaded —
  ⚠️ one slow command blocks all others (never `KEYS *`), and the dataset must fit in RAM.
- **Cache vs broker in Redis?** Different durability configurations — an ephemeral cache used as
  a queue silently loses messages.
- **Why does Cassandra scale writes so well? ⭐** No single primary — every node accepts writes,
  and you design a table per query with a partition key that spreads load.
- **What's tunable consistency?** Per-query `ONE`/`QUORUM`/`ALL` — `R + W > N` gives strong
  consistency; the practical CAP dial.
- **When is a graph database genuinely better? ⭐** Deep or variable-depth traversals — 1–2 hops
  are fine in SQL, but 4+ hops and shortest-path are near-linear in a graph store.
- **What's the cost of polyglot persistence? ⭐⭐** Keeping stores in sync — dual writes, CDC,
  divergence, reconciliation — not just operating more systems.
- **How do you keep Postgres and Elasticsearch consistent?** Outbox/CDC from the system of
  record, with the index rebuildable from scratch.
