# Throttling, Rate Limiting & DDoS

> Security settings: **[security.md](security.md)** · Cache backend: **[caching.md](caching.md)**

---

## 1. Rate limiting vs DDoS defence ⭐

**They are not the same layer, and conflating them is a common interview slip.**

| | **Application rate limiting** | **DDoS mitigation** |
|---|---|---|
| Stops | abuse, scraping, brute force, runaway clients | volumetric floods from botnets |
| Where | ⭐ Django/DRF | ⭐ **CDN / WAF / network edge** (Cloudflare, AWS Shield) |
| Traffic | already reached your app | never reaches your app |

⭐⭐ **DRF throttling cannot stop a DDoS.** By the time a request is throttled it has already
consumed a TLS handshake, an nginx connection, a gunicorn worker, and a cache round trip. A
volumetric attack saturates bandwidth and worker pools regardless of the 429 you return. Say
this plainly — then describe the layered defence below.

**DoS vs DDoS:** one source vs thousands of compromised devices (a botnet) coordinating.
Distributed attacks can't be stopped by blocking a single IP, which is exactly why they're used.

**What an attack exhausts:** bandwidth (network saturation), CPU/memory (worker exhaustion),
**database connections** (the usual real bottleneck — 20 pooled connections die long before
the CPU does), and disk (log floods).

---

## 2. Defence in depth

```
 1. CDN / WAF        ⭐ absorb volumetric floods, bot scoring, geo/IP rules
 2. Load balancer    connection limits, SYN cookies
 3. nginx            ⭐ limit_req / limit_conn — cheap, before Python runs
 4. Django/DRF       ⭐ per-user & per-endpoint business limits
 5. Database         connection pool caps, statement timeout
```

```nginx
limit_req_zone $binary_remote_addr zone=api:10m rate=10r/s;
limit_conn_zone $binary_remote_addr zone=conn:10m;

location /api/ {
    limit_req  zone=api burst=20 nodelay;    # ⭐ blocked before touching gunicorn
    limit_conn conn 10;
}
```

⭐ **Push limits as far out as possible.** An nginx-rejected request costs microseconds; a
DRF-throttled one costs a full worker cycle. Use DRF for *business* rules ("100 exports per
day"), nginx for *volume*.

---

## 3. DRF throttling

```python
REST_FRAMEWORK = {
    "DEFAULT_THROTTLE_CLASSES": [
        "rest_framework.throttling.AnonRateThrottle",
        "rest_framework.throttling.UserRateThrottle",
    ],
    "DEFAULT_THROTTLE_RATES": {
        "anon":    "100/hour",
        "user":    "1000/hour",
        "login":   "5/min",        # ⭐ tight — brute force
        "payment": "30/min",
        "export":  "10/day",
    },
}
```

```python
class LoginView(APIView):
    throttle_classes = [ScopedRateThrottle]
    throttle_scope   = "login"

class PublicView(APIView):
    throttle_classes = []           # ⭐ explicitly opt OUT of the global default
```

| Class | Keyed on |
|---|---|
| `AnonRateThrottle` | ⚠️ IP, for **unauthenticated** requests |
| `UserRateThrottle` | user id (falls back to IP when anonymous) |
| `ScopedRateThrottle` | ⭐ per-view `throttle_scope` — the useful one |

**Rates:** `"100/day"`, `"20/hour"`, `"5/min"`, `"10/sec"`.

⚠️⚠️ **`AnonRateThrottle` is per-IP but `UserRateThrottle`'s anonymous fallback is too** —
and neither distinguishes a shared corporate NAT or mobile carrier gateway from an attacker.
Thousands of legitimate users behind one IP will exhaust a single bucket and get 429s. This is
the flaw your original note spotted: for public endpoints, set generous IP limits and put the
strict limits on *authenticated identity*.

⚠️ **DRF's throttle state lives in the cache** — with `LocMemCache` each gunicorn worker
counts separately, so your "100/hour" is really `100 × workers`. **It requires Redis** to be
correct ([caching.md](caching.md)).

⚠️ **`REMOTE_ADDR` behind a proxy is your load balancer's IP** — every user shares one bucket.
Configure `NUM_PROXIES` or parse `X-Forwarded-For` correctly, and ⚠️ **never trust the
leftmost `X-Forwarded-For` value** — clients can forge it. Take the entry your proxy appended.

---

## 4. Custom throttling

```python
from django.core.cache import cache
from rest_framework.throttling import SimpleRateThrottle

class BurstThrottle(SimpleRateThrottle):
    scope = "burst"
    def get_cache_key(self, request, view):
        if not request.user.is_authenticated:
            return None                                  # ⭐ None = don't throttle
        return f"throttle:burst:{request.user.pk}:{view.__class__.__name__}"
```

**Middleware for a global IP limit** (your original pattern, corrected):

```python
class IPRateLimitMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        ip = self.get_client_ip(request)
        key = f"rl:{ip}:{int(time.time() // 60)}"     # ⭐ per-minute bucket in the key
        try:
            count = cache.incr(key)                   # ⭐⭐ ATOMIC
        except ValueError:
            cache.set(key, 1, 120)                    # first request in this window
            count = 1
        if count > 300:
            return JsonResponse({"detail": "Rate limit exceeded"}, status=429)
        return self.get_response(request)
```

⚠️⚠️ **The naive `get` → `+1` → `set` version has a race**: concurrent requests all read the
same count and all write `n+1`, so the real limit is far higher than configured — precisely
when you need it most. `cache.incr()` is atomic; use it.

⚠️ **Global middleware applies to everything** — health checks, static, admin, webhooks. Prefer
per-view throttles, or exempt paths explicitly. That was the right conclusion in your notes.

---

## 5. Algorithms ⭐

| Algorithm | Behaviour |
|---|---|
| **Fixed window** | count per clock interval. Simple; ⚠️ **2× burst at the boundary** (60 at 10:59:59 + 60 at 11:00:01) |
| **Sliding window log** | timestamps per request — accurate, ⚠️ memory-heavy |
| **Sliding window counter** | ⭐ weighted blend of two windows — DRF's approach; good accuracy, cheap |
| **Token bucket** | ⭐ tokens refill at a steady rate — **allows bursts**, best UX |
| **Leaky bucket** | fixed drain rate — smooths output |

⭐ **Token bucket is usually the right choice for APIs**: a client that's been idle can spend
its accumulated allowance in one burst (a page loading 20 resources) while the long-run average
stays bounded. Fixed windows punish exactly that legitimate pattern.

---

## 6. Responding well

```http
HTTP/1.1 429 Too Many Requests
Retry-After: 60
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 0
X-RateLimit-Reset: 1735689600
```

⭐ **Always send `Retry-After`.** Without it a well-behaved client retries immediately and
makes the problem worse; with it, SDKs back off automatically. Publishing
`X-RateLimit-Remaining` lets clients self-regulate before hitting the wall.

⭐ **Fail open, not closed.** If Redis is down, DRF throttling raises — decide deliberately
whether an outage of your *cache* should take down your *API*. Usually: log and allow.

---

## 7. Beyond rate limits

- ⭐ **Rate-limit by cost, not just count** — one report export ≠ one health check. Weight
  expensive endpoints, or use a separate scope and queue.
- **Quotas** (per plan/tenant, monthly) are a *product* concern; rate limits are an
  *operational* one. Don't implement billing quotas in a throttle class.
- **Idempotency keys** on POST so client retries after a 429/timeout don't double-charge.
- ⭐ **Statement timeouts and connection pool caps** — the database is the resource that
  actually falls over. `SET statement_timeout` plus PgBouncer bounds the blast radius.
- **CAPTCHA / proof-of-work** on signup and login after N failures.
- **Account lockout** with care — an attacker can lock out real users by failing logins on
  purpose; prefer progressive delays and MFA.

---

## 8. Interview points

- **Can DRF throttling stop a DDoS? ⭐⭐** No — the request already consumed a worker. DDoS is
  handled at the CDN/WAF/network edge; app throttling handles abuse and brute force.
- **DoS vs DDoS?** Single source vs a distributed botnet — the latter can't be IP-blocked.
- **Where should rate limiting live?** As far out as possible: CDN → nginx → app, with the app
  enforcing per-user *business* limits.
- **What's wrong with IP-based limits? ⭐** NAT and carrier gateways share IPs, so real users
  collide; and behind a proxy `REMOTE_ADDR` is the load balancer unless configured.
- **Why can't you trust `X-Forwarded-For`?** Clients can forge it — only the segment your own
  proxy appends is trustworthy.
- **Why does the throttle backend matter?** Counters live in the cache; per-process
  `LocMemCache` multiplies the effective limit by the worker count.
- **What's the bug in get/increment/set rate limiting?** A race — use an atomic `INCR`.
- **Fixed window vs token bucket?** Fixed windows allow a 2× burst at the boundary and punish
  legitimate bursts; token bucket permits bursts while bounding the average.
- **What should a 429 include?** `Retry-After`, plus limit/remaining/reset headers.
- **What actually falls over first under load?** Usually database connections — cap the pool
  and set statement timeouts.
