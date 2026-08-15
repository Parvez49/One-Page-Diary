# Caching

> Query optimisation first: **[queries.md](queries.md)** · Background work: **[async_tasks.md](async_tasks.md)**

---

## 1. Cache only what you've already optimised ⭐

**The order that matters:** fix the N+1 → add the index → *then* cache. Caching an N+1 hides
it until the cache goes cold, and then the stampede takes the database down at the worst
possible moment.

**The two hard problems** (worth naming explicitly): **invalidation** and **stampedes**.
Everything below is about those.

---

## 2. Setup

```python
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.redis.RedisCache",   # ⭐ Django 4.0+ built-in
        "LOCATION": env("REDIS_URL"),
        "KEY_PREFIX": "myapp",                 # ⭐ namespace per app/environment
        "TIMEOUT": 300,
        "OPTIONS": {"socket_connect_timeout": 2, "socket_timeout": 2},   # ⭐ fail fast
    }
}
```

| Backend | Use |
|---|---|
| **Redis** | ⭐ production default — shared, persistent, atomic ops, pub/sub |
| Memcached | pure cache, slightly faster, no persistence or data types |
| `LocMemCache` | ⚠️ **per-process** — each gunicorn worker has its own; dev/tests only |
| `DatabaseCache` | when you have no Redis; ironic but workable |
| `DummyCache` | ⭐ development — disables caching without code changes |

⚠️⚠️ **`LocMemCache` in production is a classic bug**: with 4 gunicorn workers you get 4
inconsistent caches, and invalidation only clears one of them. Symptoms are "the fix works
sometimes."

⭐ **A cache must be optional.** Set short socket timeouts and ensure a Redis outage degrades
to slow, not down. `IGNORE_EXCEPTIONS` in `django-redis` does this.

---

## 3. The low-level API — the one to use ⭐

```python
from django.core.cache import cache

cache.set("key", value, timeout=300)      # timeout=None = forever, 0 = don't cache
cache.get("key", default=None)
cache.get_or_set("key", expensive_fn, 300)      # ⭐ compute only on miss
cache.delete("key")
cache.set_many({...}) / cache.get_many([...])   # ⭐ one round trip
cache.incr("counter")                            # ⭐ ATOMIC — the basis of rate limiting
cache.add("lock", "1", 60)                       # ⭐ only if absent → a poor-man's lock
```

```python
def get_dashboard(user_id):
    key = f"dashboard:v2:{user_id}"          # ⭐ version in the key
    data = cache.get(key)
    if data is None:
        data = expensive_query(user_id)
        cache.set(key, data, 600)
    return data
```

⭐ **Key design is the whole game:**
- Namespace with `:` — `product:detail:{id}:v2`.
- ⭐ **Put a version in the key.** Changing the shape of cached data with the same key serves
  the old shape to every running process — bump `v2` → `v3` instead of trying to purge.
- Include **every input** that affects the result: user/tenant id, locale, feature flags,
  permissions. ⚠️ Omitting the user id from a per-user cache leaks one user's data to another
  — a real and severe bug.
- Hash long keys (`hashlib.md5(...)`) — Memcached caps keys at 250 bytes.

---

## 4. Where to cache

```python
# --- per-view ---
@cache_page(60 * 15)                       # ⚠️ caches by URL — ignores the user!
def product_list(request): ...

# --- per-fragment (templates) ---
{% load cache %}
{% cache 300 sidebar request.user.id %}    # ⭐ vary key includes the user
    ...expensive...
{% endcache %}

# --- per-object ---
def get_config():
    return cache.get_or_set("site:config", lambda: SiteConfig.objects.first(), 3600)
```

⚠️⚠️ **`@cache_page` on an authenticated view serves one user's page to everyone.** It keys on
the URL (plus `Vary` headers) and knows nothing about `request.user`. Use it only for
genuinely public, anonymous responses, and add `@vary_on_headers("Authorization")` or
`@vary_on_cookie` if there's any chance of personalisation.

⭐ **Cache the *data*, not the rendered response**, when output varies by user — the query is
usually the expensive part, not the serialisation.

**DRF:** no built-in queryset caching. Cache inside `get_queryset`/service functions, or use
conditional requests:

```python
from django.utils.decorators import method_decorator
from django.views.decorators.http import etag, last_modified
```

⭐ **`ETag`/`Last-Modified` + `304 Not Modified`** is the cheapest cache of all — the client
already has the bytes, and you skip serialisation *and* transfer.

---

## 5. Invalidation ⭐⭐

**Three strategies, in increasing order of effort and correctness:**

```python
# 1. TTL — simplest, always correct eventually
cache.set(key, data, 300)          # ⭐ tolerate 5 min of staleness

# 2. Explicit invalidation on write
@receiver(post_save, sender=Product)
def clear_product_cache(sender, instance, **kwargs):
    cache.delete(f"product:{instance.id}:v1")
    cache.delete("product:list:v1")          # ⚠️ and every other key that included it...

# 3. ⭐ Key versioning — no deletion at all
def product_key(p):
    return f"product:{p.id}:{p.updated_at.timestamp()}"    # changes when the row changes
```

⭐⭐ **Prefer a short TTL to elaborate invalidation.** Ask "how stale can this be?" — for a
product list the answer is usually 60 seconds, and a TTL costs nothing to maintain. Explicit
invalidation is where bugs live: you delete `product:5` and forget the three list keys, the
search cache, and the sidebar fragment that embedded it.

⚠️ **Signals miss bulk operations** — `.update()`, `bulk_create` don't fire `post_save`
([orm.md §4](orm.md)), so signal-based invalidation silently leaves stale data.

**Pattern deletion** (`django-redis`) is a last resort:

```python
cache.delete_pattern("product:*")     # ⚠️ SCAN across the keyspace — slow on large caches
```

---

## 6. Stampedes & the failure modes ⭐

**Cache stampede (dogpile):** a popular key expires and 500 concurrent requests all miss and
all hit the database simultaneously.

```python
# ⭐ Lock: one worker recomputes, others serve stale or wait
if cache.add(f"{key}:lock", "1", 30):        # atomic set-if-absent
    try:
        value = expensive(); cache.set(key, value, 300)
    finally:
        cache.delete(f"{key}:lock")
```

Other mitigations: **jittered TTLs** (`300 + random.randint(0, 60)`) so keys don't expire in
lockstep, **early recomputation** (refresh at 80% of TTL), and serving stale-while-revalidate.

**The three named failure modes:**

| Problem | Cause | Fix |
|---|---|---|
| **Stampede** | popular key expires, everyone misses at once | lock, jitter, early refresh |
| **Penetration** | requests for keys that never exist (often malicious) | ⭐ **cache the negative result** (`None` for 30s), Bloom filter |
| **Avalanche** | many keys expire together, or Redis dies | jitter TTLs, Redis HA, graceful degradation |

⚠️ **Cache the empty result too.** `if data is None: query again` means every lookup for a
nonexistent id hits the database — a trivially exploitable amplification. Use a sentinel value
so "known absent" is cacheable.

---

## 7. Layers above Django ⭐

```
Browser cache  →  CDN  →  nginx  →  Django cache  →  DB query cache  →  DB
   cheapest ─────────────────────────────────────────────────────▶ most expensive
```

⭐ **Push caching as far from the database as possible.** A CDN hit never reaches your
infrastructure at all; a Django cache hit still costs a request, a worker, and a Redis round
trip.

```python
# Cache-Control drives browser and CDN behaviour
Cache-Control: public, max-age=31536000, immutable    # ⭐ hashed static assets
Cache-Control: private, no-store                       # ⚠️ authenticated responses
```

⚠️ **Never send `Cache-Control: public` on a personalised response** — a shared proxy or CDN
will serve one user's data to another. This is a real, recurring production incident.

⭐ **`Vary: Accept-Encoding, Authorization`** tells caches what makes responses differ; getting
`Vary` wrong is how CDNs mix up responses.

**Static files:** `ManifestStaticFilesStorage` appends a content hash to filenames, which lets
you cache them for a year and invalidate by changing the name.

---

## 8. Interview points

- **When would you add caching? ⭐** After fixing N+1s and adding indexes — caching a broken
  query hides it until the cache is cold.
- **What are the two hard problems?** Invalidation and stampedes.
- **Why is `LocMemCache` wrong in production?** It's per-process; each worker has a separate,
  independently stale copy.
- **What's wrong with `@cache_page` on a logged-in view? ⭐** It keys on URL, not user — one
  user's page is served to everyone.
- **How do you invalidate?** TTL first; explicit deletion or key versioning when correctness
  demands it. Signals miss bulk operations.
- **What's a cache stampede and how do you prevent it?** Simultaneous misses on an expired hot
  key; use a recompute lock, TTL jitter, or early refresh.
- **Why cache negative results?** Otherwise every request for a nonexistent key hits the
  database — cache penetration.
- **What must be in the cache key?** Everything that changes the output — user/tenant, locale,
  permissions, and a version tag.
- **Where's the cheapest place to cache?** Closest to the client: browser/CDN via
  `Cache-Control` and ETags.
- **How do you handle a Redis outage?** Short timeouts and degrade to uncached — the cache
  must never be a hard dependency.
