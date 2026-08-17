# TLS, domains & Certbot

> Proxy config that consumes the certs: **[nginx.md](nginx.md)** · **[apache.md](apache.md)** ·
> DNS records for mail: **[email.md](email.md)**

---

## 1. What Let's Encrypt actually does ⭐

Certbot proves you control a domain, then gets a free 90-day certificate from Let's Encrypt.
Two ways to prove it:

| Challenge | How | Use when |
|---|---|---|
| **HTTP-01** ⭐ | Certbot serves a token at `/.well-known/acme-challenge/`; the CA fetches it over port 80 | the default — the server is publicly reachable |
| **DNS-01** | Certbot creates a `_acme-challenge` TXT record | ⭐ **wildcard certs** (`*.example.com`), or the box isn't public |

⚠️ HTTP-01 needs **port 80 open and reachable**, even though the site itself is HTTPS-only.
Firewalling off :80 breaks renewal silently, and you find out 90 days later.

⚠️ DNS must already point at the server *before* you run certbot — the CA resolves the name
and connects. A fresh A-record that hasn't propagated = validation failure.

---

## 2. Issuing

```bash
sudo apt install certbot python3-certbot-nginx     # or python3-certbot-apache

sudo certbot --nginx                               # interactive: pick from detected vhosts
sudo certbot --nginx -d example.com -d www.example.com     # ⭐ explicit, one cert, both names
sudo certbot --apache -d api.example.com                   # additional domain, later
```

The plugin **edits the vhost in place** — that's where all the `# managed by Certbot` lines in
your nginx/Apache configs come from: the `listen 443 ssl`, the cert paths, and the HTTP→HTTPS
redirect server block.

```bash
sudo certbot certonly --nginx -d example.com       # get the cert, DON'T touch my config
```

⭐ Use `certonly` when the vhost is managed by config management or is hand-tuned — Certbot's
rewrites are otherwise clobbered on renewal, or clobber your edits.

**Adding a domain later:** run certbot again with `-d newdomain`. That issues a **separate**
certificate; the existing one is untouched. To put several names on *one* cert, list every
`-d` in a single command — including the ones already covered.

---

## 3. Where things live

```
/etc/letsencrypt/
├── live/<domain>/          # ⭐ symlinks — always reference THESE paths in configs
│   ├── fullchain.pem       # cert + intermediate chain  → ssl_certificate
│   ├── privkey.pem         # ⚠️ private key             → ssl_certificate_key
│   ├── cert.pem            # leaf only — usually NOT what you want
│   └── chain.pem
├── archive/<domain>/       # the real, versioned files
└── renewal/<domain>.conf   # how to renew this cert (plugin, domains, webroot)
```

⚠️ Point configs at `live/`, never `archive/`. The `live/` symlinks are what get repointed on
renewal — hardcode an archive path and your server keeps serving the old cert until it expires.

⚠️ `fullchain.pem`, not `cert.pem`. Without the intermediate chain, browsers usually cope
(they cache intermediates) but mobile clients, `curl`, and API consumers fail with
"unable to get local issuer certificate" — the classic "works in my browser, breaks for the
mobile app" TLS bug.

---

## 4. Renewal ⭐

Certs last 90 days. Installing certbot installs a systemd timer (or cron) that renews anything
within 30 days of expiry.

```bash
systemctl list-timers | grep certbot     # ⭐ confirm the timer exists and is active
sudo certbot renew --dry-run             # ⭐⭐ the one command worth running after every setup
sudo certbot certificates                # what's installed, and expiry dates
```

⚠️ **Renewal is not enough on its own — the web server must reload to pick up the new cert.**
The packaged plugins handle this; a hand-rolled setup needs a hook:

```bash
sudo certbot renew --deploy-hook "systemctl reload nginx"
```

⚠️ **Rate limits are real:** 5 duplicate certificates per exact domain set per week, 50 certs
per registered domain per week. Debug with `--dry-run` (staging), never by re-issuing in a
loop — you can lock yourself out of new certs for a week.

---

## 5. Verifying

```bash
curl -vI https://example.com                        # cert chain + headers
openssl s_client -connect example.com:443 -servername example.com </dev/null | openssl x509 -noout -dates
```

⭐ `-servername` matters: it sends SNI. Without it you get whatever the *default* vhost serves,
which is how you end up debugging the wrong certificate entirely.

| Symptom | Cause |
|---|---|
| `NET::ERR_CERT_COMMON_NAME_INVALID` | ⚠️ requested `example.com` but not `www.example.com` |
| "unable to get local issuer certificate" | ⚠️ `cert.pem` used instead of `fullchain.pem` |
| Cert expired despite the timer | ⚠️ port 80 blocked, DNS moved, or no reload hook |
| Wrong site's cert served | vhost/SNI mismatch — `nginx -T` / `apache2ctl -S` |
| Mixed-content warnings | app generating `http://` URLs — missing `X-Forwarded-Proto` |

---

## 6. New-domain checklist ⭐

1. **A record** (and `www` A/CNAME) → server IP. Wait for propagation (`dig +short example.com`).
2. **SPF/DKIM/DMARC** TXT records if the domain sends mail — do it now, in the same sitting
   ([email.md](email.md)).
3. Vhost with `server_name`/`ServerName`, proxying to the app.
4. `certbot --nginx -d example.com -d www.example.com`.
5. `certbot renew --dry-run`.
6. App config: `ALLOWED_HOSTS`/`CORS`, `X-Forwarded-Proto` trusted, HSTS on.
7. `curl -vI https://example.com` and confirm the HTTP→HTTPS redirect.

---

## Interview points

- **How does Let's Encrypt verify ownership?** ⭐ HTTP-01 (token served over port 80) or
  DNS-01 (TXT record — required for wildcards).
- **Why does port 80 need to stay open on an HTTPS-only site?** ⚠️ HTTP-01 renewal.
- **`fullchain.pem` vs `cert.pem`** ⭐ — the chain. Omitting it breaks non-browser clients
  while browsers appear fine.
- **`live/` vs `archive/`** — `live/` is symlinks that get repointed on renewal; configs must
  use them.
- **What breaks silently after 90 days?** Renewal without a reload hook, a firewalled :80, or
  a moved DNS record.
- **TLS termination** ⭐ — it ends at the proxy. The app is on plain HTTP behind it and must be
  told the original scheme via `X-Forwarded-Proto`.
- **Wildcard certificates** require DNS-01, so your DNS provider needs an API for automation.
