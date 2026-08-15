# Filtering, Search & Ordering

> Views & serializers: **[drf.md](drf.md)** · Permissions: **[auth.md](auth.md)** ·
> Index implications: **[queries.md](queries.md)**

---

## 1. Setup

```python
# settings.py — applies to every generic view
REST_FRAMEWORK = {
    "DEFAULT_FILTER_BACKENDS": [
        "django_filters.rest_framework.DjangoFilterBackend",   # field filtering
        "rest_framework.filters.SearchFilter",                 # ?search=
        "rest_framework.filters.OrderingFilter",               # ?ordering=
    ],
}
```

```python
class ProductViewSet(ModelViewSet):
    queryset = Product.objects.select_related("category")
    serializer_class = ProductSerializer

    filterset_fields = ["category", "status"]        # ⭐ exact matches, cheap
    search_fields    = ["name", "description", "category__name"]   # ⭐ __ spans relations
    ordering_fields  = ["name", "price", "created_at"]             # ⭐ ALLOW-LIST
    ordering         = ["-created_at"]                             # default
```

⭐ Declaring the backends in `settings.py` makes `filter_backends` on the view redundant — set
it per-view only to *deviate* from the default.

⚠️⚠️ **`ordering_fields = "__all__"` lets a client sort by any column**, including unindexed
ones — a trivial way to trigger full table sorts and take the database down. Always
allow-list, and make sure each listed field is indexed.

⚠️ `SearchFilter` uses `icontains` by default → `LIKE '%term%'`, which **cannot use a B-tree
index**. Fine for small tables; for anything large use Postgres full-text
(`SearchVector` + `GinIndex`) or a search engine. Prefix `^` (startswith), `=` (exact),
`@` (full-text), `$` (regex) in `search_fields` to change the behaviour.

---

## 2. FilterSets — the real tool

```python
from django_filters import rest_framework as filters

class NumberInFilter(filters.BaseInFilter, filters.NumberFilter):
    pass

class ProductFilter(filters.FilterSet):
    min_price   = filters.NumberFilter(field_name="price", lookup_expr="gte")
    max_price   = filters.NumberFilter(field_name="price", lookup_expr="lte")
    created_after = filters.DateFilter(field_name="created_at", lookup_expr="gte")
    category    = filters.ModelMultipleChoiceFilter(queryset=Category.objects.all())
    exclude_ids = NumberInFilter(field_name="id", exclude=True)     # ⭐ ?exclude_ids=1,2,3
    tag         = filters.CharFilter(method="filter_tag")           # ⭐ custom logic
    mine        = filters.BooleanFilter(method="filter_mine")
    in_stock    = filters.BooleanFilter(field_name="stock", lookup_expr="gt", exclude=False)

    class Meta:
        model  = Product
        fields = ["category", "status", "min_price", "max_price", "mine"]

    def filter_tag(self, queryset, name, value):
        if value.lower() == "null":
            return queryset.filter(tags__isnull=True)
        return queryset.filter(tags__slug=value).distinct()   # ⭐ distinct after M2M join

    def filter_mine(self, queryset, name, value):
        user = self.request.user
        if value and user.is_authenticated:
            return queryset.filter(created_by=user)
        return queryset


class ProductViewSet(ModelViewSet):
    filterset_class = ProductFilter        # ⭐ replaces filterset_fields
```

⚠️ **Filtering across a to-many relation duplicates rows** — `filter(tags__slug=x)` returns a
row per matching tag. Add `.distinct()`, and remember it forces a `SELECT DISTINCT` (a sort)
in the database.

⚠️ **A `method=` filter runs Python per request but must still return a QuerySet** — never
return a list, or every later filter/pagination call breaks.

**Reusable mixin** (your original pattern, tidied):

```python
class OwnedFilterMixin:
    """Adds ?mine=true to any FilterSet."""
    mine = filters.BooleanFilter(method="filter_mine")

    def filter_mine(self, queryset, name, value):
        user = self.request.user
        return queryset.filter(created_by=user) if value and user.is_authenticated else queryset

class ProductFilter(OwnedFilterMixin, filters.FilterSet): ...
```

⭐ **Typing note:** the `Protocol` from your original notes is the right instinct — a mixin
depends on attributes (`request`, `form`) it doesn't define. Declaring that contract makes
mypy able to check it. See
[../../Language/Python/typing.md](../../Language/Python/typing.md).

---

## 3. Filtering in `get_queryset` — when to skip the library

```python
def get_queryset(self):
    qs = Product.objects.select_related("category")

    if not self.request.user.is_staff:          # ⭐ SECURITY scoping — never a query param
        qs = qs.filter(owner=self.request.user)

    return qs
```

⭐⭐ **Authorisation scoping belongs in `get_queryset()`, not in a filter.** A filter is
*optional* — the client controls it. If `?mine=true` is what keeps user A from reading user
B's data, omitting the parameter exposes everything. Filters shape a result set the user is
**already allowed to see**.

Use raw `get_queryset` logic for: security scoping, always-on constraints, and anything
depending on request state. Use `FilterSet` for user-facing, optional query parameters —
you get validation, coercion, and browsable-API forms for free.

---

## 4. Dynamic filters with `Q`

```python
from django.db.models import Q

def get_queryset(self):
    qs = Product.objects.all()
    q = self.request.query_params.get("q")
    if q:
        qs = qs.filter(Q(name__icontains=q) | Q(description__icontains=q))
    return qs
```

⚠️⚠️ **Never build filters from raw client keys:**

```python
Product.objects.filter(**request.GET.dict())     # ⚠️ lets a client filter on ANY field/relation,
                                                 #    including password__startswith → oracle attack
```

Always allow-list the parameter names you accept.

---

## 5. Performance ⭐

- **Every filterable field should be indexed** — filtering is exactly what indexes are for
  ([queries.md §6](queries.md)).
- **Composite indexes must match the common filter+sort combination**: `?status=x&ordering=-created`
  wants `Index(fields=["status", "-created"])`.
- ⚠️ **`icontains` search doesn't use B-tree indexes.** Trigram (`pg_trgm`) or full-text.
- ⚠️ **`distinct()` after an M2M filter adds a sort** — measure it on large tables.
- ⭐ **Cap the page size.** An unbounded `?limit=` plus a permissive filter is a
  denial-of-service vector: `max_page_size` on the pagination class.
- ⭐ **Filters run *before* pagination**, so a slow filter costs the same whether the client
  asks for 10 rows or 1000.

---

## 6. Interview points

- **How do you add filtering to a DRF endpoint?** `django-filter` backend +
  `filterset_fields` for simple cases, a `FilterSet` class for ranges, custom methods, and
  validation.
- **`filterset_fields` vs `filterset_class`?** Declarative exact-match shorthand vs full
  control (lookups, custom methods, cross-field logic).
- **Where does authorisation scoping go, and why not in a filter? ⭐⭐** In `get_queryset()` —
  filters are client-controlled and optional, so they can't be a security boundary.
- **Why did filtering on an M2M return duplicates?** The join produces one row per match; add
  `.distinct()`.
- **What's wrong with `ordering_fields = "__all__"`?** Clients can sort by unindexed columns
  and force expensive full sorts.
- **Why is `?search=` slow on a big table?** `icontains` → `LIKE '%x%'`, which can't use a
  B-tree index. Use full-text or trigram indexes.
- **How do you support `?min_price=&max_price=`?** `NumberFilter` with
  `lookup_expr="gte"/"lte"` on the same `field_name`.
- **Risk of `filter(**request.GET.dict())`?** Arbitrary field access — an information-
  disclosure vulnerability.
