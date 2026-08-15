# Architecture, Networking & Storage

> State layer: **[state_management.md](state_management.md)** · Principles:
> **[../../SDLC/principles.md](../../SDLC/principles.md)**

---

## 1. Layers ⭐⭐

```
┌─────────────────────────────────────────────┐
│ PRESENTATION   widgets, routing              │  ⭐ no business logic, no HTTP
│                ↕ state (Bloc/Riverpod)       │
├─────────────────────────────────────────────┤
│ DOMAIN         entities, use cases           │  ⭐ PURE DART — no Flutter imports
│                repository INTERFACES         │
├─────────────────────────────────────────────┤
│ DATA           repository implementations    │
│                remote (API) + local (cache)  │
│                DTOs / models                 │
└─────────────────────────────────────────────┘
        dependencies point INWARD ⭐
```

⭐⭐ **The test that proves the layering is real: `domain/` must not import `package:flutter`.**
If it does, your business rules are welded to the UI framework and can't be unit-tested without
a widget tree. That one rule delivers most of the value of "clean architecture" without the
ceremony.

⭐ **The Repository pattern is the key boundary.** The domain declares *what* it needs; the data
layer decides *where* it comes from:

```dart
// domain/ — an interface, pure Dart
abstract interface class ProductRepository {
  Future<List<Product>> getProducts({bool forceRefresh = false});
}

// data/ — the implementation decides cache vs network
class ProductRepositoryImpl implements ProductRepository {
  ProductRepositoryImpl(this._api, this._db);

  @override
  Future<List<Product>> getProducts({bool forceRefresh = false}) async {
    if (!forceRefresh) {
      final cached = await _db.getProducts();
      if (cached.isNotEmpty) return cached;              // ⭐ cache-first
    }
    final remote = await _api.fetchProducts();
    await _db.saveProducts(remote);
    return remote.map((dto) => dto.toDomain()).toList(); // ⭐ DTO → entity
  }
}
```

⭐ **Keep DTOs (JSON shapes) separate from domain entities.** When the backend renames a field,
you change one `fromJson` — not every widget. Coupling your UI to the API's wire format is the
most common structural mistake in Flutter apps.

⚠️ **Don't over-layer a small app.** A five-screen app with three endpoints does not need
use-case classes wrapping single repository calls. Say this — knowing when *not* to apply Clean
Architecture is a senior signal.

---

## 2. Project structure ⭐

**Feature-first beats layer-first** for anything beyond a toy:

```
lib/
├── main.dart
├── core/                    shared: theme, router, errors, network client, DI
├── features/
│   ├── auth/
│   │   ├── data/            api, dto, repository_impl
│   │   ├── domain/          entity, repository interface
│   │   └── presentation/    screens, widgets, bloc/providers
│   └── cart/                same shape
└── shared/                  reusable widgets, extensions
```

⭐ **Why feature-first:** a change to "cart" touches one directory. With layer-first
(`screens/`, `models/`, `services/`) every feature is smeared across the tree, and deleting a
feature means hunting through five folders. It also maps to how teams split work.

---

## 3. Dependency injection ⭐

```dart
// get_it — a service locator
final sl = GetIt.instance;

void setupLocator() {
  sl.registerLazySingleton<ApiClient>(() => ApiClient(sl()));
  sl.registerLazySingleton<ProductRepository>(() => ProductRepositoryImpl(sl(), sl()));
  sl.registerFactory(() => ProductBloc(sl()));            // ⭐ new instance per use
}
```

```dart
// Riverpod — DI and state in one system
final apiProvider  = Provider<ApiClient>((ref) => ApiClient());
final repoProvider = Provider<ProductRepository>((ref) => ProductRepositoryImpl(ref.watch(apiProvider)));
// tests: ProviderScope(overrides: [repoProvider.overrideWithValue(FakeRepo())])
```

⭐⭐ **The point of DI is testability, not indirection.** Depend on the `ProductRepository`
*interface*, and a test injects a fake with no HTTP, no database, and no waiting. Code that
constructs `ApiClient()` inline is untestable by construction.

⚠️ **A service locator is not the same as DI** — `sl<Thing>()` called *inside* a class hides
the dependency and reintroduces global state. Inject through the constructor; use the locator
only at the composition root.

---

## 4. Networking ⭐

```dart
final dio = Dio(BaseOptions(
  baseUrl: Env.apiUrl,
  connectTimeout: const Duration(seconds: 10),    // ⭐⭐ ALWAYS set timeouts
  receiveTimeout: const Duration(seconds: 15),
))
  ..interceptors.addAll([
    AuthInterceptor(),        // ⭐ attach the token; refresh on 401
    RetryInterceptor(),       // ⭐ retry idempotent requests with backoff
    LogInterceptor(),         // ⚠️ debug builds only — never log tokens
  ]);
```

⭐ **Interceptors are where cross-cutting concerns belong** — auth headers, token refresh,
retries, logging, correlation IDs. Doing it per call site guarantees someone forgets.

⚠️⚠️ **Token refresh must be single-flight.** Five parallel requests all get a 401, all trigger
a refresh, and four of them fail or the refresh token gets rotated out from under them. Lock the
refresh: the first caller refreshes, the rest await the same Future.

**Error handling — return, don't throw:**

```dart
sealed class Failure {}
class NetworkFailure extends Failure {}          // no connection
class ServerFailure extends Failure { final int code; ServerFailure(this.code); }
class ValidationFailure extends Failure { final Map<String, String> errors; ... }

Future<Result<List<Product>, Failure>> getProducts();   // ⭐ caller must handle both
```

⭐ **Mobile networks fail constantly** — that's the defining difference from backend work.
Timeouts, retries with exponential backoff, offline detection (`connectivity_plus`), and a
queue for pending writes aren't optional extras.

⚠️ **Parse large JSON in an isolate** (`compute`) — a 2 MB response decoded on the UI thread
drops frames ([async_streams.md §5](async_streams.md)).

⭐ **Codegen for serialisation** (`json_serializable`, `freezed`, or `retrofit`) — hand-written
`fromJson` for thirty models is where silent field-name typos live.

---

## 5. Local storage ⭐

| Option | Use | Notes |
|---|---|---|
| **`shared_preferences`** | ⭐ small key–value: flags, theme, onboarding | ⚠️ **not secure**, not for tokens |
| **`flutter_secure_storage`** | ⭐⭐ tokens, credentials | Keychain (iOS) / Keystore (Android) |
| **Drift** (SQLite) | ⭐ relational data, complex queries | type-safe, compile-checked SQL |
| **Isar / Hive** | fast NoSQL object store | good for caches and offline docs |
| **`path_provider` + files** | images, documents, exports | |

⚠️⚠️ **Never put an auth token, API key, or PII in `shared_preferences`.** On a rooted or
jailbroken device it's a plain file. Use `flutter_secure_storage`.

⚠️ **Anything shipped in the app binary is public** — API keys in Dart source can be extracted
from the APK in minutes. Secrets belong on your server; the app should hold only short-lived
user tokens.

⭐ **Offline-first is a design decision, not a feature.** Decide early: read from the local
database and sync in the background, or fail when offline. Retrofitting offline support later
means rewriting every repository.

---

## 6. Configuration & flavors ⭐

```dart
// --dart-define keeps secrets out of the repo
const apiUrl = String.fromEnvironment('API_URL', defaultValue: 'https://dev.api.com');
```

```bash
flutter run --dart-define=API_URL=https://staging.api.com --flavor staging
flutter build apk --release --dart-define-from-file=env/prod.json
```

⭐ **Flavors (dev / staging / prod)** give separate bundle IDs, app icons, and names — so all
three install side by side on one device and nobody demos against production by accident.

⚠️ **`.env` files bundled as assets are readable in the built app** — `--dart-define` is
compiled in, which is better but still **not secret**. Neither is a substitute for keeping real
secrets server-side.

---

## 7. Cross-cutting concerns

```dart
// ⭐ Global error capture
FlutterError.onError = (details) => Sentry.captureException(details.exception);
PlatformDispatcher.instance.onError = (error, stack) {         // async errors
  Sentry.captureException(error, stackTrace: stack);
  return true;
};
```

⭐ **Ship crash reporting from day one** (Sentry/Crashlytics) — you cannot debug a user's device,
so a symbolicated stack trace is all you'll ever get. Upload symbol files as part of the release
build or every trace is unreadable.

**Also standard:** analytics behind an interface (so it's swappable and mockable), feature flags
for staged rollout, forced-update checks against a minimum supported version, and localisation
via `flutter_localizations` + ARB files.

---

## 8. Interview points

- **How do you structure a Flutter app? ⭐⭐** Feature-first directories with presentation /
  domain / data layers, dependencies pointing inward, and `domain/` free of Flutter imports.
- **Why the repository pattern? ⭐** It hides *where* data comes from — network, cache, or
  database — so the UI and business logic don't change when the source does.
- **Why separate DTOs from entities?** A backend field rename should touch one `fromJson`, not
  every widget.
- **Feature-first vs layer-first?** Feature-first localises change and maps to team boundaries.
- **What's the real point of DI? ⭐** Testability — inject a fake repository instead of hitting
  the network.
- **Service locator vs constructor injection?** `sl<T>()` inside a class hides dependencies and
  is global state; inject via the constructor, use the locator only at the composition root.
- **Where do auth headers and retries belong?** Interceptors — one place, applied to every
  request.
- **What's tricky about token refresh? ⭐⭐** Concurrent 401s trigger parallel refreshes — make
  it single-flight so one refresh serves all waiters.
- **How do you handle errors from the network?** A sealed `Failure` type returned to the caller,
  rather than exceptions thrown across layers.
- **Where do you store an auth token? ⭐⭐** `flutter_secure_storage` (Keychain/Keystore) —
  never `shared_preferences`.
- **Can you keep an API key in the app?** No — anything in the binary is extractable. Proxy
  through your server.
- **What are flavors for?** Separate dev/staging/prod builds with distinct bundle IDs so they
  coexist and can't be confused.
- **When would you *not* use Clean Architecture? ⭐** A small app — wrapping single repository
  calls in use-case classes is ceremony without benefit.
