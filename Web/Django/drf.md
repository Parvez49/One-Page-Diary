# Django REST Framework — Views, Serializers, Routers

> Filtering & permissions: **[filtering.md](filtering.md)** · Auth: **[auth.md](auth.md)** ·
> Query efficiency: **[queries.md](queries.md)**

---

## 1. The DRF request pipeline ⭐

```
URL router
   ▼
ViewSet.dispatch()
   ├─ 1. Parser          request.data  (JSON / form / multipart)
   ├─ 2. Authentication  → request.user, request.auth
   ├─ 3. Permission      has_permission()          → 401 / 403
   ├─ 4. Throttling      rate limits               → 429
   ├─ 5. handler         list/create/retrieve/update/destroy
   │      ├─ get_queryset()  → filter_backends → pagination
   │      └─ serializer: validate → save
   └─ 6. Renderer        → JSON
```

⭐ **Order matters in the answer:** authentication (*who are you?*) always precedes permission
(*may you?*), and object-level permissions run **after** the object is fetched, inside
`get_object()`.

---

## 2. The view ladder — pick the right rung

| Level | Use when |
|---|---|
| `APIView` | ⭐ non-CRUD actions, full control (login, webhook, report) |
| `GenericAPIView` + mixins | you want some generic behaviour, custom wiring |
| `ListCreateAPIView` etc. | one resource, standard CRUD, distinct URLs |
| **`ModelViewSet`** | ⭐⭐ full CRUD on a model + router-generated URLs |
| `ReadOnlyModelViewSet` | list + retrieve only |

```python
class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.all()
    permission_classes = [IsAuthenticated, IsOwnerOrReadOnly]

    def get_queryset(self):                                  # ⭐⭐ the important override
        return (
            Product.objects
            .select_related("category")                      # ⭐ kill N+1 HERE
            .prefetch_related("tags")
            .filter(owner=self.request.user)                 # ⭐ scope to the user
        )

    def get_serializer_class(self):                          # ⭐ different shape per action
        if self.action == "list":
            return ProductListSerializer                     # lean
        return ProductDetailSerializer                       # nested, expensive

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)             # ⭐ inject server-side fields

    @action(detail=True, methods=["post"])                   # → /products/1/publish/
    def publish(self, request, pk=None):
        product = self.get_object()                          # ⭐ runs object permissions
        product.publish()
        return Response({"status": "published"})

    @action(detail=False, methods=["get"], url_path="mine")  # → /products/mine/
    def mine(self, request): ...
```

⚠️⚠️ **Never trust the client for ownership.** `serializer.save(owner=request.user)` in
`perform_create` — if `owner` is a writable serializer field, anyone can create records
belonging to someone else. Same for `is_staff`, `price`, `status`.

⚠️ **`queryset` as a class attribute is evaluated once at import** for the router's basename,
but re-fetched per request. Any *request-dependent* filtering must go in `get_queryset()` —
putting `filter(user=...)` at class level is impossible and putting it in `__init__` is a
cross-request data leak.

---

## 3. Routers & URLs

```python
from rest_framework.routers import DefaultRouter

router = DefaultRouter()
router.register(r"products", ProductViewSet, basename="product")

urlpatterns = [path("api/v1/", include((router.urls, "shop"), namespace="v1"))]
```

Generates:

| URL | Methods | Name |
|---|---|---|
| `/products/` | GET (list), POST (create) | `product-list` |
| `/products/{pk}/` | GET, PUT, PATCH, DELETE | `product-detail` |
| `/products/{pk}/publish/` | POST (`@action(detail=True)`) | `product-publish` |

```python
reverse("v1:product-detail", kwargs={"pk": 1})
```

⭐ `basename` is required when the viewset has no static `queryset` attribute — DRF can't infer
the URL name otherwise.

**Nested resources:** `drf-nested-routers`, or a flat URL with a query param
(`/products/?category=3`) — flatter is usually easier to cache and paginate.

---

## 4. Serializers ⭐⭐

**Serializers do three jobs**: serialize (model → JSON), deserialize + **validate** (JSON →
validated data), and save.

```python
class ProductSerializer(serializers.ModelSerializer):
    category      = CategorySerializer(read_only=True)            # ⭐ nested READ
    category_id   = serializers.PrimaryKeyRelatedField(           # ⭐ flat WRITE
        queryset=Category.objects.all(), source="category", write_only=True,
        error_messages={"does_not_exist": "No category with id {pk_value}"},
    )
    owner         = serializers.StringRelatedField(read_only=True)
    order_count   = serializers.IntegerField(read_only=True)      # ⭐ from annotate()
    display_price = serializers.SerializerMethodField()

    class Meta:
        model  = Product
        fields = ["id", "name", "price", "category", "category_id",
                  "owner", "order_count", "display_price"]
        read_only_fields = ["owner"]

    def get_display_price(self, obj):
        return f"${obj.price:,.2f}"

    def validate_price(self, value):                  # ⭐ FIELD-level
        if value <= 0:
            raise serializers.ValidationError("Price must be positive.")
        return value

    def validate(self, attrs):                        # ⭐ OBJECT-level (cross-field)
        if attrs.get("sale_price") and attrs["sale_price"] > attrs["price"]:
            raise serializers.ValidationError({"sale_price": "Cannot exceed price."})
        return attrs

    def create(self, validated_data):
        return Product.objects.create(**validated_data)
```

⭐⭐ **The read/write asymmetry is the pattern to know**: nested objects are pleasant to *read*
but ambiguous to *write*. Expose a nested serializer `read_only=True` plus a
`PrimaryKeyRelatedField(source=..., write_only=True)` — the client sends an id, receives an
object.

⚠️⚠️ **`fields = "__all__"` is a security bug waiting to happen.** Add a `password_hash`,
`is_staff`, or `internal_notes` field to the model and it's instantly exposed — and writable.
**List fields explicitly.**

⚠️ **`SerializerMethodField` is where N+1 hides.** `get_x` running a query executes once per
row. Annotate in `get_queryset()` and read the annotation instead.

⚠️ **Nested writes don't work by default** — a nested serializer that isn't read-only raises
on `create()` unless you write it yourself. Usually a sign the endpoint should be flatter.

**Validation order:** field `to_internal_value` → `validate_<field>` → `validate()` →
model `validators` (only if you call `full_clean`, which DRF does **not** do automatically).

⭐ **Serializer validation ≠ model validation.** `Model.save()` skips `full_clean()`, so
`CheckConstraint`s are your only database-level guarantee. Validate in the serializer *and*
constrain in the database.

**Context & performance:**

```python
serializer.context["request"]                     # ⭐ available inside serializer methods
ProductSerializer(qs, many=True)                  # bulk serialize
```

⚠️ Deeply nested serializers are the second-biggest DRF performance problem after N+1 —
each level multiplies work. Flatten, or provide `?expand=` opt-in.

---

## 5. Pagination

```python
REST_FRAMEWORK = {
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": 25,
}
```

| Class | Mechanism | Trade-off |
|---|---|---|
| `PageNumberPagination` | `?page=3` | familiar; ⚠️ **deep offsets get slow**, items shift |
| `LimitOffsetPagination` | `?limit=20&offset=100` | flexible; same offset problem |
| **`CursorPagination`** | ⭐ opaque cursor, ordered field | O(1) at any depth, **stable** under inserts; no page numbers, no jumping |

⭐ **Use `CursorPagination` for feeds, logs, and anything large or real-time** — offset
pagination re-scans every skipped row and duplicates/skips items when rows are inserted
between requests. See [queries.md §7](queries.md).

⚠️ The `count` in a paginated response costs a `COUNT(*)` on every request; on a big table
that can dominate. Cursor pagination omits it.

---

## 6. Status codes ⭐

```python
from rest_framework import status
from rest_framework.response import Response
return Response({"id": obj.id}, status=status.HTTP_201_CREATED)
```

**Success**

| Code | Use |
|---|---|
| **200 OK** | successful GET/PUT/PATCH |
| **201 CREATED** | ⭐ POST created a resource — return it, and a `Location` header |
| **202 ACCEPTED** | ⭐ queued for async processing (Celery) — not done yet |
| **204 NO CONTENT** | successful DELETE, empty body |
| 206 PARTIAL CONTENT | range/partial response |

**Client errors**

| Code | Use |
|---|---|
| **400 BAD REQUEST** | validation failed / malformed |
| **401 UNAUTHORIZED** | ⭐ *not authenticated* — "who are you?" |
| **403 FORBIDDEN** | ⭐ authenticated but **not allowed** |
| **404 NOT FOUND** | no such resource — ⭐ also use it to hide existence from unauthorised users |
| 405 METHOD NOT ALLOWED | wrong verb for this endpoint |
| 409 CONFLICT | duplicate / state conflict (concurrent edit) |
| 422 UNPROCESSABLE | semantically invalid (some APIs prefer this to 400) |
| **429 TOO MANY REQUESTS** | throttled — ⭐ include `Retry-After` |

**Server errors:** 500 (unhandled), 502 (bad upstream), 503 (down/maintenance — send
`Retry-After`), 504 (upstream timeout).

⭐⭐ **401 vs 403 is asked constantly:** **401** = no or invalid credentials, and the response
should carry `WWW-Authenticate`; **403** = credentials are fine, the action isn't permitted.
Retrying with the same token can fix a 401; it will never fix a 403.

**Consistent error shape** — define one and stick to it:

```python
def custom_exception_handler(exc, context):
    response = exception_handler(exc, context)
    if response is not None:
        response.data = {"error": {"code": response.status_code, "detail": response.data}}
    return response
# REST_FRAMEWORK = {"EXCEPTION_HANDLER": "app.utils.custom_exception_handler"}
```

---

## 7. Versioning & docs

```python
REST_FRAMEWORK = {
    "DEFAULT_VERSIONING_CLASS": "rest_framework.versioning.URLPathVersioning",
    "DEFAULT_VERSION": "v1",
    "ALLOWED_VERSIONS": ["v1", "v2"],
}
```

⭐ **URL path versioning (`/api/v1/`) is the pragmatic default** — visible, cacheable, trivial
to route in nginx. Header/accept versioning is purer REST but harder to debug and cache.

⭐ **Prefer additive change to a new version.** Adding an optional field breaks no one;
removing or renaming does. A new major version means maintaining two code paths, so earn it.

```python
# drf-spectacular → OpenAPI 3
SPECTACULAR_SETTINGS = {"TITLE": "Shop API", "VERSION": "1.0.0"}
```

---

## 8. Interview points

- **Walk me through a DRF request. ⭐** Parser → authentication → permission → throttle →
  handler → `get_queryset` → filters → pagination → serializer → renderer.
- **`APIView` vs `ViewSet`?** Full manual control vs router-generated CRUD; ViewSets remove
  boilerplate when the resource is a model.
- **Where do you prevent N+1 in DRF? ⭐** `get_queryset()` with
  `select_related`/`prefetch_related`; watch `SerializerMethodField` and nested serializers.
- **How do you use a different serializer per action?** Override `get_serializer_class()` on
  `self.action`.
- **How do you set the owner on create?** `perform_create(serializer)` with
  `serializer.save(owner=self.request.user)` — never from client input.
- **Why is `fields = "__all__"` dangerous?** Any new model field is auto-exposed and writable.
- **`validate_<field>` vs `validate`?** Single field vs cross-field/object-level.
- **Does DRF run model validators?** Not automatically — `save()` skips `full_clean()`. Use
  serializer validation plus database constraints.
- **401 vs 403? ⭐** Unauthenticated vs authenticated-but-forbidden.
- **When do you return 202?** The work was accepted and queued (Celery), not completed.
- **Which pagination for an infinite feed, and why?** Cursor — constant cost at depth and
  stable when rows are inserted.
- **How do you version an API without breaking clients?** Prefer additive changes; use URL
  path versioning when a breaking change is unavoidable.
