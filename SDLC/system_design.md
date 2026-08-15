# System Design Fundamentals

> Interview framing: **requirements → estimation → high-level design → deep dive → bottlenecks
> & trade-offs.** There is no "correct" design — you are graded on the **trade-offs you name**.

---

## 1. Scaling

**Application scaling** = increasing or decreasing an application's capacity to handle more
users, requests and data efficiently, while keeping performance and reliability stable as
demand changes.

### Vertical vs Horizontal ⭐

| | **Vertical (Scale Up)** | **Horizontal (Scale Out)** |
|---|---|---|
| How | Add RAM / CPU / SSD to **one** server | Add **more** servers |
| Limit | **Hard ceiling** — biggest machine available | Effectively unlimited |
| Complexity | Simple, no code change | Needs a **load balancer**, stateless app |
| Downtime | Usually requires a restart | Zero-downtime (rolling) |
| Failure | **SPOF** — one machine dies, all dies | Redundant by design |
| Cost curve | Exponential at the high end | Linear, commodity hardware |
| Data consistency | Trivial (one node) | Hard (distributed state) |

> Rule of thumb: **scale up first** (cheap and simple), **scale out when** you hit the ceiling,
> need HA, or need geographic distribution.

**Prerequisite for horizontal scaling: a stateless application.** No local session storage,
no local file uploads, no in-process cache holding truth. Push state to Redis / DB / S3.

*Is Django scalable?* Yes — it handles increased traffic and data loads when deployed properly,
and supports both vertical and horizontal scaling (stateless WSGI/ASGI workers behind a load
balancer, sessions in Redis, media on S3, Celery for background work, read replicas for the DB).

---

## 2. CAP Theorem ⭐

> In a distributed system you can guarantee only **2 of 3**: **C**onsistency,
> **A**vailability, **P**artition tolerance.

| | Meaning |
|---|---|
| **C — Consistency** | Every read returns the most recent write (or an error) |
| **A — Availability** | Every request gets a non-error response (possibly stale) |
| **P — Partition tolerance** | System keeps working despite dropped/delayed messages between nodes |

> ⚠️ **The nuance that impresses interviewers:** network partitions are a **fact of life**, not
> a choice. So **P is mandatory**, and the real decision is **CP vs AP** *during a partition*.
> When there is no partition, you get both C and A.

| Choice | Behaviour during a partition | Examples | Use when |
|---|---|---|---|
| **CP** | Reject requests rather than serve stale data | PostgreSQL (single-primary), MongoDB, HBase, Zookeeper, etcd | Banking, inventory, bookings |
| **AP** | Keep serving, reconcile later | Cassandra, DynamoDB, CouchDB, Riak | Social feeds, product catalogues, analytics |

**PACELC** (the extension): *if **P**artition → **A** or **C**; **E**lse → **L**atency or **C**onsistency.*
Even with a healthy network you trade latency against consistency.

### Consistency models
| Model | Guarantee | Example |
|---|---|---|
| **Strong** | Read always sees the latest write | Bank balance |
| **Eventual** | Replicas converge *eventually* | DNS, S3, social likes |
| **Read-your-writes** | *You* see your own writes immediately; others may lag | Posting a comment |
| **Causal** | Causally related ops seen in order | Comment appears after its post |
| **Monotonic reads** | Never read older data than you already saw | Avoids "the like count went down" |

**ACID vs BASE**
- **ACID** (Atomicity, Consistency, Isolation, Durability) — relational DBs, correctness-first.
- **BASE** (**B**asically **A**vailable, **S**oft state, **E**ventual consistency) — NoSQL, availability-first.

---

## 3. Load Balancing

Distributes traffic across servers. Layer 4 (TCP — fast, no payload inspection) vs
**Layer 7** (HTTP — routes by URL/header/cookie, can do SSL termination).

| Algorithm | How | Best for | Drawback |
|---|---|---|---|
| **Round Robin** | Sequential rotation | Identical servers, uniform requests | Ignores actual load |
| **Weighted Round Robin** | Bigger servers get more | Mixed hardware | Static weights |
| **Least Connections** | Fewest active connections | Long-lived/variable requests | Slight overhead |
| **Least Response Time** | Fastest responder | Latency-sensitive | Needs live metrics |
| **IP Hash** | Hash client IP → same server | Sticky sessions | Uneven distribution; breaks on server change |
| **Consistent Hashing** | Hash ring | **Caches & sharding** — minimal reshuffle when a node joins/leaves | More complex |

**Health checks** are essential — the LB must remove unhealthy nodes automatically.
⚠️ **The LB itself is a SPOF** → run it in active-passive pairs with a floating IP, or use a
managed LB (ALB/ELB).

> **Sticky sessions** (session affinity) are a smell: they break even distribution and lose
> sessions on failover. Prefer a **stateless app + shared session store (Redis)**.

---

## 4. Caching ⭐

> *"There are only two hard things in Computer Science: cache invalidation and naming things."*

### Where caching happens
```
Browser cache ▸ CDN ▸ Load balancer ▸ Application cache (Redis) ▸ Database cache ▸ Disk
    (closest & cheapest) ──────────────────────────▶ (furthest & most expensive)
```

### Strategies

| Strategy | Flow | ✅ Pros | ❌ Cons |
|---|---|---|---|
| **Cache-Aside** (lazy loading) ⭐ most common | App checks cache → miss → read DB → populate cache | Only caches what's used; cache failure isn't fatal | Cold-start misses; risk of stale data; 3 trips on a miss |
| **Read-Through** | App only talks to the cache; cache loads from DB itself | Simpler app code | Cold start; needs cache-provider support |
| **Write-Through** | Write to cache **and** DB synchronously | Cache never stale | Write latency ↑; caches data that may never be read |
| **Write-Behind** (write-back) | Write to cache, flush to DB async | **Fastest writes**, absorbs spikes | ⚠️ **Data loss** if cache dies before flush |
| **Refresh-Ahead** | Proactively refresh hot keys before TTL | Low latency on hot keys | Wasted work on wrong predictions |

### Eviction policies
**LRU** (least recently used — the default choice) · **LFU** (least frequently used — good for
stable hot sets) · **FIFO** · **TTL** (time-based expiry).

### Invalidation approaches
1. **TTL** — simplest; accepts bounded staleness. *Start here.*
2. **Write-through / explicit delete on update** — accurate, but easy to miss a code path.
3. **Versioned keys** (`user:123:v7`) — no deletion needed, old entries age out.
4. **Event-based** — publish an invalidation event to all nodes.

**⚠️ Cache failure modes to name:**
- **Cache stampede / thundering herd** — a hot key expires and 10 000 requests hit the DB at once.
  *Fix:* lock/single-flight, staggered TTL jitter, refresh-ahead.
- **Cache penetration** — queries for keys that don't exist bypass the cache every time.
  *Fix:* cache the negative result, or a Bloom filter.
- **Cache avalanche** — many keys expire simultaneously. *Fix:* randomised TTLs.
- **Hot key** — one key overwhelms a single node. *Fix:* local replica of that key, or key splitting.

---

## 5. Database Scaling

### Replication
| Type | Description | ✅ | ❌ |
|---|---|---|---|
| **Primary–Replica** | Writes → primary, reads → replicas | Scales **reads**, backups, HA | **Replication lag** → stale reads; writes still single-node |
| **Multi-Primary** | Writes to several nodes | Write availability, geo-distribution | **Write conflicts**, complex resolution |

> **Replication lag trap:** user posts a comment (write → primary) then refreshes (read →
> replica) and it's missing. *Fix:* route a user's reads to the primary for N seconds after
> their write ("read-your-writes").

### Partitioning
- **Vertical partitioning** — split *columns/tables* by feature (users table ↔ orders table on separate DBs).
- **Horizontal partitioning / Sharding** — split *rows* across DBs.

| Shard key strategy | How | ❌ Watch out |
|---|---|---|
| **Range** (A–M, N–Z) | Simple, range queries work | **Hotspots** if data is skewed |
| **Hash** | Even distribution | Range queries need scatter-gather; resharding is painful |
| **Consistent hashing** | Minimal movement on resize | More complex |
| **Directory/lookup** | Flexible, a lookup table maps key→shard | The lookup service is a SPOF |
| **Geo** | Data near users, compliance (GDPR) | Uneven load per region |

**❌ Sharding drawbacks (say these!):** cross-shard **JOINs and transactions become very hard**,
rebalancing is operationally risky, a bad shard key is extremely expensive to change, and
`AUTO_INCREMENT` IDs break (→ use UUID/ULID or Snowflake IDs).

> **Order of escalation — do these in order, don't jump to sharding:**
> **indexes → query tuning → caching → read replicas → vertical partition → shard.**

**Other levers:** connection pooling (PgBouncer), denormalisation for read speed,
materialised views, and a separate **OLAP** warehouse for analytics so reporting queries
never touch the OLTP database.

---

## 6. API Design

### REST vs GraphQL vs gRPC ⭐

| | **REST** | **GraphQL** | **gRPC** |
|---|---|---|---|
| Transport / format | HTTP + JSON | HTTP + JSON | HTTP/2 + **Protobuf** (binary) |
| Data fetching | Fixed endpoints | **Client specifies exact fields** | Fixed RPC methods |
| Over/under-fetching | Common problem | Solved | N/A |
| Round trips | Often several (N+1) | **One** query | One |
| Caching | **Easy** — HTTP caching for free | Hard (POST, dynamic queries) | Hard |
| Performance | Good | Good | **Best** (binary, multiplexed, streaming) |
| Browser support | Native | Native | Needs grpc-web proxy |
| Learning curve | Low | Medium | Medium-high |
| **Best for** | Public APIs, CRUD, simplicity | Mobile/varied clients, complex nested data | **Internal service-to-service**, low latency, streaming |

**GraphQL ❌ drawbacks:** HTTP caching is lost; a malicious deeply-nested query can DoS you
(→ query depth/complexity limits); the **N+1 resolver problem** (→ DataLoader batching);
rate limiting by "requests" is meaningless (→ cost analysis); file uploads are awkward.

### REST conventions
```
GET    /api/v1/orders          # list        200
POST   /api/v1/orders          # create      201 + Location header
GET    /api/v1/orders/123      # read        200 / 404
PUT    /api/v1/orders/123      # full update 200
PATCH  /api/v1/orders/123      # partial     200
DELETE /api/v1/orders/123      # delete      204
GET    /api/v1/orders/123/items    # nested resource
```
- **Nouns, not verbs** — `/orders`, not `/getOrders`. Plural. Hierarchy via nesting.
- **Status codes:** `200` OK · `201` Created · `204` No Content · `400` Bad Request ·
  `401` Unauthenticated · `403` Forbidden · `404` Not Found · `409` Conflict ·
  `422` Unprocessable · `429` Too Many Requests · `500` Server Error · `503` Unavailable.
- **Idempotency:** `GET`, `PUT`, `DELETE` are idempotent; `POST` is not. Use an
  **`Idempotency-Key`** header for payment-style POSTs so a retry can't double-charge.
- **Pagination:** offset (`?page=2&limit=20` — simple but slow & unstable on deep pages) vs
  **cursor** (`?after=xyz` — stable and fast, but no random access).
- **Versioning:** URL path `/v1/` (explicit, easy) · header `Accept: application/vnd.api+json;version=1`
  (clean URLs, less visible) · query param `?version=1`.

---

## 7. Reliability & Resilience

| Concept | Meaning |
|---|---|
| **Availability** | % uptime. **99.9%** ≈ 8.8 h/yr down · **99.99%** ≈ 52 min · **99.999%** ≈ 5 min |
| **SLA / SLO / SLI** | Contract / internal target / the actual measurement |
| **Latency vs Throughput** | Time per request vs requests per second |
| **p50 / p95 / p99** | Percentile latency. ⚠️ **Always design to p99, not average** — averages hide the users who are suffering |
| **Redundancy** | Spare capacity: active-active vs active-passive |
| **Failover** | Automatic switch to standby |
| **Graceful degradation** | Turn off recommendations to keep checkout alive |
| **Circuit breaker** | Stop calling a failing dependency; fail fast, then probe (closed → open → half-open) |
| **Backpressure** | Signal upstream to slow down instead of collapsing |
| **Retry + exponential backoff + jitter** | ⚠️ Retries **without** jitter cause synchronised retry storms |
| **Bulkhead** | Isolate resource pools so one failure can't exhaust everything |
| **Timeout** | Every network call needs one. No timeout = hung threads = cascading failure |

### Rate Limiting

| Algorithm | How | ✅ | ❌ |
|---|---|---|---|
| **Fixed Window** | N requests per clock minute | Trivial, low memory | **Burst at the boundary** — 2N across two windows |
| **Sliding Window Log** | Timestamp of every request | Exact | Memory-heavy |
| **Sliding Window Counter** | Weighted blend of two windows | Good accuracy/memory balance | Approximate |
| **Token Bucket** ⭐ | Tokens refill at a fixed rate; each request spends one | **Allows controlled bursts** | Two params to tune |
| **Leaky Bucket** | Queue drains at a constant rate | **Smooths** output perfectly | No bursts; queue adds latency |

Respond with **`429 Too Many Requests`** + a `Retry-After` header.

---

## 8. Networking

### Performance factors
- **DNS delay** — resolution before any request; mitigate with DNS caching / prefetch.
- **High latency** — physical distance & round trips; mitigate with a **CDN** and edge caching.
- **Too many hops** — each proxy adds latency.
- **No CDN** — static assets served from origin, far from users.
- **TCP handshake + TLS handshake** — use keep-alive, HTTP/2 multiplexing, TLS session resumption.

### Network security layers
- **JWT / OAuth2** (application layer auth)
- **Firewall / security groups** (allow-list ports)
- **Private subnets** — DB never publicly reachable; app tier in private subnet behind a NAT
- **HTTPS/TLS** everywhere (the 🔒 lock) + **HSTS**
- **IP restriction / allow-listing** for admin endpoints
- **WAF** (blocks SQLi/XSS patterns) and **DDoS protection** (Cloudflare, AWS Shield)

### What happens when a URL is hit in the browser ⭐ *classic question*
```
https://www.example.com/products/123
  │       │               │
  │       │               └─ path   → /products/123
  │       └───────────────── domain → www.example.com
  └───────────────────────── protocol → https (default port 443; http = 80)
```
1. **URL parsed** → protocol, domain, path, query, port.
2. **DNS resolution** — browser cache → OS cache → router → ISP resolver → root → TLD → authoritative NS → **IP address**.
3. **TCP handshake** (SYN → SYN-ACK → ACK) to that IP on port 443.
4. **TLS handshake** — certificate validated, session keys negotiated.
5. **HTTP request** sent (`GET /products/123` + headers + cookies).
6. Request traverses **CDN → load balancer → web server → app server → cache/DB**.
7. **HTTP response** returns (status, headers, HTML body).
8. **Browser renders**: parse HTML → build DOM → fetch CSS/JS/images (more requests) → CSSOM →
   render tree → layout → paint. JS executes, may trigger XHR/fetch.

### Protocols for real-time
| | Direction | Use case |
|---|---|---|
| **HTTP polling** | Client asks repeatedly | Simple, wasteful |
| **Long polling** | Server holds the request open | Legacy fallback |
| **SSE** | Server → client, one-way | Notifications, live feeds |
| **WebSocket** | **Full duplex**, persistent | Chat, multiplayer, trading |
| **WebRTC** | Peer-to-peer | Video/voice calls |

---

## 9. Back-of-the-Envelope Numbers

| Operation | Latency |
|---|---|
| L1 cache reference | 0.5 ns |
| Main memory reference | 100 ns |
| SSD random read | 150 µs |
| Round trip within a datacenter | 0.5 ms |
| Disk seek (HDD) | 10 ms |
| Round trip CA → Netherlands | **150 ms** |

**Rules of thumb:** memory is ~100 000× faster than disk · 1 day ≈ 86 400 s ≈ **100k s** ·
1 M DAU with 10 requests/day ≈ **~115 RPS average**, and peak ≈ **2–3× average** ·
1 KB × 1 M rows = 1 GB.

---

## 10. System Design Interview Framework

1. **Clarify requirements (5 min)** — functional, non-functional (scale, latency, consistency),
   and explicitly state what is **out of scope**. *Never start drawing immediately.*
2. **Estimate (5 min)** — DAU, RPS, read:write ratio, storage/year, bandwidth.
3. **High-level design (10–15 min)** — boxes and arrows: client → LB → services → cache → DB.
4. **Data model & API** — schema, choice of SQL vs NoSQL **with justification**, key endpoints.
5. **Deep dive (10–15 min)** — the interviewer picks one area; go deep.
6. **Bottlenecks & trade-offs (5 min)** — SPOFs, hot spots, what breaks at 10×, monitoring.

> **What actually gets you the offer:** thinking aloud, asking clarifying questions, and
> **naming the trade-off in every decision**. "I'd use Cassandra here — we need write
> availability across regions and can tolerate eventual consistency for the feed, though we'd
> lose ad-hoc query flexibility" beats a perfect diagram with no reasoning.

---

**Related:** [architecture.md](architecture.md) · [project_types.md](project_types.md) · `../Database/` · `../Deploy/` · `../CyberSecurity/`
