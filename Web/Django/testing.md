# Testing

> Strategy & pyramid: **[../../SDLC/testing.md](../../SDLC/testing.md)** ·
> pytest basics: **[../../Language/Python/modules.md](../../Language/Python/modules.md)**

---

## 1. What to test in a Django project ⭐

| Layer | Test | Cost |
|---|---|---|
| **Unit** | model methods, services, utils, validators — **no DB where possible** | ⭐ fast, many |
| **Integration** | view ↔ serializer ↔ model, permissions, DB queries | medium |
| **API / functional** | full request → response through the URL, as a client | slower, fewer |
| **Regression** | a test reproducing each fixed bug | ⭐ cheap insurance |
| **Performance** | ⭐ **query counts**, load tests on hot endpoints | targeted |

⭐ **The Django-specific advice:** most value sits in **API-level tests** — one test through
the real URL exercises routing, auth, permissions, serializer validation, and the ORM at once.
Heavy mocking of Django internals tests your mocks, not your app.

⭐ **Test behaviour, not implementation.** Assert response status and payload, not which
internal method was called — otherwise every refactor breaks the suite and people stop
trusting it.

---

## 2. Setup

```bash
pip install pytest pytest-django pytest-cov pytest-mock factory-boy
```

```ini
# pytest.ini
[pytest]
DJANGO_SETTINGS_MODULE = config.settings.test
python_files = test_*.py
addopts = -ra -q --strict-markers --reuse-db      # ⭐ --reuse-db skips recreating the schema
```

```python
# config/settings/test.py
from .base import *

DEBUG = False                                     # ⭐ test what production does
PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]   # ⭐ big speedup
EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"        # ⭐ mail.outbox
CELERY_TASK_ALWAYS_EAGER = True                   # ⚠️ see below
CACHES = {"default": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache"}}
STORAGES = {"default": {"BACKEND": "django.core.files.storage.InMemoryStorage"}}
```

⭐ **Swapping PBKDF2 for MD5 in tests is the single biggest speed win** — password hashing is
deliberately slow, and a suite creating hundreds of users spends most of its time there.

⚠️ **SQLite-in-memory for tests when production runs Postgres is a trap.** It's fast, but it
silently accepts things Postgres rejects (constraint timing, `ArrayField`, `JSONField`
lookups, transaction behaviour), so tests pass and production fails. ⭐ Use Postgres in CI —
`--reuse-db` and `--no-migrations` recover most of the speed.

⚠️ **`CELERY_TASK_ALWAYS_EAGER = True` runs tasks synchronously and inline**, which hides the
`transaction.on_commit` race and retry behaviour ([async_tasks.md](async_tasks.md)). Convenient
default, but test critical tasks by calling the function directly and asserting the enqueue
separately.

---

## 3. Fixtures & factories

```python
# conftest.py — ⭐ global fixtures
import pytest
from rest_framework.test import APIClient

@pytest.fixture
def api_client():
    return APIClient()

@pytest.fixture
def user(db):
    return UserFactory()

@pytest.fixture
def auth_client(api_client, user):
    api_client.force_authenticate(user=user)     # ⭐ skips the login round trip
    return api_client
```

```python
# factories.py — factory_boy
import factory

class UserFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = User
        django_get_or_create = ("email",)

    email = factory.Sequence(lambda n: f"user{n}@test.com")   # ⭐ unique, no collisions
    first_name = "Test"
    is_active = True

class OrderFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Order

    customer = factory.SubFactory(UserFactory)                # ⭐ builds the graph
    total    = factory.Faker("pydecimal", left_digits=3, positive=True)

    @factory.post_generation
    def items(self, create, extracted, **kwargs):
        if create and extracted:
            for item in extracted: self.items.add(item)
```

⭐⭐ **Factories over JSON fixtures.** `loaddata` fixtures rot: every model change breaks them,
they're invisible in the test (you can't see what matters), and they force you to maintain
data you don't care about. A factory declares only the fields relevant to *this* test and
fills the rest.

```python
UserFactory(is_staff=True)               # override only what matters
UserFactory.build()                      # ⭐ no DB write — for pure unit tests
UserFactory.create_batch(10)
```

⚠️ **`Faker` with a random seed makes flaky tests.** If a test only passes for some generated
values, that's a real bug — but pin the seed when you need reproducibility.

---

## 4. Writing tests

```python
import pytest
from django.urls import reverse

pytestmark = pytest.mark.django_db          # ⭐ whole module needs the DB


class TestProductAPI:
    def test_list_requires_auth(self, api_client):
        assert api_client.get(reverse("v1:product-list")).status_code == 401

    def test_list_returns_only_own(self, auth_client, user):
        ProductFactory.create_batch(3, owner=user)
        ProductFactory.create_batch(2)                       # ⭐ another user's — must not leak
        resp = auth_client.get(reverse("v1:product-list"))
        assert resp.status_code == 200
        assert len(resp.data["results"]) == 3

    @pytest.mark.parametrize("price,expected", [(10, 201), (0, 400), (-5, 400)])
    def test_price_validation(self, auth_client, price, expected):
        resp = auth_client.post(reverse("v1:product-list"), {"name": "x", "price": price})
        assert resp.status_code == expected

    def test_cannot_edit_others(self, auth_client):
        other = ProductFactory()                              # not owned by our user
        resp = auth_client.patch(reverse("v1:product-detail", args=[other.pk]), {"name": "h"})
        assert resp.status_code in (403, 404)                 # ⭐ 404 hides existence
```

⭐⭐ **Test the negative cases.** "A logged-in user can read their own orders" is the easy
test; "user A gets 404 for user B's order" is the one that catches the IDOR
([security.md](security.md)). Every permission rule deserves a test that it *denies*.

**Common assertions:**

```python
from django.core import mail
assert len(mail.outbox) == 1                       # ⭐ locmem email backend

with pytest.raises(ValidationError, match="positive"):
    product.full_clean()

assert Product.objects.filter(name="x").exists()
resp.json()["error"]["code"] == "invalid"
```

---

## 5. Query-count tests ⭐⭐

```python
def test_list_is_efficient(auth_client, django_assert_num_queries):
    ProductFactory.create_batch(20, owner=...)
    with django_assert_num_queries(4):             # ⭐ FIXED, not proportional to 20
        auth_client.get(reverse("v1:product-list"))
```

⭐ **This is the highest-value Django test there is.** It's the only thing that stops an N+1
from creeping back in when someone adds a nested serializer field
([queries.md](queries.md)). Create *several* objects so a per-row query shows up — with one
row, N+1 and O(1) look identical.

---

## 6. Mocking ⭐

```python
def test_payment_success(auth_client, mocker):
    charge = mocker.patch("billing.services.stripe.Charge.create",     # ⭐ where it's USED
                          return_value={"id": "ch_1", "status": "succeeded"})
    resp = auth_client.post(reverse("v1:checkout"))
    assert resp.status_code == 201
    charge.assert_called_once()

def test_task_enqueued(auth_client, mocker):
    delay = mocker.patch("orders.views.send_confirmation.delay")
    auth_client.post(reverse("v1:order-list"), {...})
    delay.assert_called_once()
```

⭐⭐ **Patch where the name is *looked up*, not where it's defined** —
`orders.views.send_confirmation`, not `orders.tasks.send_confirmation`. `from x import y`
binds `y` into the importing module's namespace, so patching the source has no effect. This is
the #1 reason a mock "doesn't work."

⭐ **Mock at the boundary only** — third-party HTTP, payment gateways, email, S3, time. Mocking
your own service layer means the test passes while the real integration is broken.
`responses`/`respx` for HTTP, `freezegun` for time.

⚠️ **Don't mock the ORM.** It's fast enough against a real test database and mocking it tests
nothing real.

---

## 7. Running & coverage

```bash
pytest                                  # everything
pytest -x -q                            # stop at first failure
pytest -k "permission and not slow"
pytest --reuse-db --no-migrations       # ⭐ fastest local loop
pytest -n auto                          # ⭐ pytest-xdist, parallel
pytest --cov=apps --cov-report=term-missing --cov-fail-under=80
```

⭐ **Coverage is a *floor*, not a goal.** 100% coverage with no assertions on permissions or
error paths is worse than 70% that covers them. Track it to spot untested modules, don't
optimise for the number.

⚠️ **Test isolation:** `pytest.mark.django_db` wraps each test in a transaction that's rolled
back. `django_db(transaction=True)` (needed for `on_commit` and threads) **truncates** instead
— slower, and it doesn't reset sequences, so don't assume ids.

⚠️ **Flaky tests are a bug, not noise.** Usual causes: shared state between tests, time
dependence (`freezegun`), ordering assumptions on unordered querysets (`Meta.ordering` or
explicit `order_by`), and randomised factory data.

---

## 8. Interview points

- **What do you test in a Django app? ⭐** Mostly API-level tests through real URLs — they
  exercise routing, auth, serializers, and the ORM together — plus unit tests for business
  logic and regression tests for fixed bugs.
- **Factories vs fixtures?** Factories: declare only what the test cares about, don't rot with
  schema changes, and are readable in place.
- **How do you prevent N+1 regressions? ⭐⭐** `django_assert_num_queries` with a fixed
  expected count and several rows in the fixture.
- **Why does my mock not take effect?** You patched the definition site, not the module where
  the name is used.
- **What should you mock?** External boundaries only — HTTP, payments, email, time. Not the
  ORM, not your own services.
- **Why not SQLite for tests when production is Postgres?** Behavioural differences
  (constraints, JSON/array fields, transactions) let bugs through.
- **What does `CELERY_TASK_ALWAYS_EAGER` hide?** Serialisation, retries, and the
  `transaction.on_commit` race — tasks run inline and synchronously.
- **How do you speed up a slow suite?** MD5 password hasher, `--reuse-db`, `--no-migrations`,
  `pytest-xdist`, `Factory.build()` where no DB is needed.
- **Is high coverage the goal?** No — it measures execution, not assertion quality. Cover the
  denial paths and error branches.
- **What's the most important security test?** That user A gets 403/404 for user B's object.
