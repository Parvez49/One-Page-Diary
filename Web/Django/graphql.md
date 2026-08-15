# GraphQL with Django

> REST comparison: **[drf.md](drf.md)** · Query performance: **[queries.md](queries.md)**

---

## 1. What GraphQL is, and what it fixes ⭐

**A query language for APIs plus a runtime** — the client specifies exactly what it wants;
the server returns exactly that shape, from a **single endpoint**.

**The two REST problems it targets:**

```
Over-fetching   GET /users/1  → 40 fields; the screen needs 3.
                A REST serializer's shape is fixed by the server.

Under-fetching  GET /users/1            ⚠️ 3 round trips to render one screen
                GET /users/1/orders        — brutal on mobile networks
                GET /orders/5/items
```

```graphql
query {                                   # ⭐ one request, exactly the needed fields
  user(id: 1) {
    name
    orders(last: 5) { total items { product { name } } }
  }
}
```

**Other consequences:** one endpoint (simpler auth/gateway/routing), a **typed schema** that
generates client code and docs, and evolution by **deprecation instead of versioning** —
adding a field breaks nobody, so `/v2/` is rarely needed.

⭐ **The design split worth noting:** GraphQL separates **queries** (read) from **mutations**
(write) at the schema level, whereas a DRF serializer usually does both — which is why DRF
needs the read-only-nested / write-only-id dance ([drf.md §4](drf.md)).

---

## 2. Schema — types, queries, mutations

```python
# strawberry-django
import strawberry, strawberry_django
from strawberry import auto

@strawberry_django.type(Product)
class ProductType:
    id: auto
    name: auto
    price: auto
    category: "CategoryType"          # ⭐ resolvers for relations are generated
    orders: list["OrderType"]

@strawberry.type
class Query:
    products: list[ProductType] = strawberry_django.field()

    @strawberry.field
    def product(self, id: int) -> ProductType | None:
        return Product.objects.filter(id=id).first()

@strawberry.input
class ProductInput:
    name: str
    price: float

@strawberry.type
class Mutation:
    @strawberry.mutation
    def create_product(self, info, data: ProductInput) -> ProductType:
        user = info.context.request.user                    # ⭐ auth context
        if not user.is_authenticated:
            raise PermissionError("Login required")
        return Product.objects.create(**vars(data), owner=user)

schema = strawberry.Schema(query=Query, mutation=Mutation)
```

**Libraries:** **strawberry-django** (⭐ modern, type-hint native, async) ·
**graphene-django** (older, larger ecosystem, more boilerplate) · **Ariadne** (schema-first).

**Vocabulary:** `type` (output) · `input` (mutation arguments) · **resolver** (function
producing a field's value) · `Query` / `Mutation` / `Subscription` (the three roots) ·
`!` non-null · `[T]` list.

---

## 3. The N+1 problem is worse here ⭐⭐

REST has a fixed query shape you can optimise once. **GraphQL lets the client choose the
shape at runtime**, so you cannot pre-plan `select_related` — a nested query fires a resolver
per parent, per level.

```graphql
{ products { category { name } } }     # ⚠️ 1 + N queries — one per product
```

⭐ **DataLoader is the standard fix**: batch all keys requested in one tick into a single
`WHERE id IN (...)`, and cache per request.

```python
from strawberry.dataloader import DataLoader

async def load_categories(keys: list[int]) -> list[Category]:
    qs = {c.id: c for c in Category.objects.filter(id__in=keys)}   # ⭐ ONE query
    return [qs.get(k) for k in keys]                                # ⚠️ MUST match key order

# per-request instance — ⚠️ a global loader leaks data between users
loader = DataLoader(load_fn=load_categories)
```

⭐ `strawberry_django` can also apply `select_related`/`prefetch_related` by inspecting the
requested field set (`optimizer`) — enable it; it removes most hand-written loaders.

⚠️ **DataLoader must return results in the same order as the input keys**, with `None` for
misses — a subtle bug source.

---

## 4. The hard parts ⭐

| Problem | Why | Mitigation |
|---|---|---|
| **N+1** | client-chosen nesting | ⭐ DataLoader + query optimiser |
| **Query complexity/DoS** | ⚠️ deeply nested query can be exponential | ⭐ **depth limit + cost analysis + timeout** |
| **HTTP caching** | ⚠️ everything is `POST /graphql` — CDNs can't cache by URL | persisted queries, response caching by hash |
| **Authorisation** | must be enforced **per field**, not per endpoint | field-level permission checks / a policy layer |
| **File uploads** | not in the spec | multipart spec extension, or a REST endpoint |
| **Error handling** | ⚠️ always `200 OK` with an `errors` array | client must inspect the body |
| **Rate limiting** | one endpoint, wildly varying cost | ⭐ limit by **query cost**, not request count |

⚠️⚠️ **Query-depth attacks are the security issue to name.** With cyclic relations
(`user → orders → user → orders …`) a small query can request millions of rows. Always deploy
with a depth limit, a complexity budget, and a statement timeout — and ⚠️ **disable
introspection in production** so the schema isn't a free map for attackers.

⭐ **Losing CDN caching is the most underrated cost.** REST `GET /products/1` caches at the
edge for free; GraphQL POSTs don't. Persisted queries (client sends a hash, server holds the
text) restore some of it and also act as an allow-list against arbitrary queries.

---

## 5. REST or GraphQL? ⭐

| Choose **REST** when | Choose **GraphQL** when |
|---|---|
| CRUD over well-defined resources | ⭐ clients need **varied shapes** of the same data |
| ⭐ HTTP caching / CDN matters | mobile clients on slow networks (round trips hurt) |
| Simple auth per endpoint | ⭐ many consumers, one backend team |
| File uploads, webhooks, streaming | rapidly evolving frontends |
| Small team, small surface | aggregating several backends (BFF/gateway) |

⭐ **The balanced answer:** GraphQL moves complexity from the client to the server. You trade
over/under-fetching for N+1 management, query-cost policing, and lost HTTP caching. For a
single first-party frontend with predictable screens, **DRF is usually less total work**. For
several clients with different data needs — web, iOS, Android, partners — GraphQL earns its
cost.

⭐ **They coexist.** Plenty of teams keep REST for uploads, webhooks, and public integrations
while serving the app's own screens over GraphQL.

---

## 6. Interview points

- **What problems does GraphQL solve? ⭐** Over-fetching (fixed server-defined shapes) and
  under-fetching (multiple round trips per screen).
- **Why is versioning less necessary?** Clients request specific fields, so additive changes
  are invisible; removals use `@deprecated`.
- **Why is N+1 worse in GraphQL? ⭐⭐** The query shape is decided by the client at runtime,
  so you can't pre-optimise; fix with DataLoader batching plus a query optimiser.
- **What does DataLoader do?** Batches the keys collected in one execution tick into a single
  query and caches per request.
- **What's the DoS risk?** Deeply nested/cyclic queries — mitigate with depth limits,
  complexity scoring, timeouts, and persisted queries.
- **Why is caching harder?** One POST endpoint means no URL-based CDN caching; use persisted
  queries or application-level caching.
- **How do errors work?** Usually HTTP 200 with an `errors` array — clients must check the
  body, and monitoring on status codes alone will miss failures.
- **Where does authorisation live?** Per field/resolver, not per endpoint — a single missed
  check exposes data through any query path that reaches it.
- **When would you *not* use GraphQL?** A single frontend with predictable screens, heavy
  reliance on CDN caching, or a small team — REST is less total complexity.
