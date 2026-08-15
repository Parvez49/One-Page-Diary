# Widgets, Trees & Layout

> Dart foundations: **[dart.md](dart.md)** · Rebuild costs: **[performance.md](performance.md)**

---

## 1. The three trees ⭐⭐⭐

**The single most important Flutter concept, and the most common senior interview question.**

```
   Widget tree            Element tree            RenderObject tree
  (configuration)      (instance + lifecycle)      (layout & paint)
   ─────────────        ────────────────────       ──────────────────
   IMMUTABLE            MUTABLE, persistent        MUTABLE, expensive
   rebuilt constantly   ⭐ holds State             does the real work
   cheap to create      updated in place           layout / paint / hit-test
```

⭐⭐ **Widgets are not what's on screen.** A widget is a **lightweight, immutable
description** — a blueprint. Flutter throws away and recreates widgets on every build; that's
*designed* to be cheap.

The **Element** is the long-lived instance that sits between: it holds the `State` object, its
position in the tree, and a reference to the RenderObject. The **RenderObject** does the
expensive work — layout, painting, hit testing.

⭐ **Why this design is fast:** when you call `setState`, Flutter rebuilds widgets (cheap
objects) and then **diffs** them against the existing element tree. If a new widget has the
**same `runtimeType` and `key`** as the old one, Flutter *updates the existing element and
RenderObject in place* rather than recreating them. Only genuinely changed RenderObjects get
re-laid-out and repainted.

⚠️ **This is why "rebuild" isn't the same as "repaint".** A rebuild that produces an identical
widget configuration costs almost nothing downstream — which is the whole justification for
Flutter's rebuild-everything model.

---

## 2. StatelessWidget vs StatefulWidget ⭐

```dart
class Greeting extends StatelessWidget {
  final String name;
  const Greeting({super.key, required this.name});     // ⭐ const constructor

  @override
  Widget build(BuildContext context) => Text('Hi $name');
}
```

```dart
class Counter extends StatefulWidget {
  const Counter({super.key});
  @override
  State<Counter> createState() => _CounterState();
}

class _CounterState extends State<Counter> {
  int _count = 0;                                       // ⭐ survives rebuilds

  void _increment() => setState(() => _count++);        // ⭐ mark dirty → schedule rebuild

  @override
  Widget build(BuildContext context) =>
      TextButton(onPressed: _increment, child: Text('$_count'));
}
```

⭐⭐ **Why is `State` a separate class?** Because the **widget is immutable and disposable**,
while state must survive rebuilds. The `State` object lives on the **Element**, so the parent
can recreate the `Counter` widget a thousand times and `_count` persists.

⚠️ **`setState` doesn't rebuild immediately** — it marks the element dirty and schedules a
rebuild for the next frame. Calling it in a loop is not more expensive than calling it once.

⚠️ **Never call `setState` after `dispose`** (`setState() called after dispose()`) — a completed
async callback on an unmounted widget. Guard with `if (!mounted) return;`.

⚠️ **Never call `setState` inside `build`** — infinite loop.

---

## 3. State lifecycle ⭐

```
createState()
   ↓
initState()          ⭐ ONCE. Subscriptions, controllers, initial fetch.
   ↓                 ⚠️ context exists but has NO ancestor data yet
didChangeDependencies()   ⭐ after initState AND whenever an InheritedWidget changes
   ↓
build()              ⭐ may run MANY times per second — keep it pure and cheap
   ↕
didUpdateWidget(old) ⭐ parent rebuilt with new config → compare old.x vs widget.x
   ↓
deactivate()
   ↓
dispose()            ⭐⭐ ALWAYS cancel/close/dispose here
```

```dart
@override
void initState() {
  super.initState();                                    // ⚠️ call super FIRST
  _controller = AnimationController(vsync: this);
  _sub = stream.listen(_onData);
}

@override
void didUpdateWidget(covariant Counter old) {
  super.didUpdateWidget(old);
  if (old.userId != widget.userId) _refetch();          // ⭐ react to a changed prop
}

@override
void dispose() {
  _controller.dispose();
  _sub.cancel();                                        // ⭐⭐ THE memory-leak fix
  super.dispose();                                      // ⚠️ call super LAST
}
```

⚠️⚠️ **Undisposed controllers and stream subscriptions are the #1 Flutter memory leak.**
`AnimationController`, `TextEditingController`, `ScrollController`, `StreamSubscription`, and
`Timer` all need explicit cleanup — the GC can't collect them because the framework still holds
a reference.

⚠️ **Don't use `InheritedWidget` data (`Theme.of`, `MediaQuery.of`) in `initState`** — ancestors
aren't wired up yet. Use `didChangeDependencies`.

---

## 4. Keys ⭐⭐

**Keys tell Flutter which element corresponds to which widget when the tree changes.**

Without a key, Flutter matches old and new widgets **by position and type**. That's fine until
the *order* changes:

```dart
// ⚠️ Reordering a list of StatefulWidgets without keys → state attaches to the WRONG item
ListView(children: items.map((i) => TodoTile(i)).toList());

// ⭐ Correct
ListView(children: items.map((i) => TodoTile(key: ValueKey(i.id), item: i)).toList());
```

⭐⭐ **The classic symptom:** you delete the first item in a list of stateful tiles and the
*wrong* checkbox appears ticked, or a dismissed card reappears with another item's text. Because
type and position still match, Flutter reuses the element — and its state — for a different
item.

| Key | Use |
|---|---|
| **`ValueKey(id)`** | ⭐ list items with a stable identifier |
| `ObjectKey(obj)` | identity of a whole object |
| **`UniqueKey()`** | ⚠️ *always* different → forces a full rebuild + state loss. Rarely what you want |
| **`GlobalKey`** | ⭐ access state/context from elsewhere (`Form`, `Scaffold`) — ⚠️ expensive, avoid at scale |

⭐ **When do you need a key?** Only when **reordering, adding, or removing** *stateful* widgets
of the same type in a collection. Static layouts don't need them.

---

## 5. Layout — constraints go down, sizes go up ⭐⭐

**The one sentence that explains all Flutter layout:**

> **Constraints go down. Sizes go up. The parent sets the position.**

A parent passes a `BoxConstraints` (min/max width and height) to a child; the child picks its
size within those constraints and returns it; the parent then positions it. **A widget never
knows or decides its own position.**

⭐ **This is why layout is O(n) — a single pass, no multi-pass negotiation** (unlike web layout,
where a child can influence its parent's size in complicated ways).

⚠️⚠️ **The most common layout errors and what they mean:**

| Error | Cause | Fix |
|---|---|---|
| **"RenderBox was not laid out"** / unbounded height | ⭐ `ListView`/`Column` inside a `Column` — infinite height constraint | `Expanded`, `Flexible`, `SizedBox(height:)`, or `shrinkWrap: true` |
| **"A RenderFlex overflowed by N pixels"** | children exceed the available space | `Expanded`, `Flexible`, `SingleChildScrollView`, `FittedBox` |
| **Infinite width in a Row** | unbounded horizontal constraint | same family of fixes |

⭐ **`Expanded` vs `Flexible`:** `Expanded` *forces* the child to fill the remaining space;
`Flexible` *allows* it to be smaller. `Expanded` is `Flexible(fit: FlexFit.tight)`.

⚠️ **`shrinkWrap: true` makes a `ListView` measure all its children**, destroying the lazy
building that makes `ListView.builder` efficient. Use it only for genuinely short lists; prefer
`Expanded` or a `CustomScrollView` with slivers.

**Debugging layout:** `LayoutBuilder` to read the incoming constraints, `debugPaintSizeEnabled`,
and the **Flutter Inspector's Layout Explorer** — which visualises the constraints/size flow
directly.

---

## 6. Widgets worth knowing ⭐

| Category | Widgets |
|---|---|
| Layout | `Column` `Row` `Stack` `Expanded` `Flexible` `Wrap` `Align` `Padding` `SizedBox` |
| Boxes | `Container` (⭐ convenience wrapper), `DecoratedBox`, `ConstrainedBox` |
| Lists | ⭐ `ListView.builder` `GridView.builder` `CustomScrollView` + slivers |
| Conditional | `Visibility` `Opacity` `Offstage` `IndexedStack` |
| Reactive | ⭐ `FutureBuilder` `StreamBuilder` `ValueListenableBuilder` `AnimatedBuilder` |
| Structure | `Scaffold` `AppBar` `SafeArea` (⭐ notches), `MaterialApp` |

⭐⭐ **`ListView.builder` vs `ListView(children: [...])`** — the builder creates items **lazily,
only for what's visible**, and recycles them on scroll. A plain `ListView` with 10,000 children
builds all 10,000 widgets up front. Always use the builder for anything long or unbounded.

⚠️ **`Container` is not free** — it composes several widgets. Prefer `Padding`, `Align`, or
`DecoratedBox` when you need only one of its behaviours, and make them `const`.

⚠️ **`Opacity` is expensive** (it forces an offscreen layer). For show/hide, use `Visibility`
or simply omit the widget from the tree.

---

## 7. `BuildContext` ⭐

**A `BuildContext` *is* the Element** — a handle to this widget's location in the tree.

```dart
Theme.of(context)          // ⭐ walks UP the tree to the nearest ancestor of that type
MediaQuery.of(context)
Navigator.of(context)
```

⚠️⚠️ **The "wrong context" bug** — `Scaffold.of(context)` fails when called with the context of
the widget that *created* the `Scaffold`, because it looks **upward** and the Scaffold is below:

```dart
// ⚠️ Fails: this context is ABOVE the Scaffold
onPressed: () => ScaffoldMessenger.of(context).showSnackBar(...)

// ⭐ Fix: use a Builder to get a context BELOW the Scaffold, or a GlobalKey
Builder(builder: (innerContext) => IconButton(
  onPressed: () => ScaffoldMessenger.of(innerContext).showSnackBar(...),
))
```

⚠️ **Don't use a `BuildContext` across an `await`** — the widget may have been unmounted:

```dart
await save();
if (!context.mounted) return;                 // ⭐ Flutter 3.7+ guard
Navigator.of(context).pop();
```

---

## 8. Interview points

- **Explain the three trees. ⭐⭐⭐** Widgets are immutable configuration; Elements are the
  persistent instances holding `State` and doing the diff; RenderObjects do layout and painting.
  Rebuilding widgets is cheap because only changed RenderObjects are re-laid-out.
- **Why are widgets immutable?** They're throwaway descriptions — recreating them is cheap, and
  immutability makes diffing safe and predictable.
- **Where does `State` actually live? ⭐** On the Element, which is why it survives parent
  rebuilds that recreate the widget.
- **What does `setState` do?** Marks the element dirty and schedules a rebuild for the next
  frame — it doesn't rebuild synchronously.
- **When is `initState` vs `didChangeDependencies` vs `didUpdateWidget`? ⭐** Once at creation ·
  when inherited dependencies change (and after initState) · when the parent supplies new
  configuration.
- **What's the most common memory leak? ⭐⭐** Controllers, subscriptions, and timers not
  disposed in `dispose()`.
- **What are keys for, and when do you need one? ⭐⭐** To match widgets to elements when order
  changes — required for reordering/inserting/removing **stateful** widgets of the same type.
- **What happens without keys in a reorderable list?** Flutter matches by position and type, so
  state attaches to the wrong item.
- **Explain Flutter's layout algorithm. ⭐⭐** Constraints go down, sizes come up, the parent
  positions the child — a single O(n) pass.
- **What causes "unbounded height"?** A scrollable or flexible child inside an unbounded
  parent — fix with `Expanded`, a fixed size, or `shrinkWrap`.
- **`Expanded` vs `Flexible`?** Tight fit (must fill) vs loose fit (may be smaller).
- **Why `ListView.builder`? ⭐** It builds only visible items lazily and recycles them.
- **What is `BuildContext`?** The Element — a handle to the position in the tree, used to look
  **upward** for ancestors.
- **Why does `Scaffold.of(context)` sometimes fail?** The context is above the Scaffold; use a
  `Builder` or a `GlobalKey`.
