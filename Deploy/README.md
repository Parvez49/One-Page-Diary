# Deployment & Operations — Index

Everything between "it works on my machine" and "it serves users at 3am." Focused on the
single-VPS stack most projects actually run (nginx + gunicorn + supervisor + certbot), with
containers and orchestration for when that stops being enough.

**Conventions:** ⭐ = high interview value · ⚠️ = a trap that causes real incidents ·
every file ends with an **Interview points** section.

---

## Files

| File | Covers | Interview weight |
|---|---|---|
| [nginx.md](nginx.md) | **Reverse proxy**, `sites-available/enabled`, **`alias` vs `root`**, load balancing, **proxy cache**, rate limiting, 502 debugging | ⭐⭐⭐ |
| [app_servers.md](app_servers.md) | Gunicorn config, **worker count**, **WSGI vs ASGI**, daphne/websockets, **deploy order** | ⭐⭐⭐ |
| [tls_certbot.md](tls_certbot.md) | **HTTP-01 vs DNS-01**, `fullchain` vs `cert`, **renewal & reload hooks**, new-domain checklist | ⭐⭐ |
| [process_management.md](process_management.md) | Supervisor, **`reread`/`update`**, systemd units, **the environment trap**, Celery + beat | ⭐⭐ |
| [docker.md](docker.md) | Architecture, **layer caching**, multi-stage, **networking & the `localhost` trap**, volumes, Compose, security | ⭐⭐⭐ |
| [kubernetes.md](kubernetes.md) | Pod/node/cluster, control plane, **reconciliation loop**, Services, **readiness vs liveness**, debugging | ⭐⭐ |
| [static_frontend.md](static_frontend.md) | SPA builds, **the refresh-404 problem**, cache headers, ⚠️ build-time env vars | ⭐⭐ |
| [apache.md](apache.md) | vhosts, `ProxyPass`/`ProxyPassReverse`, **`AllowOverride`/`.htaccess`**, `a2enmod` | ⭐ |
| [email.md](email.md) | Provider choice, **why not self-host / not Gmail**, SPF/DKIM/DMARC, sending off the request path | ⭐⭐ |
| [tunnels.md](tunnels.md) | ngrok, webhook development, multi-port config, ⚠️ what a public tunnel exposes | ⭐ |
| [interview.md](interview.md) | **Q&A across every topic** + rapid fire | ⭐⭐⭐ |
| [shared_vps_deployment.md](shared_vps_deployment.md) | **Real end-to-end case study**: 3 repos on a shared VPS — two-nginx-layer edge, R2 media, deploy keys, Cloudflare/certbot traps, **every failure that actually fired** | ⭐⭐⭐ |

---

## Suggested study order

1. **[nginx.md](nginx.md)** + **[app_servers.md](app_servers.md)** — the two-process stack is
   the answer to "walk me through a production request."
2. **[tls_certbot.md](tls_certbot.md)** — TLS termination explains half of all
   "works locally, breaks in prod" bugs.
3. **[process_management.md](process_management.md)** — what keeps it running after you log out.
4. **[docker.md](docker.md)** — layer caching and container networking are asked everywhere.
5. **[static_frontend.md](static_frontend.md)** — the SPA 404 is a guaranteed question if
   you've shipped a React app.
6. **[email.md](email.md)** — a small topic that reliably exposes deployment inexperience.
7. **[kubernetes.md](kubernetes.md)** — enough to discuss it honestly, including when not to.
8. **[apache.md](apache.md)**, **[tunnels.md](tunnels.md)** — situational.
9. **[interview.md](interview.md)** — rehearse out loud the day before.

---

## The senior answers worth memorising

| Question | Short answer |
|---|---|
| Why nginx *and* gunicorn? ⭐ | Edge concerns (TLS, static, slow clients) vs running app code. |
| Nginx vs Apache ⭐ | Event loop vs process-per-connection — cost per active request vs per open connection. |
| WSGI vs ASGI ⭐ | Sync request-per-worker vs event loop. ASGI is for websockets, not speed. |
| One blocking call in an async view | ⚠️ Stalls every concurrent request on that worker. |
| How many workers? | `2 × cores + 1`, but ⚠️ database connections cap you first → PgBouncer. |
| Gunicorn `timeout` | ⚠️ Kills the worker — the client gets a 502, not a graceful error. |
| 502 vs 504 | Can't reach the upstream vs the upstream was too slow. |
| `alias` vs `root` ⭐ | Replaces the location prefix vs appends the full URI. |
| Infinite redirects / `http://` in emails ⚠️ | Missing `X-Forwarded-Proto` — TLS ended at the proxy. |
| Config change did nothing | ⚠️ Not symlinked into `sites-enabled/`, or not reloaded. |
| Caching an authenticated endpoint | ⚠️ Serves one user's response to another. Put identity in the cache key. |
| Where do you rate limit? ⭐ | At the edge — an app throttle has already paid for the request. |
| Renewal broke after 90 days | ⚠️ Port 80 firewalled, DNS moved, or no reload hook. |
| `fullchain.pem` vs `cert.pem` ⭐ | The chain — browsers cope, `curl` and mobile don't. |
| Works manually, dies under supervisor ⚠️ | No shell, no venv, no profile — only `environment=`. |
| Edited supervisor config, restarted, nothing | ⚠️ `restart` doesn't re-read — `reread && update`. |
| `celery beat` replicas | Exactly one, or every periodic task double-fires. |
| Slow Docker builds ⭐ | Dependencies before source; layer caching. `.dockerignore`. |
| Deleting a file to shrink an image | ⚠️ Layers are additive — use multi-stage. |
| `EXPOSE` vs `-p` ⚠️ | Documentation vs actually publishing a port. |
| Container can't reach the DB on `localhost` ⭐ | `localhost` is the container — use the service name. |
| `depends_on` waits for readiness? | ⚠️ No — order only. Healthcheck + app-side retry. |
| Secrets in an image | ⚠️ Recoverable from `docker history`. Runtime injection only. |
| The Kubernetes idea ⭐ | Reconciliation loops closing the gap to declared desired state. |
| Readiness vs liveness ⭐ | Pulled from load balancing vs restarted. ⚠️ Don't probe the DB for liveness. |
| Refresh on `/dashboard` 404s ⭐ | Client-side routing — `try_files … /index.html`. |
| White screen after deploy | ⚠️ `index.html` was cached. Assets immutable, HTML `no-cache`. |
| Are frontend env vars secret? | ⚠️ No — compiled into the bundle. |
| Deploy order ⭐ | Backwards-compatible migrate → collectstatic → reload → restart. |
| Self-hosted mail server | ⚠️ IP reputation. Use a transactional provider. |
| Sending email in the request | ⚠️ Queue it — a provider timeout shouldn't hold a worker. |
| Most common "server down" cause | Disk full — unrotated logs, or Docker build cache. |

---

## Related directories

`../Web/Django/deployment.md` app-side deploy · `../Web/Django/async_tasks.md` Celery ·
`../Web/NextJS/` SSR hosting · `../CICD/` pipelines & automation ·
`../Database/` connections, pooling, backups · `../CyberSecurity/` hardening ·
`../linux/` shell, systemd, permissions · `../SDLC/` architecture
