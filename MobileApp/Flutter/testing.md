# Testing

> Strategy: **[../../SDLC/testing.md](../../SDLC/testing.md)** · Injecting fakes:
> **[architecture.md §3](architecture.md)**

---

## 1. The three levels ⭐

| Type | Tests | Speed | Where the value is |
|---|---|---|---|
| **Unit** | pure logic, blocs, repositories, utils | ⭐ ms | ⭐⭐ most of your tests |
| **Widget** | one widget/screen in a test harness | ~100 ms | ⭐ rendering, interaction, state wiring |
| **Integration (E2E)** | the real app on a device/emulator | ⚠️ minutes | a few critical flows only |
| **Golden** | pixel comparison against a reference PNG | fast | ⭐ design systems, visual regressions |

⭐ **The Flutter-specific point: widget tests are unusually cheap.** `flutter_test` runs them
headless with a fake clock and no device, so they're closer to unit-test speed than to
Selenium. That makes a *wider* middle layer viable than the classic pyramid suggests — many
teams sit closer to a "testing trophy" with widget tests as the bulk.

⭐⭐ **Architecture determines testability.** If business logic lives in widgets and repositories
are constructed inline, you *cannot* unit test — you're forced into slow, flaky integration
tests. Testability is an architecture outcome, not a testing-effort outcome.

---

## 2. Unit tests

```dart
void main() {
  group('CartBloc', () {
    late MockCartRepository repo;

    setUp(() => repo = MockCartRepository());          // ⭐ fresh per test

    blocTest<CartBloc, CartState>(
      'emits [Loading, Success] when an item is added',
      build: () {
        when(() => repo.add(any())).thenAnswer((_) async => testCart);
        return CartBloc(repo);
      },
      act: (bloc) => bloc.add(ItemAdded(testItem)),
      expect: () => [isA<CartLoading>(), isA<CartSuccess>()],   // ⭐ the state sequence
      verify: (_) => verify(() => repo.add(testItem)).called(1),
    );
  });
}
```

⭐ **`bloc_test` asserts the *sequence* of emitted states** — which is exactly the contract a
Bloc promises. Riverpod's equivalent is a `ProviderContainer` with `overrides`.

**Mocking:** `mocktail` (⭐ no codegen, null-safe) or `mockito` (needs `build_runner`).

⭐ **Mock at the boundary only** — HTTP clients, platform plugins, clocks. Mocking your own
repository *interface* is right; mocking a value object or a widget is not.

---

## 3. Widget tests ⭐

```dart
testWidgets('shows items and handles tap', (tester) async {
  await tester.pumpWidget(
    ProviderScope(
      overrides: [repoProvider.overrideWithValue(FakeRepo())],   // ⭐ inject a fake
      child: const MaterialApp(home: CartScreen()),              // ⚠️ MaterialApp needed
    ),
  );

  await tester.pumpAndSettle();                    // ⭐ run until no frames are scheduled

  expect(find.text('Widget A'), findsOneWidget);
  expect(find.byType(CircularProgressIndicator), findsNothing);

  await tester.tap(find.byKey(const Key('add-button')));
  await tester.pump();                             // ⭐ ONE frame — process the setState

  expect(find.text('1 item'), findsOneWidget);
});
```

⭐⭐ **`pump()` vs `pumpAndSettle()` is the classic widget-test question.**
`pump()` advances **exactly one frame**; `pumpAndSettle()` pumps repeatedly until no frames are
scheduled. ⚠️ **`pumpAndSettle` hangs forever on an infinite animation** (a spinner, a repeating
`AnimationController`) — use `pump(Duration(...))` there instead.

⚠️ **Missing wrapper widgets are the most common failure.** A widget using `Theme.of`,
`Navigator`, or `MediaQuery` throws unless wrapped in `MaterialApp`. Write a `pumpApp()` helper
so every test gets a consistent harness.

**Finders and actions:**

```dart
find.text('x')  find.byType(Button)  find.byKey(k)  find.byIcon(Icons.add)
find.descendant(of: find.byType(Card), matching: find.text('x'))

await tester.enterText(find.byType(TextField), 'hello');
await tester.drag(find.byType(ListView), const Offset(0, -300));
await tester.longPress(finder);
```

⭐ **Add `Key`s to the elements you test** — `find.text('Save')` breaks the moment the copy
changes or is localised; `find.byKey(const Key('save-btn'))` doesn't.

⚠️ **The test surface is 800×600 by default** — off-screen widgets aren't found. `scrollUntilVisible`,
or set `tester.view.physicalSize`.

⚠️ **A real HTTP call in a widget test returns 400** — `flutter_test` installs a mock
`HttpClient`. Inject a fake client rather than fighting it.

---

## 4. Golden tests ⭐

```dart
testWidgets('button matches golden', (tester) async {
  await tester.pumpWidget(pumpApp(const PrimaryButton(label: 'Save')));
  await expectLater(find.byType(PrimaryButton),
      matchesGoldenFile('goldens/primary_button.png'));
});
```

```bash
flutter test --update-goldens        # ⭐ regenerate after an intentional change
```

⭐ **Golden tests catch visual regressions that assertions never will** — a padding change, a
wrong colour token, a broken dark theme. They're the reason design-system work is safe to
refactor.

⚠️⚠️ **Goldens are famously flaky across platforms** — font rendering differs between macOS,
Linux, and CI, so a golden generated on a laptop fails in CI. Fix by generating them **in CI or
Docker only**, or use `alchemist`/`golden_toolkit`, which handle font loading and platform
normalisation.

---

## 5. Integration tests

```dart
// integration_test/app_test.dart
void main() {
  IntegrationTestWidgetsFlutterBinding.ensureInitialized();

  testWidgets('login → browse → checkout', (tester) async {
    app.main();
    await tester.pumpAndSettle();

    await tester.enterText(find.byKey(const Key('email')), 'a@b.com');
    await tester.tap(find.byKey(const Key('login')));
    await tester.pumpAndSettle();

    expect(find.byType(HomeScreen), findsOneWidget);
  });
}
```

```bash
flutter test integration_test/            # on a device/emulator
```

⭐ **Keep these few and critical** — login, purchase, the one flow whose breakage means
revenue loss. They're slow, need real devices, and break for environmental reasons.

⚠️ **Point them at a dedicated test backend**, not production, and seed deterministic data.
An E2E suite that fails because someone changed staging data teaches the team to ignore red
builds.

⭐ **Firebase Test Lab / BrowserStack** for real-device matrices — emulator-only testing misses
OEM-specific bugs, which are the majority of Android field crashes.

---

## 6. Practices ⭐

```dart
// ⭐ a shared harness — write this once
Widget pumpApp(Widget child, {List<Override> overrides = const []}) =>
    ProviderScope(
      overrides: overrides,
      child: MaterialApp(theme: appTheme, home: child),
    );
```

- ⭐ **Test behaviour, not implementation.** Assert what the user sees, not that a private
  method ran — otherwise every refactor breaks the suite and people stop trusting it.
- ⭐ **Test the failure paths**: empty list, network error, permission denied, offline. That's
  where mobile bugs actually live, and where coverage is usually absent.
- **`FakeAsync` / `fakeAsync`** to control time — never `sleep` in a test.
- **A regression test per fixed bug** — cheap insurance.
- ⚠️ **Flaky tests are a bug.** Usual causes: real timers, real network, `pumpAndSettle` on an
  infinite animation, and shared state between tests.
- ⚠️ **Coverage is a floor, not a goal** — 90% coverage with no assertions on error paths is
  worse than 70% that covers them.

```bash
flutter test --coverage && genhtml coverage/lcov.info -o coverage/html
flutter analyze                              # ⭐ static analysis in CI
dart format --set-exit-if-changed .
```

---

## 7. Interview points

- **What do you test in a Flutter app? ⭐** Mostly unit tests for logic and blocs, a broad layer
  of widget tests (they're cheap and headless), and a handful of integration tests for critical
  flows.
- **Why are widget tests unusually valuable in Flutter?** They run headless with a fake clock —
  near unit-test speed while exercising real rendering and interaction.
- **`pump` vs `pumpAndSettle`? ⭐⭐** One frame vs pump until no frames are scheduled —
  ⚠️ `pumpAndSettle` hangs on infinite animations.
- **Why does my widget test throw about `Theme`/`Navigator`?** It needs a `MaterialApp` wrapper
  — use a shared `pumpApp` helper.
- **How do you inject a fake repository? ⭐** Constructor injection, `ProviderScope(overrides:)`
  in Riverpod, or a `BlocProvider` with a mock — which is why DI exists.
- **What should you mock?** External boundaries only — HTTP, platform channels, clocks. Not your
  own value objects or widgets.
- **What are golden tests, and their weakness? ⭐** Pixel comparison for visual regressions;
  ⚠️ platform font rendering makes them flaky unless generated in a fixed environment.
- **Why keep integration tests few?** Slow, device-dependent, and environmentally flaky —
  reserve them for revenue-critical flows.
- **How do you make a test deterministic?** Fake clock, fake network, fresh state per test, and
  keys instead of text finders.
- **What makes an app testable? ⭐⭐** Architecture — logic outside widgets and dependencies
  injected. Untestable code is a design problem, not a testing problem.
