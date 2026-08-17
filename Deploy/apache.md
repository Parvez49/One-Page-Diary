# Apache (httpd)

> Preferred front door: **[nginx.md](nginx.md)** · Certificates: **[tls_certbot.md](tls_certbot.md)** ·
> SPA hosting: **[static_frontend.md](static_frontend.md)**

Apache is the one you inherit — legacy VPS boxes, cPanel hosting, and anything that depends on
`.htaccess`. Everything below is the reverse-proxy-in-front-of-an-app-server setup, which is
what it's almost always doing in a modern stack.

---

## 1. Modules — nothing works until they're enabled ⚠️

```bash
sudo a2enmod ssl proxy proxy_http rewrite headers
sudo systemctl restart apache2
```

⚠️⚠️ **`ProxyPass` in a vhost with `proxy_http` disabled is not an error — it's a 500.** Apache
silently ignores directives from unloaded modules at parse time and fails at request time.
Same for `RewriteRule` without `rewrite`. This is the #1 Apache time-sink.

| Command | Does |
|---|---|
| `a2enmod` / `a2dismod` | enable/disable a **module** |
| `a2ensite` / `a2dissite` | enable/disable a **vhost** (symlinks into `sites-enabled/`) |
| `apache2ctl configtest` | ⭐ validate config — the equivalent of `nginx -t` |

---

## 2. Directory structure

```
/etc/apache2/
├── apache2.conf         # main config, global <Directory> blocks
├── ports.conf           # Listen directives
├── sites-available/     # vhost files — inactive until a2ensite
├── sites-enabled/       # symlinks (a2ensite creates these)
├── mods-available/ mods-enabled/
└── conf-available/ conf-enabled/
```

Same available/enabled split as nginx — Apache just gives you `a2ensite` instead of `ln -s`.

---

## 3. Reverse proxy vhost ⭐

`/etc/apache2/sites-available/api.example.com.conf`:

```apache
<VirtualHost *:80>
    ServerName api.example.com
    Redirect permanent / https://api.example.com/          # everything to TLS
</VirtualHost>

<VirtualHost *:443>
    ServerName api.example.com

    SSLEngine on
    SSLCertificateFile    /etc/letsencrypt/live/api.example.com/fullchain.pem
    SSLCertificateKeyFile /etc/letsencrypt/live/api.example.com/privkey.pem

    ProxyPreserveHost On                                   # ⭐ pass the real Host header through
    RequestHeader set X-Forwarded-Proto "https"            # ⭐⭐ see below
    ProxyPass        / http://localhost:8000/
    ProxyPassReverse / http://localhost:8000/              # rewrite Location: headers on redirects

    ErrorLog  ${APACHE_LOG_DIR}/api.example.com-error.log
    CustomLog ${APACHE_LOG_DIR}/api.example.com-access.log combined
</VirtualHost>
```

```bash
sudo a2ensite api.example.com.conf
sudo apache2ctl configtest && sudo systemctl reload apache2
```

⭐ **The three directives that matter and why:**
- `ProxyPass` — forward requests to the backend.
- `ProxyPassReverse` — rewrite `Location`/`Content-Location` in *responses*, so a backend
  redirect to `http://localhost:8000/x` becomes `https://api.example.com/x`. ⚠️ Omitting it
  leaks `localhost:8000` into the user's browser bar on every redirect.
- `ProxyPreserveHost On` — the backend sees `api.example.com`, not `localhost`. Without it,
  framework `ALLOWED_HOSTS` checks, absolute URL generation, and multi-tenant host routing all
  break.

⚠️ Same `X-Forwarded-Proto` trap as nginx — TLS ends at Apache, so the app thinks it's on
plain HTTP: redirect loops, `http://` links in emails, `secure` cookies never set.

⚠️ **Multiple domains on one box:** each gets its own vhost file with its own `ServerName`.
Apache matches on `ServerName`/`ServerAlias`; the *first* enabled vhost on a port is the
default for anything unmatched — which is how a new domain mysteriously serves the old site.

---

## 4. `.htaccess` and `AllowOverride`

Apache's differentiator: per-directory config read at request time, no reload needed.

```apache
<Directory /var/www/>
    Options Indexes FollowSymLinks
    AllowOverride All          # was None — .htaccess files are IGNORED under None ⚠️
    Require all granted
</Directory>
```

⚠️ **`AllowOverride None` (the Debian/Ubuntu default) means `.htaccess` is silently ignored.**
An SPA rewrite rule or a redirect that "does nothing" is nearly always this.

⚠️ Trade-off: `AllowOverride All` makes Apache stat `.htaccess` in every parent directory on
**every request**. It's slower, and it lets anyone with write access to the docroot change
server behaviour. Prefer putting the rules in the vhost; use `.htaccess` only on shared
hosting where you don't control the vhost.

⚠️ `Options Indexes` serves a directory listing when there's no index file — turn it off
(`-Indexes`) on anything public.

---

## 5. Nginx vs Apache — the decision ⭐

| Choose | When |
|---|---|
| **Nginx** ⭐ | new deployments, high concurrency, static/proxy heavy, container images |
| **Apache** | inherited servers, `.htaccess` required, `mod_php`/cPanel, legacy modules |

The reason is architectural — event loop vs process-per-connection. Full comparison in
**[nginx.md](nginx.md) §1**.

---

## 6. Operating it

```bash
sudo apache2ctl configtest          # ⭐ before every reload
sudo systemctl reload apache2       # graceful
sudo apache2ctl -S                  # ⭐ dump the vhost map — which vhost wins for which name
sudo apache2ctl -M                  # list loaded modules
tail -f /var/log/apache2/error.log
```

⭐ `apache2ctl -S` is the tool for "the wrong site is being served" — it prints exactly which
vhost handles which `ServerName` on which port, in match order.

### Removing it cleanly

```bash
sudo systemctl stop apache2
sudo apt-get remove --purge apache2 apache2-utils apache2-bin apache2.2-common
sudo rm -rf /etc/apache2
sudo apt-get autoremove && sudo apt-get clean
```

⚠️ Do **not** `rm -rf /etc/letsencrypt` unless you're truly done with the certificates — that
directory holds the private keys and the renewal config for every domain on the box. Certbot
issuance is rate-limited (5 duplicate certs per domain per week), so re-issuing after a
mistaken delete can leave you without TLS for days.

---

## Interview points

- **`ProxyPass` vs `ProxyPassReverse`** ⭐ — forwards the request vs rewrites `Location`
  headers in the response. Without the second, backend redirects expose `localhost:8000`.
- **`ProxyPreserveHost On`** — the backend sees the public hostname; without it, host-based
  logic and absolute URLs break.
- **Why is `.htaccess` ignored?** ⚠️ `AllowOverride None`. And why you'd avoid `.htaccess`
  anyway: a per-request filesystem stat in every parent directory.
- **`a2enmod`/`a2ensite`** — Apache's module and vhost toggles; a missing module makes proxy
  directives fail at *request* time, not parse time.
- **Why nginx over Apache today** ⭐ — connection-scaling model, not features.
- **Both terminate TLS** — so both need `X-Forwarded-Proto` set and the app configured to
  trust it.
