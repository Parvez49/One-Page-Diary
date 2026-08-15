# Request Lifecycle, Middleware & Signals

> DRF layer on top: **[drf.md](drf.md)** · Servers & ASGI: **[deployment.md](deployment.md)**

---

## 1. The full path of a request ⭐⭐

```
Browser
   │  HTTP
   ▼
nginx  (TLS, static files, gzip, rate limit)
   │  proxy_pass
   ▼
gunicorn / uvicorn        ← the WSGI/ASGI SERVER (process + worker management)
   │  WSGI callable: environ dict → (status, headers, body)
   ▼
Django WSGIHandler
   │
   ├─ MIDDLEWARE (top → bottom)          ← request phase
   │     Security → Session → CommonMiddleware → CSRF → Auth → Message
   │
   ├─ URL RESOLVER  urls.py → view + kwargs
   │
   ├─ view middleware → VIEW → (DRF: authentication → permission → throttle → handler)
   │                             │
   │                             └─ ORM → database
   │
   ├─ MIDDLEWARE (bottom → top)          ← response phase
   │
   ▼
HttpResponse → gunicorn → nginx → Browser
```

⭐ **The distinction interviewers probe: WSGI/ASGI is a *specification*, not a server.**
gunicorn/uvicorn implement it; Django is the application. WSGI is a **synchronous** contract
(one request per worker at a time); **ASGI** adds async and long-lived connections
(WebSockets, SSE) — see [deployment.md](deployment.md).

⚠️ **Django does not serve static files in production.** `runserver` does it as a
convenience; nginx or a CDN must handle `/static/` and `/media/`.

---

## 2. Middleware ⭐⭐

**Middleware is an onion.** Each layer sees the request on the way in and the response on the
way out — in **reverse order**.

```python
class TimingMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response          # ⭐ runs ONCE at startup

    def __call__(self, request):
        start = time.perf_counter()               # ── request phase (top → bottom)

        response = self.get_response(request)     # ── call the next layer / the view

        response["X-Duration"] = f"{time.perf_counter() - start:.3f}"   # ── response phase
        return response                           #    (bottom → top)
```

```python
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",        # ⭐ first: HTTPS redirect, HSTS
    "django.contrib.sessions.middleware.SessionMiddleware", # must precede Auth
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",            # must precede Auth
    "django.contrib.auth.middleware.AuthenticationMiddleware",   # ⭐ sets request.user
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]
```

⚠️⚠️ **Order is semantic, not cosmetic.** `AuthenticationMiddleware` needs
`SessionMiddleware` to have run (it reads the session to populate `request.user`); putting
auth first gives `AttributeError: 'WSGIRequest' object has no attribute 'session'`. Security
middleware belongs at the top so it applies before anything else does work.

⭐ **Short-circuiting:** if `__call__` returns a response **without** calling
`get_response()`, the view never runs and only the middleware *above* it sees the response.
That's how rate limiting, maintenance mode, and auth gates work
([throttling.md](throttling.md)).

**The optional hooks**, called between the request phase and the view:

| Hook | When |
|---|---|
| `process_view(request, view_func, args, kwargs)` | ⭐ after URL resolution, **before** the view — you know which view will run |
| `process_exception(request, exception)` | the view raised |
| `process_template_response(request, response)` | response has a `.render()` |

⚠️ **Middleware runs on *every* request** — a database query or an external HTTP call there
multiplies across your entire traffic. Keep it to cheap header/session work.

⚠️ Django's async support: a sync middleware in an async stack forces a thread-pool hop
(`sync_to_async`) per request. Mark middleware with `async_capable`/`sync_capable` to avoid
silently serialising an async deployment.

---

## 3. URL resolution

```python
# project/urls.py
urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/v1/", include(("shop.urls", "shop"), namespace="v1")),
]

# shop/urls.py
app_name = "shop"
urlpatterns = [
    path("products/<int:pk>/", ProductDetail.as_view(), name="product-detail"),
    path("search/<slug:term>/", search, name="search"),
    re_path(r"^legacy/(?P<code>[A-Z]{3})/$", legacy),
]
```

⭐ **Always `name=` your routes** and reverse them — never hard-code paths:

```python
reverse("v1:product-detail", kwargs={"pk": 1})     # → /api/v1/products/1/
{% url 'v1:product-detail' pk=1 %}                 # template
```

Hard-coded URLs break the moment a prefix changes; `reverse()` fails loudly at that point
instead.

**Path converters:** `str` (default, no `/`), `int`, `slug`, `uuid`, `path` (matches `/`).
Matching is **top to bottom, first match wins** — put specific patterns above generic ones.

---

## 4. Views — FBV vs CBV

```python
def product_list(request):                          # function-based: explicit, simple
    if request.method == "POST": ...
    return render(request, "list.html", {"products": qs})

class ProductList(ListView):                        # class-based: inherited behaviour
    model = Product
    paginate_by = 20
    def get_queryset(self):
        return super().get_queryset().select_related("category")
```

⭐ **FBV for one-off, unusual logic; CBV when you're repeating CRUD.** The honest trade:
CBVs remove boilerplate but hide control flow across a mixin chain, so debugging means
reading the MRO. DRF's `ViewSet` is where CBVs genuinely pay off
([drf.md](drf.md)).

`as_view()` returns a closure; `dispatch()` routes by HTTP method to `get()`/`post()`/etc.

---

## 5. Request & response objects

```python
request.method                  # "GET"
request.GET / request.POST      # QueryDict — ⚠️ immutable
request.body                    # raw bytes (JSON APIs)
request.user                    # ⭐ set by AuthenticationMiddleware; AnonymousUser if not logged in
request.META["HTTP_X_FORWARDED_FOR"]
request.headers["Authorization"]   # ⭐ nicer than META
request.session["cart"] = [...]
```

```python
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse, HttpResponse, StreamingHttpResponse, Http404

JsonResponse({"ok": True}, status=201)
StreamingHttpResponse(row_generator())          # ⭐ big exports — constant memory
get_object_or_404(Product, pk=pk)               # ⭐ 404 instead of DoesNotExist → 500
```

⚠️ `request.GET.getlist("tag")` for repeated params — `request.GET["tag"]` returns only the
last one.

---

## 6. Signals ⭐

Decoupled notifications: a sender emits, receivers react.

```python
from django.db.models.signals import post_save, pre_delete
from django.dispatch import receiver

@receiver(post_save, sender=Order)
def on_order_saved(sender, instance, created, **kwargs):
    if created:
        transaction.on_commit(lambda: send_confirmation.delay(instance.id))   # ⭐
```

**Built-ins:** `pre_save`/`post_save`, `pre_delete`/`post_delete`, `m2m_changed`,
`request_started`/`finished`, `user_logged_in`.

⚠️⚠️ **Signals are synchronous and in-process** — they are *not* a message queue. A slow
receiver blocks the request that triggered it.

⚠️ **Signals don't fire for `.update()`, `bulk_create()`, `bulk_update()`, or queryset
`.delete()` cascades.** Logic that *must* run belongs in the model's `save()` or an explicit
service function.

⭐ **The senior opinion, worth stating:** signals make control flow invisible — you read a
`save()` and can't tell that four receivers in three apps also ran. Use them for genuinely
cross-cutting concerns (audit logs, cache invalidation) or when you can't modify the sender
(third-party models). For your own domain logic, **call the function explicitly** — a
service layer beats action-at-a-distance.

Register receivers in `AppConfig.ready()`, and set `dispatch_uid` to avoid double
registration.

---

## 7. Settings & app config

```python
# settings/base.py, dev.py, prod.py   ⭐ split by environment
DEBUG = env.bool("DJANGO_DEBUG", default=False)
SECRET_KEY = env("DJANGO_SECRET_KEY")          # ⭐ from env, never committed
ALLOWED_HOSTS = env.list("ALLOWED_HOSTS")
```

⚠️⚠️ **`DEBUG = True` in production leaks your settings, SQL, and stack traces** to anyone who
triggers an error, and disables `ALLOWED_HOSTS` checking. It's the single most damaging
misconfiguration in Django. See [security.md](security.md).

⭐ **Never import settings at module level for values that change**: `from django.conf import
settings` then `settings.X` at call time — `settings` is a lazy object, and importing the
*value* at import time freezes it and breaks test overrides.

```python
class ShopConfig(AppConfig):
    name = "shop"
    def ready(self):
        from . import signals        # ⭐ import receivers here, not at module top
```

---

## 8. Interview points

- **Walk me through a Django request. ⭐⭐** nginx → WSGI/ASGI server → middleware (in order)
  → URL resolver → view → ORM → response back up through middleware in reverse.
- **What is WSGI, and how does ASGI differ?** A sync spec between server and app; ASGI adds
  async and long-lived protocols (WebSockets).
- **How does middleware work?** An onion — `__call__` sees the request going down and the
  response coming back; returning early short-circuits the view.
- **Why does middleware order matter?** Dependencies: auth needs the session; security should
  run first. Wrong order gives missing-attribute errors or unenforced protections.
- **How would you add a request ID to every log line?** Middleware that generates a UUID,
  stores it in a `ContextVar`, and adds it to the response headers.
- **FBV vs CBV?** Explicit and simple vs less boilerplate but hidden MRO control flow.
- **What are signals good and bad at? ⭐** Good: cross-cutting concerns and third-party models.
  Bad: domain logic — they're synchronous, invisible, and skipped by bulk operations.
- **Why didn't my `post_save` fire?** `.update()`/`bulk_create` bypass `save()`.
- **Why `transaction.on_commit` around a Celery call in a signal?** The worker may run before
  the transaction commits and fail to find the row.
- **What does `DEBUG=True` do in production?** Exposes settings and tracebacks, disables host
  validation, and retains every SQL query in memory.
