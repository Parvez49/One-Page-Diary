# Database — Interview Questions

> Claim first, then the *why*. Depth lives in the linked files.

---

## 1. Fundamentals

**DBMS vs RDBMS vs SQL?**
Storage/management software · adds the **relational model** (tables, keys, referential
integrity) and ACID · the *language* (MySQL/Postgres are products implementing it).

**`DELETE` vs `TRUNCATE` vs `DROP`? ⭐**
Row-level DML (rollback-able, fires triggers, `WHERE`) · fast DDL removing all rows and
resetting identity · removes the table entirely.

**Surrogate vs natural key? ⭐⭐**
Natural keys carry meaning but **change** — and a changing PK cascades everywhere. Use a
**surrogate PK plus a `UNIQUE` constraint on the natural key**: stability *and* the business
rule.

**UUID or auto-increment? ⭐**
UUIDs are distributed and opaque but 16 bytes and **random**, which fragments indexes —
severely in MySQL where the PK is clustered. **UUIDv7** (time-ordered) is the modern
compromise.

**Why enforce constraints in the database? ⭐⭐**
Application validation is bypassed by migrations, bulk imports, admin tools, and other
services. The database is the only guarantee that's always enforced.
→ [fundamentals.md](fundamentals.md)

**What's special about `NULL`? ⭐**
It means *unknown*: `NULL = NULL` is unknown, aggregates skip it, and **`NOT IN` with a NULL
returns no rows at all**.

---

## 2. Design

**What does normalisation prevent? ⭐⭐**
The **insertion, update, and deletion anomalies** — not merely "duplication". 1NF→3NF in one
line: every non-key column depends on *the key, the whole key, and nothing but the key*.

**How far do you normalise?**
⭐ **3NF for OLTP**, then denormalise deliberately with evidence.

**When would you denormalise? ⭐⭐**
After indexing and caching have failed on a *specific measured* query — and knowing you now own
keeping the duplicate consistent. Prefer a materialised view or trigger so the **database** owns
the invariant.

**Is storing `unit_price` on an order line denormalisation? ⭐**
No — the price *paid* is a different fact from the *current* price. It's a point-in-time
snapshot, and deriving it later would rewrite history.

**Normalised or denormalised — which is right?**
Neither: **OLTP normalised, OLAP denormalised** (star schema, columnar storage), with ETL
between them.
→ [normalization.md](normalization.md)

---

## 3. SQL

**What's the logical execution order? ⭐⭐**
`FROM → WHERE → GROUP BY → HAVING → SELECT → ORDER BY → LIMIT` — which is why a `SELECT` alias
isn't available in `WHERE`.

**`WHERE` vs `HAVING`?**
Rows before grouping vs groups after aggregation. Filter early in `WHERE`.

**Why did my `LEFT JOIN` lose the unmatched rows? ⭐⭐**
A `WHERE` condition on the right table converts it to an inner join — move the condition into
`ON`.

**`RANK` vs `DENSE_RANK` vs `ROW_NUMBER`? ⭐**
Ties share a rank with a **gap** · ties share a rank with **no gap** · always unique.

**How do you get the top N per group? ⭐**
`ROW_NUMBER() OVER (PARTITION BY ... ORDER BY ...)` in a subquery, filtered outside — window
functions run *after* `WHERE`, so you can't filter one there.

**`UNION` vs `UNION ALL`?**
Dedup (needs a sort) vs raw concatenation — use `ALL` unless you need deduplication.

**Why is `WHERE YEAR(created_at) = 2024` slow? ⭐**
Non-SARGable — the function prevents index use. Rewrite as a range.
→ [sql.md](sql.md)

---

## 4. Indexing

**What is an index and what does it cost? ⭐⭐**
A sorted structure for fast lookups — paid for with **slower writes** (every index updated per
DML) and disk space.

**Why B+trees and not binary trees? ⭐⭐**
Disk I/O is page-based; high fan-out keeps the tree **3–4 levels deep for billions of rows**,
and linked leaves make range scans fast. A binary tree would be ~30 random I/Os.

**Explain the leftmost prefix rule. ⭐⭐**
An index on `(a, b, c)` serves `a`, `(a,b)`, `(a,b,c)` — **never `b` alone**. Like a phone book
sorted by (last, first): useless for finding everyone named "Sara".

**How do you order composite index columns?**
Equality columns → the range column → sort columns. After a range predicate, later columns can
only filter, not seek.

**What's a covering index? ⭐**
One containing every column the query needs → an **index-only scan**, no table access. (Another
reason to avoid `SELECT *`.)

**I added an index and nothing improved. Why? ⭐⭐**
Function/cast on the column, leading wildcard, type mismatch, **low selectivity**, small table,
or stale statistics.

**When is a sequential scan correct? ⭐**
When the predicate matches a large fraction of rows — random I/O per row costs more than
streaming pages. The planner is often right.

**Does Postgres index foreign keys automatically? ⭐**
**No** (MySQL does) — a common cause of slow parent deletes and reverse joins.
→ [indexing.md](indexing.md)

---

## 5. Transactions

**Explain ACID. ⭐⭐**
Atomicity (all or nothing) · Consistency (**your** constraints) · Isolation (MVCC/locks) ·
Durability (⭐ **WAL fsynced before commit returns**).

**Name the concurrency anomalies. ⭐⭐**
Dirty read · non-repeatable read · phantom read · lost update · **write skew**.

**Non-repeatable vs phantom read?**
An existing row **changed** vs the **set** of matching rows changed.

**What is write skew? ⭐**
Two individually-valid transactions together break an invariant — the on-call doctors example.
Only **Serializable** prevents it.

**Isolation levels and defaults?**
Read Uncommitted → Read Committed → Repeatable Read → Serializable.
⭐ **Postgres defaults to Read Committed; MySQL to Repeatable Read.**

**What is MVCC and why does it matter? ⭐⭐**
Writers create **new row versions** instead of overwriting, so **readers never block writers and
writers never block readers**. Only writer-vs-writer on the same row conflicts.

**What does MVCC cost? ⭐**
Cleanup: **VACUUM** in Postgres (old versions live in the table) vs undo logs in InnoDB.
⚠️ A long-running or `idle in transaction` session blocks vacuum and bloats the table.

**Optimistic vs pessimistic locking? ⭐⭐**
`SELECT ... FOR UPDATE` upfront (contention, deadlock risk) vs a **version column** checked at
write time (retry on conflict). ⭐ Often best: a single atomic
`UPDATE ... SET stock = stock - 1 WHERE stock > 0`.

**How do you prevent overselling the last item? ⭐**
Row lock, or an atomic conditional `UPDATE` plus a `CHECK (stock >= 0)` constraint.

**What causes deadlocks and how do you prevent them? ⭐⭐**
Circular lock waits. **Acquire locks in a consistent order**, keep transactions short, set
`lock_timeout` — and **retry**, because deadlocks are expected under load.

**Why must transactions be short? ⭐**
Locks are held until commit, and open transactions block vacuum. **Never make an HTTP call
inside one.**

**How do you build a job queue in SQL?**
`SELECT ... FOR UPDATE SKIP LOCKED`.

**Transactions across microservices? ⭐**
Don't — use **sagas with compensating actions** and the **outbox pattern**, with idempotent
operations. 2PC is blocking and rarely used.
→ [transactions.md](transactions.md)

---

## 6. Performance

**"The database is slow" — walk me through it. ⭐⭐**
Find *which* query (`pg_stat_statements` sorted by **total** time, not mean) → `EXPLAIN ANALYZE`
→ missing index or bad row estimate → N+1 → lock contention → resources. **Cache last.**

**What do you look for in a plan? ⭐**
Estimated vs actual rows (stale stats → `ANALYZE`), `Seq Scan` on a large selective query, rows
removed by filter, sorts spilling to disk.

**Are `cost` numbers meaningful?**
Only relative to each other within one plan — use actual time.

**Why is `OFFSET 100000` slow, and the fix? ⭐⭐**
The database generates and discards every skipped row. Use **keyset pagination**
(`WHERE id > :last_seen`) — O(1) at any depth and stable under inserts.

**What is N+1, and how does it look in DB metrics? ⭐**
One query per row from lazy relations; in `pg_stat_statements` it's a trivial query with an
enormous `calls` count.

**How do you delete 10 million rows safely? ⭐**
In batches with commits — or **partition** and `DROP` the partition instantly.

**What runs out before CPU? ⭐⭐**
**Connections** — each Postgres connection is a process. Use **PgBouncer** in transaction mode.

**What's the catch with transaction pooling?**
Session features break (prepared statements, `SET`, advisory locks) and app-side persistent
connections must be disabled.
→ [performance.md](performance.md)

---

## 7. Scaling

**How would you scale a database? ⭐⭐**
Queries/indexes → pooling → caching → **vertical scaling** → read replicas → partitioning →
sharding. Each step is an order of magnitude more complexity.

**Is "buy a bigger box" a valid answer? ⭐**
Yes — a single modern Postgres instance handles far more than most teams assume. Premature
sharding is a common architectural mistake.

**What do read replicas scale? ⭐⭐**
**Reads only.** Every replica applies every write, so they don't help write throughput.

**What is replication lag and what breaks? ⭐⭐**
Replicas trail the primary, so a user can fail to see **their own write**. Fix with
read-your-writes routing to the primary after a write.

**Partitioning vs sharding? ⭐⭐**
Many physical tables in **one** database (joins, transactions, one connection) vs data split
across **many** databases.

**Why partition? ⭐**
Partition pruning keeps scans and indexes small, and dropping old data becomes an instant
`DROP TABLE`.

**How do you choose a shard key? ⭐⭐**
So most queries hit **one** shard — often `tenant_id`. It's effectively irreversible.

**What do you lose by sharding?**
Cross-shard joins, transactions, global uniqueness, cheap aggregates — plus N databases to
operate.

**Explain CAP. ⭐⭐**
Under a network **partition**, choose consistency or availability — P isn't optional. ⭐
**PACELC** adds the everyday trade: *else*, choose latency or consistency.
→ [scaling.md](scaling.md)

---

## 8. NoSQL & search

**SQL or NoSQL — how do you choose? ⭐⭐**
Default to Postgres (relational + JSONB + full-text + GIS + ACID). Choose a specialised store
for an access pattern it serves dramatically better — Redis for sub-ms lookups, Cassandra for
write volume, Elasticsearch for relevance, Neo4j for deep traversal.

**Is NoSQL schemaless? ⭐**
No — the schema moves into application code, and multiple versions coexist unvalidated in
production.

**Embed or reference in MongoDB? ⭐⭐**
Embed bounded data read together; reference shared or **unbounded** data — an unbounded embedded
array eventually hits the 16 MB document limit.

**Why is Redis fast, and what's the constraint?**
In-memory, mostly single-threaded — ⚠️ one slow command blocks all others (**never `KEYS *`**),
and the dataset must fit in RAM.

**When do you need Elasticsearch over Postgres full-text? ⭐**
When you need **relevance ranking**, stemming, typo tolerance, and faceted aggregations at
scale. ⚠️ Never as the source of truth.

**`text` vs `keyword` in Elasticsearch? ⭐**
Analysed for full-text vs stored whole for exact match, filtering, sorting, and aggregations.

**How do you keep Postgres and Elasticsearch in sync? ⭐⭐**
Outbox or CDC from the source of truth — **never dual writes** — and keep a full reindex
possible.
→ [nosql.md](nosql.md) · [elasticsearch.md](elasticsearch.md)

---

## 9. Rapid fire

| Question | Answer |
|---|---|
| `COUNT(*)` vs `COUNT(col)` | All rows vs non-NULL values only. |
| `IN` vs `EXISTS` | `EXISTS` short-circuits and is NULL-safe; `NOT IN` with NULL returns nothing. |
| Clustered index in Postgres? | ⭐ None — heap storage. InnoDB clusters on the PK. |
| Why does a wide PK hurt in MySQL? | Every secondary index stores the PK value. |
| `utf8` vs `utf8mb4` in MySQL ⭐ | `utf8` is 3-byte — **cannot store emoji**. |
| Transactional DDL? | ⭐ Postgres yes, MySQL no. |
| `mysqldump --single-transaction` | Consistent InnoDB snapshot **without locking tables**. |
| Most important MySQL setting | `innodb_buffer_pool_size` ≈ 70–80% of RAM. |
| `work_mem` mistake ⭐ | It's **per sort node per connection**, not global. |
| SSD config win ⭐ | `random_page_cost = 1.1` — the default assumes spinning disks. |
| Adding an index without downtime | `CREATE INDEX CONCURRENTLY` (PG) / online DDL (MySQL). |
| Finding useless indexes | `pg_stat_user_indexes` where `idx_scan = 0`. |
| View vs materialised view | Recomputed query vs stored (stale) result. |
| Money column type ⭐ | `NUMERIC`/`DECIMAL` — **never `FLOAT`**. |
| Storing images in the DB | ⚠️ Don't — object storage + a URL column. |
| Backup that isn't a backup | ⭐ An untested one. Run restore drills. |

---

## 10. The five to have ready

1. **Indexing** — B+tree fan-out, leftmost prefix, and why an index sometimes isn't used.
2. **ACID + isolation levels** — with the anomalies each one prevents.
3. **MVCC** — readers don't block writers, and what VACUUM is for.
4. **Diagnosing a slow query** — `pg_stat_statements` → `EXPLAIN ANALYZE` → index → N+1.
5. **The scaling ladder** — and why vertical scaling and read replicas come long before
   sharding.
