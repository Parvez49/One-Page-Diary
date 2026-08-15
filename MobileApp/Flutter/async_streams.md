# Async — Futures, Streams & Isolates

> Dart basics: **[dart.md](dart.md)** · Jank & frames: **[performance.md](performance.md)**

---

## 1. The event loop ⭐⭐

**Dart is single-threaded per isolate.** One thread runs your code *and* the UI. Concurrency
comes from the **event loop**, not from threads.

```
        ┌──────────────┐
        │  Microtask   │  ⭐ ALWAYS drained completely first
        │    queue     │     (scheduleMicrotask, Future.value callbacks)
        └──────┬───────┘
               ▼
        ┌──────────────┐
        │  Event queue │  I/O, timers, gestures, Future.delayed
        └──────────────┘
```

⭐ **The rule: the microtask queue is drained to empty before *any* event is processed.** So an
infinite chain of microtasks starves the event loop entirely — the UI freezes and no gestures are
delivered. That's why you almost never use `scheduleMicrotask`.

⭐⭐ **`async`/`await` does not create a thread.** `await` *suspends the function* and returns
control to the event loop, letting other work run. It makes **waiting** concurrent, not
**computing**:

```dart
// ⚠️ This still freezes the UI for 3 seconds — async doesn't help CPU work
Future<int> sum() async {
  var total = 0;
  for (var i = 0; i < 1000000000; i++) total += i;    // never yields
  return total;
}
```

For CPU-bound work you need an **isolate** (§5). This distinction is the most commonly missed
point about Dart concurrency.

---

## 2. Futures ⭐

```dart
Future<User> fetch() async => User.fromJson(await api.get('/me'));

final user = await fetch();

// ⭐⭐ PARALLEL — total time = the slowest, not the sum
final [profile, orders] = await Future.wait([fetchProfile(), fetchOrders()]);

await Future.delayed(const Duration(seconds: 1));
final r = await fetch().timeout(const Duration(seconds: 10));   // ⭐ ALWAYS set a timeout
```

⚠️⚠️ **Sequential awaits are the mobile equivalent of an N+1 query:**

```dart
final a = await fetchA();     // 300 ms
final b = await fetchB();     // 300 ms  → 600 ms total ⚠️

final [a, b] = await Future.wait([fetchA(), fetchB()]);   // ⭐ 300 ms
```

Only sequence when the second call genuinely needs the first's result.

⚠️ **`Future.wait` fails fast** — one rejection discards the others' results. Use
`eagerError: false`, or wrap each future so it returns a `Result` instead of throwing.

⚠️ **An unawaited Future swallows its error** and surfaces as an unhandled async exception far
from the cause. Either `await` it, attach `.catchError`, or mark it explicitly with
`unawaited()` from `dart:async`.

**`FutureBuilder`:**

```dart
FutureBuilder<User>(
  future: _future,                       // ⭐⭐ from initState — NOT created inline
  builder: (context, snapshot) => switch (snapshot.connectionState) {
    ConnectionState.waiting => const CircularProgressIndicator(),
    _ when snapshot.hasError => ErrorView(snapshot.error!),
    _ => UserView(snapshot.data!),
  },
);
```

⚠️⚠️ **`future: fetchUser()` written inline re-fires the request on every rebuild** — an
infinite refetch loop if the result triggers a rebuild. Store the Future in a field, created in
`initState`. This is the single most common `FutureBuilder` bug.

---

## 3. Streams ⭐

**A Future is one value later; a Stream is many values over time.**

```dart
Stream<int> counter() async* {                  // ⭐ async* generator
  for (var i = 0; i < 5; i++) {
    await Future.delayed(const Duration(seconds: 1));
    yield i;                                    // ⭐ emit
  }
}

await for (final v in counter()) print(v);      // consume
final sub = stream.listen(onData, onError: ..., onDone: ...);
await sub.cancel();                             // ⭐⭐ MUST cancel — see below
```

| | **Single-subscription** (default) | **Broadcast** |
|---|---|---|
| Listeners | ⚠️ exactly **one**, ever | ⭐ many |
| Buffers before listen | yes | ⚠️ **no — events are lost** |
| Use | file/HTTP reads, one consumer | ⭐ app-wide events, multiple widgets |

⚠️⚠️ **"Bad state: Stream has already been listened to"** means two `StreamBuilder`s (or a
rebuild) subscribed to a single-subscription stream. Convert with `.asBroadcastStream()`, or
better, keep one subscription in your state layer and expose the data.

⚠️ **A broadcast stream drops events that occur before you subscribe** — late listeners miss
history. `BehaviorSubject` (rxdart) or a `ValueNotifier` replays the latest value.

```dart
stream
  .where((x) => x.isValid)
  .map((x) => x.value)
  .distinct()                                   // ⭐ needs correct == / hashCode
  .debounce(const Duration(milliseconds: 300))  // ⭐ rxdart — search-as-you-type
  .listen(...);
```

⭐ **Debounce is the canonical mobile use** — a search field that fires a request per keystroke
burns battery and rate limits; debouncing to 300 ms fixes it in one line.

**`StreamBuilder`:**

```dart
StreamBuilder<int>(
  stream: _stream,
  initialData: 0,                               // ⭐ avoids a null flash on first frame
  builder: (context, snapshot) { ... },
);
```

⚠️ Same trap as `FutureBuilder` — don't construct the stream inline in `build`.

⭐⭐ **`StreamController` must be closed and subscriptions cancelled in `dispose()`** — the
most common Flutter memory leak ([widgets.md §3](widgets.md)):

```dart
@override
void dispose() {
  _sub.cancel();
  _controller.close();
  super.dispose();
}
```

---

## 4. Handling async in the UI ⭐

```dart
// ⚠️ the wrong way — three loose fields that can contradict each other
bool isLoading = false; String? error; List<Item>? data;

// ⭐ one type, exhaustively handled
sealed class ItemsState {}
class Loading extends ItemsState {}
class Loaded extends ItemsState { final List<Item> items; Loaded(this.items); }
class Failed extends ItemsState { final String message; Failed(this.message); }
```

⭐ **Modelling async state as a sealed union makes impossible combinations unrepresentable**
(loading *and* error at once) and lets the compiler reject a missing branch. Riverpod's
`AsyncValue` is this pattern built in ([state_management.md](state_management.md)).

⚠️ **Always guard `setState`/`context` after an await:**

```dart
final data = await repo.fetch();
if (!mounted) return;                           // ⭐ widget may be gone
setState(() => _data = data);
```

⭐ **Cancel in-flight work when the widget dies** — an HTTP client with a `CancelToken` (dio) or
cancelling the subscription. Otherwise a slow response resolves into a disposed widget.

---

## 5. Isolates ⭐⭐

**For CPU-bound work.** Each isolate has its **own memory and event loop** — nothing is shared,
so there are no locks and no data races. Communication is by **message passing**, and messages
are **copied**.

```dart
// ⭐ compute() — the easy 90% case
final parsed = await compute(parseLargeJson, jsonString);

List<Item> parseLargeJson(String json) =>       // ⚠️ MUST be a top-level or static function
    (jsonDecode(json) as List).map(Item.fromJson).toList();
```

```dart
// Full control
final receivePort = ReceivePort();
await Isolate.spawn(worker, receivePort.sendPort);
```

⭐ **When you need one:** parsing a large JSON payload, image processing/decoding, encryption,
compression, complex sorting or filtering of thousands of records, database migrations.

⚠️ **When you *don't*:** network waiting, file I/O, and database queries are already
asynchronous — they don't block the thread, so an isolate adds cost for nothing.

⚠️⚠️ **Isolate costs are real:** spawning takes a few milliseconds and a couple of MB, and
**arguments and results are copied**, not shared. Sending a 50 MB list to an isolate can cost
more than the computation. `compute` is fine for a one-off; for repeated work use a long-lived
isolate or `Isolate.run` (Dart 2.19+).

⚠️ **The function must be top-level or static** — a closure capturing `this` can't be sent
across the isolate boundary.

⭐ **The senior framing:** *"Dart avoids shared-memory concurrency entirely. Isolates trade the
convenience of shared state for the elimination of an entire class of bugs — races, deadlocks,
torn reads — at the cost of copying messages."*

---

## 6. Frames & jank ⭐

The UI thread must produce a frame every **16.7 ms** (60 fps) or **8.3 ms** (120 Hz).

⚠️ **Anything synchronous on the UI isolate longer than one frame budget causes visible jank** —
`jsonDecode` of a large payload, a synchronous file read, a big `.sort()`, or building
thousands of widgets at once.

```dart
WidgetsBinding.instance.addPostFrameCallback((_) {
  // ⭐ runs AFTER the first frame — safe for context-dependent work, snackbars, scroll jumps
});
```

⭐ `SchedulerBinding` phases and `Timeline` events are what the DevTools performance overlay
visualises — see [performance.md](performance.md).

---

## 7. Interview points

- **Is Dart multi-threaded? ⭐⭐** No — one thread per isolate, with an event loop. Concurrency
  comes from `async`/`await`; **parallelism** requires isolates.
- **Does `async` make code run in parallel?** No — `await` suspends and yields to the event
  loop. CPU-bound work still blocks the UI.
- **Microtask vs event queue? ⭐** Microtasks are drained completely before any event; an
  endless microtask chain starves the UI.
- **How do you run two requests concurrently? ⭐** `Future.wait` — sequential awaits sum their
  latencies.
- **Future vs Stream?** One value later vs many values over time.
- **Single-subscription vs broadcast stream? ⭐** One listener ever (buffers) vs many listeners
  (⚠️ drops events emitted before subscribing).
- **Why does "Stream has already been listened to" happen?** Two subscribers to a
  single-subscription stream — usually a rebuild creating a second `StreamBuilder`.
- **What's wrong with `future: fetch()` inside `build`? ⭐⭐** It re-fires on every rebuild —
  create the Future in `initState` and store it.
- **When do you need an isolate? ⭐⭐** CPU-bound work only — JSON parsing, image processing,
  encryption. Network and file I/O are already async.
- **What's the cost of an isolate?** Spawn time, memory, and **copied** messages — sending large
  data can outweigh the computation.
- **How do isolates communicate, and why that design?** Message passing over ports with copied
  data — no shared memory means no locks and no data races.
- **What causes jank?** Any synchronous work exceeding the ~16 ms frame budget on the UI
  isolate.
- **How do you avoid leaking a stream?** Cancel subscriptions and close controllers in
  `dispose()`.
