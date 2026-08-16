# Indexing

> Reading query plans: **[performance.md](performance.md)** · B-tree structure:
> **[../Algorithm/Tree/trees.md](../Algorithm/Tree/trees.md)**

---

## 1. What an index is ⭐⭐

**A separate, sorted data structure that maps column values to row locations** — so the database
can find rows without scanning the table.

```
Without index:  SELECT * FROM users WHERE email = 'x'   →  ⚠️ Seq Scan, 10M rows
With index:     B-tree lookup                            →  ⭐ ~3-4 page reads
```

**Why a B+tree and not a binary tree** — the answer that separates memorised from understood:

> Disk (and SSD) I/O happens in **pages**, typically 8 KB. A B+tree node holds *hundreds* of
> keys, so the fan-out is huge and the tree stays **3–4 levels deep even for billions of rows**.
> A binary tree of a billion rows is 30 levels — 30 random I/Os instead of 3. The structure is
> shaped by the storage medium, not by comparison count.

```
                  [ 50 | 100 ]                     ← root (cached in memory)
                 /      |      \
       [10|30]      [60|80]      [120|150]         ← internal: keys only
      /   |   \    /   |   \    /    |    \
   leaf─leaf─leaf─leaf─leaf─leaf─leaf─leaf─leaf    ⭐ leaves hold data/pointers
     └────────── linked list ──────────┘           ⭐ makes RANGE SCANS fast
```

⭐ **In a B+tree only the leaves hold data, and they're linked** — that's what makes
`WHERE created_at BETWEEN a AND b` and `ORDER BY` efficient: find the start, then walk the leaf
chain sequentially.

**The trade — always state it:**

| Indexes give | Indexes cost |
|---|---|
| ⭐ fast reads (lookup, range, sort, join) | ⚠️ **slower writes** — every INSERT/UPDATE/DELETE updates every affected index |
| unique constraint enforcement | ⚠️ disk space (often comparable to the table) |
| ⭐ can satisfy a query without touching the table | ⚠️ more for the planner to consider |

⚠️⚠️ **"Just add an index" is not free.** A table with 12 indexes has 12× the write
amplification. The right answer is always *"index what you filter, join, and sort by — and
remove the ones nothing uses."*

---

## 2. Index types ⭐

| Type | Good for | Note |
|---|---|---|
| **B-tree** | ⭐ equality, ranges, sorting, prefix `LIKE 'abc%'` | the default; ~99% of cases |
| **Hash** | equality only | ⚠️ no ranges, no sorting — rarely worth it |
| **GIN** | ⭐ full-text, `JSONB`, arrays | "does this document contain X" |
| **GiST** | geometry, ranges, nearest-neighbour | PostGIS |
| **BRIN** | ⭐ huge, naturally-ordered tables (time-series logs) | tiny index, block-range summaries |
| **Bitmap** | low-cardinality columns in OLAP | Postgres builds these on the fly |
| **Full-text** | ⭐ `tsvector` + GIN, or Elasticsearch | see [elasticsearch.md](elasticsearch.md) |

⭐ **Clustered vs non-clustered** — a frequent question, and the answer differs by engine:

| | **Clustered** | **Non-clustered (secondary)** |
|---|---|---|
| What it is | ⭐ the **table itself is stored in index order** | a separate structure pointing at rows |
| Count | one per table | many |
| MySQL/InnoDB | ⭐⭐ **the PK is always clustered** | leaves store the **PK**, not a row pointer |
| Postgres | ⚠️ **no clustered indexes** — heap storage; `CLUSTER` is a one-off reorder | leaves store a tuple id (`ctid`) |

⭐⭐ **The InnoDB consequence:** a secondary index lookup does **two** traversals — find the PK
in the secondary index, then find the row in the clustered PK index. This is why **a wide
primary key (a 36-char UUID string) bloats every secondary index** in MySQL, and why sequential
PKs matter more there than in Postgres.

---

## 3. Composite indexes & the leftmost prefix rule ⭐⭐

```sql
CREATE INDEX idx_orders ON orders (customer_id, status, created_at);
```

**This one index serves:**

| Query | Uses index? |
|---|---|
| `WHERE customer_id = 1` | ⭐ yes |
| `WHERE customer_id = 1 AND status = 'paid'` | ⭐ yes |
| `WHERE customer_id = 1 AND status = 'paid' ORDER BY created_at` | ⭐⭐ yes — **including the sort** |
| `WHERE status = 'paid'` | ⚠️ **no** — skips the leftmost column |
| `WHERE customer_id = 1 AND created_at > x` | ⭐ partially — uses `customer_id`, then filters |

⭐⭐ **The leftmost prefix rule:** an index on `(a, b, c)` can serve `a`, `(a,b)`, and `(a,b,c)` —
never `b` alone or `(b,c)`. Think of a phone book sorted by *(last name, first name)*: useless
for finding everyone named "Sara".

**Column order matters. The rule of thumb:**

```
1. Equality columns first     (a = ?, b = ?)
2. Then the range column      (c > ?)      ⭐ only ONE range benefits
3. Then sort columns          ORDER BY d
```

⚠️ **After a range predicate, later index columns can't be used for seeking** — only for
filtering. `WHERE a = 1 AND b > 5 AND c = 3` on `(a,b,c)` seeks on `a,b` and then filters `c`.
Put the equality columns first.

⭐ **One well-ordered composite index usually beats three single-column indexes.** Postgres can
combine separate indexes with a bitmap scan, but it's slower than a single seek — and each extra
index costs writes.

---

## 4. Covering indexes ⭐

```sql
CREATE INDEX idx_cover ON orders (customer_id) INCLUDE (status, total);   -- Postgres 11+
-- or simply:  CREATE INDEX ON orders (customer_id, status, total);
```

⭐⭐ **If the index contains every column the query needs, the database never reads the table** —
an **index-only scan**. On a wide table this can be an order of magnitude faster, because you
read a narrow index instead of full rows.

```sql
SELECT status, total FROM orders WHERE customer_id = 7;   -- ⭐ index-only scan
SELECT * FROM orders WHERE customer_id = 7;               -- ⚠️ must fetch the heap rows
```

⭐ **This is a concrete reason to avoid `SELECT *`** — it makes covering indexes impossible.

⚠️ In Postgres, an index-only scan still consults the **visibility map**; a table that hasn't
been vacuumed recently forces heap fetches anyway ([postgres.md](postgres.md)).

---

## 5. When indexes are *not* used ⚠️⚠️

**The most practically valuable section here — "I added an index and nothing changed."**

```sql
-- 1. Function on the column → not SARGable
WHERE YEAR(created_at) = 2024                 -- ⚠️ index unusable
WHERE created_at >= '2024-01-01' AND created_at < '2025-01-01'   -- ⭐

WHERE LOWER(email) = 'a@b.com'                -- ⚠️
CREATE INDEX ON users (LOWER(email));         -- ⭐ expression index fixes it

-- 2. Leading wildcard
WHERE name LIKE '%son'                        -- ⚠️ full scan
WHERE name LIKE 'John%'                       -- ⭐ prefix — index range scan

-- 3. Type mismatch / implicit cast
WHERE phone = 1234567                         -- ⚠️ phone is VARCHAR → cast → no index

-- 4. OR across different columns
WHERE a = 1 OR b = 2                          -- ⚠️ often a scan; UNION of two seeks may win

-- 5. Low selectivity
WHERE is_active = true                        -- ⚠️ matches 95% of rows → scan is CHEAPER

-- 6. Small table
                                              -- ⭐ a seq scan of 500 rows beats index overhead

-- 7. Stale statistics
ANALYZE orders;                               -- ⭐ the planner is guessing from old data
```

⭐⭐ **"Selectivity" is the concept to name.** An index pays off when it eliminates most rows.
If a predicate matches a large fraction of the table, a **sequential scan is genuinely faster** —
random I/O per row costs more than streaming pages. The planner choosing a seq scan is often
*correct*, and fighting it is the mistake.

⭐ **Low-cardinality columns** (boolean, status with 3 values) are poor index candidates alone —
but excellent as the **leading column of a composite index**, or with a **partial index**.

---

## 6. Partial & expression indexes ⭐

```sql
-- ⭐ Partial: index only the rows you query
CREATE INDEX idx_pending ON orders (created_at) WHERE status = 'pending';

-- ⭐ Expression: index a computed value
CREATE INDEX idx_lower_email ON users (LOWER(email));

-- ⭐ Unique + partial: enforce uniqueness among non-deleted rows only
CREATE UNIQUE INDEX ON users (email) WHERE deleted_at IS NULL;
```

⭐ **Partial indexes are underused and very effective.** If 99% of orders are `completed` and
you only ever query `pending`, a partial index is ~1% of the size, stays in memory, and skips
maintenance for the rows you don't care about.

⭐ The **unique-partial index is the correct solution for soft deletes** — a plain unique
constraint on `email` blocks a user from re-registering after deletion.

---

## 7. Maintenance ⭐

```sql
-- What exists, and is it used?
SELECT * FROM pg_stat_user_indexes WHERE idx_scan = 0;      -- ⭐⭐ UNUSED indexes
SELECT * FROM pg_stat_user_tables WHERE seq_scan > idx_scan; -- tables lacking indexes

CREATE INDEX CONCURRENTLY ...;      -- ⭐⭐ don't block writes (Postgres)
REINDEX INDEX CONCURRENTLY ...;     -- rebuild a bloated index
ANALYZE table;                      -- ⭐ refresh planner statistics
```

⚠️⚠️ **`CREATE INDEX` takes a write lock** on the table — on a large production table that's an
outage. **Always `CONCURRENTLY`** in Postgres (⚠️ which can't run inside a transaction, and can
leave an `INVALID` index if it fails — check and drop it). MySQL 5.6+ does online DDL by
default. See [../Web/Django/migrations.md](../Web/Django/migrations.md).

⭐ **Audit for unused indexes regularly** — they cost writes and space for nothing. `idx_scan =
0` after a full business cycle is a strong candidate for dropping.

⚠️ **Index bloat**: heavy update/delete churn leaves dead entries. Postgres autovacuum handles
most of it; `REINDEX CONCURRENTLY` for the rest.

---

## 8. The indexing checklist ⭐

```
1. Index every FOREIGN KEY column         ⭐ Postgres does NOT do this automatically
2. Index what you filter, join, sort by
3. Composite: equality cols → range col → sort col   ⭐ leftmost prefix
4. Consider covering (INCLUDE) for hot queries
5. Partial index for skewed data          ⭐ status flags, soft deletes
6. Expression index for LOWER()/casts
7. EXPLAIN ANALYZE to confirm it's used   ⭐⭐ never assume
8. Drop unused indexes                     writes aren't free
```

⚠️⚠️ **Unindexed foreign keys are a classic Postgres pitfall** — MySQL/InnoDB creates an index
for an FK automatically; **Postgres does not**. The symptom is a slow `DELETE` on the parent
(it must scan children to check the constraint) and slow reverse joins.

---

## 9. Interview points

- **What is an index and what does it cost? ⭐⭐** A sorted structure for fast lookups —
  paid for with slower writes and disk space.
- **Why B+trees rather than binary trees? ⭐⭐** Disk reads pages; high fan-out keeps depth at
  3–4 levels even for billions of rows. Linked leaves make range scans fast.
- **Clustered vs non-clustered? ⭐** The table stored in index order (one per table) vs a
  separate structure. InnoDB clusters on the PK; **Postgres has no clustered index**.
- **Why does a wide PK hurt in MySQL? ⭐** Every secondary index stores the PK, so a 36-char
  UUID bloats them all — and lookups traverse two trees.
- **Explain the leftmost prefix rule. ⭐⭐** An index on `(a,b,c)` serves `a`, `(a,b)`, `(a,b,c)`
  — never `b` alone.
- **How do you order columns in a composite index?** Equality first, then the range column,
  then sort columns — after a range, later columns can only filter.
- **What is a covering index? ⭐** One containing every column the query needs, enabling an
  index-only scan with no table access.
- **I added an index and the query is still slow. Why? ⭐⭐** Function on the column, leading
  wildcard, type mismatch, low selectivity, small table, or stale statistics.
- **When is a sequential scan the right choice? ⭐** When the predicate matches a large fraction
  of rows — random I/O per row costs more than streaming.
- **When would you use a partial index?** Skewed data — e.g. only `pending` rows — or to enforce
  uniqueness among non-soft-deleted rows.
- **How do you add an index without downtime?** `CREATE INDEX CONCURRENTLY` (Postgres) / online
  DDL (MySQL).
- **How do you find indexes worth dropping?** `pg_stat_user_indexes` with `idx_scan = 0` over a
  full business cycle.
- **Does Postgres index foreign keys automatically? ⭐** **No** — a common cause of slow parent
  deletes and reverse joins.
