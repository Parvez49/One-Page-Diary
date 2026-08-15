# Flutter — Index

Domain knowledge for **senior mobile interviews** and production work. Assumes you can build
screens — the focus is on the rendering model, the traps that only appear on real devices, and
the answers that distinguish "I've shipped a Flutter app" from "I understand how Flutter works."

**Conventions:** ⭐ = high interview value · ⚠️ = a trap that causes real bugs ·
every file ends with an **Interview points** section. Examples target **Flutter 3.x / Dart 3**.

---

## Files

| File | Covers | Interview weight |
|---|---|---|
| [widgets.md](widgets.md) | ⭐⭐ **The three trees**, Stateless vs Stateful, **State lifecycle**, **keys**, **constraints-down/sizes-up**, `BuildContext` | ⭐⭐⭐ |
| [state_management.md](state_management.md) | `InheritedWidget` internals, **setState vs Provider vs Riverpod vs Bloc**, scoping rebuilds, immutable state | ⭐⭐⭐ |
| [async_streams.md](async_streams.md) | Event loop, Futures, **Streams**, **isolates**, `FutureBuilder` traps, jank | ⭐⭐⭐ |
| [performance.md](performance.md) | **UI vs raster thread**, `const`, lists, **image memory**, `RepaintBoundary`, DevTools, app size | ⭐⭐⭐ |
| [dart.md](dart.md) | **JIT/AOT**, null safety, **`final` vs `const`**, `copyWith`, **sealed classes**, records | ⭐⭐ |
| [architecture.md](architecture.md) | Layering, **repository pattern**, DI, networking & **token refresh**, **secure storage**, flavors | ⭐⭐⭐ |
| [navigation.md](navigation.md) | Navigator 1.0 vs **2.0**, **go_router**, auth redirects, **deep links** | ⭐⭐ |
| [testing.md](testing.md) | Unit/widget/golden/integration, **`pump` vs `pumpAndSettle`**, injecting fakes | ⭐⭐ |
| [platform_release.md](platform_release.md) | **Platform channels**, Pigeon, iOS/Android differences, **build & release**, staged rollout | ⭐⭐ |
| [interview.md](interview.md) | **Q&A across every topic** + rapid fire | ⭐⭐⭐ |

---

## Suggested study order

1. **[widgets.md](widgets.md)** — the three trees explain rebuilds, keys, performance, and half
   the other answers. Start here.
2. **[state_management.md](state_management.md)** — "which one do you use and why" is the most
   common senior discussion; answer with criteria, not a brand.
3. **[async_streams.md](async_streams.md)** — the isolate/async distinction separates people who
   read the docs from people who've fixed a frozen UI.
4. **[performance.md](performance.md)** — UI vs raster thread is the diagnostic skill.
5. **[dart.md](dart.md)** — `final`/`const` and sealed classes underpin everything above.
6. **[architecture.md](architecture.md)** — how you'd structure a real app, and where secrets go.
7. **[navigation.md](navigation.md)** + **[testing.md](testing.md)** — supporting depth.
8. **[platform_release.md](platform_release.md)** — shipping, which is where mobile differs most
   from web.
9. **[interview.md](interview.md)** — rehearse out loud the day before.

---

## The senior answers worth memorising

| Question | Short answer |
|---|---|
| The three trees ⭐⭐⭐ | Widget = immutable config · Element = persistent instance holding `State` · RenderObject = layout/paint. |
| Why are rebuilds cheap? | Widgets are throwaway objects; only changed RenderObjects re-layout. |
| Where does `State` live? | On the **Element** — that's why it survives parent rebuilds. |
| `final` vs `const` ⭐ | Runtime binding vs compile-time, deeply immutable, **canonicalised**. |
| Why `const` widgets? ⭐⭐ | Identical instance ⇒ the diff skips the subtree entirely. |
| When do you need keys? ⭐⭐ | Reordering/inserting/removing **stateful** widgets of the same type. |
| Layout in one sentence ⭐⭐ | Constraints go down, sizes go up, the parent positions. |
| Is Dart multi-threaded? ⭐⭐ | No — one thread per isolate. `async` = concurrency; isolates = parallelism. |
| When do you need an isolate? | CPU-bound work only — I/O is already async. |
| `future:` inside `build` ⭐ | Re-fires every rebuild — create it in `initState`. |
| Top memory leak ⭐ | Undisposed controllers, subscriptions, timers. |
| Image OOM ⭐⭐ | Decoded size is `w × h × 4` bytes — use `cacheWidth`. |
| Diagnosing jank ⭐⭐ | Profile mode; is the **UI** or **raster** thread over 16 ms? |
| Which state management? ⭐ | By criteria — the principles (immutable, logic outside widgets, scoped rebuilds) matter more. |
| How does `Theme.of` work? | `InheritedWidget` — O(1) lookup **plus** dependent registration. |
| Where does the auth token go? ⭐⭐ | `flutter_secure_storage`, never `shared_preferences`. |
| `pump` vs `pumpAndSettle` ⭐ | One frame vs until idle — ⚠️ hangs on infinite animations. |
| Rolling back a release ⭐ | You can't — staged rollout, feature flags, forced update. |

---

## Related directories

`../../Language/Python/` — the same depth for Python · `../../Web/NextJS/` &
`../../Web/Django/` — the frontend/backend this app talks to ·
`../../SDLC/` — architecture patterns and SOLID · `../../Algorithm/` — DSA ·
`../../CICD/` — pipelines · `../../CyberSecurity/` — mobile security context
