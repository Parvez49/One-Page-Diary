# Nginx

> TLS/certs: **[tls_certbot.md](tls_certbot.md)** · What sits behind it: **[app_servers.md](app_servers.md)** ·
> The other reverse proxy: **[apache.md](apache.md)**

---

## 1. What it is, and why it's the default ⭐

Nginx is a web server, **reverse proxy**, **load balancer**, and HTTP cache. The reason it
displaced Apache as the default front door is the concurrency model, not the feature list.

| | Nginx | Apache (prefork/worker MPM) |
|---|---|---|
| Model | ⭐ **event loop**, async I/O | process/thread **per connection** |
| 10 concurrent requests | one worker handles all 10, non-blocking | needs 10 workers, or they queue |
| Memory under load | flat | grows with connections |
| Slow clients | cheap (a parked fd) | ⚠️ expensive (a whole worker held) |
| Config style | central, `sites-available` | ⭐ per-directory `.htaccess` too |
| Dynamic modules | compile/load | rich ecosystem, `a2enmod` |

⭐ **The senior framing:** it's C10K. Apache's cost is *per connection*; nginx's cost is
*per active request*. That's why nginx is put in front — it absorbs slow clients, TLS, and
static files, and only hands real work to the application.

**Master vs worker processes:**
- **Master** — reads and validates config, binds ports, spawns/maintains workers. Runs as root
  only to bind :80/:443.
- **Workers** — do the actual request processing. `worker_processes auto;` = one per core.

---

## 2. Directory structure

```
/etc/nginx/
├── nginx.conf          # entry point: worker/http blocks, logging, include directives
├── sites-available/    # one file per virtual host — INACTIVE until symlinked
├── sites-enabled/      # symlinks to the active configs  ⭐
├── conf.d/             # auto-included global fragments: caching zones, upstreams, SSL
└── snippets/           # reusable partials included inside server/location blocks
```

⚠️ Editing a file in `sites-available/` changes nothing until it is symlinked into
`sites-enabled/` **and** nginx is reloaded. This is the single most common "my config isn't
taking effect."

```bash
sudo ln -s /etc/nginx/sites-available/domain.com /etc/nginx/sites-enabled/
sudo nginx -t && sudo systemctl reload nginx     # ⭐ ALWAYS -t first
sudo rm /etc/nginx/sites-enabled/domain.com      # disable a site
```

⭐ `nginx -t && reload` — the `&&` matters. `nginx -t & reload` (single `&`) backgrounds the
test and reloads regardless, which is how a broken config reaches production. `reload` is
graceful: old workers finish in-flight requests, new workers pick up the new config, zero
dropped connections. `restart` drops them.

---

## 3. Reverse proxy — the standard block ⭐

```nginx
upstream app_backend {
    server localhost:3001;
    keepalive 64;                       # ⭐ reuse upstream connections, big latency win
}

server {
    server_name example.com;

    location / {
        proxy_pass http://app_backend;

        proxy_http_version 1.1;                          # ⭐ required for keepalive AND websockets
        proxy_set_header Upgrade    $http_upgrade;       # websocket handshake
        proxy_set_header Connection "upgrade";

        proxy_redirect off;
        proxy_set_header Host              $host;
        proxy_set_header X-Real-IP         $remote_addr;
        proxy_set_header X-Forwarded-For   $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;      # ⭐⭐ see warning below
        proxy_set_header X-Forwarded-Host  $server_name;
    }

    listen 443 ssl;                                              # managed by Certbot
    ssl_certificate     /etc/letsencrypt/live/example.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/example.com/privkey.pem;
    include             /etc/letsencrypt/options-ssl-nginx.conf;
    ssl_dhparam         /etc/letsencrypt/ssl-dhparams.pem;
}

server {                                    # HTTP → HTTPS redirect
    listen 80;
    server_name example.com;
    return 301 https://$host$request_uri;
}
```

⚠️⚠️ **`X-Forwarded-Proto` is not cosmetic.** TLS terminates at nginx, so the app sees plain
HTTP. Without this header (and the framework trusting it) you get: infinite redirect loops
from `SECURE_SSL_REDIRECT`, `http://` links in password-reset emails, and `secure` cookies
never set. In Django that's `SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")`.

⚠️ Only trust forwarding headers when nginx is genuinely the only ingress. If the app port is
also reachable directly, a client can forge `X-Forwarded-For` and defeat IP-based rate limits
and audit logs.

⭐ **Trailing-slash trap:** `proxy_pass http://backend;` passes the URI through unchanged;
`proxy_pass http://backend/;` (with the slash) *replaces* the matched location prefix. Two
different behaviours from one character.

---

## 4. Unix socket vs TCP upstream ⭐

```nginx
proxy_pass http://unix:/run/gunicorn_app.sock;    # ⭐ same-host: faster, not network-reachable
proxy_pass http://127.0.0.1:8000;                 # different host, or containers
```

Sockets skip the TCP stack and — more importantly — **cannot be reached from outside the box**,
so nobody bypasses the proxy. Cost: nginx's user (`www-data`) must have permission on the
socket file. ⚠️ A `502` right after deploy is usually socket permissions or the socket path
not existing yet, not the app being down — check `journalctl -u nginx` and `ls -l /run/*.sock`.

---

## 5. Static and media files

```nginx
location = /favicon.ico { access_log off; log_not_found off; }

location /static/ { alias /opt/app/staticfiles/; }
location /media/  { root  /opt/app/project/;    }
```

⭐ **`alias` vs `root`** — the classic confusion. `root` **appends** the full request URI to
the path (`/media/x.png` → `/opt/app/project/media/x.png`). `alias` **replaces** the matched
location prefix (`/static/x.css` → `/opt/app/staticfiles/x.css`). Wrong one = 404s that look
like a permissions problem.

⭐ Never serve static files through the application. nginx does it with `sendfile()` at
kernel speed and doesn't occupy an application worker.

---

## 6. Load balancing

```nginx
upstream app_servers {
    server 127.0.0.1:3001;
    server 127.0.0.1:3002 weight=2;
    server 127.0.0.1:3003 backup;      # only used when the others are down
}
```

Multiple `server` lines in one `upstream` block *is* the load balancing.

| Strategy | Directive | Use |
|---|---|---|
| Round robin | (default) | stateless apps ⭐ |
| Least connections | `least_conn;` | uneven request durations |
| IP hash | `ip_hash;` | ⚠️ sticky sessions — a crutch for state that should be in Redis |

⚠️ Round-robin across app servers only works if the app is stateless. If sessions live in
local memory, users get logged out at random. Fix the session store, don't reach for `ip_hash`.

---

## 7. Proxy caching

**Step 1 — declare the zone** (`/etc/nginx/conf.d/cache.conf`):

```nginx
proxy_cache_path /var/cache/nginx/api_cache_dir
                 levels=1:2
                 keys_zone=api_cache:10m     # zone name : shared memory for KEYS/metadata
                 max_size=100m               # max on-disk size of cached BODIES
                 inactive=60m                # evict entries unused for this long
                 use_temp_path=off;          # ⭐ write straight into the cache dir
```

**Step 2 — a bypass switch** in the `http` block (`nginx.conf`):

```nginx
map $arg_page $no_cache {      # cache only the first few pages of a paginated list
    1 0; 2 0; 3 0; 4 0; 5 0;
    default 1;                 # 1 = do NOT cache
}
include /etc/nginx/conf.d/*.conf;
include /etc/nginx/sites-enabled/*;
```

**Step 3 — apply it in a snippet** (`/etc/nginx/snippets/api_cache_list.conf`):

```nginx
location ^~ /api/incidents/v1/incidents/ {
    proxy_cache api_cache;
    proxy_cache_valid 200 60s;
    proxy_cache_use_stale error timeout updating http_500 http_502 http_503 http_504;  # ⭐⭐
    proxy_cache_lock on;                                   # ⭐ collapse a stampede

    proxy_pass http://unix:/run/gunicorn_app.sock;
    include proxy_params;

    proxy_cache_key "$scheme$host$request_uri$is_args$args";
    proxy_no_cache     $no_cache;      # don't STORE the response
    proxy_cache_bypass $no_cache;      # don't SERVE from cache

    add_header X-Cache-Status $upstream_cache_status;      # ⭐ HIT/MISS/BYPASS/STALE — debug with curl -I
}
```

**Step 4 — include it in the server block**, *before* the catch-all `location /`:

```nginx
include snippets/api_cache_list.conf;
```

⭐ **`proxy_cache_use_stale` is the highest-value line here** — it serves the last good
response while the backend is down or slow. Your API keeps answering through a deploy or a
database hiccup. `updating` means one request refreshes while everyone else gets stale content
rather than piling onto the origin.

⭐ **`proxy_cache_lock on`** is the stampede defence at the edge: on a cache miss, one request
goes to the origin and the rest wait for it. Same problem as the application-level cache
stampede — see `../Web/Django/caching.md`.

⚠️ **Caching an authenticated endpoint leaks data between users.** The cache key above has no
user in it, so user A's response is served to user B. Either exclude anything behind auth
(`proxy_no_cache $http_authorization;`) or put the identity in `proxy_cache_key`. This is a
real-incident class of bug, not a theoretical one.

⚠️ `proxy_cache_valid 200 0s;` caches nothing — it's the *disabled* state, useful when you
want the zone wired up and ready but off.

---

## 8. Rate limiting and hardening

```nginx
limit_req_zone $binary_remote_addr zone=api:10m rate=10r/s;      # ⭐ track by client IP

server {
    client_max_body_size 20M;         # ⚠️ default 1M → surprise 413 on file upload
    server_tokens off;                # hide the version number

    add_header X-Frame-Options        SAMEORIGIN         always;
    add_header X-Content-Type-Options nosniff            always;
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;

    location /api/ {
        limit_req zone=api burst=20 nodelay;             # ⭐ allow short bursts
        limit_req_status 429;
    }
}
```

⭐ **Rate limit at the edge, not in the app.** A request throttled by DRF has already consumed
a worker, a connection, and a database round trip. Nginx rejects it before any of that. The
application throttle is for fairness/quota; the edge throttle is for load.
⚠️ Neither one is DDoS protection — volumetric attacks are handled upstream of your box
(Cloudflare, the cloud LB).

⚠️ `add_header` is **not inherited** into a `location` block that declares its own
`add_header`. Security headers silently vanish on exactly the routes you added a header to.
Use `always` and re-declare, or use `include snippets/security_headers.conf;` everywhere.

---

## 9. Operating it

```bash
sudo nginx -t                       # ⭐ validate config — before every reload
sudo systemctl reload nginx         # graceful, zero dropped connections
sudo systemctl restart nginx        # drops connections — avoid
sudo nginx -T                       # dump the FULLY resolved config (all includes) ⭐
tail -f /var/log/nginx/error.log    # 502s explain themselves here
tail -f /var/log/nginx/access.log
```

| Symptom | Usual cause |
|---|---|
| **502 Bad Gateway** | app not running, wrong socket/port, ⚠️ socket permissions |
| **504 Gateway Timeout** | app slower than `proxy_read_timeout` (60s default) |
| **413 Entity Too Large** | ⚠️ `client_max_body_size` (default 1M) |
| **404 on a static file** | ⚠️ `alias` vs `root` mix-up, or permissions on the parent dir |
| Redirect loop | ⚠️ missing `X-Forwarded-Proto` |
| Config "not applying" | ⚠️ not symlinked into `sites-enabled/`, or not reloaded |

---

## Interview points

- **Nginx vs Apache** ⭐ — event loop vs process-per-connection. Nginx costs per *active
  request*, Apache per *open connection*, which is why slow clients are cheap for one and
  expensive for the other.
- **Master vs worker** — master reads config and binds privileged ports; workers serve
  requests. `worker_processes auto` = one per core.
- **Why put nginx in front of gunicorn at all?** ⭐ TLS termination, static files, slow-client
  buffering, rate limiting, caching, and load balancing — none of which the app server should
  be doing.
- **`sites-available` vs `sites-enabled`** — the second holds symlinks; only symlinked configs
  are live.
- **`alias` vs `root`** ⭐ — replaces the location prefix vs appends the whole URI.
- **`reload` vs `restart`** — reload is graceful and drops nothing.
- **Unix socket vs TCP** — faster and unreachable from off-box; costs you socket permissions.
- **Debugging a 502** ⭐ — is the app up, is the socket path right, can `www-data` read it,
  what does `error.log` say. In that order.
- **Where do you rate limit?** ⭐ At the edge — an app-level throttle has already paid for the
  request. Neither stops a DDoS.
- **The proxy cache trap** ⚠️ — caching authenticated responses without the user in the cache
  key serves one user's data to another.
