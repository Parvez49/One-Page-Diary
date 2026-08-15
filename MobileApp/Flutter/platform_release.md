# Platform Integration & Release

> Flavors & config: **[architecture.md §6](architecture.md)** · CI concepts:
> **[../../CICD/](../../CICD/)**

---

## 1. How Flutter reaches the platform ⭐⭐

```
   Dart code
      ↕  ⭐ Platform Channel (async, message passing over the engine)
   Kotlin/Java (Android)  ·  Swift/Obj-C (iOS)
      ↕
   OS APIs — camera, sensors, Bluetooth, biometrics
```

⭐⭐ **Flutter draws its own UI, so it never needs a bridge to render** — that's the core
difference from React Native. The channel is only for **capabilities the OS owns**: hardware,
system services, and native SDKs. Rendering never crosses it, which is why Flutter's
performance story doesn't depend on bridge throughput.

```dart
// Dart side
const channel = MethodChannel('com.example/battery');

Future<int> getBatteryLevel() async {
  try {
    return await channel.invokeMethod<int>('getBatteryLevel') ?? -1;
  } on PlatformException catch (e) {
    throw BatteryException(e.message);        // ⭐ translate to a domain error
  }
}
```

```kotlin
// Android side
MethodChannel(flutterEngine.dartExecutor.binaryMessenger, "com.example/battery")
  .setMethodCallHandler { call, result ->
    when (call.method) {
      "getBatteryLevel" -> result.success(batteryLevel)
      else -> result.notImplemented()
    }
  }
```

| Channel type | Direction | Use |
|---|---|---|
| **MethodChannel** | ⭐ Dart → native, one response | one-off calls |
| **EventChannel** | ⭐ native → Dart, a **stream** | sensors, location updates, BLE scans |
| **BasicMessageChannel** | both ways, custom codec | continuous messaging |
| **Pigeon** | ⭐⭐ **code-generated, type-safe** | production — eliminates string typos |

⭐ **Use `Pigeon` for anything non-trivial.** Hand-written channels pass method names as strings
and arguments as untyped maps — a rename on one side fails silently at runtime. Pigeon generates
matching Dart and Kotlin/Swift interfaces from one definition.

⚠️ **Channel calls are asynchronous and can fail** — the platform side may not be registered
yet, or may throw. Always handle `PlatformException` and `MissingPluginException` (⭐ the latter
usually means you need a **hot restart**, not a hot reload, after adding a plugin).

⚠️ **Channel calls are marshalled and cross a thread boundary** — don't call one per list item
in a scroll. Batch.

⭐ **Check pub.dev before writing a channel.** `camera`, `geolocator`, `local_auth`,
`connectivity_plus` already exist and are maintained. Write your own only for a proprietary SDK.

---

## 2. Platform differences ⭐

```dart
if (Platform.isIOS) ... else if (Platform.isAndroid) ...      // ⚠️ throws on web
if (kIsWeb) ...                                                // ⭐ check web FIRST
Theme.of(context).platform                                     // ⭐ testable/overridable
```

⭐ **`Theme.of(context).platform` over `Platform.isIOS`** — it can be overridden in tests and
respects `MaterialApp`'s platform setting.

| Concern | Difference |
|---|---|
| Back navigation | ⭐ Android has a **system back button/gesture**; iOS has swipe-from-edge only |
| Permissions | iOS asks **once** (⚠️ a denial is permanent until Settings); Android can re-prompt |
| Background work | ⚠️ iOS is far stricter — no reliable long-running background execution |
| Notifications | iOS requires explicit opt-in; Android 13+ now does too |
| App review | ⚠️ Apple reviews manually (days); Google is mostly automated (hours) |
| Storage | scoped storage on Android 11+; sandboxed on iOS |

⚠️⚠️ **The most common cross-platform mistake: assuming Android's back button works like iOS's
back arrow.** On Android it's a system-level gesture that can dismiss dialogs, pop routes, or
background the app. Handle it with `PopScope` (Flutter 3.16+; formerly `WillPopScope`) — for
example to confirm before discarding an edited form.

⭐ **Adaptive vs Cupertino/Material:** `.adaptive` constructors (`Switch.adaptive`) give
platform-appropriate controls. A full Cupertino UI on iOS doubles the work — most teams ship
Material everywhere and adapt only navigation transitions, dialogs, and switches.

---

## 3. Permissions

```dart
final status = await Permission.camera.request();     // permission_handler
if (status.isPermanentlyDenied) await openAppSettings();   // ⭐ the only recovery on iOS
```

⭐ **Request in context, not at launch.** Ask for the camera when the user taps "take photo" —
with a short explanation first. A cold permission wall on first launch is the single biggest
cause of permanent denials, and on iOS you cannot ask again.

⚠️ Declare purpose strings (`NSCameraUsageDescription`) in `Info.plist` and permissions in
`AndroidManifest.xml` — ⚠️ **App Store review rejects missing or vague purpose strings**.

---

## 4. Build & release ⭐

```bash
flutter build appbundle --release --flavor prod   # ⭐⭐ AAB for Play Store
flutter build apk --split-per-abi --release       # direct distribution
flutter build ipa --release                       # iOS → then Transporter/Xcode
```

**Versioning** — `pubspec.yaml`: `version: 1.4.2+87`
→ **`1.4.2`** is the user-visible name, **`87`** is the build number.
⚠️ **The build number must strictly increase** for every upload; both stores reject a reused
one.

**Signing:** ⚠️ **Never commit keystores or `.p12` files.** Store them in CI secrets. ⭐ Losing
an Android upload key means you cannot update the app under that listing without Google's key
reset — use **Play App Signing** so Google holds the app signing key.

**Obfuscation:**

```bash
flutter build apk --release --obfuscate --split-debug-info=build/symbols
```

⚠️⚠️ **Obfuscation makes crash reports unreadable unless you upload the symbol files.** Keep
`build/symbols` per release and upload to Sentry/Crashlytics as a build step — otherwise every
production stack trace is meaningless hex.

⭐ **Obfuscation is not security** — it raises the effort to reverse-engineer, nothing more. Any
secret in the binary is still extractable ([architecture.md §5](architecture.md)).

---

## 5. CI/CD ⭐

```yaml
# a realistic pipeline
- flutter analyze                    # ⭐ static analysis, fail on warnings
- dart format --set-exit-if-changed .
- flutter test --coverage            # unit + widget
- flutter build appbundle --release --dart-define-from-file=env/prod.json
- upload symbols → Sentry
- deploy → Play internal track / TestFlight
```

⭐ **Fastlane** (or **Codemagic**/**Bitrise**) automates the store upload — the manual path
involves certificates, provisioning profiles, and Xcode, all of which break at the worst time.
⚠️ iOS builds require **macOS runners**, which is a real cost and scheduling constraint.

⭐ **Staged rollout** (Play: 5% → 20% → 100%; iOS phased release) with crash-rate monitoring —
because unlike a web deploy, **you cannot roll back an app release**. Users who updated are
updated. Halting a rollout is the only lever, which is why staged release and a **remote kill
switch / feature flag** matter far more on mobile than on the web.

⭐ **Ship a forced-update mechanism early** — a minimum supported version checked at launch. You
will eventually need to retire a broken client version, and without it you can't.

---

## 6. Post-release ⭐

- ⭐⭐ **Crash reporting with symbolication** (Sentry/Crashlytics) from day one — you can't
  attach a debugger to a user's device; the stack trace is all you get.
- ⭐ **Watch crash-free-users rate** (aim >99.5%) and ANR rate on Android, per version.
- **Analytics behind an interface** so it's swappable and mockable.
- ⭐ **Test on low-end real devices** — emulators hide jank, thermal throttling, and OEM-specific
  bugs, which dominate real Android crash reports.
- ⚠️ **OEM fragmentation is an Android reality**: aggressive battery managers (Xiaomi, Huawei,
  Samsung) kill background work and delay notifications regardless of what your code does.

---

## 7. Interview points

- **How does Flutter talk to native code? ⭐⭐** Platform channels — async message passing.
  Rendering never crosses it, since Flutter draws its own UI; the channel is only for OS
  capabilities.
- **MethodChannel vs EventChannel?** One call/one response vs a continuous native → Dart stream
  (sensors, location).
- **Why use Pigeon? ⭐** It generates type-safe interfaces on both sides, removing stringly-typed
  method names and untyped argument maps.
- **What is `MissingPluginException` usually?** A plugin added without a **hot restart** (or a
  missing platform implementation).
- **Biggest Android/iOS behavioural differences? ⭐** The system back button, permission
  re-prompting (iOS denies permanently), background execution limits, and review turnaround.
- **How do you handle the Android back button?** `PopScope` — e.g. confirm before discarding
  unsaved changes.
- **When should you request permissions? ⭐** In context, at the moment of use, with an
  explanation — a launch-time wall causes permanent denials.
- **APK vs AAB?** AAB lets the store deliver device-specific slices — smaller downloads and the
  required format for new Play submissions.
- **What breaks crash reports? ⭐⭐** Obfuscation without uploaded symbol files.
- **Is obfuscation security?** No — it raises reverse-engineering effort; secrets in the binary
  remain extractable.
- **How do you roll back a bad mobile release? ⭐** You can't. Halt the staged rollout, ship a
  hotfix, and rely on feature flags or a kill switch — which is why staged rollout and forced
  update are essential.
- **Why test on real low-end devices?** Emulators hide thermal throttling, jank, and OEM
  battery-manager behaviour that causes most field failures.
