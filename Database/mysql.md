# MySQL

> Postgres comparison: **[postgres.md §7](postgres.md)** · Index internals:
> **[indexing.md](indexing.md)**

---

## 1. Setup & client ⭐

```bash
sudo apt-get update
sudo apt-get install python3-dev default-libmysqlclient-dev build-essential
pip install mysqlclient          # ⭐ needs the dev headers above

mysql -u root -p
mysql -u user -p -h host -P 3306 dbname
```

```sql
SHOW DATABASES;              SHOW TABLES;
DESCRIBE users;              -- or:  SHOW COLUMNS FROM users;
SHOW CREATE TABLE users\G    -- ⭐ full DDL including indexes and engine
SHOW INDEX FROM users;
SHOW PROCESSLIST;            -- ⭐ what's running now
SHOW ENGINE INNODB STATUS\G  -- ⭐⭐ deadlocks, lock waits, buffer pool
SELECT VERSION();
```

⭐ **`\G` instead of `;`** gives vertical output — the MySQL equivalent of psql's `\x`, and
essential for reading `SHOW ENGINE INNODB STATUS`.

---

## 2. Users & permissions

```sql
CREATE USER 'appuser'@'%' IDENTIFIED BY 'secret';         -- ⚠️ '%' = any host
CREATE USER 'appuser'@'10.0.%' IDENTIFIED BY 'secret';    -- ⭐ scope by network

GRANT SELECT, INSERT, UPDATE, DELETE ON mydb.* TO 'appuser'@'10.0.%';
FLUSH PRIVILEGES;
SHOW GRANTS FOR 'appuser'@'%';
DROP USER 'olduser'@'%';

-- change the root password
ALTER USER 'root'@'localhost' IDENTIFIED WITH mysql_native_password BY 'newpass';
FLUSH PRIVILEGES;
```

⭐⭐ **In MySQL a user is `user@host`** — `'app'@'localhost'` and `'app'@'%'` are *different
accounts* with separate passwords and grants. "The password works locally but not remotely" is
almost always this.

⚠️ `mysql_native_password` is legacy; **`caching_sha2_password` is the default from MySQL 8**
and is what you should use unless an old client forces otherwise.

---

## 3. Backup, restore & import ⭐

```bash
# ⭐ consistent dump of an InnoDB database (no table locks)
mysqldump -u root -p --single-transaction --routines --triggers mydb > mydb.sql
mysqldump -u root -p --all-databases > all.sql

mysql -u root -p mydb < mydb.sql
```

⭐⭐ **`--single-transaction` is the flag that matters** — it takes a consistent snapshot using
InnoDB's MVCC **without locking tables**, so the application keeps running. Without it,
`mysqldump` locks tables and takes the site down. ⚠️ It only works for InnoDB (MyISAM still
locks).

⚠️ **Large imports fail on packet size** — the fix for `MySQL server has gone away`:

```ini
# /etc/mysql/my.cnf
[mysqld]
max_allowed_packet = 64M
```

```bash
sudo systemctl restart mysql
```

⭐ For big datasets, **`mysqldump` is slow to restore**. Prefer `LOAD DATA INFILE` for bulk
loading, or physical backups (**Percona XtraBackup**) with binlog-based point-in-time recovery —
`mysqldump` alone gives you last-night recovery only.

---

## 4. InnoDB — what you're actually running ⭐⭐

**InnoDB is the default engine and the only one worth using** — ACID, row-level locking, MVCC,
crash recovery, foreign keys. (⚠️ MyISAM: table-level locks, no transactions, no FKs — legacy
only.)

⭐⭐ **The clustered index is InnoDB's defining characteristic:**

```
PRIMARY KEY index  →  leaves contain THE ROW ITSELF          ⭐ the table IS the PK index
Secondary index    →  leaves contain the PRIMARY KEY value   ⚠️ not a row pointer
```

**Three consequences worth stating:**

1. **A secondary-index lookup traverses two trees** — find the PK in the secondary index, then
   find the row in the clustered index.
2. ⚠️⚠️ **A wide primary key bloats *every* secondary index.** A `VARCHAR(36)` UUID PK is copied
   into every secondary index — use `BIGINT` or `BINARY(16)`.
3. ⭐ **Sequential PKs matter more in MySQL than Postgres** — random UUID inserts cause page
   splits in the clustered index, physically fragmenting the table itself.

⭐ **Covering indexes are especially effective here** — if the secondary index contains
everything needed, InnoDB skips the second traversal entirely (`Using index` in `EXPLAIN`).

**Locking:** row-level, plus **gap locks** and **next-key locks** under Repeatable Read to
prevent phantoms. ⚠️ Gap locks cause deadlocks people didn't write explicitly — check
`SHOW ENGINE INNODB STATUS` rather than guessing
([transactions.md §7](transactions.md)).

---

## 5. MySQL-specific behaviour ⚠️

| Behaviour | Note |
|---|---|
| ⚠️⚠️ **No transactional DDL** | an `ALTER` implicitly commits — a failed migration leaves a half-applied schema |
| **Default isolation: Repeatable Read** | ⭐ Postgres uses Read Committed |
| ⚠️ **Case-insensitive collation by default** | `'Ali' = 'ali'` is **true** — surprising, and it affects unique constraints |
| ⚠️ Table names case-sensitive on Linux, not macOS/Windows | breaks deploys between environments |
| **`utf8` is not UTF-8** | ⭐⭐ use **`utf8mb4`** — plain `utf8` is 3-byte and **cannot store emoji** |
| ⚠️ Silent truncation (older/loose modes) | `STRICT_TRANS_TABLES` makes bad data an error |
| `ONLY_FULL_GROUP_BY` | ⭐ on by default in 8.0 — previously MySQL returned an arbitrary row |
| `AUTO_INCREMENT` counter | ⚠️ historically reset on restart in some versions; gaps are normal |

⭐ **`utf8mb4` is the one to remember** — MySQL's `utf8` stores at most 3 bytes per character,
so emoji and some CJK characters cause `Incorrect string value` errors. Always
`CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci`.

⭐ **Check your SQL mode** — strict mode turns silent data corruption into loud errors:

```sql
SELECT @@sql_mode;
SET GLOBAL sql_mode = 'STRICT_TRANS_TABLES,NO_ZERO_DATE,ONLY_FULL_GROUP_BY';
```

---

## 6. Performance ⭐

```sql
EXPLAIN SELECT ...;              -- ⭐ the plan
EXPLAIN ANALYZE SELECT ...;      -- ⭐⭐ 8.0.18+ — actual execution
EXPLAIN FORMAT=JSON SELECT ...;  -- full cost detail
```

**Reading `EXPLAIN` — the `type` column, best to worst:**

```
system > const > eq_ref > ref > range > index > ALL
                                          │       └── ⚠️⚠️ FULL TABLE SCAN
                                          └── full INDEX scan (better, still not a seek)
```

⭐ **`type: ALL` on a large table is the red flag.** Also check `key` (which index was chosen),
`rows` (estimated — compare with reality), and `Extra`: ⭐ `Using index` = covering index
(good), ⚠️ `Using filesort` / `Using temporary` = sorting or materialising to disk.

**Slow query log:**

```sql
SET GLOBAL slow_query_log = 'ON';
SET GLOBAL long_query_time = 1;
SET GLOBAL log_queries_not_using_indexes = 'ON';
-- analyse with:  pt-query-digest  (Percona Toolkit)  ⭐
```

**Key settings:**

| Setting | Guidance |
|---|---|
| ⭐⭐ `innodb_buffer_pool_size` | **~70–80% of RAM** — the single most important MySQL setting |
| `innodb_log_file_size` | larger = better write throughput, slower recovery |
| `innodb_flush_log_at_trx_commit` | ⭐ `1` = fully durable; `2` = faster, ⚠️ may lose ~1s on OS crash |
| `max_connections` | ⭐ keep modest; use ProxySQL for pooling |

⭐ **`innodb_buffer_pool_size` is MySQL's `shared_buffers`, but sized much larger** — it caches
both data and indexes, and it's where nearly all tuning wins come from.

---

## 7. Replication ⭐

```sql
SHOW MASTER STATUS;         SHOW REPLICA STATUS\G      -- ⭐ Seconds_Behind_Source
```

- **Binlog-based**, with ⭐ **GTIDs** (global transaction ids) making failover far easier than
  file/position tracking.
- **Formats:** `ROW` (⭐ the safe default — logs actual row changes), `STATEMENT` (compact but
  ⚠️ non-deterministic functions replicate incorrectly), `MIXED`.
- **Async by default**; semi-sync available.
- ⚠️ **Replica lag** is the same problem as everywhere — a user may not see their own write
  ([scaling.md §2](scaling.md)).
- **Group Replication / InnoDB Cluster** for multi-primary and automated failover;
  **Vitess** for sharding at scale.

⭐ MySQL replication's simplicity and maturity is a genuine reason teams pick it — it's been the
default for large-scale web deployments for two decades.

---

## 8. Interview points

- **MyISAM vs InnoDB? ⭐** InnoDB has transactions, row-level locking, MVCC, crash recovery, and
  foreign keys. MyISAM has table locks and none of that — legacy only.
- **What is a clustered index in InnoDB? ⭐⭐** The primary key index **contains the rows**; the
  table *is* the PK index.
- **Why does PK choice matter more in MySQL? ⭐⭐** Every secondary index stores the PK value, so
  a wide PK bloats them all — and random UUIDs fragment the clustered index itself.
- **How does a secondary index lookup work?** Two traversals — secondary index → PK → clustered
  index; a covering index avoids the second.
- **What's MySQL's default isolation level?** Repeatable Read (Postgres uses Read Committed),
  with gap/next-key locks preventing phantoms.
- **Does MySQL support transactional DDL? ⭐⭐** **No** — DDL implicitly commits, so a failed
  migration can leave a half-applied schema.
- **Why `utf8mb4` instead of `utf8`? ⭐⭐** MySQL's `utf8` is 3-byte and cannot store emoji or
  some CJK characters.
- **What does `--single-transaction` do in `mysqldump`? ⭐** Takes a consistent MVCC snapshot
  without locking tables — the difference between a safe backup and an outage.
- **How do you read `EXPLAIN`? ⭐** The `type` column (`ALL` = full scan, worst), which `key` was
  chosen, estimated `rows`, and `Extra` (`Using index` good, `Using filesort`/`temporary` bad).
- **The most important MySQL setting?** `innodb_buffer_pool_size` — ~70–80% of RAM.
- **What does `innodb_flush_log_at_trx_commit = 2` trade?** Faster commits for up to ~1 second
  of possible loss on an OS crash.
- **`'app'@'localhost'` vs `'app'@'%'`? ⭐** Different accounts — a frequent cause of "works
  locally, fails remotely."
- **Postgres or MySQL? ⭐** Postgres for richer types, transactional DDL, and stricter
  correctness; MySQL for simple high-read workloads, mature replication, and ubiquity.
