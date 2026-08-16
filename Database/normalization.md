# Normalization & Denormalization

> Keys & constraints: **[fundamentals.md](fundamentals.md)** · Read performance:
> **[performance.md](performance.md)**

---

## 1. Why normalise ⭐

**Normalisation organises tables to eliminate redundancy** — because redundancy causes three
**anomalies** that interviewers ask for by name:

```
StudentID  Name    Course      Instructor  InstructorEmail
1          Ali     Databases   Dr. Khan    khan@uni.edu
1          Ali     Networks    Dr. Rahman  rahman@uni.edu
2          Sara    Databases   Dr. Khan    khan@uni.edu      ← ⚠️ repeated
```

| Anomaly | What goes wrong here |
|---|---|
| **Insertion** | ⚠️ Can't add a new instructor until *someone enrols* in their course |
| **Update** | ⚠️ Dr. Khan's email changes → must update **every** row; miss one and the data contradicts itself |
| **Deletion** | ⚠️ The last student drops Databases → **the course and instructor vanish** |

⭐ **State the anomalies, not the definition.** "Normalisation reduces redundancy" is a
textbook answer; naming which specific failure each normal form prevents is the senior one.

**Functional dependency** — `A → B` means A determines B. `StudentID → Name`. Normalisation is
the process of ensuring **every non-key column depends on the key, the whole key, and nothing
but the key** — that phrase alone summarises 1NF→3NF.

---

## 2. The normal forms ⭐⭐

### 1NF — atomic values, no repeating groups

```
⚠️ VIOLATION                          ⭐ 1NF
id  name   phones                     id  name   |  student_id  phone
1   Ali    "0171, 0192"               1   Ali    |  1           0171
                                                  |  1           0192
```

**Rules:** each cell holds a **single value**; no repeating column groups (`phone1`, `phone2`,
`phone3`); each row is unique.

⚠️ **Comma-separated values in a column** are the everyday 1NF violation — you can't index
them, join on them, or constrain them, and every query needs string parsing.

### 2NF — no *partial* dependency on a composite key

Applies only when the PK is **composite**. Every non-key column must depend on the **whole**
key.

```
⚠️ VIOLATION — PK is (StudentID, CourseID)
StudentID  CourseID  Grade   StudentName
                             ↑ depends only on StudentID — a PARTIAL dependency

⭐ 2NF
enrollments(StudentID, CourseID, Grade)      students(StudentID, StudentName)
```

### 3NF — no *transitive* dependency

A non-key column must not depend on **another non-key column**.

```
⚠️ VIOLATION
OrderID  CustomerID  CustomerCity
                     ↑ OrderID → CustomerID → CustomerCity  (transitive)

⭐ 3NF
orders(OrderID, CustomerID)      customers(CustomerID, CustomerCity)
```

⭐ **3NF is the practical target for OLTP systems.** It removes essentially all update anomalies
while keeping joins manageable.

### BCNF — the stricter 3NF

**Every determinant must be a candidate key.** Fixes the edge case where a non-key column
determines part of a key.

```
⚠️ VIOLATION — Student can take a subject from one teacher; each teacher teaches one subject
(Student, Subject) → Teacher      Teacher → Subject      ⚠️ Teacher isn't a candidate key

⭐ BCNF
teaches(Teacher, Subject)      studies(Student, Teacher)
```

⭐ **BCNF only differs from 3NF when there are overlapping composite candidate keys** — rare in
practice. Knowing *that* is a better answer than reciting the definition.

**Beyond:** **4NF** removes multi-valued dependencies (independent multi-valued facts in one
table); **5NF** handles join dependencies. ⚠️ Rarely needed; say so.

---

## 3. Worked example ⭐

**Unnormalised order table:**

```
OrderID  CustName  CustCity  Products              Total
1        Ali       Dhaka     "Laptop, Mouse"       1200
```

**→ 1NF** (atomic values, one row per product):

```
order_lines(OrderID, CustName, CustCity, Product, Price)
```

**→ 2NF** (PK is `(OrderID, Product)`; customer data depends only on `OrderID`):

```
orders(OrderID, CustName, CustCity)
order_lines(OrderID, Product, Price)
```

**→ 3NF** (`CustCity` depends on the customer, not the order):

```
customers(CustomerID, CustName, CustCity)
orders(OrderID, CustomerID, OrderDate)
order_lines(OrderID, ProductID, Quantity, UnitPrice)   -- ⭐ see below
products(ProductID, Name, CurrentPrice)
```

⭐⭐ **`UnitPrice` stays on `order_lines` — and that is *not* a normalisation failure.** The
product's *current* price and the price *paid at the time of purchase* are **different facts**.
Storing the paid price is correct; deriving it from `products` later would silently rewrite
history when prices change. Recognising the difference between redundancy and a point-in-time
snapshot is exactly what distinguishes a senior answer.

---

## 4. Denormalization ⭐⭐

**Deliberately reintroducing redundancy to avoid expensive joins or aggregates.**

```sql
-- ⭐ store a computed value instead of counting on every read
ALTER TABLE posts ADD COLUMN comment_count INT NOT NULL DEFAULT 0;

-- ⭐ duplicate a hot column to skip a join
ALTER TABLE orders ADD COLUMN customer_name TEXT;
```

| Technique | Use |
|---|---|
| **Precomputed aggregate** | ⭐ `comment_count`, `total_orders` — avoids `COUNT(*)` per read |
| **Duplicated column** | avoid a join for one hot field |
| **Materialised view** | ⭐ dashboards and reports ([fundamentals.md](fundamentals.md)) |
| **Summary/rollup table** | daily/monthly aggregates for analytics |
| **JSON snapshot** | ⭐ an immutable record of a payload as it was |

⚠️⚠️ **The cost is that you now own consistency.** Every write path must update the duplicate —
including bulk imports, admin tools, migrations, and the other service nobody told you about.
`comment_count` drifting from the real count is one of the most common production data bugs.

⭐ **Denormalise only when you can name the query that's slow, and you've already tried
indexing.** The correct order:

```
1. Normalise (3NF)                 ⭐ correctness first
2. Index properly                  ⭐ fixes most "slow join" complaints
3. Cache                           ⭐ often removes the need entirely
4. Materialised view / rollup      ⭐ redundancy the DATABASE maintains
5. Denormalise columns             ⚠️ last — you maintain consistency by hand
```

⭐ **Prefer a materialised view or a trigger over hand-maintained duplication** — then the
database owns the invariant rather than every future code path.

---

## 5. OLTP vs OLAP ⭐

| | **OLTP** (transactional) | **OLAP** (analytical) |
|---|---|---|
| Workload | many small reads/writes | few huge scans and aggregates |
| Schema | ⭐ **normalised (3NF)** | ⭐ **denormalised — star/snowflake** |
| Optimised for | write throughput, consistency | read/scan throughput |
| Storage | row-oriented | ⭐ **column-oriented** |
| Example | order processing, user accounts | dashboards, BI, reporting |

⭐⭐ **This is the honest resolution of "normalise or denormalise?"** — they're different
workloads, not competing opinions. Keep the transactional database normalised, and **ETL into a
denormalised warehouse** (star schema: a fact table plus dimension tables) for analytics.
Running heavy reporting queries against your OLTP primary is what makes both slow.

⭐ **Column-oriented storage** (ClickHouse, BigQuery, Redshift, DuckDB, Parquet) is why
analytics databases are so much faster at aggregates: `SUM(revenue)` reads *one column*, not
every row, and compresses far better because a column holds homogeneous values.

---

## 6. Interview points

- **What is normalisation, and what does it prevent? ⭐⭐** Organising tables to eliminate
  redundancy — specifically the **insertion, update, and deletion anomalies**.
- **Summarise 1NF–3NF in one line. ⭐** Every non-key column depends on *the key* (1NF), *the
  whole key* (2NF), and *nothing but the key* (3NF).
- **Give a 1NF violation.** Comma-separated values or repeating `phone1/phone2` columns —
  unindexable and unconstrainable.
- **When does 2NF apply?** Only with a composite primary key — it removes partial dependencies.
- **What's a transitive dependency?** A non-key column determined by another non-key column.
- **3NF vs BCNF? ⭐** BCNF requires every determinant to be a candidate key; they differ only
  with overlapping composite candidate keys — rare in practice.
- **How far should you normalise?** ⭐ **3NF for OLTP**, then denormalise deliberately with
  evidence.
- **When would you denormalise? ⭐⭐** After indexing and caching have failed to fix a specific
  measured query — and knowing you now own keeping the duplicate consistent.
- **Is storing `unit_price` on an order line denormalisation? ⭐** No — the price paid is a
  different fact from the current price. It's a point-in-time snapshot.
- **How do you keep a denormalised counter correct?** Let the database own it — a trigger or
  materialised view — rather than every application write path.
- **Normalised or denormalised — which is better?** Neither: **OLTP normalised, OLAP
  denormalised** (star schema, columnar storage), with ETL between them.
