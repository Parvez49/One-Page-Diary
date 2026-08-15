# Deployment — WSGI/ASGI, Servers, Scaling

> Migration sequencing: **[migrations.md](migrations.md)** · Settings hardening: **[security.md](security.md)** ·
> Infra: **[../../Deploy/](../../Deploy/)** · **[../../linux/systemd.md](../../linux/systemd.md)**

---

## 1. The production stack ⭐

```
Internet
   │
   ▼
CDN / WAF              static assets, TLS, DDoS absorption
   │
   ▼
nginx                  ⭐ TLS termination, /static/ + /media/, gzip, buffering, rate limit
   │  proxy_pass unix:/run/gunicorn.sock
   ▼
gunicorn (WSGI)        ⭐ process manager: N workers, each running Django
   │
   ▼
Django  ──▶ PostgreSQL (+ PgBouncer)
        ──▶ Redis (cache, sessions, Celery broker)
        ──▶ Celery workers + beat
```

⚠️⚠️ **`runserver` is never production.** Single-threaded, auto-reloading, serves static files,
no process supervision, and it explicitly says so in the docs.

⭐ **Why nginx in front of gunicorn:** gunicorn is a slow-client magnet — a client dribbling a
request body ties up a whole worker (a Slowloris attack for free). nginx **buffers** requests
and responses, serves static files without touching Python, terminates TLS, and handles
compression. Gunicorn's own docs recommend it.

---

## 2. WSGI vs ASGI ⭐⭐

| | **WSGI** | **ASGI** |
|---|---|---|
| Model | ⭐ **synchronous** — one request per worker at a time | async event loop; many concurrent requests per worker |
| Protocols | HTTP only | ⭐ HTTP, **WebSocket**, SSE, long-lived connections |
| Servers | gunicorn, uWSGI | uvicorn, hypercorn, daphne |
| Best for | ⭐ typical CRUD apps (most Django) | WebSockets, high-concurrency I/O, streaming |

```bash
gunicorn config.wsgi:application --workers 5 --bind unix:/run/gunicorn.sock
gunicorn config.asgi:application -k uvicorn.workers.UvicornWorker --workers 5   # ⭐ ASGI
```

⭐⭐ **ASGI is not automatically faster.** Django's ORM is synchronous; an `async def` view
calling the ORM goes through `sync_to_async`, hopping to a thread pool — often *slower* than
plain WSGI plus more workers. ASGI wins when you genuinely need concurrent I/O or persistent
connections (WebSockets via Channels). Saying "we moved to ASGI for performance" without that
context is a red flag.

⚠️ **`SynchronousOnlyOperation`** — calling the ORM from async context without
`sync_to_async`. The reverse trap: a blocking call inside an async view stalls the whole event
loop ([../../Language/Python/concurrency.md](../../Language/Python/concurrency.md)).

**Worker maths:**

```bash
--workers $((2 * $(nproc) + 1))       # ⭐ the standard starting point for sync workers
--worker-class gthread --threads 4     # ⭐ I/O-bound: threads inside each process
--timeout 30 --graceful-timeout 30
--max-requests 1000 --max-requests-jitter 100    # ⭐ recycle workers (memory high-water mark)
```

⚠️ **Each worker is a full Python process holding its own DB connections.** 8 workers × 4
Django instances × `CONN_MAX_AGE` connections can exhaust Postgres's `max_connections` long
before CPU matters — this is the real scaling ceiling. **PgBouncer** (transaction pooling) is
the fix.

⚠️ `--max-requests` without **jitter** makes all workers recycle simultaneously → a periodic
latency spike.

---

## 3. Settings & configuration

```
config/settings/
├── base.py        shared
├── local.py       DEBUG=True, console email
├── test.py
└── production.py  ⭐ strict
```

```python
import environ
env = environ.Env()

SECRET_KEY  = env("DJANGO_SECRET_KEY")            # ⭐ crashes at boot if missing — good
DEBUG       = env.bool("DJANGO_DEBUG", default=False)
DATABASES   = {"default": env.db("DATABASE_URL")}
CONN_MAX_AGE = 60                                  # ⭐ persistent connections
```

⭐ **Twelve-factor: config in the environment.** Same image promoted from staging to
production, only env vars differ. Secrets from a manager (Vault, AWS Secrets Manager, k8s
secrets) — ⚠️ never committed, never baked into the image.

⭐ **Fail fast at startup** on missing required config. A `default=""` that silently disables
auth is worse than a container that refuses to boot.

⚠️ `CONN_MAX_AGE` with **PgBouncer in transaction mode** must be `0` — otherwise Django holds
a pooled connection and defeats the pooler.

---

## 4. Static & media

```python
STATIC_ROOT = "/srv/app/staticfiles"          # ⭐ collectstatic target
STORAGES = {
    "staticfiles": {"BACKEND": "django.contrib.staticfiles.storage.ManifestStaticFilesStorage"},
    "default": {"BACKEND": "storages.backends.s3.S3Storage"},     # ⭐ user uploads → S3
}
```

```bash
python manage.py collectstatic --noinput
```

⭐ **`ManifestStaticFilesStorage` hashes filenames** (`app.a3f9c2.js`), so you can serve them
with `Cache-Control: max-age=31536000, immutable` and invalidate by changing the name. That's
the whole cache-busting strategy.

⚠️⚠️ **Never store user uploads on the app server's local disk.** They vanish on redeploy,
don't exist on the other replicas, and can't be scaled. S3/GCS + CDN.

⚠️ **Serve user-uploaded files from a separate domain** — an uploaded HTML/SVG file served
from your app's origin executes with your cookies ([security.md](security.md)).

`whitenoise` is a reasonable middle ground when you have no nginx (Heroku, small containers).

---

## 5. Deploy sequence ⭐

```bash
# 1. build & push image
# 2. run migrations ONCE (not per replica)
python manage.py migrate --noinput
# 3. collectstatic → CDN
# 4. rolling restart of app replicas
# 5. restart Celery workers (⭐ they hold OLD code until restarted)
```

⚠️⚠️ **Migrations must be backwards compatible for the duration of a rolling deploy** — old
and new code run against one database simultaneously. Expand/contract, never a bare rename
([migrations.md §4](migrations.md)).

⚠️ **Run migrations from exactly one place** — a k8s `Job` or an init container with a lock,
not from every pod's entrypoint. Concurrent `migrate` runs race on `django_migrations`.

⭐ **Zero-downtime restarts:** gunicorn reloads on `SIGHUP`; better, use overlapping
replicas behind the load balancer with a **readiness probe** so traffic only shifts to a pod
that's actually up. `graceful-timeout` lets in-flight requests finish.

```python
# health checks — ⭐ distinguish the two
path("healthz/", lambda r: HttpResponse("ok")),        # liveness: is the process alive
path("readyz/",  readiness),                           # readiness: DB + cache reachable
```

⚠️ **A readiness check that hits the database will take your whole fleet out** when the
database blips — every pod fails readiness at once. Keep liveness dumb.

---

## 6. Observability

```python
LOGGING = {                       # ⭐ log to stdout — the platform collects it
    "version": 1,
    "handlers": {"console": {"class": "logging.StreamHandler",
                             "formatter": "json"}},
    "root": {"handlers": ["console"], "level": "INFO"},
}
```

⭐ **Structured JSON logs to stdout** ([../../linux/systemd.md](../../linux/systemd.md)) —
never manage log files or rotation in the app. Attach a **request/correlation id** in
middleware so one user's journey is traceable across web, worker, and database logs.

**What to watch:** p50/p95/p99 latency, error rate, **queue depth**, DB connection count and
slow queries, worker restarts, and cache hit rate. Sentry for exceptions;
OpenTelemetry/Datadog for traces.

⚠️ **Log level `DEBUG` in production** floods disk and leaks data. `INFO`, with `DEBUG`
toggleable per-module.

---

## 7. Scaling order ⭐

Cheapest and most effective first:

1. **Fix the queries** — indexes, N+1 ([queries.md](queries.md)). Usually the whole problem.
2. **Cache** ([caching.md](caching.md)).
3. **Move slow work to Celery** ([async_tasks.md](async_tasks.md)).
4. **Scale out web workers** (stateless — ⭐ requires shared sessions/cache, no local disk).
5. **Connection pooling** (PgBouncer), then **read replicas** for read-heavy loads.
6. **Shard / split services** — last resort, high complexity
   ([../../SDLC/architecture.md](../../SDLC/architecture.md)).

⭐ **Django scales horizontally only if the app is stateless.** Local-disk uploads, in-process
caches, and in-memory sessions all break the moment there's a second replica — that's the
actual work of "making it scalable."

---

## 8. Interview points

- **Why not `runserver` in production?** Single-threaded, no supervision, auto-reload, serves
  static — explicitly not designed for it.
- **What does gunicorn do that Django doesn't?** Process management: workers, restarts,
  timeouts, graceful reloads.
- **Why nginx in front? ⭐** Buffers slow clients (protecting workers), serves static files,
  terminates TLS, compresses.
- **WSGI vs ASGI, and is ASGI faster? ⭐⭐** Sync vs async spec; ASGI is faster only for
  genuinely concurrent I/O or WebSockets — with a sync ORM it can be slower.
- **How many workers?** `2 × cores + 1` as a starting point, then measure; watch **database
  connections**, which usually cap you first.
- **What's the danger of scaling out workers?** Connection exhaustion — use PgBouncer.
- **How do you deploy without downtime? ⭐** Backwards-compatible migrations run once, rolling
  replicas with readiness probes, then restart Celery workers.
- **Where do migrations run in Kubernetes?** A single Job/init container — never per pod.
- **Where do user uploads go, and why not local disk?** Object storage — local disk isn't
  shared across replicas and is lost on redeploy.
- **How do you handle secrets?** Environment/secret manager, injected at runtime, never in the
  image or repo.
- **Liveness vs readiness?** Is the process alive vs is it able to serve — keep liveness free
  of external dependencies.
