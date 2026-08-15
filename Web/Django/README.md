# Django & DRF — Index

Domain knowledge for **senior/staff backend interviews** and production work. Assumes you can
already build CRUD — the focus is on what breaks at scale, the security holes that recur, and
the answers that distinguish "I've shipped Django" from "I've operated Django."

**Conventions:** ⭐ = high interview value · ⚠️ = a trap that causes real incidents ·
every file ends with an **Interview points** section.

---

## Files

| File | Covers | Interview weight |
|---|---|---|
| [request_lifecycle.md](request_lifecycle.md) | **Request path**, WSGI/ASGI, **middleware order**, URLs, views, **signals**, settings | ⭐⭐⭐ |
| [orm.md](orm.md) | Models, `null` vs `blank`, `on_delete`, **`through` models**, lazy QuerySets, **Q/F**, aggregation, **transactions & locking** | ⭐⭐⭐ |
| [queries.md](queries.md) | **N+1**, `select_related` vs `prefetch_related`, `only`/`values`, **indexes & EXPLAIN**, pagination, bulk ops | ⭐⭐⭐ |
| [drf.md](drf.md) | View ladder, **ViewSets**, routers, **serializers**, pagination, **status codes (401 vs 403)**, versioning | ⭐⭐⭐ |
| [auth.md](auth.md) | Custom user model, **session vs token vs JWT**, permissions, **object vs list scoping**, sessions | ⭐⭐⭐ |
| [security.md](security.md) | Deploy checklist, SQL injection, XSS, **CSRF vs CORS**, headers, **IDOR**, secrets | ⭐⭐⭐ |
| [caching.md](caching.md) | Backends, key design, **invalidation**, **stampede/penetration/avalanche**, CDN layers | ⭐⭐ |
| [async_tasks.md](async_tasks.md) | Celery rules, **`on_commit` race**, idempotency, **Redis vs RabbitMQ vs Kafka**, Celery ≠ EDA | ⭐⭐⭐ |
| [migrations.md](migrations.md) | Migration graph, **data migrations**, **zero-downtime expand/contract**, locking | ⭐⭐ |
| [filtering.md](filtering.md) | django-filter, FilterSets, search/ordering, **why filters ≠ authorisation** | ⭐⭐ |
| [throttling.md](throttling.md) | DRF throttles, **rate limiting ≠ DDoS defence**, algorithms, atomic counters | ⭐⭐ |
| [testing.md](testing.md) | pytest-django, **factories**, **query-count tests**, mocking boundaries | ⭐⭐ |
| [deployment.md](deployment.md) | nginx + gunicorn, **WSGI vs ASGI**, workers & connections, deploy order, scaling | ⭐⭐ |
| [graphql.md](graphql.md) | Over/under-fetching, schema, **DataLoader**, depth attacks, **REST vs GraphQL** | ⭐ |
| [interview.md](interview.md) | **Q&A across every topic** + rapid fire | ⭐⭐⭐ |

---

## Suggested study order

1. **[queries.md](queries.md)** — N+1 is the single most-asked Django performance question and
   the most common real bug.
2. **[orm.md](orm.md)** — `F()`, transactions, and `select_for_update` are the concurrency
   answers.
3. **[drf.md](drf.md)** + **[auth.md](auth.md)** — the API surface and who's allowed to touch
   it.
4. **[security.md](security.md)** — CSRF vs CORS and IDOR are reliable discriminators.
5. **[request_lifecycle.md](request_lifecycle.md)** — "walk me through a request" is a
   standard opener.
6. **[async_tasks.md](async_tasks.md)** — the `on_commit` race and idempotency show production
   scars.
7. **[caching.md](caching.md)**, **[migrations.md](migrations.md)**,
   **[deployment.md](deployment.md)** — operating it, not just building it.
8. **[filtering.md](filtering.md)**, **[throttling.md](throttling.md)**,
   **[testing.md](testing.md)**, **[graphql.md](graphql.md)** — supporting depth.
9. **[interview.md](interview.md)** — rehearse out loud the day before.

---

## The senior answers worth memorising

| Question | Short answer |
|---|---|
| What is N+1? ⭐ | One query for the list + one per row for a lazy relation. |
| `select_related` vs `prefetch_related` | JOIN for FK/O2O vs second query for M2M/reverse (joins fan out rows). |
| Prefetch didn't help | You called `.filter()`/`.count()` on the related manager — only `.all()` uses the cache. |
| Concurrent increments | `F("stock") + 1` — atomic in SQL; Python read-modify-write loses updates. |
| Celery task can't find the row | Enqueue inside `transaction.on_commit`. |
| CSRF vs CORS ⭐ | An attack vs a browser mechanism that *relaxes* same-origin. CORS doesn't stop CSRF. |
| Session vs JWT | Statelessness costs **revocation** — short access + revocable refresh. |
| JWT in `localStorage`? | ⚠️ Any XSS reads it. `HttpOnly` cookie + CSRF defence. |
| 401 vs 403 | Not authenticated vs authenticated-but-forbidden. |
| User A reads user B's record | **IDOR** — scope `get_queryset()`; object permissions don't run on lists. |
| `fields = "__all__"` | New model fields become exposed and writable. |
| Signals on `.update()` | ⚠️ Don't fire — bulk ops bypass `save()`. |
| Zero-downtime rename | Expand/contract across deploys — old and new code run together. |
| Caching an N+1 | Hides it until the cache is cold, then the stampede kills the DB. |
| What caps your scaling? | Database connections, not CPU — PgBouncer. |
| Can DRF throttling stop a DDoS? | No — the request already consumed a worker. That's the edge's job. |

---

## Related directories

`../NextJS/` frontend · `../basics.md` web fundamentals ·
`../../Language/Python/` Python depth · `../../Database/` SQL, indexes, NoSQL ·
`../../SDLC/` architecture & design patterns · `../../Deploy/` Docker, K8s, nginx ·
`../../CICD/` pipelines · `../../CyberSecurity/` security · `../../linux/` shell & git
