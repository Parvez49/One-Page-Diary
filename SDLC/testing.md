# Software Testing

> Two independent questions, often confused:
> **1. How much do you know about the internals?** → black / white / grey box
> **2. What level are you testing at?** → unit / integration / system / acceptance
>
> These are **different axes**, not a single list.

---

## 1. Black Box vs White Box vs Grey Box ⭐

| | **Black Box** | **White Box** | **Grey Box** |
|---|---|---|---|
| Knowledge of code | **None** — sees only inputs/outputs | **Full** — code, data structures, internal design | **Partial** — knows architecture/DB, not every line |
| Tests | *What* the software does (behaviour vs requirements) | *How* it does it (paths, branches, logic) | Both |
| Who | QA, end users | Developers | QA with system knowledge |
| Basis | Requirements & specifications | Source code | Architecture, DB schema, API contracts |
| Finds | Missing/wrong features, usability issues | Logic errors, dead code, uncovered branches | Integration & data-flow issues |
| Misses | Hidden paths, untested branches | Missing requirements (can't test what was never written) | — |
| Coverage measure | Requirements coverage | **Code coverage** (statement/branch/path) | Mixed |
| Example | "Enter a wrong password 5× → account locks" | "Assert the `else` branch of the lockout counter executes" | "Check the DB row is actually written after checkout" |

**White box techniques:** statement coverage, branch/decision coverage, path coverage,
condition coverage, loop testing, control-flow & data-flow analysis.

**Black box techniques:**
- **Equivalence Partitioning** — age 18–65 valid → test one value from `<18`, `18–65`, `>65`.
- **Boundary Value Analysis** ⭐ — bugs hide at edges: test `17, 18, 19 … 64, 65, 66`.
- **Decision Table** — all combinations of conditions.
- **State Transition** — legal/illegal status changes.
- **Error Guessing** — experience-driven (empty string, `null`, emoji, `0`, negative, huge input).

> ⚠️ **Clarifying a common confusion:** *Unit, Regression, Functional, Non-functional* are
> **test types/levels**, not exclusively black or white box. The same type can be done either way:
> - **Unit testing** → usually **white box** (the dev knows the code).
> - **Functional testing** → usually **black box** (driven by requirements).
> - **Regression testing** → **either** — re-running unit tests (white) *and* UI/API suites (black).
> - **Non-functional (performance/security)** → **either** — load testing via the UI (black) or
>   profiling the code (white).
>
> So "Regression appears under both" is correct — but the reason is that **regression describes
> *why* you run a test (to catch breakage from a change), not *how* you designed it**.

---

## 2. The Test Pyramid ⭐

```
              ╱╲            E2E / UI          — few, slow, brittle, expensive
             ╱  ╲           (5–10%)             but highest confidence
            ╱────╲
           ╱      ╲         Integration       — some, medium speed
          ╱        ╲        (15–30%)            tests the wiring
         ╱──────────╲
        ╱            ╲      Unit              — many, fast (ms), cheap
       ╱______________╲     (60–70%)            pinpoint failures
```

| Level | Scope | Speed | When it fails you know… |
|---|---|---|---|
| **Unit** | One function/class, dependencies mocked | ms | …exactly which function broke |
| **Integration** | Several components together (service + real DB, API + cache) | seconds | …the wiring/contract broke |
| **System / E2E** | Whole app through the real UI/API | minutes | …something, somewhere broke |
| **Acceptance / UAT** | Business validates against real needs | — | …you built the wrong thing |

**⚠️ Anti-patterns:**
- **Ice-cream cone** (inverted pyramid) — mostly manual/E2E tests. Slow suites, flaky builds,
  and a failure tells you nothing about *where* the bug is.
- **Hourglass** — many unit + many E2E, no integration. Modules each work but don't fit together.

---

## 3. Functional vs Non-Functional Testing

### Functional — *does it do the right thing?*
| Type | Purpose |
|---|---|
| **Unit** | Individual functions in isolation |
| **Integration** | Modules working together |
| **System** | The complete integrated product |
| **Smoke** | "Is the build even worth testing?" — a few critical paths, run first |
| **Sanity** | Narrow, deep check that one specific fix works after a small change |
| **Regression** | Did the new change break existing features? |
| **UAT** | End users validate against business needs — **Alpha** (internal) / **Beta** (real users) |

> **Smoke vs Sanity:** Smoke = **wide and shallow** (does the app start, can you log in?),
> run on every build. Sanity = **narrow and deep** (does the discount bug fix actually work?),
> run after a targeted change.

> **Verification vs Validation:** Verification = *"are we building the product **right**?"*
> (reviews, static analysis, unit tests). Validation = *"are we building the **right** product?"* (UAT).

### Non-Functional — *how well does it do it?*
| Type | Question |
|---|---|
| **Performance** | Response time & throughput under expected load |
| **Load** | Behaviour at expected peak |
| **Stress** | Where does it break, and does it fail *gracefully*? |
| **Spike** | Sudden 10× traffic burst |
| **Soak / Endurance** | Run for 48 h — reveals **memory leaks** and connection exhaustion |
| **Scalability** | Does adding servers actually increase capacity? |
| **Security** | Penetration testing, vulnerability scanning, auth/authz checks |
| **Usability** | Can real users complete the task? |
| **Compatibility** | Browsers, devices, OS versions |
| **Reliability / Recovery** | Failover, backup restore, disaster recovery drills |
| **Accessibility** | WCAG, screen readers, keyboard-only navigation |

---

## 4. TDD, BDD, ATDD

### TDD — Test-Driven Development
```
🔴 RED  ──▶  🟢 GREEN  ──▶  🔵 REFACTOR  ──▶ (repeat)
Write a      Write the        Clean up with
failing      simplest code    tests as a
test         to pass it       safety net
```

```python
# 1️⃣ RED — write the test first
def test_discount_applies_10_percent_over_100():
    assert apply_discount(200) == 180

# 2️⃣ GREEN — simplest thing that passes
def apply_discount(total):
    return total * 0.9 if total > 100 else total

# 3️⃣ REFACTOR — extract the rate, add edge cases, tests keep you safe
```

**✅ Advantages:** forces testable design (naturally pushes you toward **DIP**/loose coupling);
100% of new code is covered; tests document intent; refactoring becomes safe; catches bugs at
the cheapest moment; you clarify requirements before coding.

**❌ Drawbacks:** slower initially (real cost, real pushback); useless if you write bad tests;
hard for UI, exploratory work and spikes; **tests coupled to implementation** become a change
tax — every refactor breaks 40 tests; requires genuine discipline, so teams often abandon it
under deadline pressure.

### BDD — Behaviour-Driven Development
TDD expressed in **business language** so non-developers can read and write specs (Cucumber, `pytest-bdd`).

```gherkin
Feature: Checkout discount
  Scenario: Order above the discount threshold
    Given a cart with a total of 200
    When the customer checks out
    Then a 10% discount is applied
    And the final total is 180
```
**✅ Pros:** shared vocabulary between business/QA/dev; living documentation; focuses on
behaviour not implementation.
**❌ Cons:** heavy tooling & step-definition maintenance; often only devs actually read them,
making the overhead pure cost; slow to run.

**ATDD** — Acceptance-Test-Driven Development: the whole team agrees acceptance tests *before*
development starts.

---

## 5. Test Doubles (Mocks & friends) ⭐

| Double | What it does | Example |
|---|---|---|
| **Dummy** | Passed but never used, just fills a parameter | `None` for an unused arg |
| **Stub** | Returns hard-coded answers | `get_rate()` always returns `1.15` |
| **Spy** | A stub that also **records** how it was called | Assert `send_email` was called once |
| **Mock** | Pre-programmed with **expectations**; fails if they aren't met | Expect `charge()` called with `199.99` |
| **Fake** | A working but simplified implementation | In-memory repository instead of Postgres |

```python
from unittest.mock import Mock

def test_order_sends_confirmation():
    notifier = Mock()                          # spy/mock
    place_order(cart, notifier=notifier)       # dependency injected → testable
    notifier.send.assert_called_once_with("order_confirmed")
```

**Why mock?** Speed (no network/DB), determinism (no flaky third parties), isolation (test *your*
logic), and reaching hard-to-trigger error paths (simulate a payment gateway timeout).

**⚠️ Over-mocking is a real risk:** if you mock everything, tests pass while the real system is
broken — you're testing your mocks. Mock at **architectural boundaries** (network, time,
randomness, filesystem, third-party APIs), not internal collaborators.

---

## 6. Code Coverage

| Metric | Measures |
|---|---|
| **Statement** | % of lines executed |
| **Branch/Decision** ⭐ | % of `if/else` outcomes taken — **stronger than statement** |
| **Function** | % of functions called |
| **Path** | % of execution paths — exhaustive, usually infeasible |

```python
def f(a, b):
    if a: print("A")
    if b: print("B")
# Call f(True, True) → 100% statement coverage,
# but the a=False and b=False branches are NEVER tested. Branch coverage: 50%.
```

**⚠️ Coverage is a *negative* indicator, not a positive one:** low coverage definitely means
you're under-tested; high coverage does **not** mean you're well tested. Code can be executed
without a single meaningful assertion. Making coverage a hard KPI produces assertion-free tests
written to hit lines. **80%** is a common pragmatic target — with the point being *which* 20%
you skip (getters, generated code) is a deliberate choice.

**Mutation testing** (`mutmut`, Stryker) is the real answer: it deliberately introduces bugs and
checks whether your tests catch them — measuring assertion quality, not line execution.

---

## 7. Testing in the Pipeline

```
pre-commit ──▶ CI on PR ─────────────▶ merge ──▶ staging ──────▶ production
 lint,          unit + integration      build     E2E, smoke,     smoke tests,
 format         + coverage gate                   perf, security  monitoring
 fast unit      (must be < ~10 min)               UAT             canary/blue-green
```

- **Shift-left testing** — test earlier (design reviews, static analysis, unit tests) where bugs are cheapest.
- **Shift-right / testing in production** — canary releases, feature flags, synthetic monitoring, chaos engineering.
- **Flaky tests** are toxic: they train the team to ignore red builds. **Quarantine and fix
  them**, never `@skip` and forget. Common causes: timing/`sleep`, shared state between tests,
  test-order dependence, real network calls, time zones/clock.

---

## 8. Common Interview Questions

- **Q: What makes a *good* unit test?**
  → **FIRST**: **F**ast, **I**ndependent (any order, no shared state), **R**epeatable
  (same result everywhere — no clock/network/randomness), **S**elf-validating (pass/fail, no
  human reading output), **T**imely (written with the code). Plus: one logical assertion,
  a name that describes the behaviour, and **Arrange-Act-Assert** structure.

- **Q: You inherit a legacy codebase with 0% test coverage. What do you do?**
  → Don't stop to write tests for everything. Add **characterisation tests** around the areas
  you're about to change (locking in current behaviour, bugs included), require tests for all
  new code, and prioritise coverage by **risk × change frequency** — money paths first.

- **Q: How do you test something that depends on the current time or a random value?**
  → Inject them. Pass a clock/`now()` function and a seeded RNG as dependencies (**DIP**) so
  the test controls them — never call `datetime.now()` deep inside business logic.

- **Q: Should QA or developers write tests?**
  → Both, at different levels. Devs own unit and integration; QA owns E2E, exploratory and
  non-functional. "Throwing it over the wall to QA" is the anti-pattern — quality is the
  whole team's responsibility.

---

**Related:** [sdlc_models.md](sdlc_models.md) · [process.md](process.md) · [principles.md](principles.md) · `../CICD/`
