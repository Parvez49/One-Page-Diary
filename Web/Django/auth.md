# Authentication, Permissions & Sessions

> Attacks & headers: **[security.md](security.md)** · Rate limiting: **[throttling.md](throttling.md)**

---

## 1. Authentication vs authorisation ⭐

- **Authentication** — *who are you?* Wrong/missing credentials → **401**.
- **Authorisation** — *may you do this?* Valid identity, insufficient rights → **403**.

DRF runs them in that order: authentication classes populate `request.user`, then permission
classes decide.

---

## 2. Django's auth system

```python
from django.contrib.auth import authenticate, login, logout, get_user_model

user = authenticate(request, username=u, password=p)   # ⭐ None if invalid
if user is not None:
    login(request, user)                                # writes the session
```

⭐ **Passwords are hashed with PBKDF2 (default), Argon2, bcrypt, or scrypt** — never stored or
reversible. Django auto-upgrades a hash on successful login when you change the hasher.

⚠️ **`User.objects.create(password=...)` stores the password in plaintext.** Use
`create_user()`, or `user.set_password(p)` then `save()`.

⭐⭐ **Use a custom user model from day one:**

```python
class User(AbstractUser):
    email = models.EmailField(unique=True)
    USERNAME_FIELD  = "email"
    REQUIRED_FIELDS = []

# settings.py
AUTH_USER_MODEL = "accounts.User"           # ⭐ set BEFORE the first migration
```

⚠️ Swapping `AUTH_USER_MODEL` after migrations exist is genuinely painful — every FK points at
the old table. Start with `AbstractUser` even if you change nothing; it costs nothing now and
saves a migration nightmare later. Always reference it as
`settings.AUTH_USER_MODEL` / `get_user_model()`, never `from django.contrib.auth.models import User`.

**Authentication backends** — chained, first success wins. Add one for email login, LDAP, or
SSO:

```python
AUTHENTICATION_BACKENDS = ["accounts.backends.EmailBackend",
                           "django.contrib.auth.backends.ModelBackend"]
```

---

## 3. Sessions vs tokens vs JWT ⭐⭐

| | **Session cookie** | **DRF Token** | **JWT** |
|---|---|---|---|
| State | ⭐ **server-side** (DB/cache) | server-side row | ⭐ **stateless**, self-contained |
| Revocation | ⭐ **instant** — delete the row | instant | ⚠️ **hard** — valid until expiry |
| Payload | opaque id | opaque key | claims (user id, roles, exp) |
| Scaling | needs shared session store | DB hit per request | ⭐ no lookup |
| Best for | ⭐ browser apps, same domain | simple internal APIs | ⭐ microservices, mobile, cross-domain |
| CSRF risk | ⚠️ **yes** (cookies auto-sent) | no (header) | no, unless stored in a cookie |

⭐⭐ **The trade-off to articulate: statelessness costs you revocation.** A JWT is valid until
it expires because nothing is consulted at verification time — that's the whole point, and
it's why "log out everywhere", banning a user, or a permission downgrade don't take effect
immediately. The standard mitigation is **short-lived access tokens (5–15 min) plus a
long-lived, revocable refresh token** stored server-side.

```python
# djangorestframework-simplejwt
SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME":  timedelta(minutes=15),   # ⭐ short
    "REFRESH_TOKEN_LIFETIME": timedelta(days=7),
    "ROTATE_REFRESH_TOKENS":  True,                    # ⭐ new refresh on each use
    "BLACKLIST_AFTER_ROTATION": True,                  # ⭐ detects token replay
}
```

⚠️⚠️ **Where you store a JWT in a browser is the real question.**

| Storage | Risk |
|---|---|
| `localStorage` | ⚠️ **readable by any XSS** — one injected script exfiltrates the token |
| memory (JS variable) | safe from persistence, lost on refresh |
| ⭐ **`HttpOnly` + `Secure` + `SameSite` cookie** | invisible to JS; ⚠️ reintroduces **CSRF**, so pair with `SameSite=Lax/Strict` or a CSRF token |

⭐ **"Just use JWT" is not a senior answer.** For a first-party browser app on one domain,
**Django's session cookie is simpler and strictly more secure** — server-side, instantly
revocable, HttpOnly by default. Reach for JWT when you have multiple services or clients that
can't hold cookies (mobile, third-party).

⚠️ Never put secrets in a JWT payload — it's **base64, not encrypted**, and anyone can read it.

```python
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework_simplejwt.authentication.JWTAuthentication",
        "rest_framework.authentication.SessionAuthentication",   # ⭐ for the browsable API
    ],
    "DEFAULT_PERMISSION_CLASSES": ["rest_framework.permissions.IsAuthenticated"],  # ⭐ deny by default
}
```

⭐ **Default to `IsAuthenticated` globally** and open up per view. The inverse (default open,
lock down per view) fails silently the first time someone forgets.

---

## 4. Permissions

```python
from rest_framework.permissions import BasePermission, SAFE_METHODS

class IsOwnerOrReadOnly(BasePermission):
    def has_permission(self, request, view):          # ⭐ runs BEFORE the object exists
        return request.user and request.user.is_authenticated

    def has_object_permission(self, request, view, obj):   # ⭐ per-object, in get_object()
        if request.method in SAFE_METHODS:            # GET, HEAD, OPTIONS
            return True
        return obj.owner_id == request.user.id


class IsAdminOrReadOnly(BasePermission):
    def has_permission(self, request, view):
        return request.method in SAFE_METHODS or (request.user and request.user.is_staff)
```

```python
class ProductViewSet(ModelViewSet):
    permission_classes = [IsAuthenticated, IsOwnerOrReadOnly]     # ⭐ ALL must pass (AND)
    # DRF 3.9+: composable — [IsAdmin | IsOwner], ~IsBanned
```

⚠️⚠️ **`has_object_permission` only runs when `get_object()` is called.** A custom `@action`
or a list view never triggers it — so an object permission alone does **not** protect a list
endpoint. Scope list queries in `get_queryset()`
([filtering.md §3](filtering.md)), and call `self.check_object_permissions(request, obj)`
manually if you fetch an object yourself.

**Django's own permission layer:**

```python
user.has_perm("shop.change_product")
@permission_required("shop.change_product")
user.groups.add(editors)                              # ⭐ group-based roles
```

⭐ For anything beyond model-level CRUD permissions, use groups as roles, or
`django-guardian` (per-object) / a policy layer. Rolling your own `if user.role == "admin"`
checks scattered through views is what produces the security bug you'll be asked about.

---

## 5. Session configuration

```python
SESSION_ENGINE = "django.contrib.sessions.backends.cache"   # ⭐ Redis — fast, auto-expiring
SESSION_COOKIE_AGE      = 1209600        # 2 weeks
SESSION_COOKIE_SECURE   = True           # ⭐ HTTPS only
SESSION_COOKIE_HTTPONLY = True           # ⭐ invisible to JavaScript
SESSION_COOKIE_SAMESITE = "Lax"          # ⭐ CSRF mitigation
SESSION_EXPIRE_AT_BROWSER_CLOSE = False
```

⚠️ **`cache` session backend + a non-persistent Redis = everyone logged out on restart.** Use
`cached_db` for durability with cache speed, and a Redis instance with persistence enabled.

⭐ **`login()` cycles the session key** — that's session-fixation protection, and it's why you
must call Django's `login()` rather than setting `request.session["user_id"]` yourself.

---

## 6. Practices

- ⭐ **Rate-limit login and password-reset endpoints** — otherwise credential stuffing is
  free. `ScopedRateThrottle` with a tight scope ([throttling.md](throttling.md)).
- ⭐ **Same generic error for "no such user" and "wrong password"** — distinct messages are a
  user-enumeration oracle. Same for password reset: always report "if the account exists, an
  email was sent."
- **Timing attacks:** `authenticate()` runs the hasher even for a missing user, deliberately.
  Don't short-circuit that.
- **MFA:** `django-otp` / `django-two-factor-auth`.
- **Social/SSO:** `django-allauth` (batteries included) or `python-social-auth`; OAuth2
  provider via `django-oauth-toolkit`.
- **Log auth events** — logins, failures, permission denials — with the request ID and IP.
- ⚠️ **Password reset tokens must be single-use and short-lived**; Django's
  `PasswordResetTokenGenerator` invalidates on password change by hashing the current hash into
  the token.

---

## 7. Interview points

- **Authentication vs authorisation? ⭐** Who you are (401) vs what you may do (403).
- **Session vs JWT — which and why? ⭐⭐** Sessions for first-party browser apps (revocable,
  HttpOnly, simpler); JWT for multi-service/mobile/cross-domain where a shared session store
  is impractical.
- **How do you revoke a JWT?** You largely can't — that's the cost of statelessness. Short
  access-token lifetimes plus a revocable refresh token, or a blacklist (which reintroduces
  state).
- **Where should a browser store a JWT? ⭐** `HttpOnly` cookie (then handle CSRF), not
  `localStorage` — which any XSS can read.
- **Is a JWT encrypted?** No — signed. The payload is base64 and publicly readable.
- **`has_permission` vs `has_object_permission`?** Before the view runs vs per-object inside
  `get_object()` — the latter never fires on list endpoints.
- **How do you stop user A reading user B's records in a list view?** Filter in
  `get_queryset()`; object permissions don't apply to lists.
- **How does Django store passwords?** Salted PBKDF2/Argon2/bcrypt hashes, with automatic
  upgrade on login.
- **Why a custom user model from the start?** Changing `AUTH_USER_MODEL` later requires
  rewriting every FK and migration.
- **Why the same error for unknown user and wrong password?** To prevent account enumeration.
- **What does `login()` do beyond setting a cookie?** Cycles the session key to prevent
  session fixation.
