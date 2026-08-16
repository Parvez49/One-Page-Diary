# PostgreSQL

> MVCC & isolation: **[transactions.md](transactions.md)** · Tuning: **[performance.md](performance.md)**

---

## 1. psql cheat sheet ⭐

```bash
sudo -i -u postgres     # switch to the postgres OS user
psql                    # open the shell
psql -U user -d dbname -h host -p 5432
```

```
\l                  list databases            \dt          list tables
\c dbname           connect to another DB     \d table     ⭐ describe a table (+ indexes, FKs)
\du                 list roles                \di          list indexes
\dn                 list schemas              \df          list functions
\x                  ⭐ expanded output — essential for wide rows
\timing             ⭐ show query duration
\e                  edit the last query in $EDITOR
\i file.sql         run a script
\copy t FROM 'f.csv' CSV HEADER    ⭐ CLIENT-side copy (no server file access needed)
\q                  quit
```

```sql
SELECT version();
SELECT current_user, current_database();
SELECT pg_size_pretty(pg_database_size('mydb'));
```

⭐ **`\x` + `\timing` are the two you'll use constantly** — expanded output makes wide rows
readable, and timing tells you immediately whether a change helped.

---

## 2. Roles & permissions

```sql
CREATE USER appuser WITH PASSWORD 'secret';        -- ⭐ USER = ROLE with LOGIN
ALTER USER appuser WITH PASSWORD 'newpass';
GRANT CONNECT ON DATABASE mydb TO appuser;
GRANT USAGE ON SCHEMA public TO appuser;
GRANT SELECT, INSERT, UPDATE ON ALL TABLES IN SCHEMA public TO appuser;
ALTER DEFAULT PRIVILEGES IN SCHEMA public          -- ⭐ applies to FUTURE tables too
  GRANT SELECT ON TABLES TO readonly;

DROP USER olduser;                                  -- ⚠️ fails if it owns objects
REASSIGN OWNED BY olduser TO postgres;              -- ⭐ the correct sequence
DROP OWNED BY olduser;
DROP USER olduser;
```

⚠️⚠️ **`GRANT ... ON ALL TABLES` only affects tables that exist *now*.** New tables created
later are inaccessible — which is why `ALTER DEFAULT PRIVILEGES` exists and why "the migration
broke the read-only user" is a recurring incident.

⭐ **Grant to a *role*, then grant the role to users** — permissions stay manageable as people
come and go. And give the application a least-privilege role, not superuser.

---

## 3. Remote access & auth

```
# /etc/postgresql/<version>/main/postgresql.conf
listen_addresses = '*'          # ⚠️ '*' means all interfaces — firewall it
port = 5432
ssl = on                        # ⭐ keep ON for anything crossing a network

# /etc/postgresql/<version>/main/pg_hba.conf   ⭐ evaluated TOP-DOWN, first match wins
# TYPE  DATABASE  USER   ADDRESS         METHOD
local   all       all                    peer
host    mydb      appuser 10.0.0.0/8     scram-sha-256      # ⭐ not md5
hostssl all       all     0.0.0.0/0      scram-sha-256      # ⚠️ scope this properly
```

```bash
sudo systemctl restart postgresql        # after postgresql.conf changes
sudo systemctl reload postgresql         # ⭐ pg_hba.conf only needs a reload
```

⚠️⚠️ **`listen_addresses = '*'` plus `host all all 0.0.0.0/0` exposes the database to the
internet.** Restrict by CIDR, require SSL, and keep it behind a private network or bastion
([../linux/gitssh.md](../linux/gitssh.md)). ⭐ Prefer **SSH tunnelling** for ad-hoc access over
opening the port at all.

⭐ Use **`scram-sha-256`**, not `md5` — md5 authentication is deprecated and weak.

---

## 4. Backup & restore ⭐

```bash
# ⭐ custom format — compressed, parallel restore, selective objects
pg_dump -U postgres -h localhost -Fc mydb > mydb.dump
pg_restore -U postgres -d mydb -j 4 mydb.dump

# plain SQL (readable, portable)
pg_dump -U postgres -h localhost -p 5432 mydb > mydb.sql
psql -U postgres -d mydb -f mydb.sql

pg_dumpall -U postgres --globals-only > roles.sql   # ⭐ roles/tablespaces aren't in pg_dump

scp root@1.2.3.4:/root/mydb.dump .                  # fetch from a remote host
```

⭐ **`-Fc` (custom format) over plain SQL** — it compresses, restores in parallel (`-j`), and
lets you restore a single table.

⚠️⚠️ **`pg_dump` is a logical backup, and it does not include roles or other databases.** For
production you also want **physical backups with PITR** (`pgBackRest`, `barman`, or
`pg_basebackup` + WAL archiving) so you can recover to a point in time rather than to last
night.

⚠️ **An untested backup is not a backup.** Schedule restore drills — the failure mode is
discovering at 3 a.m. that the dump has been silently failing for a month.

---

## 5. What makes Postgres distinctive ⭐⭐

**MVCC + VACUUM** — Postgres keeps old row versions **in the table** rather than an undo log
([transactions.md §4](transactions.md)):

```sql
SELECT relname, n_dead_tup, last_autovacuum FROM pg_stat_user_tables ORDER BY n_dead_tup DESC;
VACUUM (VERBOSE, ANALYZE) mytable;
```

⚠️⚠️ **A long-running or `idle in transaction` session blocks vacuum from cleaning *any* newer
dead tuples**, so the table and its indexes bloat and everything slows down. Set
`idle_in_transaction_session_timeout` and monitor `pg_stat_activity`. This is the single most
common self-inflicted Postgres problem.

⚠️ **Transaction ID wraparound** — if autovacuum falls far enough behind, Postgres **stops
accepting writes** to protect data. Rare, catastrophic, and entirely preventable by monitoring.

**Rich types** — a genuine differentiator:

```sql
JSONB          -- ⭐⭐ binary JSON, indexable with GIN — a competent document store
ARRAY          -- integer[], text[]
UUID  INET  CIDR  MACADDR
TSTZRANGE      -- ⭐ range types with EXCLUDE constraints (no double-booking!)
tsvector       -- full-text search
PostGIS        -- geospatial (extension)
hstore  ENUM  MONEY  INTERVAL
```

```sql
-- ⭐ JSONB with an index — often removes the need for a separate document store
CREATE INDEX idx_meta ON events USING GIN (metadata);
SELECT * FROM events WHERE metadata @> '{"type": "click"}';

-- ⭐⭐ prevent overlapping bookings AT THE DATABASE LEVEL
ALTER TABLE bookings ADD CONSTRAINT no_overlap
  EXCLUDE USING GIST (room_id WITH =, during WITH &&);
```

⭐ **The `EXCLUDE` constraint is a great thing to know** — it enforces "no two bookings for the
same room overlap" declaratively, which no amount of application code can guarantee under
concurrency.

**Other Postgres-specific strengths:**

| Feature | Why it matters |
|---|---|
| ⭐⭐ **Transactional DDL** | `BEGIN; ALTER TABLE ...; ROLLBACK;` — **migrations are atomic** |
| **`CREATE INDEX CONCURRENTLY`** | ⭐ add an index without blocking writes |
| **Partial & expression indexes** | ⭐ see [indexing.md](indexing.md) |
| **Extensions** | PostGIS, `pg_stat_statements`, TimescaleDB, `pgvector` (⭐ embeddings), Citus |
| **`RETURNING`** | get generated ids without a second query |
| **Window functions, CTEs, `LATERAL`** | ⭐ excellent analytical SQL |
| **`LISTEN`/`NOTIFY`** | lightweight pub/sub |
| **Logical replication** | selective, cross-version replication |

⭐⭐ **Transactional DDL is a real operational advantage over MySQL**: a failed migration rolls
back cleanly instead of leaving the schema half-applied
([../Web/Django/migrations.md](../Web/Django/migrations.md)).

---

## 6. Configuration ⭐

```
shared_buffers = 25% of RAM              # ⭐ Postgres's own cache
effective_cache_size = 50-75% of RAM     # ⚠️ a planner HINT, not an allocation
work_mem = 16MB                          # ⚠️⚠️ PER sort/hash node PER connection
maintenance_work_mem = 512MB             # VACUUM, index builds
max_connections = 100                    # ⭐ keep low; use PgBouncer
wal_buffers = 16MB
checkpoint_completion_target = 0.9
random_page_cost = 1.1                   # ⭐ lower for SSD (default 4.0 assumes spinning disk)
```

⚠️ **`work_mem` is the classic mistake** — 100 connections × 3 sort nodes × 64 MB is 19 GB, not
64 MB. Raise it per-session for a known heavy query instead.

⭐ **`random_page_cost = 1.1` on SSDs** is one of the highest-value single changes — the default
of 4.0 encodes an assumption about seek time that hasn't been true for a decade, and it makes
the planner avoid indexes it should use.

```sql
SHOW work_mem;  SELECT name, setting FROM pg_settings WHERE name LIKE '%mem%';
```

---

## 7. Postgres vs MySQL ⭐

| | **PostgreSQL** | **MySQL/InnoDB** |
|---|---|---|
| Philosophy | ⭐ correctness, extensibility, SQL standards | ⭐ speed, simplicity, ubiquity |
| DDL in transactions | ⭐⭐ **yes** | ⚠️ no — implicit commit |
| MVCC storage | in-table + **VACUUM** | undo log |
| Clustered index | ⚠️ none (heap) | ⭐ PK is clustered |
| Default isolation | Read Committed | Repeatable Read |
| Types | ⭐⭐ JSONB, arrays, ranges, GIS, custom | JSON (weaker indexing) |
| Index types | ⭐ B-tree, GIN, GiST, BRIN, hash, partial, expression | mainly B-tree, some full-text |
| Replication | logical + streaming | ⭐ mature, simple, very widely deployed |
| Simple read throughput | good | ⭐ often faster |

⭐ **The balanced answer:** *"Postgres by default — richer types, stricter correctness,
transactional DDL, and better analytical SQL. MySQL is a fine choice for simple high-read
workloads, and it's what a lot of managed hosting and legacy stacks assume."* Details:
[mysql.md](mysql.md).

---

## 8. Interview points

- **What is VACUUM and why is it needed? ⭐⭐** MVCC leaves dead row versions **in the table**;
  vacuum reclaims them and updates statistics.
- **What blocks vacuum, and what happens? ⭐⭐** A long-running or `idle in transaction` session
  — the table and indexes bloat and performance degrades globally.
- **What is transaction ID wraparound?** If vacuum falls far enough behind, Postgres refuses
  writes to protect data integrity.
- **What's distinctive about Postgres? ⭐** Transactional DDL, JSONB with GIN indexes, rich
  types (arrays, ranges, GIS), many index types, extensions, and `CREATE INDEX CONCURRENTLY`.
- **Why does transactional DDL matter?** A failed migration rolls back cleanly instead of
  leaving a half-applied schema.
- **Does Postgres have clustered indexes?** ⭐ No — it's heap storage; `CLUSTER` is a one-off
  physical reorder, not maintained.
- **How would you store semi-structured data? ⭐** `JSONB` with a GIN index — often removing the
  need for a separate document database.
- **How do you prevent double-booking a room?** An `EXCLUDE USING GIST` constraint on a range
  type — enforced by the database, not application code.
- **What's `work_mem` and the common error? ⭐** Memory per sort/hash node **per connection** —
  setting it globally high can exhaust RAM.
- **One config change with outsized impact on SSD?** `random_page_cost = 1.1` — the default
  assumes spinning disks and discourages index use.
- **`pg_dump` vs physical backup? ⭐** Logical (portable, no roles, no PITR) vs physical with WAL
  archiving for point-in-time recovery.
- **How do you drop a role that owns objects?** `REASSIGN OWNED` → `DROP OWNED` → `DROP USER`.
- **Why did the read-only user lose access after a migration?** `GRANT ON ALL TABLES` covers
  only existing tables — use `ALTER DEFAULT PRIVILEGES`.
