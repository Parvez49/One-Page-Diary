# Application servers — Gunicorn, Daphne, WSGI vs ASGI

> The proxy in front: **[nginx.md](nginx.md)** · Keeping them alive:
> **[process_management.md](process_management.md)** · Django angle: `../Web/Django/deployment.md`

---

## 1. Why there are two servers at all ⭐

`runserver` is single-threaded, auto-reloading, and explicitly not for production. The
production stack is:

```
client → nginx (TLS, static, buffering) → gunicorn/daphne (N workers) → your app
```

Two processes because they solve different problems: nginx is optimised for many idle
connections; the app server is optimised for running your code. Nginx also **buffers slow
clients**, so a user on 3G doesn't hold an application worker hostage for 30 seconds.

---

## 2. WSGI vs ASGI ⭐⭐

| | WSGI (gunicorn) | ASGI (uvicorn / daphne) |
|---|---|---|
| Model | one request per worker, **synchronous** | ⭐ event loop, many concurrent requests per worker |
| Websockets | ❌ impossible — the protocol has no concept of them | ✅ |
| Long-poll / SSE / streaming | ⚠️ pins a worker for the duration | ✅ cheap |
| Blocking DB/ORM call | fine — that's the model | ⚠️⚠️ blocks the **whole event loop** |
| Default choice | ⭐ ordinary request/response APIs | websockets, or genuinely I/O-bound fan-out |

⭐ **The senior answer:** ASGI is not "faster Django." It's a different concurrency model. A
standard CRUD API whose time is spent in the database gets nothing from ASGI — the database
connection pool is the bottleneck either way. ASGI earns its keep when you need **persistent
connections** (websockets, SSE) or when a request spends its life waiting on *many* external
I/O calls.

⚠️⚠️ **The ASGI trap:** one synchronous ORM call inside an `async def` view blocks the event
loop for *every* concurrent request on that worker. Async is all-or-nothing per code path —
`sync_to_async` or a threadpool for anything blocking.

Run both when you need both: gunicorn for HTTP, daphne/uvicorn for the websocket routes,
split by `location` in nginx.

---

## 3. Gunicorn

```bash
pip install gunicorn
```

`gunicorn_config.py`:

```python
bind = "unix:/run/gunicorn_app.sock"    # ⭐ socket for same-host nginx; "0.0.0.0:8000" otherwise
workers = 3                             # see the formula below
worker_class = "sync"                   # "gthread" / "gevent" / "uvicorn.workers.UvicornWorker"
threads = 1
timeout = 30                            # ⚠️ worker killed after this many seconds
graceful_timeout = 30
keepalive = 5
max_requests = 1000                     # ⭐ recycle workers — papers over slow memory leaks
max_requests_jitter = 100               # ⭐ so they don't all restart at once
accesslog = "-"
errorlog  = "-"
```

```bash
gunicorn myproject.wsgi:application -c gunicorn_config.py
gunicorn myproject.wsgi:application -c gunicorn_config.py --reload    # dev only
gunicorn myproject.asgi:application -k uvicorn.workers.UvicornWorker  # ASGI via gunicorn
```

### Worker count ⭐

**`(2 × CPU cores) + 1`** is the starting point, then measure.

⚠️ The real ceiling is usually **database connections**, not CPU. 4 servers × 9 workers = 36
connections against a Postgres `max_connections` of 100 — add Celery workers and you hit
"too many connections" under load. Put **PgBouncer** in front before scaling workers up.

| Worker class | Use |
|---|---|
| `sync` ⭐ | default; simple, robust, one request at a time |
| `gthread` | ⭐ I/O-bound views — more concurrency per worker, less memory than processes |
| `gevent` | high concurrency on I/O, ⚠️ needs monkey-patching, breaks some C libraries |
| `UvicornWorker` | ASGI apps under gunicorn's process manager ⭐ |

⚠️ **`timeout = 30` is a worker *kill*, not an HTTP timeout.** A slow report endpoint gets its
worker SIGKILLed mid-request and the client sees a 502. Fix the query or move it to Celery —
don't just raise the timeout, or you've traded an error for a pinned worker.

⚠️ Workers are **separate processes**. Anything in module-level memory — a local cache,
a counter, `LocMemCache` — is per-worker and inconsistent. Symptom: "the fix works about a
third of the time."

### Processes

```bash
pgrep gunicorn              # PIDs
ps -A | grep gunicorn
kill -HUP  <master_pid>     # ⭐ graceful reload of workers (new code, config re-read)
kill -TERM <master_pid>     # graceful shutdown
kill -9    <pid>            # ⚠️ last resort — drops in-flight requests
```

⭐ In production don't manage PIDs by hand — that's systemd's or supervisor's job
([process_management.md](process_management.md)). `kill -HUP` is still the fastest way to pick
up new code without dropping a request.

---

## 4. Daphne (ASGI, websockets)

```bash
daphne -u /run/daphne/daphne0.sock --access-log - --proxy-headers config.asgi:application
```

⭐ `--proxy-headers` makes daphne trust `X-Forwarded-For`/`-Proto` from nginx — without it,
every client appears to be `127.0.0.1` and the scheme is wrong.

Under supervisor it's run as an `fcgi-program` with a bound socket passed as `--fd 0` — see
[process_management.md](process_management.md) for the full config.

Websockets also need nginx configured for the upgrade handshake (`proxy_http_version 1.1` plus
the `Upgrade`/`Connection` headers — [nginx.md](nginx.md) §3), and a **channel layer** (Redis)
so that a message published by one worker reaches clients connected to another. ⚠️ The
in-memory channel layer works in dev and silently drops cross-worker messages in production.

---

## 5. Deploy order ⭐

```bash
pip install -r requirements.txt
python manage.py migrate            # ⭐ backwards-compatible migrations FIRST
python manage.py collectstatic --noinput
sudo systemctl reload nginx         # if config changed
sudo supervisorctl restart app      # or: systemctl restart gunicorn / kill -HUP
```

⭐ Migrate **before** restarting the app, and make migrations backwards-compatible, because
old and new code run simultaneously during the restart. That's the expand/contract rule —
`../Web/Django/migrations.md`.

⚠️ `collectstatic` must run *before* the new code serves pages, or nginx 404s on the new
hashed asset filenames — a blank page with a working API.

---

## Interview points

- **Why nginx *and* gunicorn?** ⭐ TLS, static files, and slow-client buffering belong at the
  edge; the app server should only run application code.
- **WSGI vs ASGI** ⭐⭐ — synchronous request-per-worker vs an event loop. ASGI is for
  persistent connections, not general speed.
- **The async trap** ⚠️ — one blocking ORM call in an async view stalls every concurrent
  request on that worker.
- **How many workers?** ⭐ `2 × cores + 1` as a start; the true limit is usually database
  connections → PgBouncer.
- **What does `timeout` do?** ⚠️ Kills the worker. It's not a graceful HTTP timeout.
- **`max_requests`** ⭐ — periodic worker recycling that survives a slow memory leak.
- **Why is my in-process cache inconsistent?** ⚠️ Workers are separate processes.
- **Deploy order** ⭐ — migrate, collectstatic, then restart; migrations must be
  backwards-compatible because both versions run at once.
- **Websockets at scale** — ASGI server + Redis channel layer; the in-memory layer doesn't
  cross workers.
