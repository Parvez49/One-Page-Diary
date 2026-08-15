# Flutter — Interview Questions

> Claim first, then the *why*. Depth lives in the linked files.

---

## 1. Fundamentals

**Why Flutter, and how does it differ from React Native? ⭐⭐**
Flutter **draws every pixel itself** with its own rendering engine (Skia/Impeller) and compiles
Dart **AOT to native machine code**. React Native maps to native components across a JavaScript
bridge. Consequences: pixel-identical UI across platforms, no bridge bottleneck, full control of
rendering — at the cost of a larger binary (~7–8 MB floor) and non-native-by-default widgets.

**Why Dart? ⭐**
**JIT** in debug gives **hot reload**; **AOT** in release gives native performance. Plus sound
null safety and a GC tuned for the many short-lived objects widget rebuilds create.
→ [dart.md](dart.md)

**Hot reload vs hot restart? ⭐**
Reload injects new code and **keeps state**, but doesn't re-run `initState`/`main` or handle
changed class hierarchies. Restart rebuilds from scratch.

**`final` vs `const`? ⭐⭐**
`final` fixes the binding at runtime (the object may still mutate); `const` is compile-time,
deeply immutable, and **canonicalised** — which is what makes `const` widgets skip rebuilds.

---

## 2. Widgets & rendering

**Explain the three trees. ⭐⭐⭐**
**Widget** = immutable configuration, recreated constantly and cheap.
**Element** = the persistent instance that holds `State`, sits in the tree, and performs the
diff. **RenderObject** = layout, paint, hit testing — expensive.
Rebuilding widgets is cheap because Flutter matches new widgets to existing elements by
`runtimeType` + `key` and only re-lays-out RenderObjects that actually changed.
→ [widgets.md](widgets.md)

**Why are widgets immutable?**
They're disposable descriptions — cheap to recreate, and immutability makes diffing safe.

**Where does `State` live, and why? ⭐**
On the **Element**, not the widget — so it survives the parent recreating the widget.

**What does `setState` actually do?**
Marks the element dirty and **schedules** a rebuild for the next frame; it doesn't rebuild
synchronously.

**Walk through the State lifecycle. ⭐**
`createState` → `initState` (once) → `didChangeDependencies` (also on inherited changes) →
`build` (many times) → `didUpdateWidget` (new config from parent) → `dispose`.
⚠️ Don't read `Theme.of`/`MediaQuery.of` in `initState` — ancestors aren't wired yet.

**What's the most common memory leak? ⭐⭐**
Controllers, `StreamSubscription`s, and `Timer`s not disposed in `dispose()`.

**What are keys, and when do you need one? ⭐⭐**
They tell Flutter which element matches which widget when the tree changes. Required when
**reordering/inserting/removing stateful widgets of the same type** — without them Flutter
matches by position and type, so state attaches to the wrong item (the classic "wrong checkbox
ticked" bug).

**Explain Flutter's layout algorithm. ⭐⭐**
**Constraints go down, sizes go up, the parent sets position** — a single O(n) pass. A widget
never decides its own position.

**What causes "unbounded height" / RenderFlex overflow?**
A scrollable or flexible child inside an unbounded parent — fix with `Expanded`, a fixed size,
or `shrinkWrap`.

**What is `BuildContext`?**
The Element — a handle to a position in the tree, used to look **upward** for ancestors. That's
why `Scaffold.of(context)` fails when the context is *above* the Scaffold.

---

## 3. State management

**How would you choose a state-management approach? ⭐⭐**
Local UI state → `setState`. Shared state → a solution chosen by criteria: **Riverpod** for
compile-time safety and testability without `BuildContext`; **Bloc** when a large team or
event-driven domain justifies explicit, observable transitions; **Provider** on existing
codebases. What matters more than the package: **immutable state, logic outside widgets, and
scoped rebuilds**.
→ [state_management.md](state_management.md)

**How does `Provider`/`Theme.of` work under the hood? ⭐⭐**
`InheritedWidget` — an **O(1)** ancestor lookup that also **registers the element as a
dependent**, so only subscribers rebuild when `updateShouldNotify` returns true.

**Why does `MediaQuery.of(context)` cause extra rebuilds?**
It subscribes you to every MediaQuery change — keyboard, rotation. Use `MediaQuery.sizeOf`.

**`read` vs `watch` vs `select`? ⭐**
No subscription (use in callbacks) · full subscription (use in `build`) · subscription to one
derived value (performance).

**Bloc vs Cubit?**
Events in / states out (traceable, more boilerplate) vs methods in / states out (simpler).
Start with Cubit.

**Why must state be immutable? ⭐**
Cheap, correct equality checks → reliable change detection. Mutating in place can leave
listeners thinking nothing changed.

**How do you avoid rebuilding a whole page?**
Scope with `select`/`buildWhen`/`Consumer`, push state down, keep `const` subtrees, and extract
widgets so the rebuild boundary is small.

---

## 4. Async

**Is Dart multi-threaded? ⭐⭐**
No — **one thread per isolate** with an event loop. `async`/`await` gives **concurrency**
(interleaved waiting); **parallelism** requires isolates.

**Does `async` help CPU-bound work?**
No — `await` yields to the event loop, but a long synchronous loop still blocks the UI. Use
`compute`/an isolate.
→ [async_streams.md](async_streams.md)

**When do you need an isolate, and what does it cost? ⭐⭐**
CPU-bound work — large JSON parsing, image processing, encryption. Cost: spawn time, memory,
and **copied** messages, so sending huge data can exceed the computation.

**Why message passing instead of shared memory?**
No shared state means no locks, no races, no torn reads — an entire class of bugs eliminated.

**Future vs Stream? Single-subscription vs broadcast? ⭐**
One value later vs many over time. Single-subscription allows one listener ever and buffers;
broadcast allows many but **drops events emitted before subscribing**.

**What's wrong with `future: fetchUser()` inside `build`? ⭐⭐**
It re-fires on every rebuild — potentially an infinite refetch loop. Create the Future in
`initState` and store it.

**How do you run two requests concurrently?**
`Future.wait` — sequential `await`s sum their latencies.

---

## 5. Performance

**How do you diagnose jank? ⭐⭐**
Profile in **profile mode** (never debug — it's 2–10× slower and meaningless), then use DevTools
to determine whether the **UI (Dart)** thread or the **raster (GPU)** thread is over the ~16 ms
budget. The fixes are completely different: expensive builds/parsing vs shaders, opacity,
clipping, and images.
→ [performance.md](performance.md)

**Why does `const` improve performance? ⭐⭐**
Const widgets are canonicalised, so the diff sees an identical instance and skips rebuild,
layout, and paint for that subtree.

**Does splitting `build()` into private methods help?**
No — it's still the same widget's rebuild. Extract a **separate widget class**.

**`ListView` vs `ListView.builder`? ⭐**
Builds all children eagerly vs lazily building only visible items and recycling them.
`itemExtent` further removes measurement cost.

**Why do images cause OOM crashes? ⭐⭐**
Decoded size is `width × height × 4` bytes regardless of display size — a 4000×3000 photo is
~48 MB. Use `cacheWidth`/`cacheHeight`.

**When do you use `RepaintBoundary`?**
When a static subtree repaints alongside an animating neighbour — verified with "Highlight
repaints", not sprinkled everywhere (each costs a layer).

**What is shader jank and what fixed it?**
First-run shader compilation stutter — largely solved by **Impeller**, now the default engine.

---

## 6. Architecture, testing, release

**How do you structure a Flutter app? ⭐⭐**
Feature-first folders with presentation/domain/data layers, dependencies pointing inward, and
`domain/` containing **no Flutter imports** — the test that proves the layering is real.
→ [architecture.md](architecture.md)

**Why the repository pattern?**
It hides whether data comes from network, cache, or database, so the UI doesn't change when the
source does. Keep DTOs separate from domain entities.

**What's tricky about token refresh? ⭐**
Concurrent 401s trigger parallel refreshes — make it **single-flight** so one refresh serves all
waiters.

**Where do you store an auth token? ⭐⭐**
`flutter_secure_storage` (Keychain/Keystore) — **never `shared_preferences`**, which is a plain
file on a rooted device. And no API keys in the binary at all.

**`pump` vs `pumpAndSettle`? ⭐⭐**
One frame vs pumping until no frames are scheduled — ⚠️ `pumpAndSettle` **hangs forever** on an
infinite animation.
→ [testing.md](testing.md)

**What makes an app testable? ⭐**
Architecture — logic outside widgets and dependencies injected. Untestable code is a design
problem.

**How does Flutter call native code? ⭐⭐**
Platform channels (async message passing). **Rendering never crosses them** — Flutter draws its
own UI; channels are only for OS capabilities. Use **Pigeon** for type safety.
→ [platform_release.md](platform_release.md)

**How do you roll back a bad mobile release? ⭐⭐**
You can't. Halt the staged rollout, ship a hotfix, and rely on feature flags / a kill switch —
which is why staged rollout, crash monitoring, and a forced-update mechanism matter far more
than on the web.

**What breaks production crash reports?**
Obfuscation without uploaded symbol files.

---

## 7. Rapid fire

| Question | Answer |
|---|---|
| `StatelessWidget` vs `StatefulWidget` | No mutable state vs a `State` object on the Element. |
| `mainAxisAlignment` vs `crossAxisAlignment` | Along the scroll/flex direction vs perpendicular. |
| `Expanded` vs `Flexible` | Must fill remaining space vs may be smaller. |
| `Container` cost | ⚠️ Composes several widgets — prefer `Padding`/`DecoratedBox` + `const`. |
| `SizedBox` vs `Container` for spacing | ⭐ `const SizedBox` — cheaper and can be const. |
| `WidgetsBinding.addPostFrameCallback` | Run code after the first frame (context-safe work). |
| `mounted` check | ⭐ Guard `setState`/`context` after an `await`. |
| `UniqueKey()` | ⚠️ Always different → forces rebuild + **state loss**. Rarely correct. |
| `GlobalKey` cost | Expensive — for `Form`/`Scaffold` access, not routine use. |
| `Opacity` alternative | Omit the widget, or use a colour with alpha — `Opacity` forces a layer. |
| `shrinkWrap: true` | ⚠️ Measures all children — defeats lazy building. |
| Why `dispose()` | Cancel subscriptions/controllers — the top memory leak. |
| Web/desktop support | Same codebase; ⚠️ `Platform.isX` throws on web — check `kIsWeb` first. |
| App size floor | ~7–8 MB — the bundled engine. |
| `PopScope` | Handles the Android system back button (replaced `WillPopScope`). |

---

## 8. The five to have ready

1. **The three trees** — and why rebuilding widgets is cheap.
2. **Keys** — what breaks without them in a reorderable list.
3. **Constraints down, sizes up** — Flutter's whole layout model in one sentence.
4. **Isolates vs async** — concurrency is not parallelism in Dart.
5. **Profiling jank** — UI thread vs raster thread, in profile mode.
