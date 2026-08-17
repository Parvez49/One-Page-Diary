# Deployment — Interview Q&A

> Per-topic depth in the other files; this is the rehearsal sheet. ⭐ = high value ·
> ⚠️ = the trap they're fishing for.

---

## 1. Architecture

**Q: Walk me through what happens when a user hits your production API.** ⭐⭐

DNS resolves to the server IP → nginx accepts the connection on :443 and terminates TLS →
matches a `server` block by `server_name` → static paths are served directly from disk, and
everything else is proxied to gunicorn over a Unix socket with `X-Forwarded-*` headers set →
gunicorn hands the request to a worker → the app queries Postgres, maybe Redis, and returns →
nginx buffers the response back to the client. Gunicorn is kept alive by systemd/supervisor,
Celery handles anything slow, and certbot renews the certificate on a timer.

**Q: Why nginx *and* gunicorn? Isn't one server enough?** ⭐

Different jobs. Nginx handles TLS, static files, buffering slow clients, rate limiting and
caching with an event loop that costs almost nothing per idle connection. Gunicorn runs
application code with a worker per concurrent request. Expose gunicorn directly and one client
on a slow connection occupies an entire worker for the duration of the transfer.

**Q: Nginx vs Apache?** ⭐

Event loop vs process-per-connection. Nginx's cost scales with *active requests*, Apache's
with *open connections*. Apache's remaining advantages are `.htaccess`, `mod_php`, and the
fact that you inherited it.

**Q: WSGI vs ASGI?** ⭐⭐

WSGI is synchronous, one request per worker, no websockets. ASGI is an event loop that can
hold many concurrent connections per worker and supports websockets/SSE. ASGI is not "faster
Django" — a CRUD API bounded by database time gains nothing. ⚠️ And one blocking ORM call
inside an async view stalls every concurrent request on that worker.

**Q: How many gunicorn workers?**

`2 × cores + 1` as a starting point, then measure. ⭐ The real ceiling is usually database
connections, not CPU — workers × servers × Celery can exhaust `max_connections`, so PgBouncer
comes before more workers.

---

## 2. Nginx & TLS

**Q: `sites-available` vs `sites-enabled`?** — the latter holds symlinks; only symlinked
configs are live. `nginx -t && systemctl reload nginx` after any change.

**Q: `reload` vs `restart`?** ⭐ Reload is graceful — old workers drain in-flight requests.
Restart drops connections.

**Q: `alias` vs `root`?** ⭐ `root` appends the whole URI to the path; `alias` replaces the
matched location prefix.

**Q: You're getting a 502. Debug it.** ⭐

Is the app process running (`supervisorctl status` / `systemctl status`)? Is nginx pointed at
the right socket/port? Can `www-data` read the socket file? What does
`/var/log/nginx/error.log` say? — in that order. 502 is nginx failing to reach the upstream;
504 is the upstream being too slow.

**Q: The app redirects infinitely / emails contain `http://` links.** ⚠️⭐

TLS terminates at the proxy, so the app sees plain HTTP. Set `X-Forwarded-Proto` at the proxy
and configure the framework to trust it. Only trust it if the app port isn't independently
reachable.

**Q: How does Let's Encrypt verify you own a domain?** ⭐ HTTP-01 (a token served over port 80)
or DNS-01 (a TXT record — required for wildcards). ⚠️ Port 80 must stay open for renewal even
on an HTTPS-only site.

**Q: `fullchain.pem` vs `cert.pem`?** ⭐ The intermediate chain. Browsers cache intermediates
and appear fine; `curl` and mobile clients fail — the "works in my browser" TLS bug.

**Q: Where would you cache, and what's the risk?** ⭐ At the edge with `proxy_cache` for hot
read-only endpoints; `proxy_cache_use_stale` keeps you serving through a backend outage.
⚠️ Caching an authenticated response without the user in the cache key serves one user's data
to another.

---

## 3. Process management

**Q: Why a supervisor rather than `nohup`?** ⭐ Auto-restart on crash, start on boot, ordered
startup, log capture, unprivileged user.

**Q: It works when I run it manually but dies under supervisor.** ⚠️⭐

Environment. The supervised process gets no shell, no profile, no activated virtualenv — only
`environment=` / `EnvironmentFile=`. Use absolute paths into the venv.

**Q: You changed a supervisor config and restarted; nothing happened.** ⚠️ `restart` doesn't
re-read config — `reread && update`. systemd's equivalent is `daemon-reload`.

**Q: How many `celery beat` processes should run?** ⭐ Exactly one. Two means every periodic
task fires twice.

---

## 4. Docker

**Q: Container vs VM?** ⭐ Namespaces and cgroups isolating processes on the *host kernel*, vs
virtualised hardware booting its own kernel. Hence millisecond starts and a shared kernel
requirement.

**Q: Your image is 2GB and builds take 8 minutes. Fix it.** ⭐⭐

Copy `requirements.txt` and install *before* copying source, so the dependency layer stays
cached. Multi-stage build so build tools don't ship. Slim base. `.dockerignore` for `.git`,
`node_modules`, `venv`. ⚠️ Deleting files in a later layer doesn't shrink anything — layers
are additive.

**Q: `ENTRYPOINT` vs `CMD`?** ⭐ Fixed executable vs overridable default args. Use exec form —
shell form wraps in `/bin/sh`, which swallows SIGTERM and breaks graceful shutdown.

**Q: `EXPOSE` vs `-p`?** ⚠️ `EXPOSE` is documentation. `-p host:container` publishes.

**Q: The container can't reach Postgres on `localhost`.** ⭐⭐ Inside a container `localhost` is
that container. Use the service name on a user-defined network; the *default* bridge has no
inter-container DNS.

**Q: Does `depends_on` wait for the database to be ready?** ⚠️ No — start order only. Use a
healthcheck with `condition: service_healthy`, and make the app retry regardless.

**Q: Volume vs bind mount?** ⭐ Docker-managed, portable, backup-able (production data) vs a
host path (development live-reload). ⚠️ A containerised database without a volume loses
everything on `docker rm`; `docker-compose down -v` deletes volumes.

**Q: My container exits immediately.** It lives exactly as long as PID 1. `docker ps -a` for
the exit code, then `docker logs`. 137 = OOM/SIGKILL.

**Q: Where do secrets go?** ⚠️ Never in the image — `ENV`, `ARG` and a copied `.env` are all
visible in `docker history`/`inspect`. Inject at runtime.

**Q: Why not run as root in a container?** ⚠️ Container root + a bind mount writes host files;
and membership of the host `docker` group is effectively root on the host.

---

## 5. Kubernetes

**Q: What does Kubernetes actually do?** ⭐ Schedules containers across machines, restarts what
dies, scales what's loaded, and gives stable networking over ephemeral pods.

**Q: What's the core idea?** ⭐⭐ The reconciliation loop — you declare desired state,
controllers continuously drive actual state toward it. Everything else follows from that.

**Q: Pod vs container?** The pod is the scheduling unit; containers within it share a network
namespace (they reach each other on `localhost`) and are co-scheduled.

**Q: Why do you need a Service?** ⭐ Pod IPs churn. A Service is a stable name and virtual IP
that load-balances across pods matched **by label**.

**Q: Readiness vs liveness probe?** ⭐⭐ Readiness failure removes the pod from load balancing;
liveness failure restarts the container. ⚠️ A liveness probe that hits the database turns a
slow database into a cluster-wide restart storm.

**Q: A pod is `Pending` / `CrashLoopBackOff` / `ImagePullBackOff`.** ⭐ `describe` first — the
events explain it: unschedulable resources, a bad image tag or missing pull secret, or a
container that starts and dies (`logs --previous`).

**Q: Are Kubernetes Secrets encrypted?** ⚠️ Base64-encoded, not encrypted, unless you enable
encryption at rest or use an external secret manager.

**Q: When would you *not* use Kubernetes?** ⭐ One app, one team, one server. The operational
cost dwarfs the benefit — a VPS or a PaaS wins. Knowing this is the point of the question.

---

## 6. Frontend & deploys

**Q: Refreshing `/dashboard` returns 404 but clicking to it works.** ⭐⭐ Client-side routing —
no file exists at that path. Rewrite anything that isn't a real file or directory to
`index.html` (`try_files $uri $uri/ /index.html`, or `mod_rewrite` with `!-f`/`!-d`).
⚠️ Without the `!-f`/`!-d` conditions, JS and CSS also get `index.html` back — that's the
"Unexpected token '<'" error.

**Q: After every deploy users see a white screen until they hard-refresh.** ⭐ `index.html` is
being cached. Hashed assets `immutable, 1y`; `index.html` `no-cache`.

**Q: Are `REACT_APP_*` / `VITE_*` variables secret?** ⚠️ No — they're compiled into the bundle
and shipped to every visitor. That's also why changing one requires a rebuild.

**Q: What order do you deploy in?** ⭐ Backwards-compatible migrations → `collectstatic` →
reload nginx if config changed → restart the app. Migrations must be backwards-compatible
because old and new code run simultaneously during the rollout (expand/contract).

**Q: How do you roll back?** ⭐ Release directories with a symlink swap (or an image tag /
`kubectl rollout undo`). ⚠️ The database is the part that doesn't roll back — which is the
whole argument for expand/contract migrations.

---

## Rapid fire

| Question | Answer |
|---|---|
| 502 vs 504 | Can't reach upstream vs upstream too slow. |
| `nginx -t` | Validate config before reloading. Always. |
| `-p 4000:80` | host:container — in that order. |
| Unix socket vs TCP upstream | Faster, and unreachable from off-box. |
| `client_max_body_size` | Default 1M — the cause of surprise 413s on upload. |
| `reread` vs `update` | Detect config changes vs apply them. |
| Beat replicas | One. Always one. |
| `docker system df` | Check before Docker fills the disk. |
| Secrets in an image | Recoverable from layer history. Never. |
| `depends_on` | Start order, not readiness. |
| K8s exit 137 | OOMKilled — over the memory limit. |
| etcd | All cluster state; back it up. |
| ngrok authtoken | A live credential — never commit it. |
| Self-hosted mail server | IP reputation. Don't. |
| Email in the request cycle | ⚠️ Queue it — a third-party timeout shouldn't hold a worker. |
| Biggest single-server risk | Disk full from unrotated logs. |
