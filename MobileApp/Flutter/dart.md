# Dart — Language Essentials

> Widgets built on this: **[widgets.md](widgets.md)** · Futures/Streams in depth:
> **[async_streams.md](async_streams.md)**

---

## 1. Why Dart, and how it compiles ⭐⭐

**The answer interviewers want is about the two compilation modes:**

| Mode | Used in | Gives you |
|---|---|---|
| **JIT** (just-in-time) | ⭐ **debug** | **hot reload** — sub-second edit→see cycles |
| **AOT** (ahead-of-time) | ⭐ **release** | native ARM machine code — no interpreter, no bridge |

⭐ **This is Flutter's core performance argument.** React Native marshals calls across a
JavaScript bridge at runtime; Flutter compiles to native code and draws every pixel itself, so
there is no bridge to be the bottleneck. The same language gives you a fast dev loop *and* fast
releases.

Other reasons Dart fits: **sound null safety**, a single-threaded isolate model (no shared-memory
data races), fast object allocation with a generational GC tuned for **many short-lived
objects** — which is exactly what rebuilding widget trees produces.

⚠️ **Hot reload ≠ hot restart.** Hot reload injects new code and **keeps state**, but it does
**not** re-run `initState`, `main()`, or global initialisers, and it can't handle changed class
hierarchies or `const` values. When something "doesn't update," hot **restart** is the fix.

---

## 2. Null safety ⭐⭐

```dart
String name = 'flutter';      // ⭐ non-nullable — cannot ever be null
String? maybe;                // nullable
int len = maybe!.length;      // ⚠️ ! asserts non-null — THROWS if wrong
int len = maybe?.length ?? 0; // ⭐ safe: null-aware access + default
maybe ??= 'default';          // assign only if null
```

⭐ **"Sound" null safety means the *compiler* guarantees it** — if a variable's type is
`String`, no code path can put null in it, so the runtime doesn't need null checks at all. This
is why it also improves performance, not just safety.

⚠️⚠️ **`!` is the escape hatch that reintroduces crashes.** Every `!` is a promise you're making
to the compiler; a wrong one is a production `Null check operator used on a null value`. Prefer
`?.`, `??`, or an explicit `if (x != null)` — which **promotes** the type:

```dart
if (maybe != null) {
  print(maybe.length);        // ⭐ promoted to non-nullable String inside this block
}
```

⚠️ **Promotion doesn't work on class fields** (another isolate could change them between the
check and the use). Copy to a local first:

```dart
final m = widget.message;     // ⭐ local copy promotes; the field wouldn't
if (m != null) print(m.length);
```

**`late`** — non-nullable but initialised after declaration:

```dart
late final Database db;       // ⭐ common for initState / DI
```

⚠️ Reading a `late` variable before assignment throws `LateInitializationError`. Use it when you
*know* initialisation happens first (e.g. `initState`), not to silence the compiler.

---

## 3. Variables & immutability ⭐

```dart
var x = 5;                    // inferred, mutable
final list = [1, 2];          // ⭐ reference fixed at RUNTIME
const nums = [1, 2];          // ⭐⭐ COMPILE-TIME constant, deeply immutable
```

⭐⭐ **`final` vs `const` is asked constantly.** `final` means the *binding* can't be reassigned,
but the object can still mutate (`list.add(3)` is legal). `const` means the value is created at
**compile time**, is deeply immutable, and — crucially in Flutter — is **canonicalised**: two
identical `const` values are the *same object*.

```dart
final a = [1, 2];  a.add(3);  // ✅ allowed — the list itself is mutable
const b = [1, 2];  b.add(3);  // ❌ runtime error — unmodifiable
identical(const [1], const [1]);   // ⭐ true — same canonical instance
```

⭐ **That canonicalisation is why `const` widgets matter**: Flutter can skip rebuilding a
subtree when the widget instance is literally identical
([performance.md](performance.md)).

---

## 4. Functions

```dart
int add(int a, int b) => a + b;                        // arrow for a single expression

void greet(String name, {int age = 0, required String city}) {}   // ⭐ named params
greet('a', city: 'Dhaka');

void log(String msg, [String? tag]) {}                 // optional POSITIONAL

final onTap = (int i) => print(i);                     // closure
list.sort((a, b) => a.value.compareTo(b.value));
```

⭐ **Named parameters are the Flutter idiom** — widget constructors have many optional
arguments, and `Container(width: 10, height: 20)` is far clearer than positional order.
`required` enforces them at compile time.

**`typedef`** for callback types: `typedef OnChanged = void Function(String value);`

---

## 5. Classes ⭐

```dart
class User {
  final String name;
  final int age;

  const User({required this.name, this.age = 0});      // ⭐ const constructor
  User.guest() : name = 'Guest', age = 0;              // ⭐ named constructor

  factory User.fromJson(Map<String, dynamic> json) =>  // ⭐ factory — may return a cached
      User(name: json['name'], age: json['age'] ?? 0); //    or subclass instance

  User copyWith({String? name, int? age}) =>           // ⭐⭐ THE immutable-update idiom
      User(name: name ?? this.name, age: age ?? this.age);

  @override
  bool operator ==(Object other) =>
      other is User && other.name == name && other.age == age;

  @override
  int get hashCode => Object.hash(name, age);          // ⚠️ MUST match ==
}
```

⭐⭐ **`copyWith` is fundamental to Flutter state management.** Immutable state means new state
is a *new object*, which makes equality checks cheap and rebuilds predictable — every
Bloc/Riverpod state class has one.

⚠️ **Override `==` and `hashCode` together.** State classes compared only by reference will
always look "changed", causing rebuilds on every emit — or worse, `distinct()` on a stream
silently stops deduplicating.

⭐ **Use `freezed` or Dart 3 records** to generate `copyWith`/`==`/`hashCode` — hand-written
versions rot the moment someone adds a field.

**`factory` vs a normal constructor:** a factory isn't required to create a *new* instance — it
can return a cached one, a subclass, or throw. That's how singletons and `fromJson` polymorphism
are done.

---

## 6. Dart 3 features ⭐

```dart
// Records — lightweight multiple returns, no class needed
(String, int) getUser() => ('parvez', 30);
final (name, age) = getUser();                          // ⭐ destructuring

// Patterns & exhaustive switch
final msg = switch (status) {
  Status.loading => 'Loading…',
  Status.success => 'Done',
  Status.error   => 'Failed',                           // ⭐ compiler enforces exhaustiveness
};

// sealed classes — ⭐ the modern way to model state
sealed class Result<T> {}
class Success<T> extends Result<T> { final T data; Success(this.data); }
class Failure<T> extends Result<T> { final String message; Failure(this.message); }

final widget = switch (result) {
  Success(:final data) => ListView(children: data),     // ⭐ destructure in the pattern
  Failure(:final message) => ErrorView(message),
};
```

⭐⭐ **`sealed` + exhaustive `switch` is the state-modelling answer for modern Flutter.** The
compiler *fails the build* if you add a new state and forget a branch — which beats a
`if (isLoading) … else if (error != null) …` chain that silently renders nothing for an
unhandled combination.

---

## 7. Collections & the cascade

```dart
final doubled = [for (final x in nums) x * 2];          // ⭐ collection-for
final w = [
  const Header(),
  if (isLoggedIn) const Profile(),                      // ⭐⭐ collection-if — very idiomatic
  ...items.map(ItemTile.new),                           // ⭐ spread
  ...?maybeNullList,                                    // null-aware spread
];

nums.where((x) => x.isEven).map((x) => x * 2).toList();  // ⚠️ LAZY until toList()
nums.fold(0, (sum, x) => sum + x);
nums.firstWhere((x) => x > 3, orElse: () => -1);         // ⚠️ throws without orElse
```

⭐ **`collection-if` and spread inside widget lists** replace the `List<Widget> children = [];
children.add(...)` pattern — this is what idiomatic Flutter layout code looks like.

```dart
final p = Paint()                                        // ⭐ cascade — chain on one object
  ..color = Colors.red
  ..strokeWidth = 2;
```

⚠️ `map`/`where` return **lazy `Iterable`s**. Iterating twice re-runs the work; call `.toList()`
when you need a materialised, reusable result.

---

## 8. Async — the essentials

```dart
Future<User> fetchUser() async {
  final res = await http.get(uri);                       // suspends, doesn't block
  return User.fromJson(jsonDecode(res.body));
}

final results = await Future.wait([fetchA(), fetchB()]);  // ⭐ PARALLEL, not sequential

await for (final value in stream) { }                     // consume a stream
```

⭐ **`Future.wait` vs sequential `await`s** is the async equivalent of the N+1 question: two
sequential awaits of 300 ms cost 600 ms; `Future.wait` costs 300 ms. Full treatment in
[async_streams.md](async_streams.md).

⚠️ **`async` doesn't mean parallel** — Dart is single-threaded per isolate. `await` yields to the
event loop; CPU-heavy work still blocks the UI and needs an **isolate**.

---

## 9. Error handling

```dart
try {
  await risky();
} on SocketException catch (e) {          // ⭐ specific type first
  return Failure('No connection');
} on FormatException catch (e, stack) {   // ⭐ capture the stack trace
  logger.e('parse failed', e, stack);
  rethrow;                                // ⭐ rethrow preserves the original stack
} finally {
  cleanup();
}
```

⚠️ **`catch (e)` alone swallows the stack trace** — always take the second parameter when
logging. ⚠️ `throw` inside a catch block creates a *new* stack; use **`rethrow`**.

⭐ **Prefer returning a `Result`/`Either` type over throwing** for expected failures (no
network, validation) — it forces the caller to handle them, and pairs with `sealed` classes
above. Reserve exceptions for genuinely exceptional conditions.

---

## 10. Interview points

- **Why does Flutter use Dart? ⭐⭐** JIT for hot reload in development, AOT to native code for
  release — no JavaScript bridge — plus sound null safety and a GC tuned for short-lived objects.
- **`final` vs `const`? ⭐⭐** Runtime-fixed binding (object may still mutate) vs compile-time,
  deeply immutable, and **canonicalised** — which is what makes `const` widgets cheap.
- **What is sound null safety?** The compiler guarantees non-nullable types are never null, so
  no runtime checks are needed.
- **When is `!` acceptable?** Rarely — each one is an unchecked promise. Prefer `?.`, `??`, or a
  null check that promotes the type.
- **Why doesn't type promotion work on a field?** It could change between the check and the use;
  copy to a local.
- **What is `late` for, and its risk?** Deferred initialisation of a non-nullable variable;
  reading it early throws `LateInitializationError`.
- **What's a `factory` constructor?** One that isn't obliged to create a new instance — it can
  return a cached object or a subclass (`fromJson`, singletons).
- **Why `copyWith`? ⭐** Immutable state updates — new object, cheap equality checks,
  predictable rebuilds.
- **If you override `==`, what else must you do?** `hashCode` — mismatched implementations break
  sets, maps, and stream deduplication.
- **What do `sealed` classes give you? ⭐** Exhaustive `switch` — the compiler rejects a build
  that forgets a state, which is why they're the modern way to model UI state.
- **Is `async` parallel?** No — one isolate, one thread. `await` yields to the event loop;
  CPU-bound work needs an isolate.
- **Hot reload vs hot restart? ⭐** Reload injects code and preserves state but skips
  `initState`/`main`; restart rebuilds everything from scratch.
