# Query Performance & Tuning

> Index design: **[indexing.md](indexing.md)** · Locking: **[transactions.md](transactions.md)** ·
> ORM-level N+1: **[../Web/Django/queries.md](../Web/Django/queries.md)**

---

## 1. The diagnostic order ⭐⭐

**"The database is slow" — work in this order. The first two find most problems.**

```
1. WHICH query?          ⭐ pg_stat_statements / slow query log — don't guess
2. EXPLAIN ANALYZE it    ⭐⭐ read the plan, don't theorise
3. Missing index?        Seq Scan on a big table with a selective filter
4. Bad plan?             estimated rows ≫ actual → stale stats → ANALYZE
5. Too many queries?     ⭐ N+1 from the ORM — one query per row
6. Lock contention?      pg_stat_activity / SHOW ENGINE INNODB STATUS
7. Resource limits?      connections, memory, disk I/O
8. Only then: cache, denormalise, scale out
```

⭐ **Measure before changing anything.** The most common wasted effort is adding indexes to a
query that isn't the problem, or caching an N+1 instead of fixing it.

---

## 2. Finding the slow queries ⭐

```sql
-- Postgres: ⭐⭐ the single most useful extension
CREATE EXTENSION pg_stat_statements;

SELECT calls, mean_exec_time, total_exec_time, rows, query
FROM pg_stat_statements
ORDER BY total_exec_time DESC LIMIT 20;        -- ⭐ TOTAL, not mean
```

⭐⭐ **Sort by `total_exec_time`, not `mean_exec_time`.** A 5 ms query run 2 million times costs
far more than a 4-second report run twice a day — and it's usually easier to fix. Optimising by
"slowest single query" is the classic misdirection.

```sql
-- MySQL
SET GLOBAL slow_query_log = 'ON';
SET GLOBAL long_query_time = 1;
-- then: mysqldumpslow / pt-query-digest

-- Currently running / stuck
SELECT pid, state, wait_event_type, now() - query_start AS dur, query
FROM pg_stat_activity WHERE state != 'idle' ORDER BY dur DESC;
```

⚠️ **Watch for `idle in transaction`** — a session holding a transaction open blocks vacuum and
locks ([transactions.md §4](transactions.md)).

---

## 3. Reading `EXPLAIN ANALYZE` ⭐⭐

```sql
EXPLAIN (ANALYZE, BUFFERS) SELECT ...;   -- ⭐ ANALYZE actually RUNS it; BUFFERS shows I/O
```

```
Seq Scan on orders  (cost=0.00..18334.00 rows=1000 width=64)
                    (actual time=0.021..245.3 rows=980123 loops=1)
                     │                       │            └── ⚠️ ran 980k times?
                     │                       └── ACTUAL rows
                     └── ESTIMATED rows  ⭐ compare these two
```

**What to look for, in priority order:**

| Signal | Meaning |
|---|---|
| ⭐⭐ **estimate ≫ actual** (or vice versa) | **stale statistics** → `ANALYZE`; the planner is choosing badly |
| **`Seq Scan`** on a large table with a selective `WHERE` | ⭐ missing index |
| **`Rows Removed by Filter`** large | index isn't selective enough, or wrong column order |
| **`Nested Loop`** with high `loops=` | ⚠️ often an N+1-shaped plan; a hash join may be better |
| **`Sort`** with `external merge Disk` | ⚠️ `work_mem` too small — spilling to disk |
| **`Hash Batches > 1`** | hash join spilling — same cause |
| ⭐ **`Index Only Scan`** | ideal — covering index, no heap access |
| `Heap Fetches` high on an index-only scan | table needs vacuum ([postgres.md](postgres.md)) |

⭐ **Cost units are arbitrary and only comparable within one plan** — never say "cost 5000 is
slow." Use `ANALYZE` and read **actual time**.

⭐ **Read plans bottom-up and inside-out.** The deepest node runs first; time at a parent
*includes* its children.

**Join strategies — know when each is right:**

| Join | Good when |
|---|---|
| **Nested Loop** | ⭐ one side is tiny and the other is indexed |
| **Hash Join** | ⭐ large unsorted sets, equality condition |
| **Merge Join** | both inputs already sorted (or indexed on the key) |

⚠️ A **Nested Loop over two large tables** is the classic bad plan — usually a missing index or
a bad row estimate.

---

## 4. Query anti-patterns ⭐

```sql
-- ⚠️ Non-SARGable: function/cast on the indexed column
WHERE YEAR(created_at) = 2024
WHERE created_at >= '2024-01-01' AND created_at < '2025-01-01'      -- ⭐

-- ⚠️ Leading wildcard
WHERE name LIKE '%son'          -- full scan; use full-text / trigram

-- ⚠️ SELECT * — blocks covering indexes, ships unused bytes
SELECT id, name FROM ...        -- ⭐

-- ⚠️ Deep OFFSET: the DB scans and discards every skipped row
LIMIT 20 OFFSET 100000
WHERE id > :last_seen_id ORDER BY id LIMIT 20                        -- ⭐⭐ KEYSET pagination

-- ⚠️ NOT IN with a NULL → returns NOTHING
WHERE id NOT IN (SELECT parent_id FROM t)     -- ⚠️ parent_id may be NULL
WHERE NOT EXISTS (SELECT 1 FROM t WHERE t.parent_id = x.id)          -- ⭐

-- ⚠️ COUNT(*) on a huge table for pagination metadata
SELECT reltuples::bigint FROM pg_class WHERE relname='orders';        -- ⭐ estimate
```

⭐⭐ **Keyset (cursor) pagination is the fix for slow deep pages.** `OFFSET 100000` makes the
database produce and throw away 100,000 rows; a `WHERE id > last_seen` seek is O(1) at any
depth, and it's also **stable** when rows are inserted between requests
([../Web/Django/drf.md](../Web/Django/drf.md)).

⚠️ **The `COUNT(*)` in a paginated API response is often the slowest part of the endpoint** —
cache it, estimate it, or drop it.

---

## 5. The N+1 problem ⭐⭐

```python
for order in orders:            # 1 query
    print(order.customer.name)  # ⚠️ +1 query PER ROW → 1001 queries
```

⭐ **This is an *application* problem visible only in the database** — each individual query is
fast, so `pg_stat_statements` shows a trivial query with a huge `calls` count. That pattern (low
`mean_exec_time`, enormous `calls`) is the signature.

**Fixes:** eager loading (`select_related`/`prefetch_related`, `JOIN FETCH`), a single query
with a join, or `WHERE id IN (...)` batching. Full treatment in
[../Web/Django/queries.md](../Web/Django/queries.md).

⚠️ **Caching an N+1 hides it until the cache is cold**, at which point the stampede takes the
database down.

---

## 6. Bulk operations ⭐

```sql
-- ⚠️ one statement per row: 10,000 round trips
INSERT INTO t (a,b) VALUES (1,2);   -- ×10000

-- ⭐ one statement
INSERT INTO t (a,b) VALUES (1,2), (3,4), ...;

-- ⭐⭐ fastest bulk load by far
COPY t (a,b) FROM STDIN;            -- Postgres  (LOAD DATA INFILE in MySQL)
```

⭐ **`COPY` is often 10–100× faster than `INSERT`** — it bypasses per-statement parsing and
planning. For a big load, also consider dropping indexes, loading, then rebuilding them.

⚠️⚠️ **Batch large `DELETE`/`UPDATE`s.** A single statement touching 10 million rows holds locks
for its whole duration, generates enormous WAL, and can stall replication:

```sql
DELETE FROM logs WHERE id IN (
  SELECT id FROM logs WHERE created_at < now() - interval '90 days' LIMIT 10000
);                                   -- ⭐ loop this, committing each batch
```

⭐ For time-based purging, **partitioning turns a 10-million-row `DELETE` into an instant
`DROP TABLE`** ([scaling.md](scaling.md)).

---

## 7. Connections & memory ⭐

⚠️⚠️ **Connections are the resource that actually runs out first** — long before CPU. Each
Postgres connection is a **process** with its own memory; a few hundred idle connections can
consume gigabytes and thrash the scheduler.

```
web workers × app instances × pool size  →  ⚠️ easily exceeds max_connections
```

⭐ **Use a pooler.** **PgBouncer** in *transaction* mode lets 1,000 client connections share 20
server connections, because most are idle between statements. This is the standard fix for
"too many connections" and it usually improves throughput too.

⚠️ In transaction pooling, session-level features break — prepared statements, `SET`,
advisory locks, `LISTEN/NOTIFY`. And set your ORM's persistent-connection setting to 0
(`CONN_MAX_AGE = 0` in Django) or it defeats the pooler.

**Key memory settings (Postgres):**

| Setting | Guidance |
|---|---|
| `shared_buffers` | ⭐ ~25% of RAM |
| `effective_cache_size` | ~50–75% of RAM — a *hint* to the planner, not an allocation |
| `work_mem` | ⚠️ **per sort/hash node, per connection** — 100 connections × 3 sorts × 64 MB = 19 GB |
| `maintenance_work_mem` | larger — for VACUUM and index builds |

⭐ **`work_mem` is the setting people get badly wrong**: it's not global. Raise it per-session
for a known heavy query rather than globally.

---

## 8. Caching layers ⭐

```
Application cache (Redis)  →  DB buffer cache (shared_buffers)  →  OS page cache  →  disk
```

⭐ **The database already caches aggressively.** A "slow query" that reads from `shared_buffers`
is a CPU/plan problem, not an I/O problem — `EXPLAIN (ANALYZE, BUFFERS)` distinguishes
`shared hit` (cached) from `read` (disk).

⭐ **Materialised views** for expensive recurring aggregates; **summary tables** updated
incrementally for dashboards ([normalization.md](normalization.md)). Application caching:
[../Web/Django/caching.md](../Web/Django/caching.md).

---

## 9. Maintenance ⭐

```sql
ANALYZE orders;                    -- ⭐ refresh planner statistics
VACUUM (VERBOSE, ANALYZE) orders;  -- reclaim dead tuples
REINDEX INDEX CONCURRENTLY idx;    -- rebuild a bloated index

-- table/index sizes
SELECT relname, pg_size_pretty(pg_total_relation_size(relid))
FROM pg_stat_user_tables ORDER BY pg_total_relation_size(relid) DESC LIMIT 10;
```

⚠️ **Autovacuum keeping up is a health metric.** On a high-churn table, tune
`autovacuum_vacuum_scale_factor` down so it runs more often — otherwise bloat grows until
performance falls off a cliff.

⭐ **Alert on:** slow-query count, cache hit ratio (<99% on OLTP is suspicious), connection
count, replication lag, deadlocks/sec, autovacuum lag, and disk usage.

---

## 10. Interview points

- **"The database is slow" — walk me through it. ⭐⭐** Identify *which* query
  (`pg_stat_statements` by **total** time), `EXPLAIN ANALYZE` it, check for a missing index or
  bad row estimate, look for N+1 and lock contention — cache last.
- **Why sort by total time, not mean? ⭐** A 5 ms query run millions of times costs more than a
  rare slow report.
- **What do you look for in a plan? ⭐⭐** Estimated vs actual rows (stale stats), `Seq Scan` on a
  large selective query, rows removed by filter, sorts spilling to disk.
- **Are cost numbers meaningful?** Only relative to each other within one plan — use actual
  time.
- **Nested loop vs hash vs merge join?** Small indexed side · large unsorted equality ·
  pre-sorted inputs.
- **Why is `OFFSET 100000` slow, and the fix? ⭐⭐** The DB generates and discards every skipped
  row; use keyset pagination (`WHERE id > last_seen`).
- **What is N+1, and how does it look in DB metrics? ⭐** One query per row; a trivial query with
  an enormous `calls` count.
- **How do you delete 10 million rows safely? ⭐** In batches with commits — or partition and
  `DROP` the partition.
- **What runs out before CPU? ⭐⭐** **Connections** — each is a process; use PgBouncer in
  transaction mode.
- **What's the catch with transaction pooling?** Session features break — prepared statements,
  `SET`, advisory locks — and app-side persistent connections must be disabled.
- **What is `work_mem` and the common mistake?** Memory **per sort/hash node per connection** —
  raising it globally can exhaust RAM.
- **When would you add a materialised view?** Expensive recurring aggregates where slight
  staleness is acceptable.
