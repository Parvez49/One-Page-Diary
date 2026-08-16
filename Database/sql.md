# SQL — Queries, Joins & Window Functions

> Making them fast: **[indexing.md](indexing.md)** · **[performance.md](performance.md)** ·
> [Practice: LeetCode SQL](https://leetcode.com/problem-list/wdplk2vm/)

---

## 1. Logical execution order ⭐⭐

**You write it in one order; the database evaluates it in another.** This single table explains
most SQL confusion.

```sql
SELECT   department, COUNT(*) AS n        -- 5
FROM     employees                        -- 1
WHERE    active = true                    -- 2
GROUP BY department                       -- 3
HAVING   COUNT(*) > 5                     -- 4
ORDER BY n DESC                           -- 6
LIMIT    10 OFFSET 20;                    -- 7
```

```
FROM/JOIN → WHERE → GROUP BY → HAVING → SELECT → DISTINCT → ORDER BY → LIMIT
```

⭐⭐ **Two consequences you'll be asked about:**

1. **You can't use a `SELECT` alias in `WHERE`** — `WHERE n > 5` fails because `SELECT` hasn't
   run yet. (⚠️ MySQL permits it in `HAVING`/`ORDER BY` as an extension; Postgres allows it in
   `GROUP BY`/`ORDER BY` only.)
2. **`WHERE` vs `HAVING`:** `WHERE` filters **rows before grouping**; `HAVING` filters
   **groups after aggregation**. ⭐ Put every non-aggregate condition in `WHERE` — filtering
   early means fewer rows to group.

```sql
WHERE  active = true          -- ⭐ before grouping: cheap, can use an index
HAVING COUNT(*) > 5           -- ⭐ after grouping: only for aggregates
```

---

## 2. Joins ⭐⭐

```
  A          B              INNER      only matching rows in both
 ┌───┐    ┌───┐             LEFT       all of A + matches from B (⭐ NULLs where none)
 │ 1 │    │ 2 │             RIGHT      all of B + matches from A
 │ 2 ├────┤ 3 │             FULL       everything from both sides
 │ 3 │    │ 4 │             CROSS      ⚠️ cartesian product — every combination
 └───┘    └───┘             SELF       a table joined to itself
```

```sql
SELECT c.name, o.total
FROM customers c
LEFT JOIN orders o ON o.customer_id = c.id      -- ⭐ customers with NO orders still appear
WHERE o.id IS NULL;                             -- ⭐⭐ "customers who never ordered"
```

⭐ **`LEFT JOIN ... WHERE right.id IS NULL` is the anti-join idiom** — find rows in A with no
match in B. Worth knowing by name.

⚠️⚠️ **A `LEFT JOIN` silently becomes an `INNER JOIN`** when you filter the right table in
`WHERE`:

```sql
LEFT JOIN orders o ON o.customer_id = c.id
WHERE o.status = 'paid'          -- ⚠️ kills the unmatched rows (their o.status is NULL)

LEFT JOIN orders o ON o.customer_id = c.id AND o.status = 'paid'   -- ⭐ filter in ON
```

**The rule:** conditions on the *outer* (right) table belong in `ON`; conditions on the
preserved (left) table belong in `WHERE`.

⚠️ **A join that fans out multiplies rows** — joining two one-to-many relations gives
`n × m` rows and **inflates every aggregate**. Symptom: sums that are exactly double.
Fix with subqueries, separate queries, or `COUNT(DISTINCT ...)`.

⭐ **`USING (id)`** is shorthand when column names match, and **`NATURAL JOIN` is dangerous** —
it joins on *every* same-named column, so adding a `created_at` to both tables silently changes
your results. Never use it.

**Self-join** — hierarchies and comparisons within one table:

```sql
SELECT e.name, m.name AS manager
FROM employees e
LEFT JOIN employees m ON e.manager_id = m.id;    -- ⭐ LEFT so the CEO isn't dropped
```

---

## 3. Aggregation & NULL ⭐

```sql
COUNT(*)        -- ⭐ all rows, including NULLs
COUNT(col)      -- ⚠️ skips NULLs
COUNT(DISTINCT col)
SUM  AVG  MIN  MAX
STRING_AGG(name, ', ')       -- Postgres  (GROUP_CONCAT in MySQL)
FILTER (WHERE status='paid') -- ⭐ Postgres conditional aggregate
```

⚠️⚠️ **`NULL` is "unknown", and it propagates:**

| Expression | Result |
|---|---|
| `NULL = NULL` | ⚠️ **unknown** (not true) — use `IS NULL` |
| `5 + NULL` | `NULL` |
| `AVG(col)` with nulls | ⭐ ignores them — **denominator is the non-null count** |
| `col NOT IN (1, 2, NULL)` | ⚠️⚠️ **no rows, ever** |

⭐ **`NOT IN` with a NULL in the list returns nothing** — because `x <> NULL` is unknown, so no
row can satisfy it. Use `NOT EXISTS`, which handles NULLs correctly. This is one of the most
valuable SQL gotchas to know.

```sql
COALESCE(phone, 'N/A')    -- ⭐ first non-null
NULLIF(a, b)              -- NULL if equal — ⭐ guards division by zero: a / NULLIF(b, 0)
```

⚠️ **Every non-aggregated `SELECT` column must appear in `GROUP BY`** (Postgres enforces it;
⚠️ MySQL historically allowed it and returned an arbitrary row — `ONLY_FULL_GROUP_BY` fixes it).

---

## 4. Subqueries & CTEs ⭐

```sql
-- Scalar
SELECT name, (SELECT COUNT(*) FROM orders o WHERE o.customer_id = c.id) AS n
FROM customers c;                             -- ⚠️ CORRELATED: runs per row

-- EXISTS — ⭐ usually the fastest membership test
SELECT * FROM customers c
WHERE EXISTS (SELECT 1 FROM orders o WHERE o.customer_id = c.id);
```

⭐ **`EXISTS` beats `IN` for large subqueries** — it short-circuits at the first match, and it's
**NULL-safe**, unlike `NOT IN`. Modern optimisers often rewrite one into the other, but
`NOT EXISTS` vs `NOT IN` is a genuine correctness difference, not just performance.

**CTEs — readable, composable:**

```sql
WITH monthly AS (
    SELECT date_trunc('month', created_at) AS m, SUM(total) AS revenue
    FROM orders GROUP BY 1
),
growth AS (
    SELECT m, revenue,
           LAG(revenue) OVER (ORDER BY m) AS prev      -- ⭐ see §5
    FROM monthly
)
SELECT m, revenue, ROUND(100.0 * (revenue - prev) / prev, 1) AS pct
FROM growth WHERE prev IS NOT NULL;
```

⭐ **CTEs turn a nested-subquery pyramid into a readable pipeline** — that alone justifies them.
⚠️ In **Postgres before 12** a CTE was an **optimisation fence** (always materialised, never
inlined) — a known performance trap. Modern versions inline them unless you write
`WITH ... AS MATERIALIZED`.

**Recursive CTE** — hierarchies, graphs, generated series:

```sql
WITH RECURSIVE tree AS (
    SELECT id, parent_id, name, 1 AS depth
    FROM categories WHERE parent_id IS NULL        -- ⭐ anchor
  UNION ALL
    SELECT c.id, c.parent_id, c.name, t.depth + 1
    FROM categories c JOIN tree t ON c.parent_id = t.id   -- ⭐ recursive term
)
SELECT * FROM tree WHERE depth < 5;                -- ⚠️ ALWAYS bound the depth
```

⚠️ **A cycle in the data makes a recursive CTE run forever.** Bound the depth or track visited
nodes.

---

## 5. Window functions ⭐⭐

**Aggregate across related rows while keeping every row** — the thing `GROUP BY` cannot do.

```sql
SELECT name, department, salary,
       RANK()       OVER (PARTITION BY department ORDER BY salary DESC) AS rnk,
       AVG(salary)  OVER (PARTITION BY department)                      AS dept_avg,
       salary - LAG(salary) OVER (ORDER BY hired_at)                    AS diff_from_prev,
       SUM(salary)  OVER (ORDER BY hired_at
                          ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) AS running_total
FROM employees;
```

**Ranking — the distinction that gets asked:**

```
salary   ROW_NUMBER   RANK   DENSE_RANK
  300        1          1        1
  300        2          1        1        ⭐ ties share a rank
  200        3          3        2        ⭐ RANK skips (gap), DENSE_RANK doesn't
  100        4          4        3
```

| Function | Use |
|---|---|
| `ROW_NUMBER()` | ⭐ unique sequence — **deduplication**, pagination |
| `RANK()` | ties share a rank, then a **gap** |
| `DENSE_RANK()` | ties share a rank, **no gap** |
| `NTILE(4)` | quartiles/buckets |
| `LAG/LEAD(col, n, default)` | ⭐ previous/next row — deltas, gaps, time series |
| `FIRST_VALUE` / `LAST_VALUE` | boundary values in the window |
| `SUM/AVG/COUNT() OVER (...)` | ⭐ running totals, moving averages |

⭐⭐ **The classic "top N per group"** — an interview staple:

```sql
SELECT * FROM (
  SELECT *, ROW_NUMBER() OVER (PARTITION BY department ORDER BY salary DESC) AS rn
  FROM employees
) t WHERE rn <= 3;                          -- ⭐ can't filter a window fn in WHERE directly
```

⚠️ **Window functions are computed *after* `WHERE`/`GROUP BY`** (step 5 in §1), so you cannot
filter on one in `WHERE` — wrap it in a subquery or CTE.

⭐ **Deduplication** — keep the newest row per key:

```sql
DELETE FROM t WHERE id IN (
  SELECT id FROM (
    SELECT id, ROW_NUMBER() OVER (PARTITION BY email ORDER BY created_at DESC) rn FROM t
  ) x WHERE rn > 1
);
```

**Frames:** `ROWS BETWEEN` counts **physical rows**; `RANGE BETWEEN` groups **peer values**.
⚠️ The default frame is `RANGE UNBOUNDED PRECEDING TO CURRENT ROW`, which surprises people with
ties — be explicit with `ROWS` for running totals.

---

## 6. Modifying data ⭐

```sql
INSERT INTO users (name, email) VALUES ('Parvez', 'a@b.com')
ON CONFLICT (email) DO UPDATE SET name = EXCLUDED.name       -- ⭐ Postgres UPSERT
RETURNING id;                                                -- ⭐ get the id back, no round trip

-- MySQL:  INSERT ... ON DUPLICATE KEY UPDATE name = VALUES(name);

UPDATE orders o SET status = 'shipped'
FROM shipments s WHERE s.order_id = o.id;                    -- ⭐ UPDATE ... FROM (Postgres)

DELETE FROM logs WHERE created_at < now() - interval '90 days';
```

⚠️⚠️ **Always run the `SELECT` version of a destructive statement first.** `UPDATE`/`DELETE`
without a `WHERE` (or with a wrong join) rewrites the table, and it's inside a transaction only
if you started one.

⭐ **Batch large deletes** — a single `DELETE` of 10 million rows holds locks, bloats the WAL,
and can block replication. Loop in chunks of 10k with a commit between
([performance.md](performance.md)).

⭐ **`RETURNING`** (Postgres) avoids a second query to fetch generated ids — a real latency win
in write-heavy paths.

---

## 7. Useful functions

```sql
-- Conditional
CASE WHEN salary > 5000 THEN 'High' WHEN salary > 2000 THEN 'Mid' ELSE 'Low' END
COALESCE(a, b, c)      NULLIF(a, b)      GREATEST(a,b)      LEAST(a,b)

-- Dates ⭐ store TIMESTAMPTZ, compare in UTC
CURRENT_DATE   now()   AGE(a, b)
date_trunc('month', created_at)                     -- ⭐ grouping by period
created_at >= now() - interval '7 days'             -- ⭐ SARGable (see indexing.md)
EXTRACT(dow FROM created_at)

-- Strings
CONCAT(a,' ',b)   a || b   UPPER/LOWER   LENGTH   SUBSTRING(s,1,5)   TRIM
REPLACE  SPLIT_PART  POSITION  LIKE 'a%'  ILIKE  ~ 'regex'

-- Sets
UNION           -- ⚠️ removes duplicates → implicit sort, slower
UNION ALL       -- ⭐ keeps duplicates — use unless you need dedup
INTERSECT       EXCEPT
```

⚠️⚠️ **Never wrap an indexed column in a function in `WHERE`** — it makes the predicate
**non-SARGable** and the index unusable:

```sql
WHERE YEAR(created_at) = 2024                          -- ⚠️ full scan
WHERE created_at >= '2024-01-01'
  AND created_at <  '2025-01-01'                       -- ⭐ index range scan
```

---

## 8. Interview points

- **What's the logical execution order? ⭐⭐** `FROM → WHERE → GROUP BY → HAVING → SELECT →
  ORDER BY → LIMIT` — which is why a `SELECT` alias isn't available in `WHERE`.
- **`WHERE` vs `HAVING`? ⭐** Rows before grouping vs groups after aggregation; filter early in
  `WHERE`.
- **Explain the join types.** Inner/left/right/full/cross/self — and `LEFT JOIN ... IS NULL`
  as the anti-join.
- **Why did my `LEFT JOIN` return no unmatched rows? ⭐⭐** A `WHERE` condition on the right
  table converts it to an inner join — move the condition into `ON`.
- **`COUNT(*)` vs `COUNT(col)`?** All rows vs non-NULL values only.
- **What happens with `NOT IN` and NULL? ⭐⭐** It returns **no rows** — use `NOT EXISTS`.
- **`IN` vs `EXISTS`?** `EXISTS` short-circuits and is NULL-safe; optimisers often rewrite
  either way, but `NOT EXISTS` is the correct choice.
- **`UNION` vs `UNION ALL`? ⭐** Dedup (needs a sort) vs raw concatenation — use `ALL` unless
  you need deduplication.
- **`RANK` vs `DENSE_RANK` vs `ROW_NUMBER`? ⭐⭐** Ties with gaps · ties without gaps · always
  unique.
- **How do you get the top N per group? ⭐** `ROW_NUMBER()` in a subquery/CTE, filtered outside —
  window functions can't be filtered in `WHERE`.
- **What is a CTE, and the Postgres caveat?** A named subquery for readability and recursion;
  before PG12 it was an optimisation fence.
- **How do you write an upsert?** `INSERT ... ON CONFLICT DO UPDATE` (Postgres) /
  `ON DUPLICATE KEY UPDATE` (MySQL).
- **Why is `WHERE YEAR(col) = 2024` slow? ⭐** The function makes it non-SARGable — the index
  can't be used. Rewrite as a range.
