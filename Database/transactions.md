# Transactions, Isolation & Concurrency

> Locking impact on queries: **[performance.md](performance.md)** · Distributed trade-offs:
> **[scaling.md](scaling.md)**

---

## 1. ACID ⭐⭐

```sql
BEGIN;
  UPDATE accounts SET balance = balance - 100 WHERE id = 1;
  UPDATE accounts SET balance = balance + 100 WHERE id = 2;
COMMIT;                                    -- ⭐ both, or neither
```

| Property | Guarantee | Implemented by |
|---|---|---|
| **Atomicity** | ⭐ all statements succeed or none do | undo log / rollback segment |
| **Consistency** | constraints hold before and after | ⭐ *your* constraints + the engine |
| **Isolation** | ⭐ concurrent transactions don't corrupt each other | MVCC / locking |
| **Durability** | committed data survives a crash | ⭐ **write-ahead log (WAL)** + fsync |

⭐ **The two worth explaining mechanically:**

**Durability = WAL.** Changes are written to a sequential log and **fsynced before commit
returns**; the data pages are flushed later. A crash replays the log. Sequential log writes are
far cheaper than random data-page writes, which is why this design is universal.

⚠️ **Consistency is the odd one out** — it's not enforced by the engine alone. It means the
database moves from one *valid* state to another according to **your constraints**
(`CHECK`, `FOREIGN KEY`, `UNIQUE`). If you didn't declare the rule, ACID won't protect it
([fundamentals.md](fundamentals.md)).

---

## 2. The concurrency anomalies ⭐⭐

**Know these by name — isolation levels are defined by which ones they prevent.**

| Anomaly | What happens |
|---|---|
| **Dirty read** | ⚠️ read data another transaction wrote but **hasn't committed** — it may roll back |
| **Non-repeatable read** | ⭐ read the **same row** twice, get different values (another txn committed an UPDATE between) |
| **Phantom read** | ⭐ re-run the **same query**, get **different rows** (another txn INSERTed/DELETEd) |
| **Lost update** | ⚠️⚠️ two read-modify-writes; the second overwrites the first |
| **Write skew** | ⭐ each txn reads, sees a valid state, writes — together they break an invariant |

⭐⭐ **Non-repeatable read vs phantom read** — the distinction that gets asked:
non-repeatable is about **an existing row changing**; phantom is about **the set of matching
rows changing**. Repeatable Read stops the former; only Serializable reliably stops the latter.

⭐ **Write skew is the subtle one** — and the best example to have ready:

> Two doctors are on call; the rule is "at least one must remain on call." Both simultaneously
> check *"is anyone else on call?"*, both see yes, and both sign off. **Neither transaction did
> anything invalid on its own**, but the invariant is broken. No row conflicts, so only
> **Serializable** prevents it.

---

## 3. Isolation levels ⭐⭐

| Level | Dirty read | Non-repeatable | Phantom | Cost |
|---|---|---|---|---|
| **Read Uncommitted** | ⚠️ possible | possible | possible | ⚠️ almost never used |
| **Read Committed** | ⭐ prevented | possible | possible | ⭐ **Postgres default** |
| **Repeatable Read** | prevented | ⭐ prevented | ⚠️ possible* | ⭐ **MySQL/InnoDB default** |
| **Serializable** | prevented | prevented | ⭐ prevented | ⚠️ highest — retries/aborts |

\* ⭐ In practice **Postgres Repeatable Read prevents phantoms** (snapshot isolation), and
**InnoDB Repeatable Read prevents them for reads** via next-key locking — the SQL standard's
table describes what's *permitted*, not what each engine does. Saying this shows you've read
past the textbook.

```sql
BEGIN ISOLATION LEVEL SERIALIZABLE;        -- Postgres
SET TRANSACTION ISOLATION LEVEL READ COMMITTED;
```

⭐ **How to choose:** Read Committed for almost everything. **Repeatable Read** when a
transaction must see one consistent snapshot (a report, a multi-step calculation).
**Serializable** for invariants across multiple rows that constraints can't express — and
⚠️ **you must be prepared to catch serialization failures and retry**, because Serializable
works by *aborting* conflicting transactions, not by making them wait.

⚠️ **Read Committed re-reads a fresh snapshot for every statement**, so two `SELECT`s in one
transaction can disagree. That surprises people writing multi-statement business logic.

---

## 4. MVCC ⭐⭐

**Multi-Version Concurrency Control — the reason modern databases barely block readers.**

⭐⭐ **The core idea: writers create a *new version* of a row instead of overwriting it.** Each
transaction sees the versions that were committed when its snapshot began.

```
Row v1 (xmin=100, xmax=205)   ← visible to transactions started before 205
Row v2 (xmin=205, xmax=∞)     ← visible to transactions started after 205
```

⭐ **The consequence to state: readers never block writers, and writers never block readers.**
Only writer-vs-writer on the *same row* conflicts. That's why a long analytical `SELECT` doesn't
freeze your application — a genuine advantage over pure two-phase locking.

**The cost — and Postgres and MySQL pay it differently:**

| | **Postgres** | **MySQL/InnoDB** |
|---|---|---|
| Old versions live | ⚠️ **in the table itself** (dead tuples) | in a separate **undo log** |
| Cleanup | ⭐⭐ **VACUUM** (autovacuum) | purge thread |
| Failure mode | ⚠️ **table bloat**; a long-running txn blocks vacuum | undo log growth |

⚠️⚠️ **In Postgres, an idle-in-transaction session prevents vacuum from cleaning *any* newer
dead tuples** — the table bloats, indexes bloat, and performance degrades globally. A forgotten
`BEGIN` in application code is a real production incident. Monitor
`pg_stat_activity` for `idle in transaction` and set `idle_in_transaction_session_timeout`.

⚠️ **Transaction ID wraparound** — Postgres XIDs are 32-bit; if vacuum falls far enough behind,
the database **refuses writes** to protect itself. Rare but catastrophic; autovacuum exists to
prevent it.

---

## 5. Locking ⭐

| Lock | Blocks |
|---|---|
| **Shared (S) / read** | other writers, not other readers |
| **Exclusive (X) / write** | ⭐ everything else on that row |
| **Row-level** | ⭐ the normal case — high concurrency |
| **Table-level** | ⚠️ DDL, some ALTERs — an outage risk on big tables |
| **Advisory** | application-defined (`pg_advisory_lock`) — ⭐ cross-process mutex |

```sql
BEGIN;
SELECT * FROM inventory WHERE id = 1 FOR UPDATE;    -- ⭐ pessimistic row lock
UPDATE inventory SET stock = stock - 1 WHERE id = 1;
COMMIT;                                             -- ⭐ lock released HERE

SELECT ... FOR UPDATE NOWAIT;        -- fail fast instead of waiting
SELECT ... FOR UPDATE SKIP LOCKED;   -- ⭐⭐ the job-queue pattern
SELECT ... FOR SHARE;                -- read lock
```

⭐ **`SKIP LOCKED` is how you build a work queue in SQL** — each worker grabs the next
*unlocked* row, so N workers pull disjoint jobs without coordination or a message broker.

⚠️⚠️ **Locks are held until COMMIT.** Doing slow work inside a transaction — an HTTP call, a
file upload, sending email — holds locks for that entire duration and is a top cause of
production pile-ups. **Keep transactions short; do I/O outside them.**

---

## 6. Optimistic vs pessimistic concurrency ⭐⭐

**The classic "two users edit the same record" question.**

```sql
-- PESSIMISTIC — lock first, assume conflict
BEGIN;
SELECT stock FROM items WHERE id=1 FOR UPDATE;    -- ⭐ others wait here
UPDATE items SET stock = stock - 1 WHERE id = 1;
COMMIT;

-- OPTIMISTIC — no lock; detect conflict at write time via a version column
UPDATE items SET stock = stock - 1, version = version + 1
WHERE id = 1 AND version = 7;                     -- ⭐ 0 rows affected ⇒ someone else won
```

| | **Pessimistic** | **Optimistic** |
|---|---|---|
| Assumes | conflicts are common | ⭐ conflicts are rare |
| Cost | ⚠️ contention, deadlock risk, holds locks | ⭐ no locks; ⚠️ retry on conflict |
| Best for | inventory, seat booking, payments | ⭐ user profile edits, CMS content |

⭐ **The third option, and often the best: make the operation atomic** so there's nothing to
lock or retry:

```sql
UPDATE items SET stock = stock - 1 WHERE id = 1 AND stock > 0;   -- ⭐⭐ single statement
```

A single `UPDATE` is atomic — the read-modify-write happens inside the database, so the
**lost update** anomaly can't occur. This is what `F()` expressions do in Django
([../Web/Django/orm.md](../Web/Django/orm.md)), and pairing it with a
`CHECK (stock >= 0)` constraint makes overselling structurally impossible.

---

## 7. Deadlocks ⭐

```
Txn A: locks row 1 → wants row 2
Txn B: locks row 2 → wants row 1        ⚠️ circular wait
```

The engine detects the cycle and **kills one transaction** (`deadlock detected`).

⭐⭐ **Prevention — in order of effectiveness:**

1. **Acquire locks in a consistent order** everywhere (e.g. always ascending id). This alone
   eliminates most deadlocks, and it's the answer interviewers want.
2. **Keep transactions short** — less time holding locks.
3. **Touch fewer rows** — batch updates in a deterministic order.
4. **Set `lock_timeout`** so a stuck transaction fails fast instead of piling up.
5. ⭐ **Retry on deadlock** — deadlocks are *expected* under load, not a bug to eliminate.
   Application code should catch the error and retry with backoff.

⚠️ Deadlocks also arise from **foreign key checks** and **index gap locks** you didn't write
explicitly — inspect `pg_stat_activity` / `SHOW ENGINE INNODB STATUS` rather than guessing.

---

## 8. Distributed transactions ⭐

⚠️ **Across services or shards, ACID stops being free.**

- **2PC (two-phase commit)** — a coordinator asks everyone to prepare, then commit. ⚠️
  Blocking: if the coordinator dies after prepare, participants hold locks indefinitely. Rarely
  used in modern microservices.
- ⭐ **Saga** — a sequence of local transactions, each with a **compensating action** to undo it.
  Eventually consistent, no distributed locks. This is the practical pattern
  ([../SDLC/architecture.md](../SDLC/architecture.md)).
- ⭐ **Outbox pattern** — write the business change *and* an event row in **one local
  transaction**, then publish the event asynchronously. Solves "the DB committed but the message
  never sent" without 2PC.
- **Idempotency keys** — because at-least-once delivery means retries will happen.

⭐ **The senior framing:** *"Within one database, use a transaction. Across services, don't
reach for distributed transactions — redesign for eventual consistency with sagas and an
outbox, and make every operation idempotent."*

---

## 9. Interview points

- **Explain ACID. ⭐⭐** Atomicity (all or nothing, via undo), Consistency (your constraints),
  Isolation (MVCC/locks), Durability (⭐ **WAL fsynced before commit**).
- **Which ACID property isn't the engine's job alone?** Consistency — it enforces *your*
  declared constraints.
- **Name the concurrency anomalies. ⭐⭐** Dirty read, non-repeatable read, phantom read, lost
  update, write skew.
- **Non-repeatable vs phantom read? ⭐** An existing row changed vs the *set* of matching rows
  changed.
- **What is write skew, and which level prevents it? ⭐** Two individually-valid transactions
  break a shared invariant (the on-call doctors example) — only **Serializable**.
- **What are the isolation levels and the defaults?** Read Uncommitted → Serializable;
  **Postgres defaults to Read Committed**, **MySQL to Repeatable Read**.
- **What is MVCC and why does it matter? ⭐⭐** Writers create new row versions instead of
  overwriting, so **readers never block writers and vice versa**.
- **What does MVCC cost? ⭐** Old versions must be cleaned up — **VACUUM** in Postgres (⚠️ a
  long-running transaction blocks it and causes bloat), undo logs in InnoDB.
- **Optimistic vs pessimistic locking? ⭐⭐** Lock upfront (contention, deadlocks) vs detect at
  write time with a version column (retry). Best of all: a single atomic `UPDATE`.
- **How do you prevent overselling the last item? ⭐** `SELECT ... FOR UPDATE`, or an atomic
  `UPDATE ... WHERE stock > 0` plus a `CHECK` constraint.
- **What causes deadlocks and how do you prevent them? ⭐⭐** Circular lock waits — acquire
  locks in a consistent order, keep transactions short, and **retry**.
- **Why keep transactions short? ⭐** Locks are held until commit, and in Postgres open
  transactions block vacuum and bloat the table. Never do HTTP calls inside one.
- **How do you build a job queue in SQL?** `SELECT ... FOR UPDATE SKIP LOCKED`.
- **How do transactions work across microservices?** They don't — use **sagas with compensating
  actions** and the **outbox pattern**, with idempotent operations.
