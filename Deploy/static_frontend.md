# Deploying a frontend (SPA & static builds)

> Server config: **[apache.md](apache.md)** · **[nginx.md](nginx.md)** ·
> SSR/Next.js specifics: `../Web/NextJS/`

---

## 1. Build

```bash
yarn                # or npm ci — ⭐ ci/frozen-lockfile in CI, never a fresh resolve
yarn run build      # the "build" script in package.json → build/ (CRA) or dist/ (Vite)
```

⚠️ **Env vars are baked in at build time**, not read at runtime. `REACT_APP_*` / `VITE_*`
values become string literals in the bundle. Consequences:
- Changing an API URL means a **rebuild**, not a restart.
- ⚠️⚠️ **Anything in the bundle is public.** A secret key in `VITE_API_SECRET` ships to every
  visitor. Frontend env vars are configuration, never credentials.

⭐ Build once, deploy the same artifact to every environment — which means the API URL must
come from the *served* origin (relative `/api` paths, or a small runtime `config.json`
fetched on boot) if you want a truly environment-agnostic build.

---

## 2. Deploy the artifact

```bash
sudo rm -rf /var/www/html/*         # ⚠️ see below
sudo mv build/* /var/www/html/
```

⚠️ `rm -rf` then `mv` is a **downtime window** — for a few seconds the docroot is empty and
users get 404s or a half-loaded app. Better:

```bash
sudo rsync -a --delete build/ /var/www/html/     # atomic-ish, no empty window
```

⭐ Better still — release directories with a symlink swap, which makes rollback instant:

```
/var/www/app/releases/2026-08-17-1430/
/var/www/app/current -> releases/2026-08-17-1430     # ln -sfn, then reload
```

⚠️ Check ownership after copying: files owned by `root` with restrictive modes give a 403 that
looks like a config problem. `chown -R www-data:www-data`.

---

## 3. The SPA 404 problem ⭐⭐

**The symptom:** the app works when you click around, but a hard refresh on `/dashboard` (or
pasting the URL directly) returns **404**.

**Why:** client-side routing is a browser-history illusion. Clicking a link never touches the
server. A direct request for `/dashboard` makes the server look for a *file* at that path —
there isn't one, only `index.html`.

**The fix:** rewrite everything that isn't a real file or directory to `index.html`, and let
the JS router take it from there.

### Apache — `.htaccess` in `/var/www/html/`

```apache
<IfModule mod_rewrite.c>
    RewriteEngine On
    RewriteBase /
    RewriteRule ^index\.html$ - [L]
    RewriteCond %{REQUEST_FILENAME} !-f          # not an existing file
    RewriteCond %{REQUEST_FILENAME} !-d          # not an existing directory
    RewriteCond %{REQUEST_FILENAME} !-l          # not a symlink
    RewriteRule . /index.html [L]
</IfModule>
```

Two prerequisites, both silent when missing:

```apache
<Directory /var/www/html>
    Options Indexes FollowSymLinks
    AllowOverride All           # ⚠️⚠️ default is None → .htaccess IGNORED entirely
    Require all granted
</Directory>
```

```bash
sudo a2enmod rewrite && sudo systemctl restart apache2    # ⚠️ without this, RewriteRule does nothing
```

⭐ The `!-f`/`!-d` conditions are what stop the rewrite from swallowing your JS, CSS and
images — without them every asset request returns `index.html`, and the browser reports
"Unexpected token '<'" while parsing what it thought was JavaScript. That error message is
the fingerprint of a misconfigured SPA rewrite.

### Nginx — one line

```nginx
location / {
    root /var/www/html;
    try_files $uri $uri/ /index.html;      # ⭐ the whole fix
}
```

---

## 4. Caching — the pairing that matters ⭐

```nginx
location /static/ {                       # hashed filenames: main.a3f9c1.js
    root /var/www/html;
    expires 1y;
    add_header Cache-Control "public, immutable";
}

location = /index.html {
    root /var/www/html;
    add_header Cache-Control "no-cache";   # ⭐⭐ must revalidate, every time
}
```

⭐ **Hashed assets forever, `index.html` never.** The build fingerprints asset filenames, so a
new deploy produces new names and old caches can't collide — cache them for a year. But
`index.html` is the map to those names; cache it and returning users load the *old* HTML
pointing at assets you just deleted → a white screen until they hard-refresh.

⚠️ **The stale-tab problem:** a user with the app open since before the deploy is running old
JS requesting deleted chunk files. Either keep the previous release's assets around (another
argument for release directories) or detect the failed chunk load and prompt a reload.

---

## 5. Static host vs your own server ⭐

| Option | Notes |
|---|---|
| **Nginx/Apache on your VPS** | ⭐ same box as the API — no CORS, one certificate, full control |
| **Netlify / Vercel / Cloudflare Pages** | ⭐ CDN, atomic deploys, instant rollback, free TLS. The default for a pure SPA |
| **S3 + CloudFront** | cheap at scale; ⚠️ set the SPA error-document rewrite to `index.html` |
| **Served by the backend** | simple, but the app server now serves static files — see [nginx.md](nginx.md) §5 |

⚠️ Splitting frontend and API across origins buys you **CORS** — preflights, credentialed
requests, and cookie `SameSite` issues. Same-origin (`example.com` + `example.com/api`) avoids
the entire category. See `../Web/Django/security.md`.

---

## 6. Next.js is different ⚠️

`next build` + `next start` is a **Node server** (SSR, API routes, ISR) — it belongs behind
nginx like any app server ([app_servers.md](app_servers.md)), under a process supervisor.
None of the static-hosting section applies unless you're on `output: "export"`, which gives up
SSR and API routes. Details in `../Web/NextJS/`.

---

## Interview points

- **Why does refreshing `/dashboard` 404?** ⭐⭐ Client-side routing — the server has no file
  there. Fix: rewrite non-file requests to `index.html` (`try_files` / `mod_rewrite`).
- **Why the `!-f` / `!-d` conditions?** ⭐ Otherwise assets get `index.html` back and the
  browser throws "Unexpected token '<'".
- **`.htaccess` does nothing** ⚠️ — `AllowOverride None`, or `mod_rewrite` not enabled.
- **Cache headers for an SPA** ⭐ — hashed assets `immutable, 1y`; `index.html` `no-cache`.
  Reversed, users get a white screen after every deploy.
- **Are frontend env vars secret?** ⚠️ No — they're compiled into the bundle and shipped to
  every visitor.
- **Why does changing the API URL need a rebuild?** Build-time substitution.
- **Static host vs own server** — CDN and atomic rollback vs same-origin (no CORS) and one
  certificate.
- **Next.js vs a static SPA** ⚠️ — SSR means a long-running Node process, not a docroot.
