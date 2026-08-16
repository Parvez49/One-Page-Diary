# Database Fundamentals

> Schema design: **[normalization.md](normalization.md)** · Querying: **[sql.md](sql.md)**

---

## 1. DBMS, RDBMS, SQL ⭐

- **DBMS** — software that stores, manages, and secures data.
- **RDBMS** — a DBMS that stores data as **relations (tables)** with defined relationships
  between them, and enforces integrity constraints. Postgres, MySQL, Oracle, SQL Server.
- **SQL** — the *language*; **MySQL/Postgres** are *products* that implement it.

⭐ **The distinction interviewers listen for:** an RDBMS adds the **relational model**
(tables, keys, referential integrity) and **ACID transactions** on top of plain data storage.
A DBMS may just store documents or files with no relational guarantees.

⚠️ **SQL is standardised but portable only in theory** — pagination, upsert, JSON handling,
string functions, and recursive queries all differ. Assume dialect differences.

**The four sub-languages:**

| Language | Commands | Note |
|---|---|---|
| **DDL** — Definition | `CREATE` `ALTER` `DROP` `TRUNCATE` `RENAME` | ⚠️ mostly **auto-commit** — usually can't be rolled back (⭐ except in Postgres, which has transactional DDL) |
| **DML** — Manipulation | `SELECT` `INSERT` `UPDATE` `DELETE` | the day-to-day work |
| **DCL** — Control | `GRANT` `REVOKE` | permissions |
| **TCL** — Transaction | `COMMIT` `ROLLBACK` `SAVEPOINT` | ⭐ see [transactions.md](transactions.md) |

⚠️⚠️ **`DELETE` vs `TRUNCATE` vs `DROP`** — a standard question:

| | `DELETE` | `TRUNCATE` | `DROP` |
|---|---|---|---|
| Type | DML | DDL | DDL |
| Removes | selected rows (`WHERE`) | ⭐ **all rows**, fast | the whole table |
| Rollback | ✅ yes | ⚠️ usually no (✅ in Postgres) | ⚠️ usually no |
| Triggers fire | ✅ | ❌ | ❌ |
| Resets identity | ❌ | ✅ | n/a |
| Speed | row-by-row, logged | ⭐ deallocates pages | instant |

---

## 2. The three levels of abstraction ⭐

```
VIEW / EXTERNAL     what each user or app sees      ⭐ views, permissions
      ↕
LOGICAL / CONCEPTUAL  what data exists and how it relates   ⭐ tables, columns, constraints
      ↕
PHYSICAL             how it's actually stored        pages, files, indexes, compression
```

⭐ **The point is *independence*.** Adding an index or moving to a different filesystem
(physical change) breaks nothing above it. Adding a column (logical change) doesn't break apps
querying through a view. That decoupling is why you can tune a database without rewriting the
application.

---

## 3. Keys ⭐

| Key | Meaning |
|---|---|
| **Super key** | any set of columns that uniquely identifies a row |
| **Candidate key** | a *minimal* super key — no redundant column |
| **Primary key** | ⭐ the chosen candidate key. **Unique + NOT NULL**, one per table |
| **Alternate key** | the candidate keys you didn't choose |
| **Composite key** | a primary key spanning multiple columns |
| **Foreign key** | ⭐ references a primary key elsewhere — enforces **referential integrity** |
| **Surrogate key** | a system-generated id (serial/UUID) with no business meaning |
| **Natural key** | a real-world identifier (email, ISBN, national ID) |

⭐⭐ **Surrogate vs natural key is a real design discussion, not trivia:**

> Natural keys carry meaning and avoid a join to look up the "real" value — but they
> **change** (people change email addresses, countries change codes, ISBNs get reissued), and
> a changing PK cascades through every referencing table. Surrogate keys never change and stay
> narrow, which keeps indexes small and joins cheap. **Default to a surrogate PK and put a
> `UNIQUE` constraint on the natural key** — you get stability *and* the business rule.

⚠️ **UUID vs auto-increment as a surrogate key** — the trade worth naming:

| | `BIGSERIAL` / `AUTO_INCREMENT` | `UUID` |
|---|---|---|
| Size | 8 bytes | ⚠️ 16 bytes (36 as text!) |
| Locality | ⭐ sequential — appends to the index | ⚠️ **random → index page splits, poor cache hits** |
| Distributed generation | ⚠️ needs coordination | ⭐ generate anywhere, offline-capable |
| Leaks information | ⚠️ row counts, growth rate | ⭐ opaque |

⭐ **UUIDv7 (time-ordered) is the modern compromise** — globally unique *and* sequential, so it
doesn't fragment the index the way UUIDv4 does. ⚠️ Never store a UUID as `VARCHAR(36)` when a
native `uuid`/`BINARY(16)` type exists — it more than doubles index size.

---

## 4. Constraints ⭐

```sql
CREATE TABLE orders (
    id          BIGSERIAL PRIMARY KEY,
    customer_id BIGINT NOT NULL REFERENCES customers(id) ON DELETE RESTRICT,
    email       TEXT    NOT NULL UNIQUE,
    status      TEXT    NOT NULL DEFAULT 'pending',
    total       NUMERIC(10,2) NOT NULL CHECK (total >= 0),   -- ⭐ never FLOAT for money
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now(),          -- ⭐ TZ-aware
    CONSTRAINT valid_status CHECK (status IN ('pending','paid','shipped'))
);
```

⭐⭐ **Constraints belong in the database, not only in the application.** Application-level
validation is bypassed by a migration script, a bulk import, an admin panel, a second service,
or a bug. The database is the **last line of defence** and the only one that's always enforced.
This is the reason ORMs' `validators` are insufficient
([../Web/Django/orm.md](../Web/Django/orm.md)).

**`ON DELETE` behaviour** — a design decision, not boilerplate:

| Action | Effect |
|---|---|
| `RESTRICT` / `NO ACTION` | ⭐ block the delete — the safe default |
| `CASCADE` | ⚠️ delete children too — silent mass deletion if misapplied |
| `SET NULL` | orphan the child (needs a nullable column) |

⚠️ **`NULL` is "unknown", not "empty".** `NULL = NULL` is **unknown**, not true — use
`IS NULL`. Aggregates skip nulls (`COUNT(col)` ignores them; `COUNT(*)` doesn't), and
`NOT IN (subquery containing NULL)` returns **no rows at all** — a classic silent bug
([sql.md](sql.md)).

---

## 5. Relationships & modelling ⭐

```
One-to-One    users ── profiles          FK + UNIQUE on the child
One-to-Many   customers ──< orders       ⭐ FK on the MANY side
Many-to-Many  students >──< courses      ⭐ requires a JOIN TABLE
```

```sql
CREATE TABLE enrollments (               -- ⭐ the junction table
    student_id BIGINT REFERENCES students(id),
    course_id  BIGINT REFERENCES courses(id),
    enrolled_at TIMESTAMPTZ DEFAULT now(),   -- ⭐ attributes ON the relationship
    grade      TEXT,
    PRIMARY KEY (student_id, course_id)      -- ⭐ composite PK prevents duplicates
);
```

⭐ **A many-to-many relationship *always* becomes a table** — there's no other way to represent
it relationally. And the moment the relationship carries data (enrolment date, grade, quantity,
price-at-purchase), that table needs to be explicit in your model rather than hidden by an ORM
([../Web/Django/orm.md](../Web/Django/orm.md)).

**ER modelling vocabulary:** entity (table) · attribute (column) · relationship ·
**cardinality** (1:1, 1:N, M:N) · participation (total/partial). ⭐ Cardinality determines
where the foreign key goes — it always sits on the "many" side.

---

## 6. Schema design decisions that bite later ⭐

| Decision | Guidance |
|---|---|
| Money | ⭐⭐ `NUMERIC`/`DECIMAL`, **never `FLOAT`** — binary floats can't represent 0.10 |
| Timestamps | ⭐ `TIMESTAMPTZ`, store **UTC**, convert for display |
| Enums | `CHECK` constraint or a lookup table; ⚠️ native `ENUM` types are painful to alter |
| Soft delete | `deleted_at TIMESTAMPTZ` — ⚠️ then **every query must filter it**, and unique constraints need `WHERE deleted_at IS NULL` |
| Text | Postgres `TEXT` (no penalty); MySQL `VARCHAR(n)` |
| Booleans | `BOOLEAN`, not `CHAR(1)` or `0/1` integers |
| Audit trail | `created_at`/`updated_at` on every table — you will need them |
| JSON columns | ⭐ great for genuinely schemaless attributes; ⚠️ a schema-avoidance habit otherwise |

⚠️⚠️ **`SELECT *` in application code** breaks when a column is added or reordered, ships
columns you don't need over the wire, and prevents covering-index optimisations
([indexing.md](indexing.md)). List columns explicitly.

⭐ **The EAV anti-pattern** (entity–attribute–value: one table of `entity_id, key, value`) looks
flexible and destroys everything — no types, no constraints, no usable indexes, and a
self-join per attribute. Use a JSON column instead if the schema is genuinely dynamic.

---

## 7. Views, materialised views, and procedures

```sql
CREATE VIEW active_customers AS
SELECT id, name FROM customers WHERE status = 'active';        -- ⭐ a stored QUERY

CREATE MATERIALIZED VIEW daily_sales AS ...;                    -- ⭐ stored RESULT
REFRESH MATERIALIZED VIEW CONCURRENTLY daily_sales;
```

⭐ **A view is a named query — it computes every time.** A **materialised view stores the
result**, so reads are instant but data is stale until refreshed. Materialised views are the
right tool for expensive dashboards and reporting aggregates.

**Stored procedures & triggers** — ⚠️ powerful and easy to abuse. Business logic in triggers is
invisible to application developers, hard to version-control, untestable in CI, and surprises
everyone during debugging. ⭐ Keep them for data-integrity enforcement and audit logging; put
business rules in application code.

---

## 8. Interview points

- **DBMS vs RDBMS?** Storage/management vs the relational model with tables, keys, referential
  integrity, and ACID transactions.
- **SQL vs MySQL?** A standard language vs a specific product implementing it.
- **`DELETE` vs `TRUNCATE` vs `DROP`? ⭐** Row-level DML (rollback-able, fires triggers) ·
  fast DDL removing all rows · removes the table entirely.
- **What are the three levels of abstraction, and why do they matter?** View, logical, physical
  — they give **independence**, so physical tuning doesn't break applications.
- **Primary vs candidate vs super key?** Chosen unique identifier · minimal super key · any
  uniquely-identifying column set.
- **Surrogate vs natural key? ⭐⭐** Surrogates never change and stay narrow; natural keys carry
  meaning but change. Use a surrogate PK **plus** a unique constraint on the natural key.
- **UUID vs auto-increment? ⭐** UUIDs are distributed and opaque but 16 bytes and random,
  fragmenting indexes — UUIDv7 fixes the ordering problem.
- **Why enforce constraints in the database? ⭐⭐** Application validation is bypassed by
  migrations, bulk imports, admin tools, and other services; the DB is the only guarantee.
- **How do you model many-to-many?** A junction table — and it becomes explicit the moment the
  relationship carries attributes.
- **What's special about `NULL`? ⭐** It means *unknown*: `NULL = NULL` is unknown, aggregates
  skip it, and `NOT IN` with a NULL returns no rows.
- **View vs materialised view? ⭐** A stored query recomputed each time vs a stored result
  that's fast but stale until refreshed.
- **Why avoid `SELECT *`?** Fragile to schema changes, wasteful over the wire, and defeats
  covering indexes.
- **Why is EAV an anti-pattern?** No types, no constraints, unusable indexes, self-join per
  attribute — use JSON columns instead.
