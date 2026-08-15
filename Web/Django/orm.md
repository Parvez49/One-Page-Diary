# Django ORM — Models, Relations, Expressions

> Query performance & N+1: **[queries.md](queries.md)** · Schema changes: **[migrations.md](migrations.md)**

---

## 1. Models & fields

```python
from django.db import models

class Product(models.Model):
    name        = models.CharField(max_length=100, db_index=True)
    slug        = models.SlugField(unique=True)
    description = models.TextField(blank=True)                  # ⭐ blank ≠ null
    price       = models.DecimalField(max_digits=10, decimal_places=2)   # ⭐ never FloatField
    stock       = models.PositiveIntegerField(default=0)
    category    = models.ForeignKey("Category", on_delete=models.PROTECT, related_name="products")
    created_at  = models.DateTimeField(auto_now_add=True)       # set once, on INSERT
    updated_at  = models.DateTimeField(auto_now=True)           # ⚠️ set on every .save()

    class Meta:
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["category", "-created_at"])]   # ⭐ composite
        constraints = [
            models.CheckConstraint(check=models.Q(price__gte=0), name="price_non_negative"),
            models.UniqueConstraint(fields=["name", "category"], name="uniq_name_per_cat"),
        ]

    def __str__(self):
        return self.name
```

⚠️⚠️ **`null` vs `blank`** — the most-asked Django field question.
`null=True` is a **database** constraint (column may be `NULL`); `blank=True` is a
**validation** rule (forms/DRF may leave it empty). ⭐ **Never use `null=True` on a
`CharField`/`TextField`** — you get two representations of "empty" (`""` and `NULL`) and every
query needs to handle both. Use `blank=True` alone.

⚠️ **`auto_now` doesn't fire on `.update()` or `bulk_update()`** — those bypass `save()`, so
`updated_at` silently goes stale. Set it explicitly in bulk operations.

⚠️ **Never use `FloatField` for money** — binary floats can't represent `0.10`. `DecimalField`
or integer minor units.

**`on_delete` — a real design decision, not boilerplate:**

| Value | Effect |
|---|---|
| `CASCADE` | delete the children too ⚠️ silent mass-deletion if misapplied |
| **`PROTECT`** | ⭐ raise `ProtectedError` — safest default for reference data |
| `RESTRICT` | like PROTECT but allows deletion if another cascade path covers it |
| `SET_NULL` | needs `null=True` — keeps orphan rows |
| `SET_DEFAULT` / `SET(...)` | replace with a fallback |
| `DO_NOTHING` | ⚠️ leaves the DB to enforce it — usually a bug |

⭐ **`CASCADE` is Django's default but rarely the safe one.** Deleting a `Category` with
`CASCADE` silently removes every product. Default to `PROTECT` and opt into cascade
deliberately.

---

## 2. Relationships

```python
class Order(models.Model):
    product  = models.ForeignKey(Product, on_delete=models.PROTECT, related_name="orders")
    customer = models.ForeignKey(User, on_delete=models.CASCADE, related_name="orders")
    quantity = models.PositiveIntegerField()

class Profile(models.Model):                 # one-to-one
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profile")

class Incident(models.Model):                # many-to-many
    media = models.ManyToManyField("Media", related_name="incidents")
```

⭐ **Always set `related_name`.** Without it you're stuck with `product.order_set`, which is
unreadable and breaks the moment you have two FKs to the same model (Django then *requires*
`related_name` anyway). Use `related_name="+"` to disable the reverse accessor entirely.

**Traversal & querying across relations:**

```python
order.product.name                        # forward — ⚠️ triggers a query if not selected
product.orders.all()                      # reverse, via related_name
Order.objects.filter(product__category__name="Books")     # ⭐ __ spans joins, any depth
Media.objects.filter(incidents__date__year=2024)
Incident.objects.filter(media__phash__isnull=False)
```

### M2M: `through` model vs plain `ManyToManyField` ⭐

```python
class OrderItem(models.Model):                    # ⭐ explicit through model
    order    = models.ForeignKey(Order, on_delete=models.CASCADE)
    product  = models.ForeignKey(Product, on_delete=models.PROTECT)
    quantity = models.PositiveIntegerField()      # ← extra data on the RELATIONSHIP
    price_at_purchase = models.DecimalField(max_digits=10, decimal_places=2)

class Order(models.Model):
    products = models.ManyToManyField(Product, through="OrderItem")
```

| Use plain `ManyToManyField` when | Use a `through` model when |
|---|---|
| the link carries **no data** | ⭐ you need extra fields (quantity, status, timestamp) |
| tags, permissions, categories | you must filter/order/aggregate on the join |
| no need to query the join itself | you want constraints/indexes on the join table |

⭐ **The senior point:** a plain M2M still creates a hidden join table — you just can't put
anything on it. Adding a field later means writing the `through` model *and* a data migration,
so if the relationship is likely to acquire attributes (nearly always true for
orders/memberships/enrolments), define it explicitly from day one. `price_at_purchase` above
is the classic example: the product's price changes, but the order must remember what was paid.

```python
Order.products.through.objects.filter(quantity__gt=5)     # ⭐ query the join directly
order.products.add(p) / .remove(p) / .set([...]) / .clear()   # ⚠️ unavailable with `through`
```

---

## 3. QuerySets are lazy ⭐⭐

```python
qs = Product.objects.filter(price__gt=50)     # ⭐ NO query yet
qs = qs.exclude(stock=0)                       # still no query — chaining builds SQL
qs = qs.order_by("name")[:10]                  # slicing adds LIMIT, still no query
for p in qs: ...                               # ⭐ NOW it executes
```

**Evaluation triggers:** iteration, `list()`, `len()`, `bool()`, slicing with a step,
`repr()`, pickling, `.exists()`, `.count()`, `.first()`.

```python
if qs.exists():        # ⭐ SELECT 1 ... LIMIT 1
if qs.count() > 0:     # ⚠️ COUNT(*) over the whole table
if qs:                 # ⚠️ fetches and caches ALL rows
```

⭐ **Result caching:** once evaluated, a QuerySet caches its rows — re-iterating the *same*
object is free, but `Product.objects.filter(...)` written twice is **two queries**. Assign to
a variable and reuse it.

```python
qs.count()             # ⚠️ if qs is already evaluated, use len(qs) — no extra query
```

**Common lookups:**

```python
__exact __iexact __contains __icontains __startswith __endswith
__gt __gte __lt __lte __in __range __isnull
__date __year __month __week_day __hour
__regex __iregex
```

⚠️ **`get()` raises**: `DoesNotExist` if absent, `MultipleObjectsReturned` if >1. Use
`.filter().first()` when absence is expected, or `get_object_or_404()` in a view.

```python
obj, created = Product.objects.get_or_create(slug="x", defaults={"name": "X", "price": 1})
obj, created = Product.objects.update_or_create(slug="x", defaults={"price": 9})
```

⚠️ **`get_or_create` is not atomic without a unique constraint** — two concurrent requests
both miss, both insert. The DB-level `UniqueConstraint` is what actually prevents duplicates;
Django then converts the race into an `IntegrityError` it handles.

---

## 4. CRUD

```python
# CREATE
Product.objects.create(name="Shirt", price=19.99)
Product.objects.bulk_create(objs, batch_size=1000, ignore_conflicts=True)   # ⭐ one query

# UPDATE
p.price = 29.99; p.save(update_fields=["price"])      # ⭐ writes ONE column
Product.objects.filter(price__lt=30).update(price=30) # ⭐ one query, no Python loop
Product.objects.bulk_update(objs, ["price"], batch_size=1000)

# DELETE
Product.objects.filter(stock=0).delete()
```

⚠️⚠️ **`.update()` and `bulk_create/update` bypass `save()`, `signals`, and `auto_now`.**
No `pre_save`/`post_save` fires, no custom `save()` logic runs, `updated_at` doesn't change.
That's exactly why they're fast — but if your model relies on `save()` side effects (search
indexing, cache invalidation, audit logs), those silently don't happen.

⭐ `save(update_fields=[...])` is the cheap win in hot paths: it writes only the named columns
and avoids clobbering concurrent writes to other fields.

---

## 5. Q, F, and expressions ⭐

**`Q` — complex boolean logic:**

```python
from django.db.models import Q

Product.objects.filter(Q(price__gt=50) | Q(name__icontains="shirt"))
Product.objects.filter(~Q(stock=0))
Product.objects.filter(Q(price__gt=50) & (Q(a=1) | Q(b=2)))

filters = Q()                                  # ⭐ build dynamically
if request.GET.get("min"): filters &= Q(price__gte=min_price)
if request.GET.get("cat"): filters &= Q(category__slug=cat)
Product.objects.filter(filters)
```

⚠️ `Q` objects must come **before** keyword arguments: `filter(Q(...), name="x")`.

**`F` — reference a column, in the database:**

```python
from django.db.models import F

Product.objects.filter(price__gt=F("discount"))              # column vs column
Product.objects.update(price=F("price") - F("discount"))     # arithmetic in SQL
Product.objects.filter(id=1).update(stock=F("stock") + 5)    # ⭐⭐ ATOMIC increment
```

⭐⭐ **`F()` prevents lost updates — a genuine concurrency answer.**

```python
p = Product.objects.get(id=1)      # ⚠️ read-modify-write RACE
p.stock += 1                       # two concurrent requests both read 10,
p.save()                           # both write 11 — one increment LOST

Product.objects.filter(id=1).update(stock=F("stock") + 1)    # ⭐ UPDATE ... SET stock = stock + 1
```

The `F()` version happens entirely in the database as a single atomic statement, so
concurrent increments compose correctly. It also skips loading the row into Python.

⚠️ After an `F()` update the in-memory instance holds a `CombinedExpression`, not a number —
call `refresh_from_db()` before reading it.

**Aggregation vs annotation:**

```python
from django.db.models import Sum, Count, Avg, Min, Max, Value
from django.db.models.functions import Coalesce

Product.objects.aggregate(Sum("price"))            # ⭐ ONE dict for the whole queryset
# {"price__sum": Decimal("1234.56")}  — ⚠️ None (not 0) when empty
Product.objects.aggregate(total=Coalesce(Sum("price"), Value(0)))   # ⭐ the fix

Product.objects.annotate(order_count=Count("orders"))   # ⭐ adds a column PER ROW
Product.objects.annotate(
    completed=Count("orders", filter=Q(orders__status="completed"))    # ⭐ conditional agg
).filter(completed__gt=5)

Blog.objects.alias(n=Count("entry")).filter(n__gt=5)    # ⭐ compute without selecting it
```

⚠️⚠️ **Multiple `annotate(Count(...))` across different relations multiplies rows** — the
joins fan out and every count is inflated. Use `distinct=True`, separate queries, or
`Subquery`.

**Subqueries:**

```python
from django.db.models import OuterRef, Subquery, Exists

latest = Order.objects.filter(product=OuterRef("pk")).order_by("-created_at")
Product.objects.annotate(last_order=Subquery(latest.values("created_at")[:1]))

Product.objects.annotate(has_orders=Exists(Order.objects.filter(product=OuterRef("pk"))))
Product.objects.filter(Exists(Order.objects.filter(product=OuterRef("pk"))))   # ⭐ fast
```

⭐ **`Exists()` beats `Count() > 0`** — the database can stop at the first matching row.

**Conditional expressions:**

```python
from django.db.models import Case, When, Value, CharField

Product.objects.annotate(
    tier=Case(
        When(price__gte=100, then=Value("premium")),
        When(price__gte=50,  then=Value("standard")),
        default=Value("budget"),
        output_field=CharField(),
    )
)
```

---

## 6. Transactions ⭐

```python
from django.db import transaction

with transaction.atomic():
    order = Order.objects.create(...)
    Product.objects.filter(id=pid).update(stock=F("stock") - qty)
    # any exception here → EVERYTHING rolls back
```

```python
@transaction.atomic
def checkout(request): ...

with transaction.atomic():                     # nested = SAVEPOINT
    with transaction.atomic():
        ...
```

⚠️⚠️ **Catching an exception *inside* `atomic()` doesn't undo the rollback intent** — once a
database error occurs the transaction is marked broken and every later query raises
`TransactionManagementError`. Catch **outside** the block, or wrap the risky part in its own
inner `atomic()`.

⭐ **`transaction.on_commit()` — the Celery race everyone hits:**

```python
with transaction.atomic():
    order = Order.objects.create(...)
    send_email.delay(order.id)        # ⚠️ worker may run BEFORE the commit → DoesNotExist

with transaction.atomic():
    order = Order.objects.create(...)
    transaction.on_commit(lambda: send_email.delay(order.id))    # ⭐ fires after COMMIT
```

**Locking:**

```python
with transaction.atomic():
    p = Product.objects.select_for_update().get(id=1)     # ⭐ row lock until commit
    p.stock -= 1
    p.save()

.select_for_update(nowait=True)         # raise instead of waiting
.select_for_update(skip_locked=True)    # ⭐ queue-worker pattern: skip locked rows
```

⚠️ `select_for_update()` requires being inside `atomic()`, and holding locks across slow
work (HTTP calls, emails) is how you deadlock a production database. Keep the block tiny.

`ATOMIC_REQUESTS = True` wraps every request in a transaction — safe but holds a connection
and locks for the whole request; prefer explicit `atomic()` blocks around the parts that need it.

---

## 7. Custom managers & querysets

```python
class ProductQuerySet(models.QuerySet):
    def active(self):     return self.filter(is_active=True)
    def in_stock(self):   return self.filter(stock__gt=0)
    def with_orders(self): return self.annotate(n=Count("orders"))

class Product(models.Model):
    objects = ProductQuerySet.as_manager()      # ⭐ chainable, reusable

Product.objects.active().in_stock().with_orders()
```

⭐ **Define query logic once, on the QuerySet** — `as_manager()` makes every method chainable
and keeps business rules out of views. A manager method (`Manager.get_queryset`) is not
chainable; a QuerySet method is.

⚠️ Overriding the **default** manager to filter (e.g. soft-delete) also hides rows from
`related_name` traversal, admin, and dumpdata. Keep the default unfiltered and add a second
manager.

---

## 8. Interview points

- **`null=True` vs `blank=True`?** Database `NULL` vs form/serializer validation. Don't use
  `null=True` on text fields.
- **When would you use a `through` model instead of a plain M2M?** When the relationship
  itself carries data (quantity, price-at-purchase, joined-at) or needs its own constraints.
- **What does `on_delete=CASCADE` risk?** Silent mass deletion. `PROTECT` is the safer default
  for reference data.
- **Are QuerySets lazy?** Yes — SQL is built by chaining and executed only on evaluation, and
  the result is then cached on that object.
- **`exists()` vs `count()` vs truthiness?** `SELECT 1 LIMIT 1` vs `COUNT(*)` vs fetching all
  rows.
- **What does `F()` solve? ⭐** Read-modify-write races — the arithmetic happens atomically in
  SQL instead of in Python.
- **`aggregate()` vs `annotate()`?** One summary value for the whole queryset vs a computed
  column added to each row.
- **Why did my two `annotate(Count(...))` return wrong numbers?** Join fan-out multiplies rows
  — use `distinct=True` or subqueries.
- **What do `.update()`/`bulk_create` skip?** `save()`, signals, and `auto_now` — that's the
  trade for speed.
- **Why `transaction.on_commit` for Celery tasks?** The worker can pick up the task before the
  transaction commits and not find the row.
- **How do you prevent two users buying the last item?** `select_for_update()` inside
  `atomic()`, or an atomic `F()` update plus a `CheckConstraint`.
