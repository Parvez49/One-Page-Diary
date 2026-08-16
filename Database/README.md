# Databases — Index

Domain knowledge for **senior backend interviews** and production work. Assumes you can write
`SELECT` statements — the focus is on how the engine actually behaves, the traps that only
appear at scale, and the trade-offs behind every design choice.

**Conventions:** ⭐ = high interview value · ⚠️ = a trap that causes real incidents ·
every file ends with an **Interview points** section. Examples are PostgreSQL unless noted.

---

## Files

| File | Covers | Interview weight |
|---|---|---|
| [indexing.md](indexing.md) | ⭐⭐ **B+tree internals**, clustered vs secondary, **leftmost prefix**, covering & partial indexes, **why an index isn't used** | ⭐⭐⭐ |
| [transactions.md](transactions.md) | **ACID**, the anomalies, **isolation levels**, **MVCC**, locking, optimistic vs pessimistic, **deadlocks**, sagas | ⭐⭐⭐ |
| [performance.md](performance.md) | **Diagnostic order**, `pg_stat_statements`, **reading `EXPLAIN ANALYZE`**, anti-patterns, N+1, **connections & pooling** | ⭐⭐⭐ |
| [sql.md](sql.md) | **Logical execution order**, joins & the LEFT JOIN trap, NULL semantics, CTEs, **window functions**, upserts | ⭐⭐⭐ |
| [scaling.md](scaling.md) | **The escalation ladder**, replication & **lag**, partitioning vs **sharding**, **CAP/PACELC** | ⭐⭐⭐ |
| [fundamentals.md](fundamentals.md) | RDBMS, DDL/DML/DCL/TCL, **keys & surrogate vs natural**, constraints, relationships, schema decisions | ⭐⭐ |
| [normalization.md](normalization.md) | The **anomalies**, 1NF–BCNF worked example, **denormalisation trade-offs**, OLTP vs OLAP | ⭐⭐ |
| [nosql.md](nosql.md) | Categories, **SQL vs NoSQL trade-offs**, MongoDB **embed vs reference**, Redis, Cassandra, graph, polyglot cost | ⭐⭐ |
| [postgres.md](postgres.md) | psql, roles, backup, **VACUUM & bloat**, JSONB, `EXCLUDE`, **transactional DDL**, config | ⭐⭐ |
| [mysql.md](mysql.md) | Client, users, `mysqldump`, **InnoDB clustered index**, `utf8mb4`, `EXPLAIN`, replication | ⭐⭐ |
| [elasticsearch.md](elasticsearch.md) | **Inverted index**, analysis, `text` vs `keyword`, **filter vs must**, shards & segments, syncing | ⭐ |
| [interview.md](interview.md) | **Q&A across every topic** + rapid fire | ⭐⭐⭐ |

---

## Suggested study order

1. **[indexing.md](indexing.md)** — the highest-value topic. Nearly every performance question
   resolves to "is there a usable index, and why isn't it being used?"
2. **[transactions.md](transactions.md)** — ACID, isolation levels, and MVCC are the standard
   depth probe for senior candidates.
3. **[performance.md](performance.md)** — "the database is slow" is the most common open-ended
   question; having a *method* beats having facts.
4. **[sql.md](sql.md)** — execution order, the LEFT JOIN trap, NULL semantics, window functions.
5. **[scaling.md](scaling.md)** — replication lag and the partition/shard distinction come up in
   every system-design round.
6. **[normalization.md](normalization.md)** + **[fundamentals.md](fundamentals.md)** — schema
   design and the vocabulary.
7. **[nosql.md](nosql.md)** — the "SQL or NoSQL" question, answered with trade-offs.
8. **[postgres.md](postgres.md)** / **[mysql.md](mysql.md)** / **[elasticsearch.md](elasticsearch.md)**
   — engine specifics for whichever you run.
9. **[interview.md](interview.md)** — rehearse out loud the day before.

---

## The senior answers worth memorising

| Question | Short answer |
|---|---|
| Why B+trees? ⭐⭐ | Page-based I/O + high fan-out ⇒ 3–4 levels for billions of rows; linked leaves make ranges fast. |
| Leftmost prefix ⭐⭐ | `(a,b,c)` serves `a`, `(a,b)`, `(a,b,c)` — never `b` alone. |
| Index added, still slow ⭐⭐ | Function on the column, leading wildcard, type mismatch, **low selectivity**, stale stats. |
| When is a seq scan right? ⭐ | When the predicate matches most rows — random I/O costs more than streaming. |
| ACID's D | ⭐ **WAL fsynced before commit returns.** |
| MVCC ⭐⭐ | New row versions, not overwrites ⇒ readers never block writers. Cost: VACUUM. |
| What blocks VACUUM? ⭐ | A long-running / `idle in transaction` session ⇒ table bloat. |
| Write skew | Two valid transactions break a shared invariant — only Serializable prevents it. |
| Preventing deadlocks ⭐ | Consistent lock ordering, short transactions, and **retry**. |
| Overselling the last item ⭐ | `FOR UPDATE`, or atomic `UPDATE ... WHERE stock > 0` + `CHECK`. |
| Slow database — method ⭐⭐ | `pg_stat_statements` by **total** time → `EXPLAIN ANALYZE` → index → N+1 → locks. |
| `OFFSET 100000` ⭐ | Scans and discards every skipped row — use keyset pagination. |
| What runs out first? ⭐⭐ | **Connections**, not CPU — PgBouncer. |
| Read replicas scale… ⭐ | **Reads only** — every replica applies every write. |
| Replication lag ⭐⭐ | A user may not see their **own write** — route reads to the primary after a write. |
| Partition vs shard ⭐⭐ | Many tables, one database vs data across many databases. |
| CAP ⭐⭐ | Under a partition, pick C or A; PACELC adds latency-vs-consistency in normal operation. |
| SQL or NoSQL? ⭐⭐ | Default to Postgres; specialise only for an access pattern it serves far better. |
| `NOT IN` with NULL ⭐ | Returns **no rows** — use `NOT EXISTS`. |
| Money column ⭐ | `NUMERIC`, never `FLOAT`. |

---

## Related directories

`../Web/Django/queries.md` — N+1 and ORM query tuning · `../Web/Django/migrations.md` —
zero-downtime schema change · `../SDLC/system_design.md` — CAP, caching, sharding in system
design · `../SDLC/architecture.md` — sagas, CQRS, event-driven · `../Algorithm/Tree/trees.md`
— B-tree structure · `../linux/performance.md` — disk/IO triage under the database
