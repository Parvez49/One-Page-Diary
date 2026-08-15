# Coding Principles — DRY, KISS, SOLID, YAGNI, SoC

> These are **heuristics, not laws**. Every one of them can be over-applied into a worse design.
> Knowing *when a principle does not apply* is what separates a mid-level from a senior answer.

---

## 1. DRY — Don't Repeat Yourself

> *"Every piece of **knowledge** must have a single, unambiguous, authoritative representation."*

The point is **not** "never type the same characters twice" — it's about a single source of
truth for a **business rule**.

```python
# ❌ The VAT rate lives in 3 places — change one, forget the others → silent bug
def invoice_total(x):  return x * 1.15
def cart_preview(x):   return x * 1.15
def report_row(x):     return x * 1.15

# ✅ One authority
VAT_RATE = Decimal("0.15")
def with_vat(amount): return amount * (1 + VAT_RATE)
```

**✅ Advantages:** one place to change, fewer inconsistency bugs, smaller codebase.

**❌ Drawbacks / when NOT to apply**
- **Accidental duplication** — two pieces of code that *look* the same today but change for
  different reasons tomorrow. Merging them creates coupling between unrelated features.
- Over-DRY produces **deeply parameterised god-functions** (`process(data, flag_a, flag_b, mode)`)
  that are harder to read than the duplication they removed.
- **Rule of three:** tolerate duplication twice; abstract on the third occurrence, when you can
  actually see what the correct abstraction is.

> 🗣️ *"Duplication is far cheaper than the wrong abstraction."* — Sandi Metz

---

## 2. KISS — Keep It Simple, Stupid

Prefer the simplest thing that fully solves the problem.

```python
# ❌ Clever
status = ["inactive", "active"][bool(user.is_verified and user.last_login)]

# ✅ Boring — and boring is a feature
if user.is_verified and user.last_login:
    status = "active"
else:
    status = "inactive"
```

**✅ Advantages:** easier to read, debug, onboard, and delete. Code is read ~10× more than written.

**❌ Drawback:** "simple" is subjective, and *simple* ≠ *easy*. Sometimes the genuinely simpler
design (e.g. a proper state machine) looks more complex than a pile of `if`s. Don't use KISS
as an excuse to avoid necessary abstraction.

---

## 3. SOLID — 5 OOD Principles (Robert C. Martin)

| | Principle | One-line memory hook |
|---|---|---|
| **S** | Single Responsibility | One class, **one reason to change** |
| **O** | Open/Closed | Extend by **adding**, not editing |
| **L** | Liskov Substitution | A subclass must **honour the parent's contract** |
| **I** | Interface Segregation | Many small interfaces > one fat one |
| **D** | Dependency Inversion | Depend on **abstractions**, not concretions |

---

### S — Single Responsibility Principle (SRP)

> A class should have **one, and only one, reason to change** — i.e. serve one *actor*.

```python
# ❌ Three reasons to change: business rules, DB schema, email templates
class Order:
    def calculate_total(self): ...
    def save_to_db(self):      ...
    def send_confirmation_email(self): ...

# ✅ One reason each
class Order:            # business rules      → changes when finance changes
    def calculate_total(self): ...

class OrderRepository:  # persistence         → changes when DB changes
    def save(self, order): ...

class OrderNotifier:    # communication       → changes when marketing changes
    def send_confirmation(self, order): ...
```

**✅ Advantages:** isolated changes, far easier to unit-test (no DB needed to test totals),
clearer ownership across teams.

**❌ Drawbacks:** taken to the extreme you get **class explosion** — 40 one-method classes where
navigating the code becomes the hard part. "Responsibility" is genuinely ambiguous; use
*"who requests this change?"* as the tiebreaker.

---

### O — Open/Closed Principle (OCP)

> Software entities should be **open for extension, closed for modification**.

```python
# ❌ Without OCP — every new payment type edits this class (retest + regression risk)
class PaymentProcessor:
    def pay(self, payment_type, amount):
        if payment_type == "credit_card":
            print("Processing credit card payment")
        elif payment_type == "paypal":
            print("Processing PayPal payment")
        # ...and this if-chain grows forever

# ✅ With OCP
from abc import ABC, abstractmethod

class PaymentMethod(ABC):
    @abstractmethod
    def pay(self, amount): ...

class CreditCardPayment(PaymentMethod):
    def pay(self, amount): print(f"Processing credit card payment of {amount}")

class PayPalPayment(PaymentMethod):
    def pay(self, amount): print(f"Processing PayPal payment of {amount}")

class PaymentProcessor:
    def process(self, method: PaymentMethod, amount):
        method.pay(amount)          # never changes again

# Adding Apple Pay = adding a NEW file. PaymentProcessor is untouched.
class ApplePayPayment(PaymentMethod):
    def pay(self, amount): print(f"Processing Apple Pay payment of {amount}")
```

**✅ Advantages:** new features can't break tested code; enables plugin architectures.

**❌ Drawbacks:** you must **guess the right extension axis** upfront. If payment types are
stable but *tax rules* vary, you abstracted the wrong dimension and now carry the complexity
for nothing. Conflicts with YAGNI — apply OCP after the second or third variation appears,
not on speculation.

---

### L — Liskov Substitution Principle (LSP)

> Objects of a superclass must be **replaceable by objects of a subclass without breaking
> the program**. A subclass must not weaken guarantees the parent made.

```python
# ❌ The classic violation — Square IS-A Rectangle mathematically, but not behaviourally
class Rectangle:
    def set_width(self, w):  self.w = w
    def set_height(self, h): self.h = h
    def area(self):          return self.w * self.h

class Square(Rectangle):
    def set_width(self, w):  self.w = self.h = w   # side-effect the parent never had!
    def set_height(self, h): self.w = self.h = h

def test(r: Rectangle):
    r.set_width(5); r.set_height(4)
    assert r.area() == 20     # ✅ Rectangle → 20   ❌ Square → 16. Broken.
```

```python
# ❌ Another everyday violation — throwing where the parent didn't
class Bird:
    def fly(self): ...

class Ostrich(Bird):
    def fly(self): raise NotImplementedError("Ostriches can't fly")
    # Any code doing `for b in birds: b.fly()` now crashes.

# ✅ Fix: model the actual capability, not the taxonomy
class Bird: ...
class FlyingBird(Bird):
    def fly(self): ...
class Ostrich(Bird): pass        # simply has no fly()
```

**Rules a subclass must respect:**
| Rule | Meaning |
|---|---|
| **Preconditions** cannot be **strengthened** | Parent accepts any int → child must not demand "positive only" |
| **Postconditions** cannot be **weakened** | Parent guarantees a sorted list → child must return sorted too |
| **Invariants** must be preserved | Parent guarantees `balance >= 0` → child too |
| No **new exceptions** | Don't throw what callers of the parent don't expect |

**🚩 Smells that you're violating LSP:** a subclass overriding a method to do nothing;
`raise NotImplementedError` in a subclass; callers doing `if isinstance(x, Square)`.

**❌ Drawback of enforcing it:** LSP often pushes you away from inheritance entirely —
**composition over inheritance** is usually the real fix, at the cost of more wiring code.

---

### I — Interface Segregation Principle (ISP)

> **No client should be forced to depend on methods it does not use.** Prefer many small,
> role-specific interfaces over one fat general-purpose one.

```python
# ❌ Fat interface — a robot is forced to implement eat() and sleep()
class Worker(ABC):
    @abstractmethod
    def work(self):  ...
    @abstractmethod
    def eat(self):   ...
    @abstractmethod
    def sleep(self): ...

class RobotWorker(Worker):
    def work(self):  print("working")
    def eat(self):   raise NotImplementedError   # 🚩 also an LSP violation
    def sleep(self): raise NotImplementedError

# ✅ Segregated — implement only what applies
class Workable(ABC):
    @abstractmethod
    def work(self): ...

class Feedable(ABC):
    @abstractmethod
    def eat(self): ...

class HumanWorker(Workable, Feedable):
    def work(self): ...
    def eat(self):  ...

class RobotWorker(Workable):
    def work(self): ...
```

**✅ Advantages:** fewer forced stubs, smaller blast radius (adding a method to a fat interface
breaks every implementer), much easier mocking in tests.

**❌ Drawback:** too many micro-interfaces (`Readable`, `Writable`, `Closable`, `Flushable`…)
makes the type hierarchy hard to navigate. ISP is most valuable where **many classes implement
the same interface**; for a one-implementation interface it's noise.

---

### D — Dependency Inversion Principle (DIP) ⭐ *most asked, most misunderstood*

> 1. High-level modules should **not** depend on low-level modules — **both** should depend on **abstractions**.
> 2. Abstractions should not depend on details; **details should depend on abstractions**.

```python
# ❌ High-level business logic nailed to a concrete low-level detail
class MySQLDatabase:
    def save(self, user): print("saving to MySQL")

class UserService:
    def __init__(self):
        self.db = MySQLDatabase()      # 🚩 hard-wired. Can't swap. Can't test without MySQL.
    def register(self, user):
        self.db.save(user)
```

```python
# ✅ Both depend on the abstraction; the concrete class is injected
class UserRepository(ABC):                 # the abstraction (owned by the high-level module)
    @abstractmethod
    def save(self, user): ...

class MySQLUserRepository(UserRepository):  # detail depends on abstraction
    def save(self, user): print("saving to MySQL")

class PostgresUserRepository(UserRepository):
    def save(self, user): print("saving to Postgres")

class InMemoryUserRepository(UserRepository):   # ← makes tests instant, no DB
    def __init__(self): self.users = []
    def save(self, user): self.users.append(user)

class UserService:
    def __init__(self, repo: UserRepository):   # dependency INJECTED
        self.repo = repo
    def register(self, user):
        self.repo.save(user)

# Wiring happens at the edge of the app (composition root)
service = UserService(MySQLUserRepository())
test_service = UserService(InMemoryUserRepository())
```

**Direction of dependency — the "inversion":**
```
❌ Before:  UserService ──▶ MySQLDatabase          (high-level depends on low-level)
✅ After:   UserService ──▶ UserRepository ◀── MySQLUserRepository
                              (abstraction)        arrow FLIPPED = "inverted"
```

> ⭐ **DIP vs DI vs IoC** — interviewers love this distinction:
> - **DIP** = the *principle* (depend on abstractions).
> - **Dependency Injection (DI)** = a *technique* to achieve it (pass dependencies in via
>   constructor/setter/parameter instead of constructing them inside).
> - **IoC (Inversion of Control)** = the broader *pattern* — the framework calls your code,
>   not vice versa. A **DI container** (Spring, .NET DI) automates the wiring.

**✅ Advantages:** swap implementations (MySQL → Postgres) without touching business logic;
**testability** is the biggest practical win; enforces clean layer boundaries (hexagonal /
clean architecture).

**❌ Drawbacks:** indirection makes "jump to definition" land on an interface instead of the
real code; more boilerplate; and creating an interface with exactly **one** implementation
"just in case" is speculative — that's YAGNI territory.

---

## 4. YAGNI — You Aren't Gonna Need It

> Don't build it until you **actually** need it — not when you merely *foresee* needing it.

```python
# ❌ Speculative generality: built for 5 databases, ships with 1
class DatabaseAdapterFactoryProvider:
    def get_factory(self, db_type, region, tenant, sharding_strategy): ...

# ✅ Build for today's real requirement; refactor when the second case arrives
def save_user(user): db.execute("INSERT INTO users ...")
```

**✅ Advantages:** less code to write, test, document and maintain; faster delivery;
avoids paying for features that never ship.

**❌ Drawbacks / limits**
- Does **not** apply to things that are **expensive to retrofit**: security, authentication,
  data model design, audit logging, database schema, API contracts. Bolting on multi-tenancy
  or an audit trail later is a rewrite.
- Misused as an excuse to skip abstraction where the need is already known and concrete.

> **Tension to name in an interview:** *OCP says "prepare for extension", YAGNI says "don't
> build what you don't need"*. Resolution: **YAGNI wins until the second or third variation
> appears** — then refactor to OCP with real knowledge of the extension axis.

---

## 5. Separation of Concerns (SoC)

Divide a program into distinct sections, each handling one concern.

| Pattern | Separation |
|---|---|
| **MVC** | **M**odel (data & rules) / **V**iew (UI) / **C**ontroller (input handling) |
| **MVT** (Django) | Model / View (= logic) / Template (= UI) |
| **Layered** | Presentation → Business → Data Access → Database |
| **Hexagonal** | Domain core, isolated behind ports & adapters |

**✅ Advantages:** parallel work by specialists (frontend/backend), swap a layer (REST → GraphQL)
without touching the others, targeted testing.

**❌ Drawbacks:** more files & indirection; **anaemic layers** where a simple field addition
requires editing 5 files; performance cost when layers convert data back and forth (DTO
mapping at every boundary).

---

## 6. Honourable Mentions

| Principle | Meaning | Watch out for |
|---|---|---|
| **Composition over Inheritance** | Build behaviour by combining objects (has-a) rather than extending (is-a) | Inheritance is still right for genuine is-a with a stable contract |
| **Law of Demeter** ("don't talk to strangers") | `a.b()` ✅ but `a.get_b().get_c().do()` 🚩 — train-wreck code couples you to internals | Can produce excessive delegation/wrapper methods |
| **Principle of Least Astonishment** | Code should do what its name suggests. `get_user()` must not delete anything | — |
| **Fail Fast** | Validate early, crash loudly at the boundary rather than corrupting state silently | Not for user-facing recoverable errors |
| **Convention over Configuration** | Sensible defaults (Rails, Django) over endless config | Magic is hard to debug when you fight the convention |
| **GRASP / High Cohesion, Low Coupling** | Related things together, unrelated things independent | The umbrella goal that most of the above serve |

---

## 7. Common Interview Questions

- **Q: Which SOLID principle do you use most in practice?**
  → **SRP and DIP.** SRP because it keeps classes testable and reviewable; DIP because it's
  what actually makes unit testing possible without a live database. Give a concrete example
  from your own project — the story matters more than the definition.

- **Q: Can you over-apply SOLID?**
  → Yes. Blindly applied it produces interface-per-class, factory-per-factory enterprise
  architecture where reading one request path means opening 12 files. Apply it where change
  is *likely*, not everywhere.

- **Q: DRY vs readability — which wins?**
  → Readability. Duplication is visible and cheap to fix; a wrong abstraction is invisible and
  expensive. Prefer the rule of three.

---

**Related:** [design_patterns.md](design_patterns.md) · [architecture.md](architecture.md) · [agile.md](agile.md)
