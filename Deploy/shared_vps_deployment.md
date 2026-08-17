# Shared-VPS deployment — the jonmobhoomi staging case study

> Front door: **[nginx.md](nginx.md)** · Certificates: **[tls_certbot.md](tls_certbot.md)** ·
> App servers: **[app_servers.md](app_servers.md)** · Containers: **[docker.md](docker.md)**

Three repos (Django backend, two Next.js frontends), one Hostinger VPS that was **already
running another project**, Cloudflare DNS, media on R2. Deployed 2026-08-17. This note is the
end-to-end order of operations plus every trap that actually fired.

---

## 1. The architecture that survived contact with reality ⭐

```
Internet ──443──► HOST nginx (TLS, certbot, owns 80/443, also serves other projects)
                     │  all project hostnames, plain HTTP
                     ▼
              127.0.0.1:8080 → docker nginx (router inside the stack)
                     ├─ backend.<domain>  /      → gunicorn
                     ├─ backend.<domain>  /ws/   → daphne   (gunicorn can't websocket)
                     ├─ backend.<domain>  /static/ → collectstatic volume
                     ├─ apex              → user frontend container (edge network)
                     ├─ admin.<domain>    → admin frontend container
                     └─ analytics.<domain>→ grafana
```

**Two nginx layers, deliberately.** On a shared box you can't bind 80/443, so the host nginx
is a dumb per-hostname forwarder (`proxy_pass http://127.0.0.1:8080`, `Host` preserved,
websocket upgrade headers, `X-Forwarded-Proto`). ALL real routing stays in the docker nginx,
version-controlled in the repo, deployed by `git push`. Resist the "just remove the docker
nginx and route everything from the host" urge: that moves `/ws/` splitting, static serving,
and frontend routing into hand-edited host files, and forces every container to publish ports.
The docker nginx costs ~10 MB RAM and one loopback hop.

**One host vhost, all hostnames in one `server_name`,** rendered from the app's `.env` by an
`envsubst` script (`deploy/host-proxy/render.sh | sudo tee /etc/nginx/sites-available/…`).
Never hand-edit the rendered file — re-render.

⚠️ In the docker nginx behind a TLS-terminating proxy, `proxy_set_header X-Forwarded-Proto
$scheme` is **wrong** — `$scheme` is `http` there. Pass through the incoming
`$http_x_forwarded_proto` instead (trustworthy: only loopback can reach the listener).
Django's `SECURE_PROXY_SSL_HEADER` depends on it.

---

## 2. Order of operations (what actually has to happen, in sequence)

1. **Workstation**: commit + push ALL deploy tooling. Create the deploy branch (`staging`) in
   every repo. Nothing on the server works before this — the VPS clones had no
   `deploy/deploy.sh` for an embarrassing while.
2. **DNS first, certs later** — every hostname → VPS IP, verify with `dig +short` before any
   certbot run (failed challenges count against rate limits).
3. **VPS as root (or web console)**: `deploy` user + SSH key, `PasswordAuthentication no`,
   `PermitRootLogin no`, ufw 22/80/443 only, unattended-upgrades, Docker, and **passwordless
   sudo** — see §4.1.
4. **As deploy**: per-repo GitHub deploy keys (§4.3), clone under `/srv/<project>/`,
   `docker network create <project>_edge` once.
5. **Backend**: fill `.env` (§4.4), `make staging-config` to validate cheaply, `deploy.sh`.
6. **Host edge**: render vhost → `nginx -t` → reload → `certbot --nginx -d … -d …` (one cert,
   every hostname as a SAN).
7. **Frontends**: 2-line `.env` each (`NEXT_PUBLIC_API_URL`, Google client id), `deploy.sh`.
   `NEXT_PUBLIC_*` is baked at **build** time — changing it = rebuild, not restart.
8. **Seed** (idempotent wrapper, dependency-ordered) + bootstrap the client's admin account.
9. Host crontab for nightly `pg_dump` backups (§5) + smoke test.

---

## 3. Decisions worth repeating

- **Media → R2, not MinIO, not S3.** Any S3-compatible endpoint slots into django-storages
  unchanged. R2: zero egress fees (the dominant cost for an image-heavy site), endpoint is
  publicly reachable so presigned URLs sign against it directly — kills the whole
  `media.<domain>` hostname + MinIO container + bucket-init service. What S3 has that R2
  lacks: per-object ACLs (`public-read`) — only matters if you want public static and private
  media in one bucket. The `AWS_ACCESS_KEY_ID`/`SECRET` come from **R2 → Manage API tokens →
  Object Read & Write scoped to the bucket** — shown once, at creation. Account-level
  Cloudflare API tokens are a different thing and won't work.
- **Static stays on a volume served by the docker nginx.** Presigned-URL storage is exactly
  wrong for static assets (they want public + cached-forever). Manifest/compressed storage +
  nginx `alias` beats uploading to a bucket on every deploy. Whitenoise is the fallback if the
  nginx location vanishes.
- **Backups: host cron, not a compose service.** ⭐ A backup service dies with the stack
  (`compose down` = silent no-backup night), `sleep 86400` loops drift and reset on restart,
  and rclone off-site sync wants host credentials. The dumps land on the host filesystem
  (bind path, not a named volume) so `down -v` can't touch them either way. One crontab line:
  `15 2 * * * /srv/<p>/backend/deploy/backup.sh >> /srv/<p>/backups/backup.log 2>&1`
- **Dead code deleted, not parked.** Once behind-proxy was the only mode, the in-stack
  certbot, TLS templates, and mode-switching flags were removed entirely. A dedicated-VPS
  future re-adds them from git history; carrying both modes was pure noise.
- **www dropped entirely** — users click links, they don't type. If keeping it: either
  un-proxy it in Cloudflare and put it on the cert, or leave it proxied and 301 it with a
  Cloudflare Redirect Rule (then it never touches the origin). Don't half-do both.
- **Encryption keys ≠ regenerable.** `FIELD_ENCRYPTION_KEYS` is plural for **rotation**
  (MultiFernet: first key encrypts, all keys decrypt — rotate by prepending). It and the
  blind-index key must live off-VPS: a DB backup without them is unreadable.

---

## 4. Traps that actually fired ⚠️⚠️

### 4.1 Server setup
- `adduser --disabled-password` + "just use sudo later" = **sudo is unusable** (no password to
  type). Either `passwd deploy` from a root session/web console, or
  `echo "deploy ALL=(ALL) NOPASSWD:ALL" > /etc/sudoers.d/deploy && chmod 440 …` (docker-group
  membership is root-equivalent anyway, so NOPASSWD loses little).
- Locked out of root SSH with no root password? The **provider web console** (serial tty) is
  the back door — it wants a *password* login (SSH keys don't exist there), so use the
  provider's reset-root-password button once and store it. Do this before you need it.
- `echo "key" /path/authorized_keys` — the `>` got lost in paste; echo printed to screen and
  the file never existed. Check the file after writing it.

### 4.2 Terminal paste is an enemy
Broken pastes produced, in one session: a heredoc whose indented `EOF` never terminated;
a multi-line `printf \`-continuation executed as N separate commands; an ssh_config with
`Host` and its alias on different lines; a certbot command where `-d` became `command not
found`. **Rules:** single-line commands over continuations; heredoc terminators at column 0;
`cat` the file after writing; when a paste mangles twice, stop and use `nano`.

### 4.3 GitHub deploy keys
One key cannot be added to two repos — generate one per repo, wire `~/.ssh/config` Host
aliases, and clone via `git@<alias>:owner/repo.git` (**no `.com` on the alias**). The alias is
whatever string follows `Host` in the config, nothing else.

### 4.4 The `.env` is sourced by shell scripts
Compose interpolation tolerates `https://<ACCOUNT_ID>.r2…` placeholders; `set -a; . ./.env`
does not — `<…>` is a redirection (`ACCOUNT_ID: No such file or directory`). Same reason
`FROM="Name <mail@x>"` needs quotes. Any script that sources the env file makes angle
brackets and unquoted spaces fatal — sweep for leftovers before first render/deploy.

### 4.5 Docker
- ⚠️⚠️ **Named volume mounted where the image has no directory** → docker creates the
  mountpoint **root-owned**; a `USER app` container then dies `EACCES` (here: collectstatic →
  `/app/staticfiles`). Fix in the Dockerfile — `mkdir -p … && chown app:app …` *before*
  `USER` — and on the server delete the already-created empty volume so it re-inits with
  image ownership.
- Compose `!override` YAML tag (list replacement in overlays) breaks generic YAML parsers —
  pre-commit's `check-yaml` needs an `exclude:` for that file. (Moot once the overlay was
  deleted, but the failure mode generalises: compose YAML ≠ plain YAML.)
- Frontends join an **external** docker network (`edge`) so the router reaches them by
  container name with zero published ports; `proxy_pass` through a *variable* + `resolver
  127.0.0.11` so nginx boots before they exist and 502s per-vhost instead of dying.

### 4.6 DNS / TLS on a Cloudflare zone
- **Orange-cloud (proxied) records break HTTP-01.** The tell in certbot's error: the
  validation IP is `2606:4700:…` (Cloudflare's range) — and check **AAAA**, not just A;
  LE prefers IPv6. Grey-cloud the record, confirm both `dig +short <host> A` and `… AAAA`,
  re-run. Failures are cheap (5/hostname/hour) but not free.
- **`Cannot GET /healthz/` is an Express string, not a Django one.** A wrong-shaped 404 names
  the thing that actually answered. Cause: **stale vhosts from a previous deployment** of the
  same domain still in `sites-enabled/`, shadowing the new config (nginx exact-`server_name`
  match beats everything). Old app processes kept running for months, invisible. On any
  inherited box: `ls sites-enabled/` and `grep -rn server_name` *before* wiring new vhosts.
- An existing cert lineage for one hostname? `certbot --expand` with the full `-d` list
  replaces it with one SAN cert. `certbot --nginx` is fine non-interactively (`-n`) once the
  account exists.
- Browser showing an old "Welcome to nginx" page after fixes = cache. `curl -sI` is the
  truth, not the browser.

---

## 5. Verification ladder (cheap → expensive)

```bash
make staging-config                                  # .env complete? seconds, before any build
docker compose -f <staging.yml> ps                   # everything Up, one-shots Exited(0)
curl -H "Host: backend.<d>" http://127.0.0.1:8080/healthz/   # stack edge, pre-TLS
curl -fsS https://backend.<domain>/healthz/          # full public chain incl. DB
```
Then the money legs that have no local equivalent: registration→email→verify (SMTP),
image upload+display (R2 creds), Stripe test checkout settling **without** the CLI
(webhook + payments worker), and the `wss://…/ws/…` socket in devtools (daphne leg).
502 on a frontend hostname = that container down or not on the edge network.

---

## 6. Leftovers checklist after go-live

- [ ] Stop the old superseded app processes still holding RAM (`pm2 list` / `ps aux`)
- [ ] Crontab backup line installed; `RCLONE_REMOTE` set; **restore tested once**
- [ ] Encryption keys + secrets stored off-VPS
- [ ] CI deploy secrets per repo (`VPS_HOST/USER/SSH_KEY`) so deploys become
      "ff-merge main→staging, push"
- [ ] Swap added if RAM < ~4 GB (Next.js builds spike 1–2 GB; OOM = opaque failed deploy)
- [ ] Grafana profile only with a strong admin password — it's a public hostname
