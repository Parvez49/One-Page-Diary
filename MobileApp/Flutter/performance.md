# Performance & Rendering

> Three trees & layout: **[widgets.md](widgets.md)** · Isolates: **[async_streams.md](async_streams.md)**

---

## 1. The rendering pipeline ⭐⭐

```
setState / animation tick
   ↓
BUILD      widgets rebuilt (⭐ cheap — immutable config objects)
   ↓
LAYOUT     constraints down, sizes up (⭐ single O(n) pass)
   ↓
PAINT      RenderObjects draw into layers
   ↓
COMPOSITE  layers merged
   ↓
RASTER     ⭐ GPU turns layers into pixels (separate thread!)
```

⭐⭐ **Two threads matter, and telling them apart is the senior diagnostic skill:**

| Thread | Runs | Slow because of |
|---|---|---|
| **UI (Dart) thread** | build, layout, paint, your code | ⭐ expensive `build()`, JSON parsing, big loops |
| **Raster (GPU) thread** | rasterising layers | ⭐ shaders, opacity, clipping, blur, large images |

**Budget: 16.7 ms per frame at 60 fps, 8.3 ms at 120 Hz.** Miss it on *either* thread and the
user sees jank.

⭐ **DevTools shows both timelines separately** — that alone tells you whether to optimise your
Dart code or your visual effects. Fixing widget rebuilds won't help if the raster thread is
drowning in `BackdropFilter`.

---

## 2. Reduce rebuilds ⭐⭐

**The most common Flutter performance problem: rebuilding far more of the tree than necessary.**

```dart
// ⚠️ setState at the top rebuilds the ENTIRE page on every tick
class _PageState extends State<Page> {
  int _count = 0;
  @override
  Widget build(context) => Column(children: [
    const ExpensiveHeader(),          // rebuilt needlessly (⭐ unless const!)
    Text('$_count'),
    const ExpensiveFooter(),
  ]);
}
```

⭐⭐ **`const` is the cheapest optimisation in Flutter.** A `const` widget is **canonicalised** —
the same instance every time — so when Flutter diffs the tree it sees `identical(old, new)` and
**skips the subtree entirely**: no rebuild, no layout, no paint
([dart.md §3](dart.md)).

```dart
const SizedBox(height: 8)            // ⭐ free
const Text('Static label')
```

Enable the `prefer_const_constructors` lint and treat it as an error — it's free performance
across the whole app.

**Three techniques to scope a rebuild:**

```dart
// 1 ⭐ Push state DOWN — put setState in the smallest widget that needs it
// 2 ⭐ Use a builder that rebuilds only itself
ValueListenableBuilder<int>(valueListenable: _counter, builder: (_, v, child) => Text('$v'));

// 3 ⭐⭐ The `child` parameter — built ONCE, passed into every rebuild
AnimatedBuilder(
  animation: _controller,
  child: const ExpensiveWidget(),                    // ⭐ NOT rebuilt per frame
  builder: (context, child) => Transform.rotate(angle: _controller.value, child: child),
);
```

⭐ **The `child` escape hatch appears in `AnimatedBuilder`, `ValueListenableBuilder`,
`Consumer`, and `BlocBuilder`** — anything expensive that doesn't depend on the animating value
goes there and is built once. It's the highest-value trick in animation code.

⚠️ **Splitting a big `build()` into private *methods* (`_buildHeader()`) does not help** — the
result is still part of the same widget's rebuild. Extract into a **separate widget class** so it
gets its own element and can be `const` or skipped.

**Measuring:** DevTools **Performance → Track Widget Builds**, `debugPrintRebuildDirtyWidgets`,
or the rebuild-count overlay in the Inspector.

---

## 3. Lists ⭐

```dart
ListView.builder(                          // ⭐⭐ lazy — builds only visible items
  itemCount: items.length,
  itemExtent: 72,                          // ⭐ fixed height → skips measurement, big win
  itemBuilder: (context, i) => ItemTile(key: ValueKey(items[i].id), item: items[i]),
);
```

⚠️⚠️ **`ListView(children: [...])` builds every child up front.** With 10,000 rows that's 10,000
widgets before the first frame. Always `.builder` for anything long or unbounded
([widgets.md §6](widgets.md)).

⭐ **`itemExtent` (or `prototypeItem`) is an underrated win** — without it the list must measure
children to compute scroll extent; with it, scrolling and jumping are O(1).

⚠️ **`shrinkWrap: true` forces the list to measure *all* children**, defeating laziness. Use
`Expanded`, or a `CustomScrollView` with slivers when mixing scrollable content.

⭐ **`addAutomaticKeepAlives: false` / `addRepaintBoundaries: false`** for very simple rows;
`AutomaticKeepAliveClientMixin` when a row genuinely must retain state offscreen (⚠️ it defeats
recycling — use sparingly).

---

## 4. Images ⭐

```dart
Image.network(
  url,
  cacheWidth: 300,                         // ⭐⭐ DECODE at display size, not source size
  loadingBuilder: ...,
  errorBuilder: ...,
);

CachedNetworkImage(imageUrl: url, memCacheWidth: 300);   // ⭐ disk + memory cache
```

⚠️⚠️ **Images are the #1 memory problem in Flutter apps.** A 4000×3000 photo decodes to
**~48 MB in RAM** regardless of the 100×100 box you draw it in — the decoded bitmap is
`width × height × 4 bytes`. A grid of twenty such images will OOM on a mid-range Android device.
`cacheWidth`/`cacheHeight` decodes at the size you actually need.

⭐ **Ask the backend for correctly-sized images** (or use a thumbnail CDN). Downloading 4 MB to
display a 100 px avatar wastes bandwidth, battery, and memory.

⭐ Precache above-the-fold images: `precacheImage(NetworkImage(url), context)`.

---

## 5. Paint & raster cost ⭐

| Expensive | Cheaper alternative |
|---|---|
| ⚠️ **`Opacity`** | ⭐ `AnimatedOpacity` sparingly; better — omit the widget, or use a colour with alpha |
| ⚠️ **`ClipRRect` / `ClipPath`** | `BoxDecoration(borderRadius:)` — clipping forces a save layer |
| ⚠️ **`BackdropFilter` / blur** | ⭐ use once, over a small area — it's the most expensive common effect |
| ⚠️ Large `Stack` with overlaps | flatten the tree |
| Shadows on many widgets | precomputed images, or fewer elevation layers |

⭐ **`RepaintBoundary`** isolates a subtree into its own layer so a repaint doesn't propagate:

```dart
RepaintBoundary(child: ComplexStaticChart());     // ⭐ animation next to it won't repaint this
```

⚠️ **Don't scatter `RepaintBoundary` everywhere** — each one costs memory for its own layer.
Apply it where DevTools' **"Highlight repaints"** shows a static area flashing on every frame.

⭐ **Shader compilation jank** — the first run of an animation stutters while shaders compile.
Fix with SkSL warm-up or Impeller (⭐ now the default engine on iOS and Android, which
precompiles shaders and largely eliminates this class of jank).

---

## 6. Profiling ⭐⭐

```bash
flutter run --profile          # ⭐⭐ ALWAYS profile in PROFILE mode, never debug
flutter run --release
flutter build apk --analyze-size
```

⚠️⚠️ **Debug-mode performance is meaningless.** Assertions are on, the code is JIT-compiled, and
everything is 2–10× slower. Reporting "it's laggy" from a debug build is the classic junior
mistake — and profiling in debug will send you optimising the wrong thing.

**DevTools workflow:**

1. **Performance overlay** — two bars; ⭐ top = UI thread, bottom = raster. Which one is red?
2. **Timeline / frame chart** — find the frames over budget, expand to see what ran.
3. **Track Widget Builds** — which widgets rebuild, and how often.
4. **Highlight repaints** (Inspector) — flashing borders show unnecessary repaint areas.
5. **Memory view** — leaks and image cache size.
6. **CPU profiler** — where Dart time actually goes.

⭐ **Diagnose before optimising**: is the *UI* thread slow (your Dart code, builds, parsing) or
the *raster* thread (visual effects, images)? They have entirely different fixes.

---

## 7. App size ⭐

```bash
flutter build apk --split-per-abi        # ⭐ separate ARM/ARM64 builds
flutter build appbundle                  # ⭐⭐ AAB — Play Store delivers per-device slices
flutter build ipa
```

⭐ **Tree shaking removes unused Dart code and icon glyphs automatically**, but only in release
builds. Other levers: compress/convert images (WebP), audit dependencies (each package adds
weight), use deferred loading for rarely-used features on web, and check
`--analyze-size` output for surprises.

⚠️ A minimal Flutter APK is ~7–8 MB because it bundles the engine — that's the floor, and it's
a legitimate trade-off to acknowledge versus a native app.

---

## 8. The checklist ⭐

```
1. Profile in PROFILE mode          ⭐ never debug
2. Which thread is over budget?     UI (Dart) vs raster (GPU)
3. const everywhere                 free, enable the lint
4. ListView.builder + itemExtent    lazy, measured lists
5. Scope rebuilds                   push state down, use `child`, select/buildWhen
6. cacheWidth on images             ⭐⭐ the memory fix
7. Isolate heavy CPU work           compute() for JSON/images
8. RepaintBoundary where measured   not everywhere
9. Avoid Opacity/Clip/blur          in scrolling or animating content
10. Re-measure                      confirm the fix
```

---

## 9. Interview points

- **How do you diagnose jank? ⭐⭐** Profile mode, then DevTools: determine whether the **UI**
  or **raster** thread is over the 16 ms budget — the fixes are completely different.
- **Why never profile in debug mode?** Assertions plus JIT make it 2–10× slower; results are
  meaningless.
- **Why does `const` improve performance? ⭐⭐** Const widgets are canonicalised, so the diff
  sees an identical instance and skips rebuilding, laying out, and painting that subtree.
- **Does splitting `build()` into methods help?** No — it's the same widget's rebuild. Extract a
  separate widget class.
- **What's the `child` parameter in `AnimatedBuilder` for? ⭐** A subtree built once and reused
  every frame, instead of rebuilt on each animation tick.
- **`ListView` vs `ListView.builder`? ⭐** Eagerly builds all children vs lazily builds only
  visible ones and recycles them.
- **What does `itemExtent` do?** Tells the list the row height so it can skip measurement —
  O(1) scrolling and jumping.
- **Why is `shrinkWrap: true` a problem?** It measures every child, defeating lazy building.
- **Why do images cause OOM crashes? ⭐⭐** Decoded size is `w × h × 4` bytes regardless of
  display size — a 4000×3000 image is ~48 MB. Use `cacheWidth`/`cacheHeight`.
- **When do you use `RepaintBoundary`?** When a static subtree repaints alongside an animating
  neighbour — verify with "Highlight repaints" first, since each boundary costs memory.
- **Which widgets are expensive to paint?** `Opacity`, `ClipPath`, `BackdropFilter` — they force
  save layers.
- **What is shader jank, and what fixed it?** First-run shader compilation stutter — largely
  solved by **Impeller**, now the default engine.
- **How do you reduce app size?** App bundles / split-per-ABI, image compression, dependency
  audit, and `--analyze-size`.
