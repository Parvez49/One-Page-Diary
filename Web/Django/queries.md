# Query Performance — N+1, Joins, Indexes

> ORM basics: **[orm.md](orm.md)** · Caching layer: **[caching.md](caching.md)** ·
> Python profiling: **[../../Language/Python/performance.md](../../Language/Python/performance.md)**

---

## 1. The N+1 problem ⭐⭐⭐

**The most common performance bug in any Django codebase, and the most likely thing you'll be
asked to spot in an interview.**

```python
orders = Order.objects.all()            # 1 query
for order in orders:
    print(order.customer.name)          # ⚠️ +1 query PER ORDER → 1001 queries for 1000 rows
```

Django relations are **lazy**: `order.customer` isn't loaded until you touch it, and then it
fires a fresh `SELECT`. It looks fine on 10 rows in dev and melts the database at 10,000.

```python
orders = Order.objects.select_related("customer")     # ⭐ 1 query, SQL JOIN
```

⚠️ **Serializers hide it.** A DRF `ModelSerializer` with a nested field walks the relation for
every row — the N+1 lives in the serializer, not in code you can see in the view. Always set
the queryset up in `get_queryset()`.

---

## 2. `select_related` vs `prefetch_related` ⭐⭐

| | **`select_related`** | **`prefetch_related`** |
|---|---|---|
| Relation types | **FK, OneToOne** (single object forward) | ⭐ **M2M, reverse FK** (many objects) |
| SQL | **one query, `JOIN`** | **separate query per relation**, joined in Python |
| Strategy | *join then query* | *query then join* |
| Cost | wide rows, duplicated parent data | extra round trip, but no row multiplication |

```python
Order.objects.select_related("customer", "product__category")     # ⭐ __ follows the chain

Book.objects.prefetch_related("authors", "reviews")               # M2M + reverse FK

Order.objects.select_related("customer").prefetch_related("items__product")   # ⭐ combine
```

⭐ **Why not always `select_related`?** On a to-many relation a JOIN multiplies rows — 100
books × 10 authors = 1000 rows, with every book's columns repeated 10 times. `prefetch_related`
issues a second `SELECT ... WHERE id IN (...)` and stitches the results in Python, which is
usually far cheaper on the wire.

**`Prefetch()` — filter and shape the inner query:**

```python
from django.db.models import Prefetch

Book.objects.prefetch_related(
    Prefetch("reviews",
             queryset=Review.objects.filter(rating__gte=4).select_related("author"),
             to_attr="top_reviews"),           # ⭐ lands in book.top_reviews (a list)
)
```

⚠️⚠️ **Filtering a prefetched relation in the loop destroys the prefetch:**

```python
for book in books.prefetch_related("reviews"):
    good = book.reviews.filter(rating__gte=4)     # ⚠️ NEW query per book — prefetch wasted
    good = [r for r in book.reviews.all() if r.rating >= 4]   # ⭐ uses the cache
```

Any queryset method on the related manager (`.filter()`, `.exclude()`, `.count()`,
`.order_by()`) re-queries. Only `.all()` hits the prefetch cache — filter in Python, or use
`Prefetch(queryset=...)`.

⭐ **`.count()` on a prefetched relation is a query; `len(obj.rel.all())` is not.**

---

## 3. Fetching less data

```python
Product.objects.only("id", "name")          # ⭐ SELECT id, name — others load LAZILY
Product.objects.defer("description")        # everything EXCEPT description
Product.objects.values("id", "name")        # ⭐ dicts — no model instances
Product.objects.values_list("id", flat=True)   # ⭐ [1, 2, 3] — perfect for `__in`
```

⚠️⚠️ **`only()`/`defer()` are footguns**: touching a deferred field triggers **one query per
instance** — you've rebuilt N+1 while trying to optimise. They only pay off for genuinely
large columns (TextField, JSON blobs) you're certain you won't read.

⭐ **`values()`/`values_list()` are the real win for read-only work** — no model instantiation,
no `__init__`, no signals. Building 50,000 model objects to compute a sum is pure waste:

```python
ids = Product.objects.filter(...).values_list("id", flat=True)    # ⭐ then use ids__in
Order.objects.aggregate(total=Sum("amount"))                       # ⭐ let the DB sum it
```

**Iterating huge result sets:**

```python
for p in Product.objects.iterator(chunk_size=2000):    # ⭐ server-side cursor, no result cache
    ...
```

⚠️ `.iterator()` disables the result cache (so no re-iteration) and **cannot be combined with
`prefetch_related`** on older Django versions — it's for one-pass streaming over millions of rows.

---

## 4. Counting queries — measure, don't guess ⭐

```python
from django.db import connection, reset_queries

reset_queries()
list(MyView().get_queryset())
print(len(connection.queries))
for q in connection.queries: print(q["time"], q["sql"][:120])
```

⚠️ Requires `DEBUG=True`, and `connection.queries` grows unbounded — never leave it on in
production.

**Better tools:**

```python
# tests — ⭐ lock in the query count so a regression fails CI
def test_list_is_efficient(client):
    with django_assert_num_queries(3):
        client.get("/api/orders/")
```

- **django-debug-toolbar** — per-request query list with duplicate detection (dev)
- **nplusone** / **django-zen-queries** — raise on lazy loads
- **django-silk** — profiling with request history
- **APM** (Sentry/Datadog/New Relic) — production traces

⭐ **`assertNumQueries` in tests is the durable fix.** An optimisation without a test guarding
it gets reverted by the next serializer change.

---

## 5. Reading the SQL

```python
print(qs.query)                   # ⭐ the generated SQL
print(qs.explain(analyze=True))   # ⭐ the real execution plan + timings
```

**In the plan, look for:**

| Sign | Meaning |
|---|---|
| **`Seq Scan`** on a big table | ⚠️ **missing index** |
| `Index Scan` / `Index Only Scan` | ⭐ good |
| **Rows removed by Filter** (large) | the index isn't selective enough |
| `Nested Loop` over many rows | often a bad join order |
| estimated ≫ actual rows | stale statistics → `ANALYZE` |

⭐ **`EXPLAIN ANALYZE` before adding an index.** Guessing produces unused indexes that slow
every write.

---

## 6. Indexes

```python
class Order(models.Model):
    customer = models.ForeignKey(User, on_delete=models.PROTECT)   # ⭐ FKs are indexed already
    status   = models.CharField(max_length=20, db_index=True)
    created  = models.DateTimeField()

    class Meta:
        indexes = [
            models.Index(fields=["status", "-created"]),           # ⭐ composite, ordered
            models.Index(fields=["customer"], condition=Q(status="pending"),
                         name="idx_pending_by_customer"),          # ⭐ partial index
        ]
```

**Rules that matter:**

- ⭐ **Index what you filter, join, and order by** — not everything. Every index slows
  `INSERT`/`UPDATE` and consumes disk.
- ⭐ **Composite index order matters**: `(status, created)` serves `WHERE status=? ORDER BY
  created` and `WHERE status=?`, but **not** `WHERE created=?` alone. Leftmost-prefix rule.
- **Partial indexes** (`condition=`) are ideal for status flags where you only ever query one
  value.
- ⚠️ **A function on the column defeats the index**: `WHERE UPPER(name) = 'X'` won't use an
  index on `name`. Use `__iexact` with a functional index, or store a normalised column.
- ⚠️ `__icontains="%term%"` can't use a B-tree index at all — that's a full-text search or
  trigram (`pg_trgm`) problem.

Full-text on Postgres: `SearchVector`/`SearchQuery` + a `GinIndex`.

---

## 7. Pagination

```python
Product.objects.all()[100000:100020]      # ⚠️ OFFSET 100000 — the DB still scans 100k rows
```

⭐ **Offset pagination degrades linearly with depth.** For large or infinite-scroll datasets
use **keyset (cursor) pagination**:

```python
Product.objects.filter(created__lt=last_seen_created).order_by("-created")[:20]
```

DRF's `CursorPagination` implements this — see [drf.md](drf.md). It's O(1) per page and
immune to rows shifting between requests.

⚠️ `COUNT(*)` for the total is often the slowest part of a paginated endpoint. Drop the count,
cache it, or use an estimate.

---

## 8. Bulk operations

```python
Product.objects.bulk_create(objs, batch_size=1000)              # ⭐ 1 query, not N
Product.objects.bulk_update(objs, ["price"], batch_size=1000)
Product.objects.filter(...).update(price=F("price") * 1.1)      # ⭐ pure SQL
Product.objects.filter(...).delete()
```

⚠️ These skip `save()`, **signals**, and `auto_now` ([orm.md §4](orm.md)). If a `post_save`
signal maintains a search index or cache, bulk operations silently bypass it — handle it
explicitly.

⚠️ `.delete()` on a queryset still **loads objects** to cascade and send signals. For a mass
purge with no cascade needs, raw SQL or `_raw_delete()` is orders of magnitude faster.

---

## 9. Raw SQL — when the ORM isn't enough

```python
Product.objects.raw("SELECT * FROM shop_product WHERE price > %s", [50])   # ⭐ params, not f-string

with connection.cursor() as cur:
    cur.execute("SELECT category_id, COUNT(*) FROM shop_product GROUP BY 1")
    rows = cur.fetchall()
```

⚠️⚠️ **Never interpolate user input into SQL** — `f"WHERE name = '{name}'"` is SQL injection.
Always use `%s` placeholders; the driver escapes them. See [security.md](security.md).

⭐ Legitimate reasons to drop to SQL: window functions on older Django, recursive CTEs,
database-specific features, and bulk `UPSERT`. Otherwise the ORM's expression API
(`Window`, `Subquery`, `Case`) usually covers it.

---

## 10. The optimisation checklist ⭐

Run in this order — the first two find ~90% of problems:

1. **Count the queries.** debug-toolbar or `assertNumQueries`. Is it O(1) or O(n)?
2. **Fix N+1** — `select_related` (FK/O2O), `prefetch_related` (M2M/reverse).
3. **Fetch fewer rows/columns** — `values()`, `only()` (carefully), pagination.
4. **`EXPLAIN ANALYZE` the slow query** — look for `Seq Scan`.
5. **Add the index** the plan asks for; re-measure.
6. **Move work into SQL** — `aggregate`, `annotate`, `F()`, `Subquery` instead of Python loops.
7. **Bulk-ify writes** — `bulk_create`/`update` instead of per-row `save()`.
8. **Cache** what's still expensive ([caching.md](caching.md)) — last, not first.

⭐ **Caching is not the fix for an N+1.** It hides it until the cache is cold, then the
stampede takes the database down.

---

## 11. Interview points

- **What is the N+1 problem? ⭐** One query for the list plus one per row for a lazy relation.
  Fix with `select_related`/`prefetch_related`.
- **`select_related` vs `prefetch_related`?** SQL JOIN for FK/O2O vs a second query joined in
  Python for M2M/reverse FK — because joining a to-many relation multiplies rows.
- **Why did my `prefetch_related` not help?** You called `.filter()`/`.count()` on the related
  manager, which re-queries. Filter in Python or use `Prefetch(queryset=...)`.
- **`only()`/`defer()` risks?** Touching a deferred field triggers a query per instance.
- **`values()` vs model instances?** Dicts, no model construction — much cheaper for
  read-only aggregation and `__in` lists.
- **How do you find slow queries?** debug-toolbar/silk in dev, APM in production, then
  `EXPLAIN ANALYZE` on the offender.
- **What does a `Seq Scan` tell you?** No usable index for that predicate on a table large
  enough to matter.
- **Does composite index order matter?** Yes — leftmost prefix; `(a, b)` doesn't serve a query
  filtering only on `b`.
- **Why is deep offset pagination slow, and what's the alternative?** The DB scans and
  discards every skipped row; use keyset/cursor pagination.
- **What do bulk operations skip?** `save()`, signals, `auto_now`.
- **How do you keep a fix from regressing?** `assertNumQueries` in the test suite.
