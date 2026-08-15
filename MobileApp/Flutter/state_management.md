# State Management

> Widget rebuilds: **[widgets.md](widgets.md)** · Layering: **[architecture.md](architecture.md)**

---

## 1. What "state" means here ⭐

| Kind | Examples | Where it belongs |
|---|---|---|
| **Ephemeral / local UI** | animation progress, form field text, whether a panel is open | ⭐ **`setState` in the widget** |
| **App / shared** | logged-in user, cart, theme, cached feed | ⭐ a state-management solution |

⭐⭐ **The senior answer to "which state management should I use?" starts here:** most state is
ephemeral and doesn't need a library at all. Reaching for Bloc to track whether a dropdown is
open is over-engineering. Ask *"who else needs this, and does it outlive this widget?"*

---

## 2. The mechanism underneath: `InheritedWidget` ⭐⭐

**Every solution below is built on this.** It's how data propagates *down* the tree efficiently.

```dart
class UserScope extends InheritedWidget {
  final User user;
  const UserScope({super.key, required this.user, required super.child});

  static User of(BuildContext context) =>
      context.dependOnInheritedWidgetOfExactType<UserScope>()!.user;   // ⭐ SUBSCRIBES

  @override
  bool updateShouldNotify(UserScope old) => old.user != user;          // ⭐ rebuild gate
}
```

⭐⭐ **`dependOnInheritedWidgetOfExactType` does two things**: it finds the ancestor in
**O(1)** (elements keep a map of inherited ancestors — it isn't a tree walk), *and* it
**registers this element as a dependent**. When `updateShouldNotify` returns true, only the
registered dependents rebuild — not the whole subtree.

⚠️ **`Theme.of(context)` and `MediaQuery.of(context)` subscribe you.** A widget calling
`MediaQuery.of(context)` rebuilds on **every keyboard open/close and rotation** — a real and
frequently missed source of rebuilds. Use `MediaQuery.sizeOf(context)` (Flutter 3.10+) to depend
on one property only.

⚠️ Raw `InheritedWidget` is verbose and awkward to *update* (you need a StatefulWidget above it),
which is exactly the gap Provider fills.

---

## 3. The options ⭐⭐

| | **setState** | **Provider** | **Riverpod** | **BLoC / Cubit** | **GetX** | **signals** |
|---|---|---|---|---|---|---|
| Boilerplate | ⭐ none | low | low | ⚠️ **high** (Bloc) | ⭐ minimal | ⭐ low |
| Testability | poor | good | ⭐ **excellent** (no widget tree) | ⭐ **excellent** | ⚠️ weak | good |
| Compile-time safety | — | ⚠️ runtime `ProviderNotFoundException` | ⭐ **compile-time** | good | ⚠️ weak | good |
| Needs `BuildContext` | — | ⚠️ yes | ⭐ **no** | mostly | no | no |
| Scales to large apps | ❌ | ✅ | ⭐ ✅ | ⭐⭐ ✅ | ⚠️ contested | ✅ (newer) |
| Learning curve | ⭐ trivial | low | medium | ⚠️ **steep** | low | low |
| Team consensus | — | ⭐ safe default | ⭐ growing standard | ⭐ enterprise standard | ⚠️ divisive | emerging |

⭐⭐ **How to answer "which do you prefer?"** — with criteria, not a brand:

> *"Local UI state stays in `setState`. For shared state I default to **Riverpod** — it's
> compile-time safe, testable without a widget tree, and doesn't need `BuildContext`. For a
> large team or a complex event-driven domain I'd pick **Bloc**, because the explicit
> event→state contract and observability are worth the boilerplate. **Provider** is still a fine
> choice on an existing codebase. What matters more than the library is that state is
> **immutable**, business logic lives **outside widgets**, and rebuilds are **scoped**."*

That answer shows judgement; naming one library and dismissing the rest doesn't.

---

## 4. Provider

```dart
class CartModel extends ChangeNotifier {
  final _items = <Item>[];
  List<Item> get items => List.unmodifiable(_items);      // ⭐ expose immutably

  void add(Item i) {
    _items.add(i);
    notifyListeners();                                     // ⭐ triggers rebuilds
  }
}

ChangeNotifierProvider(create: (_) => CartModel(), child: const App());
```

```dart
context.watch<CartModel>().items          // ⭐ subscribes → rebuilds on change
context.read<CartModel>().add(item)       // ⭐⭐ NO subscription — use in callbacks
context.select<CartModel, int>((c) => c.items.length)   // ⭐ rebuild only when THIS changes

Consumer<CartModel>(builder: (_, cart, child) => ...)    // ⭐ scope the rebuild
```

⚠️⚠️ **`read` in `build` / `watch` in a callback** is the classic Provider bug. `watch` inside
`onPressed` throws; `read` inside `build` means your UI never updates.

⭐ **`select` is the performance tool** — without it, any change to the model rebuilds every
consumer, even ones that only display the item count.

⚠️ `ProviderNotFoundException` happens at **runtime** when the provider isn't above the widget
in the tree — precisely the class of error Riverpod eliminates.

---

## 5. Riverpod ⭐

```dart
final cartProvider = NotifierProvider<CartNotifier, List<Item>>(CartNotifier.new);

class CartNotifier extends Notifier<List<Item>> {
  @override
  List<Item> build() => [];

  void add(Item i) => state = [...state, i];              // ⭐ IMMUTABLE update
}

final totalProvider = Provider<double>((ref) =>           // ⭐ derived state, auto-cached
    ref.watch(cartProvider).fold(0.0, (s, i) => s + i.price));

final userProvider = FutureProvider<User>((ref) =>        // ⭐ async built in
    ref.watch(apiProvider).fetchUser());
```

```dart
class CartView extends ConsumerWidget {
  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final items = ref.watch(cartProvider);
    return ElevatedButton(
      onPressed: () => ref.read(cartProvider.notifier).add(item),
      child: Text('${items.length}'),
    );
  }
}
```

⭐ **What Riverpod fixes over Provider:** providers are **global objects, not tree nodes**, so
there's no `BuildContext` requirement and no runtime "not found" — a missing provider is a
compile error. It also gives **derived providers** that cache and invalidate automatically,
**`autoDispose`** for scoped cleanup, and **`overrideWith`** for trivially swapping fakes in
tests.

⭐ **`AsyncValue` handles all three states in one exhaustive switch**:

```dart
ref.watch(userProvider).when(
  data: (u) => Text(u.name),
  loading: () => const CircularProgressIndicator(),
  error: (e, st) => ErrorView(e),                          // ⭐ can't forget a case
);
```

---

## 6. BLoC / Cubit ⭐

**Cubit** — functions in, states out (simpler; start here):

```dart
class CounterCubit extends Cubit<int> {
  CounterCubit() : super(0);
  void increment() => emit(state + 1);                     // ⭐ emit a NEW state
}
```

**Bloc** — events in, states out (explicit, traceable):

```dart
sealed class CartEvent {}
class ItemAdded extends CartEvent { final Item item; ItemAdded(this.item); }

class CartBloc extends Bloc<CartEvent, CartState> {
  CartBloc(this._repo) : super(CartInitial()) {
    on<ItemAdded>((event, emit) async {
      emit(CartLoading());
      try {
        final cart = await _repo.add(event.item);
        emit(CartSuccess(cart));                           // ⭐ every transition is explicit
      } catch (e) {
        emit(CartFailure(e.toString()));
      }
    });
  }
}
```

```dart
BlocBuilder<CartBloc, CartState>(
  buildWhen: (prev, curr) => prev.items != curr.items,     // ⭐ scope rebuilds
  builder: (context, state) => switch (state) {            // ⭐ sealed → exhaustive
    CartLoading() => const CircularProgressIndicator(),
    CartSuccess(:final items) => ItemList(items),
    CartFailure(:final message) => ErrorView(message),
    _ => const SizedBox.shrink(),
  },
);
```

⭐ **`BlocListener` for side effects** (navigation, snackbars, dialogs) and `BlocBuilder` for UI
— ⚠️ **never navigate from inside `builder`**, which can run multiple times per frame.
`BlocConsumer` combines both.

⭐ **Bloc's real advantages in a large team:** every state change is an explicit, named,
loggable transition (`BlocObserver` gives you a free audit trail), the event→state contract is
testable without any widgets (`bloc_test`), and `sealed` states make impossible UI combinations
unrepresentable.

⚠️ **The cost is real boilerplate** — three files and a dozen classes for a feature that a Cubit
does in fifteen lines. Use Cubit unless you need the event trail.

---

## 7. Principles that outlive the library ⭐⭐

1. ⭐ **Immutable state.** New object, not mutation — cheap `==` checks, predictable rebuilds,
   and time-travel debugging. Use `copyWith`/`freezed` ([dart.md](dart.md)).
2. ⭐ **Business logic outside widgets.** A widget should read state and dispatch intent, nothing
   more. That's what makes logic unit-testable without pumping a widget tree.
3. ⭐⭐ **Scope rebuilds.** `select`, `buildWhen`, `Consumer` around the smallest subtree.
   Rebuilding an entire page on every keystroke is the most common performance complaint.
4. ⭐ **Model states explicitly** with a `sealed` class — `loading`/`data`/`error` as one type
   beats three loose booleans that can contradict each other.
5. ⭐ **Single source of truth.** The same data held in two places will diverge.
6. ⚠️ **Don't put state in a global singleton** to avoid learning the tool — it breaks tests,
   hot reload, and multi-window.

---

## 8. Interview points

- **What is state, and when does it need a library? ⭐** Ephemeral UI state belongs in
  `setState`; shared state that outlives one widget needs a solution.
- **How does `Provider`/`Theme.of(context)` actually work? ⭐⭐** `InheritedWidget` — O(1)
  ancestor lookup plus dependent registration, so only subscribers rebuild when
  `updateShouldNotify` returns true.
- **Why does `MediaQuery.of(context)` cause extra rebuilds?** It subscribes you to *every*
  MediaQuery change — keyboard, rotation. Use `sizeOf` to narrow it.
- **`context.read` vs `watch` vs `select`? ⭐** No subscription (callbacks) · full subscription
  (build) · subscription to one derived value (performance).
- **Provider vs Riverpod? ⭐** Riverpod removes the `BuildContext` dependency and converts
  runtime `ProviderNotFound` into a compile-time error, with built-in async/derived/autoDispose.
- **When is Bloc worth the boilerplate? ⭐⭐** Complex event-driven domains and larger teams —
  you get explicit, observable, testable transitions and exhaustive state handling.
- **Bloc vs Cubit?** Events in/states out (traceable, more code) vs methods in/states out
  (simpler). Start with Cubit.
- **Why must state be immutable?** Cheap equality → correct change detection; mutation in place
  can leave listeners thinking nothing changed.
- **How do you avoid rebuilding a whole page? ⭐** Scope with `select`/`buildWhen`/`Consumer`,
  keep `const` subtrees, and split widgets so the rebuild boundary is small.
- **Where do you handle navigation or a snackbar in Bloc?** `BlocListener` — never in `builder`,
  which can run several times per frame.
- **How would you choose for a new project?** By criteria — team size, domain complexity,
  testability requirements — and note that the architectural principles matter more than the
  package.
