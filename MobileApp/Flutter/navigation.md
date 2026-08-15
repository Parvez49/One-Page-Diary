# Navigation & Routing

> Widget context rules: **[widgets.md §7](widgets.md)** · App structure: **[architecture.md](architecture.md)**

---

## 1. Navigator 1.0 — the imperative stack ⭐

**The Navigator is a stack of `Route` objects**, and it's an `Overlay` under the hood.

```dart
Navigator.push(context, MaterialPageRoute(builder: (_) => DetailPage(id: 7)));
Navigator.pop(context, result);                     // ⭐ returns a value to the caller

final result = await Navigator.push<bool>(context, route);   // ⭐ await the pop result

Navigator.pushNamed(context, '/detail', arguments: 7);
Navigator.pushReplacement(context, route);          // replace the top — no back
Navigator.pushAndRemoveUntil(context, route, (r) => false);  // ⭐ clear the whole stack
Navigator.popUntil(context, ModalRoute.withName('/home'));
```

⭐ **`pushAndRemoveUntil` with `(route) => false` is the login/logout pattern** — it wipes the
stack so back doesn't return to an authenticated screen.

⚠️⚠️ **`BuildContext` across an `await`** — the widget may be gone by the time you navigate:

```dart
await saveForm();
if (!context.mounted) return;                        // ⭐ Flutter 3.7+
Navigator.pop(context);
```

⚠️ **`Navigator.of(context)` finds the *nearest* Navigator.** With nested navigators (a
`BottomNavigationBar` with per-tab stacks) that may not be the one you meant — use
`rootNavigator: true` for dialogs and full-screen routes.

**Named routes:**

```dart
MaterialApp(
  routes: {'/': (_) => const Home(), '/detail': (_) => const Detail()},
  onGenerateRoute: (settings) { ... },               // ⭐ for dynamic/parameterised routes
  onUnknownRoute: (settings) => MaterialPageRoute(builder: (_) => const NotFound()),
);
```

⚠️ **Plain named routes can't carry typed parameters** — `arguments` is `Object?` and you cast
it at the destination, which is a runtime failure waiting to happen. `onGenerateRoute` with
parsing, or a typed router, fixes it.

---

## 2. Navigator 2.0 — declarative ⭐

Navigator 1.0 is imperative: you *command* the stack. That breaks down when the **URL is the
source of truth** — web deep links, browser back/forward, and state restoration.

**Navigator 2.0** makes the whole stack a function of app state:

```dart
Navigator(
  pages: [                                           // ⭐ declarative list = the stack
    const MaterialPage(child: HomePage()),
    if (selectedId != null) MaterialPage(child: DetailPage(id: selectedId)),
  ],
  onPopPage: (route, result) {
    if (!route.didPop(result)) return false;
    setState(() => selectedId = null);               // ⭐ update STATE, not the stack
    return true;
  },
);
```

⭐⭐ **The conceptual shift: you no longer push and pop — you change state, and the stack
re-derives itself.** That's what makes deep linking work, because a URL maps to a state which
maps to a stack.

⚠️ **The raw API (`RouterDelegate`, `RouteInformationParser`, `BackButtonDispatcher`) is
notoriously verbose** — hundreds of lines for a simple app. Essentially nobody writes it by
hand; you use a router package built on it. Saying that is the correct senior answer.

---

## 3. go_router ⭐⭐

**The official recommendation** — declarative power, imperative ergonomics.

```dart
final router = GoRouter(
  initialLocation: '/',
  routes: [
    GoRoute(
      path: '/',
      builder: (context, state) => const HomeScreen(),
      routes: [                                              // ⭐ nested → /details/:id
        GoRoute(
          path: 'details/:id',
          builder: (context, state) =>
              DetailScreen(id: state.pathParameters['id']!),
        ),
      ],
    ),
    ShellRoute(                                              // ⭐ persistent bottom nav shell
      builder: (context, state, child) => ScaffoldWithNav(child: child),
      routes: [ /* tab routes keep their own stacks */ ],
    ),
  ],
  redirect: (context, state) {                               // ⭐⭐ centralised AUTH GUARD
    final loggedIn = ref.read(authProvider).isLoggedIn;
    final loggingIn = state.matchedLocation == '/login';
    if (!loggedIn && !loggingIn) return '/login?from=${state.matchedLocation}';
    if (loggedIn && loggingIn) return '/';
    return null;                                             // no redirect
  },
  refreshListenable: authNotifier,                           // ⭐ re-evaluate on auth change
  errorBuilder: (context, state) => const NotFoundScreen(),
);

MaterialApp.router(routerConfig: router);
```

```dart
context.go('/details/7');        // ⭐ REPLACE the location (declarative)
context.push('/details/7');      // ⭐ PUSH onto the stack (imperative)
context.pop();
context.goNamed('detail', pathParameters: {'id': '7'});
```

⭐⭐ **`go` vs `push` is the go_router question.** `go` sets the location and rebuilds the whole
stack from the route tree — back goes to the *parent route*. `push` adds one page on top — back
returns to where you were. Using `go` when you meant `push` produces "back button goes to the
wrong screen" bugs.

⭐ **A single `redirect` function is the correct place for auth gating** — not a check scattered
in every screen's `initState`. With `refreshListenable`, logging out immediately bounces the
user off protected routes wherever they are.

**Alternatives:** `auto_route` (⭐ code-generated, fully type-safe arguments),
`beamer`, or Navigator 1.0 for a small app that will never be a web target.

---

## 4. Deep links & app links ⭐

```
Custom scheme    myapp://product/42        ⚠️ any app can claim it — not verified
Universal Link   https://ex.com/product/42 ⭐ iOS, verified by apple-app-site-association
App Link         https://ex.com/product/42 ⭐ Android, verified by assetlinks.json
```

⭐ **Verified HTTPS links (Universal/App Links) are the right choice** — they're
domain-verified, so no other app can hijack them, and they gracefully fall back to the website
when the app isn't installed. Custom schemes do neither.

**Setup:** `android/app/src/main/AndroidManifest.xml` intent filters +
`.well-known/assetlinks.json` on your domain; `Info.plist` associated domains +
`.well-known/apple-app-site-association` for iOS. go_router handles the routing once the
platform delivers the URI.

⚠️⚠️ **Deep links must handle three cases**: app **not running** (cold start — the link arrives
before your auth state is loaded), app **backgrounded**, and app **running**. The cold-start
case is the one that breaks: a link to a protected page arrives before you know whether the user
is logged in. Handle it by deferring the redirect decision until auth state resolves.

⚠️ **Never trust a deep-link parameter** — it's untrusted input from outside the app. Validate
IDs and re-check authorisation server-side ([../../Web/Django/security.md](../../Web/Django/security.md)).

---

## 5. Passing data & returning results

```dart
// ⭐ Constructor arguments — type-safe, the default choice
context.push('/detail', extra: product);          // go_router: any object, ⚠️ not web-safe

// Path/query params — ⭐ URL-safe, survives a cold start and web reload
'/product/:id?ref=email'
state.pathParameters['id'];  state.uri.queryParameters['ref'];

// Returning a result
final confirmed = await context.push<bool>('/confirm');
context.pop(true);
```

⭐ **Prefer an ID in the path over passing the whole object.** `extra` is lost on a web reload
or a cold-start deep link, and it encourages passing stale data. Pass the id, fetch from the
repository — the screen then works from any entry point.

---

## 6. Transitions & modals

```dart
CustomTransitionPage(                                // go_router custom animation
  child: const DetailScreen(),
  transitionsBuilder: (_, animation, __, child) =>
      FadeTransition(opacity: animation, child: child),
);

Hero(tag: 'product-$id', child: Image.network(url));  // ⭐ shared element between routes

showDialog(context: context, builder: ...);
showModalBottomSheet(context: context, builder: ...);
```

⚠️ **Dialogs are routes too** — they sit on the Navigator stack, so the system back button
dismisses them and `Navigator.pop` in a dialog closes the *dialog*, not the page. Use
`rootNavigator: true` when a dialog must escape a nested navigator.

⚠️ **Hero tags must be unique per screen** — duplicates throw at runtime.

---

## 7. Interview points

- **How does Flutter navigation work?** A `Navigator` manages a **stack of `Route`s** rendered
  in an `Overlay`; push/pop mutate the stack.
- **Navigator 1.0 vs 2.0? ⭐⭐** Imperative push/pop vs a declarative `pages` list derived from
  app state — 2.0 exists so deep links, browser back, and state restoration work, since the URL
  becomes the source of truth.
- **Why doesn't anyone use the raw Navigator 2.0 API?** `RouterDelegate` +
  `RouteInformationParser` is extremely verbose; packages like **go_router** wrap it.
- **`context.go` vs `context.push`? ⭐** `go` replaces the location and re-derives the stack;
  `push` adds a page on top. Confusing them breaks the back button.
- **Where do you put auth gating? ⭐** A single `redirect` in the router with a
  `refreshListenable` — not scattered checks in each screen.
- **How do you clear the stack after login?** `pushAndRemoveUntil` with `(route) => false`, or
  `context.go('/')` in go_router.
- **Custom scheme vs App/Universal Links? ⭐** Custom schemes are unverified and hijackable;
  HTTPS links are domain-verified and fall back to the web.
- **What breaks with deep links? ⭐** Cold start — the link arrives before auth/state is
  initialised. Defer the redirect until state resolves.
- **How should you pass data between screens?** An ID in the path plus a repository fetch —
  `extra`/objects don't survive web reloads or cold-start deep links.
- **How do you return a result from a screen?** `await Navigator.push<T>` and `pop(value)`.
- **What's the risk of using `context` after `await`?** The widget may be unmounted — guard with
  `context.mounted`.
