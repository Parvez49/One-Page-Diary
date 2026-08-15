# Django — Interview Questions

> Claim first, then the *why*. Depth lives in the linked files.

---

## 1. Architecture & lifecycle

**Walk me through a Django request. ⭐⭐**
nginx (TLS, static) → gunicorn/uvicorn (WSGI/ASGI server) → **middleware top-down** → URL
resolver → view (DRF: auth → permission → throttle → handler) → ORM → response back up
through **middleware in reverse**. → [request_lifecycle.md](request_lifecycle.md)

**What is WSGI? How does ASGI differ?**
A **specification** between server and application, not a server. WSGI is synchronous (one
request per worker); ASGI adds async and long-lived protocols (WebSockets, SSE).
⚠️ ASGI isn't automatically faster — Django's ORM is sync, so `async def` views hop to a
thread pool.

**Is Django MVC or MVT?**
MVT: **Model** = data, **Template** = presentation, **View** = the controller-ish layer.
Django's "view" is what MVC calls a controller; the framework itself is the controller.

**How does middleware work, and why does order matter? ⭐**
An onion — each layer sees the request going down and the response coming back up. Order is
semantic: `AuthenticationMiddleware` needs `SessionMiddleware` to have run;
`SecurityMiddleware` must be first. Returning a response without calling `get_response()`
short-circuits the view.

---

## 2. ORM

**`null=True` vs `blank=True`? ⭐**
Database `NULL` vs form/serializer validation. ⚠️ Never `null=True` on `CharField`/`TextField`
— you get two kinds of empty.

**Are QuerySets lazy?**
Yes. Chaining builds SQL; execution happens on iteration/`list()`/`len()`/slicing-with-step,
and results are then **cached on that object**.

**`exists()` vs `count()` vs `if qs:`?**
`SELECT 1 LIMIT 1` vs `COUNT(*)` vs fetching and caching **every row**.

**What is the N+1 problem, and how do you fix it? ⭐⭐⭐**
One query for the list plus one per row for a lazy relation. `select_related` (FK/O2O — SQL
JOIN) and `prefetch_related` (M2M/reverse FK — second query joined in Python).
⚠️ It usually hides in serializers and `SerializerMethodField`.
→ [queries.md](queries.md)

**Why not always `select_related`?**
Joining a to-many relation multiplies rows — 100 books × 10 authors = 1000 rows with every
book repeated. Prefetch avoids the fan-out.

**Why didn't my `prefetch_related` help?**
You called `.filter()`/`.count()` on the related manager, which re-queries. Only `.all()` uses
the cache — filter in Python or use `Prefetch(queryset=...)`.

**What does `F()` solve? ⭐⭐**
Read-modify-write races. `update(stock=F("stock") + 1)` becomes `SET stock = stock + 1` — one
atomic SQL statement, so concurrent increments compose. The Python version loses updates.

**`aggregate()` vs `annotate()`?**
One summary dict for the whole queryset vs a computed column added to each row.
⚠️ `aggregate(Sum(...))` returns `None`, not `0`, when empty — wrap in `Coalesce`.

**What do `.update()` and `bulk_create()` skip?**
`save()`, **signals**, and `auto_now`. That's why they're fast — and why signal-based cache
invalidation silently misses them.

**When would you use a `through` model instead of a plain M2M? ⭐**
When the relationship itself carries data (quantity, `price_at_purchase`, joined_at) or needs
its own constraints/indexes. A plain M2M still creates a join table — you just can't put
anything on it.

**How do you stop two users buying the last item?**
`select_for_update()` inside `atomic()`, or an atomic `F()` decrement plus a
`CheckConstraint(stock__gte=0)`. → [orm.md](orm.md)

**Why `transaction.on_commit` around a Celery call? ⭐⭐**
The broker is faster than your commit — the worker can start before the row is visible and
raise `DoesNotExist`. Intermittent, never reproduces locally.

---

## 3. Migrations

**How does Django know what's applied?**
Rows in `django_migrations`, plus the dependency graph across migration files.

**Why `apps.get_model()` in a data migration? ⭐**
It returns the **historical** model as of that migration. Importing the real model breaks
every fresh `migrate` once the schema moves on.

**How do you rename a column with zero downtime? ⭐⭐**
Expand/contract: add the new column → dual-write and backfill → switch reads → drop the old
one in a later deploy. A bare `RenameField` breaks old code still running mid-deploy.

**Which migrations are dangerous?**
Anything taking an exclusive lock on a big table: type changes, non-concurrent index creation,
validating constraints. ⭐ Read `sqlmigrate` output before deploying.

→ [migrations.md](migrations.md)

---

## 4. DRF

**Walk me through a DRF request.**
Parser → authentication → permission → throttle → handler → `get_queryset` → filter backends →
pagination → serializer → renderer.

**Where do you prevent N+1 in DRF? ⭐**
`get_queryset()` — `select_related`/`prefetch_related`. Watch `SerializerMethodField` (a query
per row) and nested serializers.

**Why is `fields = "__all__"` dangerous? ⭐**
Any field added to the model is instantly exposed **and writable** — `is_staff`,
`internal_notes`, `password_hash`.

**How do you set `owner` on create?**
`perform_create(serializer)` → `serializer.save(owner=self.request.user)`. ⚠️ Never from client
input.

**`validate_<field>` vs `validate()`?**
Single field vs cross-field. ⚠️ DRF doesn't call `Model.full_clean()`, so model validators
don't run — use database constraints as the real guarantee.

**401 vs 403? ⭐⭐**
401 = not authenticated (send `WWW-Authenticate`); 403 = authenticated but not permitted.
Retrying with the same token can fix a 401, never a 403.

**When do you return 202?**
Work accepted and queued (Celery) but not finished.

**`has_permission` vs `has_object_permission`? ⭐**
Before the view runs vs per-object inside `get_object()`. ⚠️ Object permissions **never fire
on list endpoints** — scope the queryset instead.

**Which pagination for an infinite feed? ⭐**
Cursor — O(1) at any depth and stable when rows are inserted. Offset pagination re-scans every
skipped row and duplicates/skips items. → [drf.md](drf.md)

---

## 5. Auth & security

**Session vs JWT — which and why? ⭐⭐**
Sessions for first-party browser apps: server-side, **instantly revocable**, HttpOnly.
JWT for multiple services/mobile/cross-domain. **Statelessness costs you revocation** — a JWT
is valid until it expires, so use 15-minute access tokens plus a revocable refresh token.

**Where should a browser store a JWT?**
`HttpOnly`+`Secure`+`SameSite` cookie (then handle CSRF), **not `localStorage`** — any XSS
reads it. And a JWT is signed, **not encrypted**: never put secrets in the payload.

**CSRF vs CORS? ⭐⭐⭐**
CSRF is an **attack** (forged state-changing requests riding your cookies). CORS is a
**browser mechanism that relaxes** the same-origin policy for JavaScript.
⭐ **CORS does not prevent CSRF** — a plain `<form>` POST isn't subject to CORS at all; the
browser sends it and only blocks reading the response. The damage happens server-side.

**Do token APIs need CSRF protection?**
Not for `Authorization: Bearer` (browsers don't attach it automatically). **Yes** if the token
is in a cookie.

**How does Django prevent SQL injection, and how do you break it?**
The ORM parameterises everything. `raw()`/`extra()`/cursor calls with f-strings reintroduce
it — always use `%s` placeholders.

**How does Django prevent XSS, and where does it fail?**
Template auto-escaping. It fails via `|safe`, `mark_safe`, and ⭐ **JSON APIs** — DRF doesn't
escape, so stored payloads detonate in the SPA (`dangerouslySetInnerHTML`). CSP is the real
defence in depth.

**What is IDOR, and how do you prevent it? ⭐⭐**
Reading another user's object by guessing the id. Fix: scope in `get_queryset()` so
`get_object()` can't reach it — return 404, not 403, to avoid confirming existence.

**What does `DEBUG=True` leak in production?**
Settings, env vars, SQL, and tracebacks to anyone who triggers an error — and it disables
`ALLOWED_HOSTS`. → [security.md](security.md)

---

## 6. Performance & scale

**The site is slow — how do you diagnose it? ⭐**
Count queries first (debug-toolbar/silk/APM). Fix N+1 → check indexes with `EXPLAIN ANALYZE`
→ paginate → move work to Celery → **then** cache. Caching first just hides the problem until
the cache is cold.

**When do you add caching, and what's hard about it?**
After the queries are right. The hard parts are **invalidation** and **stampedes**; prefer a
short TTL to elaborate invalidation.
⚠️ `LocMemCache` is per-process — every gunicorn worker has its own.

**What's wrong with `@cache_page` on a logged-in view? ⭐**
It keys on URL, not user — one user's page gets served to everyone.

**Why move work to Celery?**
Latency, reliability (a failed email shouldn't roll back a paid order), and retries.
⭐ Pass **IDs, not objects**; make tasks **idempotent** (at-least-once delivery); enqueue in
`on_commit`.

**Redis vs RabbitMQ vs Kafka? ⭐**
Redis: simplest, already deployed, ⚠️ can lose messages. RabbitMQ: real delivery guarantees,
DLQ, routing. Kafka: replayable event log, many independent consumers.

**Is Celery event-driven architecture?**
No — it's a **command queue**: point-to-point, the producer names the task, nothing is
retained. EDA publishes **facts** that N unknown consumers can replay.
→ [async_tasks.md](async_tasks.md)

**How many gunicorn workers, and what limits you?**
`2 × cores + 1` to start — but ⚠️ **database connections** usually cap you first (each worker
holds its own). PgBouncer.

**How do you deploy without downtime? ⭐**
Backwards-compatible migrations run **once**, rolling replicas behind readiness probes, then
restart Celery workers (they run old code until restarted).

---

## 7. Testing

**What do you test in a Django app? ⭐**
Mostly API-level tests through real URLs — they cover routing, auth, permissions, serializers
and the ORM together — plus unit tests for business logic and a regression test per fixed bug.

**How do you stop an N+1 from coming back? ⭐⭐**
`django_assert_num_queries` with a **fixed** expected count and several rows in the fixture.

**Factories or fixtures?**
Factories — they declare only what the test cares about and don't rot with schema changes.

**Why does my mock not work?**
You patched where the function is **defined**, not where it's **used**.
→ [testing.md](testing.md)

---

## 8. Rapid fire

| Question | Answer |
|---|---|
| `get()` vs `filter().first()` | Raises `DoesNotExist`/`MultipleObjectsReturned` vs returns `None`. |
| `on_delete=CASCADE` risk | Silent mass deletion — `PROTECT` is the safer default. |
| Signals fire on `.update()`? | ⚠️ **No** — bulk operations bypass `save()`. |
| Should signals hold business logic? | No — synchronous, invisible, skipped by bulk ops. Call the service explicitly. |
| `values()` vs model instances | Dicts, no model construction — much cheaper for read-only work. |
| `only()`/`defer()` risk | Touching a deferred field = one query **per instance**. |
| Why is deep `?page=5000` slow? | `OFFSET` still scans every skipped row. Use cursor pagination. |
| `select_for_update()` requires? | Being inside `atomic()`. Keep the block tiny. |
| Custom user model — when? | ⭐ Before the first migration. Changing it later is painful. |
| `Model.save()` runs validators? | ⚠️ No — `full_clean()` isn't called. Use DB constraints. |
| Django serves static in prod? | ⚠️ No — nginx/CDN. `runserver` only. |
| Where do user uploads go? | Object storage (S3), never the app server's disk. |
| Two `beat` processes? | ⚠️ Every periodic task fires twice — run exactly one. |
| Composite index `(a, b)` serves `WHERE b=?` | ⚠️ No — leftmost prefix rule. |
| `ordering_fields = "__all__"` | ⚠️ Clients can sort by unindexed columns → full table sorts. |
| `@csrf_exempt` on a webhook | ⚠️ Verify a **signature** instead. |
| Where does authorisation scoping go? | ⭐ `get_queryset()` — never a query-param filter. |

---

## 9. The five to have ready

1. **N+1** — what it is, `select_related` vs `prefetch_related`, and how you'd *detect* it.
2. **CSRF vs CORS** — attack vs browser mechanism; CORS doesn't stop CSRF.
3. **Session vs JWT** — statelessness costs revocation.
4. **`F()` / `select_for_update`** — how you handle concurrent writes.
5. **Zero-downtime migrations** — expand/contract, because old and new code run together.
