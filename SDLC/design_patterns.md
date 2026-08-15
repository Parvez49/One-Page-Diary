# Design Patterns

> Reusable solutions to **recurring** design problems (Gang of Four, 1994). A pattern is a
> **vocabulary**, not a goal — saying *"use a Strategy here"* replaces a paragraph of explanation.
>
> ⚠️ **Pattern-itis** is a real interview red flag: forcing patterns where a plain function
> would do. Always be ready to say *when NOT to use* one.

| Category | Concern | Patterns |
|---|---|---|
| **Creational** | *How objects are created* | Singleton, Factory Method, Abstract Factory, Builder, Prototype |
| **Structural** | *How objects are composed* | Adapter, Decorator, Facade, Proxy, Composite, Bridge, Flyweight |
| **Behavioural** | *How objects communicate* | Strategy, Observer, Command, Template Method, Iterator, State, Chain of Responsibility, Mediator |

---

## 🏗️ Creational Patterns

### Singleton
**Ensure a class has exactly one instance and give global access to it.**

```python
class Config:
    _instance = None
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.settings = {"db": "postgres"}
        return cls._instance

a, b = Config(), Config()
assert a is b          # ✅ same object
```
> **Pythonic alternative:** just use a **module** — modules are imported once and cached, which
> is a singleton for free. `import settings` is better than a Singleton class.

- **Use for:** logger, DB connection pool, app configuration, cache client.
- **✅ Pros:** one shared instance, lazy initialisation, controlled access.
- **❌ Cons:** ⚠️ **it is global state in disguise** — hidden dependencies, painful unit tests
  (state leaks between tests), hard to mock, **thread-safety issues** (need a lock on `__new__`),
  and it violates **SRP** (the class manages both its job *and* its lifecycle).
  Widely considered an **anti-pattern**; prefer **dependency injection**.

### Factory Method
**Define an interface for creating an object, but let subclasses/logic decide which class to instantiate.**

```python
class Notification(ABC):
    @abstractmethod
    def send(self, msg): ...

class EmailNotification(Notification):
    def send(self, msg): print(f"Email: {msg}")

class SMSNotification(Notification):
    def send(self, msg): print(f"SMS: {msg}")

def notification_factory(channel: str) -> Notification:   # the factory
    return {"email": EmailNotification, "sms": SMSNotification}[channel]()

notification_factory("sms").send("Order shipped")
```
- **Use for:** object creation depends on config/input; you want callers decoupled from concrete classes.
- **✅ Pros:** supports **OCP** (new type = new class + registry entry), centralises creation logic.
- **❌ Cons:** extra indirection; a growing `if/dict` in the factory itself; overkill when there are only two types that never change.

### Builder
**Construct a complex object step by step; same process, different representations.**

```python
class QueryBuilder:
    def __init__(self):  self.parts = {"select": "*", "where": [], "limit": None}
    def select(self, *c): self.parts["select"] = ", ".join(c); return self   # ← fluent
    def where(self, cond): self.parts["where"].append(cond);   return self
    def limit(self, n):    self.parts["limit"] = n;            return self
    def build(self):
        q = f"SELECT {self.parts['select']} FROM users"
        if self.parts["where"]: q += " WHERE " + " AND ".join(self.parts["where"])
        if self.parts["limit"]: q += f" LIMIT {self.parts['limit']}"
        return q

QueryBuilder().select("id", "name").where("age > 18").limit(10).build()
# SELECT id, name FROM users WHERE age > 18 LIMIT 10
```
- **Use for:** objects with many optional parameters — kills the **telescoping constructor**
  problem (`User(name, email, None, None, True, None, 5)`).
- **✅ Pros:** readable, immutable end product, step-by-step validation.
- **❌ Cons:** lots of boilerplate; in Python, **keyword arguments + `@dataclass`** usually
  make Builder unnecessary.

---

## 🧩 Structural Patterns

### Adapter (Wrapper)
**Convert one interface into another the client expects** — makes incompatible classes work together.

```python
class StripeAPI:                       # third-party, can't change it
    def make_charge(self, cents, curr): print(f"Stripe: {cents} {curr}")

class PaymentGateway(ABC):             # our interface
    @abstractmethod
    def pay(self, amount): ...

class StripeAdapter(PaymentGateway):   # the adapter
    def __init__(self, stripe): self.stripe = stripe
    def pay(self, amount): self.stripe.make_charge(int(amount * 100), "USD")

StripeAdapter(StripeAPI()).pay(49.99)
```
- **Use for:** integrating third-party/legacy APIs, migrating between vendors.
- **✅ Pros:** isolates external dependencies (**anti-corruption layer**) — swapping Stripe for
  PayPal touches one file.
- **❌ Cons:** extra layer; if the two interfaces are conceptually far apart, the adapter turns
  into a mini-application of its own.

### Decorator
**Attach new behaviour to an object dynamically, without changing its class.**

```python
import functools, time

def retry(times=3):
    def deco(fn):
        @functools.wraps(fn)
        def wrapper(*a, **kw):
            for attempt in range(times):
                try:    return fn(*a, **kw)
                except Exception:
                    if attempt == times - 1: raise
                    time.sleep(2 ** attempt)
        return wrapper
    return deco

@retry(times=3)
def fetch_payment_status(order_id): ...
```
- **Use for:** cross-cutting concerns — logging, caching, retry, auth, rate limiting.
  Python decorators and Django middleware are this pattern.
- **✅ Pros:** composable (stack many), follows **OCP & SRP**, far better than subclass explosion.
- **❌ Cons:** stack traces get noisy; **order matters** and is easy to get wrong
  (`@cache` above vs below `@auth_required` is a security bug); hard to debug deep stacks.

### Facade
**A single simplified interface over a complex subsystem.**

```python
class OrderFacade:
    def place_order(self, cart, user):      # hides 5 subsystems behind 1 call
        InventoryService().reserve(cart)
        payment = PaymentService().charge(user, cart.total)
        ShippingService().schedule(cart, user.address)
        NotificationService().send_confirmation(user)
        return payment
```
- **✅ Pros:** clients depend on one small surface; decouples callers from subsystem churn.
- **❌ Cons:** risks becoming a **god object**; can hide capabilities users legitimately need.

### Proxy
**A placeholder controlling access to another object** — for lazy loading, access control, caching, or remoting.

```python
class ImageProxy:
    def __init__(self, path): self.path, self._real = path, None
    def display(self):
        if self._real is None:               # lazy load — expensive work deferred
            self._real = RealImage(self.path)
        self._real.display()
```
- **Real-world:** Django's lazy QuerySets, ORM lazy relations, API caching layers, `nginx` reverse proxy.
- **❌ Cons:** hidden cost — a "field access" may trigger a DB query (the **N+1 query** trap).

### Composite
**Treat individual objects and groups of objects uniformly** via a common interface (tree structure).
- **Real-world:** file system (file vs folder), UI component trees (React), org charts, nested menus.
- **❌ Cons:** the shared interface becomes over-general (leaf nodes forced to implement `add_child()` → **ISP** violation).

---

## 🔀 Behavioural Patterns

### Strategy ⭐ *the most useful one to know*
**Define a family of interchangeable algorithms and select one at runtime.**

```python
class ShippingStrategy(ABC):
    @abstractmethod
    def cost(self, weight): ...

class StandardShipping(ShippingStrategy):
    def cost(self, weight): return weight * 1.0

class ExpressShipping(ShippingStrategy):
    def cost(self, weight): return weight * 2.5 + 10

class FreeShipping(ShippingStrategy):
    def cost(self, weight): return 0

class Order:
    def __init__(self, strategy: ShippingStrategy): self.strategy = strategy
    def total(self, weight, subtotal): return subtotal + self.strategy.cost(weight)

Order(ExpressShipping()).total(2, 100)     # swap strategy freely at runtime
```
- **Use for:** replacing a growing `if/elif` chain over "kinds of behaviour" — payment methods,
  sorting, pricing, compression, auth backends.
- **✅ Pros:** textbook **OCP**; each algorithm independently testable; removes conditionals.
- **❌ Cons:** more classes; the client must know which strategy to pick; overkill for two
  branches that never grow.

> **Strategy vs Factory:** Factory decides **which object to create**; Strategy decides
> **which behaviour to run**. They're often used together.

### Observer (Pub/Sub)
**One-to-many dependency: when one object changes state, all its dependents are notified automatically.**

```python
class EventBus:
    def __init__(self): self.subscribers = {}
    def subscribe(self, event, handler):
        self.subscribers.setdefault(event, []).append(handler)
    def publish(self, event, data):
        for handler in self.subscribers.get(event, []):
            handler(data)

bus = EventBus()
bus.subscribe("order_placed", lambda o: print(f"📧 email for {o}"))
bus.subscribe("order_placed", lambda o: print(f"📦 reserve stock for {o}"))
bus.publish("order_placed", "ORD-123")     # publisher knows nothing about subscribers
```
- **Real-world:** Django signals, DOM event listeners, Kafka/RabbitMQ, React state subscriptions,
  webhooks. This is the foundation of **Event-Driven Architecture**.
- **✅ Pros:** loose coupling — add a subscriber without touching the publisher.
- **❌ Cons:** ⚠️ **execution flow becomes invisible** ("who ran this?"), hard to debug;
  **memory leaks** from unremoved listeners; ordering is not guaranteed; a slow subscriber
  blocks the publisher unless it's async; cascading/circular notifications.

### Command
**Encapsulate a request as an object** — enabling queuing, logging, and undo.

```python
class Command(ABC):
    @abstractmethod
    def execute(self): ...
    @abstractmethod
    def undo(self): ...

class AddItemCommand(Command):
    def __init__(self, cart, item): self.cart, self.item = cart, item
    def execute(self): self.cart.append(self.item)
    def undo(self):    self.cart.remove(self.item)

history = []
def run(cmd): cmd.execute(); history.append(cmd)
def undo_last(): history.pop().undo()
```
- **Real-world:** undo/redo, Celery tasks, job queues, transaction logs, CQRS commands.
- **❌ Cons:** a class per action → verbose for simple operations.

### Template Method
**Define the skeleton of an algorithm in a base class; let subclasses override specific steps.**

```python
class DataPipeline(ABC):
    def run(self):              # ← the template: order is FIXED
        data = self.extract()
        data = self.transform(data)
        self.load(data)
    @abstractmethod
    def extract(self): ...
    def transform(self, d): return d      # optional hook with a default
    @abstractmethod
    def load(self, d): ...

class CSVPipeline(DataPipeline):
    def extract(self):  return read_csv()
    def load(self, d):  write_to_db(d)
```
- **Real-world:** Django's class-based views / `ModelSerializer`, unittest `setUp`/`tearDown`.
- **✅ Pros:** removes duplication of the shared skeleton.
- **❌ Cons:** **inheritance-based** → tight coupling to the base class; fragile if the base
  changes; **Strategy (composition) is often the better modern choice**.

### State
**Alter an object's behaviour when its internal state changes** — the object appears to change class.
- **Use for:** order lifecycle (pending → paid → shipped → delivered), document workflows.
- **✅ Pros:** replaces sprawling `if status == ...` chains; makes **illegal transitions impossible**.
- **❌ Cons:** class per state; overkill for 2–3 simple states.

### Chain of Responsibility
**Pass a request along a chain of handlers until one handles it.**
- **Real-world:** middleware stacks (Django/Express), logging levels, approval workflows, exception handling.
- **❌ Cons:** no guarantee anything handles it; debugging a long chain is painful.

---

## 🏛️ Architectural / Enterprise Patterns

### Repository
**Abstract data access behind a collection-like interface** so business logic never sees SQL/ORM.

```python
class UserRepository(ABC):
    @abstractmethod
    def get_by_email(self, email): ...
    @abstractmethod
    def save(self, user): ...

class DjangoUserRepository(UserRepository):
    def get_by_email(self, email): return User.objects.filter(email=email).first()
    def save(self, user):          user.save()

class InMemoryUserRepository(UserRepository):   # instant unit tests, no DB
    def __init__(self): self.users = {}
    def get_by_email(self, email): return self.users.get(email)
    def save(self, user):          self.users[user.email] = user
```
- **✅ Pros:** business logic testable without a DB; swap the persistence layer; centralised queries.
  This is **DIP** applied to persistence.
- **❌ Cons:** ⚠️ an ORM (Django ORM, SQLAlchemy) **already is** a repository/data-mapper — wrapping
  it again is often a pointless layer that leaks anyway (pagination, `select_related`, transactions
  are hard to express generically).

### Others worth naming
| Pattern | One-liner |
|---|---|
| **Unit of Work** | Track changed objects and commit them in one transaction |
| **DTO** | Plain data container to move data across boundaries (API serializers) |
| **Service Layer** | Business use-cases, sits between controllers and repositories |
| **Dependency Injection** | Supply dependencies from outside instead of constructing them inside |
| **MVC / MVT** | Separate data, presentation and control flow |
| **Circuit Breaker** | Stop calling a failing downstream service; fail fast, then probe for recovery |
| **CQRS** | Separate read models from write models |

---

## Quick Selection Guide

| Your problem | Reach for |
|---|---|
| Growing `if/elif` over *behaviour* | **Strategy** |
| Growing `if/elif` over *which class to create* | **Factory** |
| Growing `if/elif` over *status/lifecycle* | **State** |
| Add behaviour without subclassing | **Decorator** |
| Third-party API doesn't match your interface | **Adapter** |
| Complex subsystem, simple use case | **Facade** |
| "When X happens, also do Y and Z" | **Observer** |
| Undo / queue / schedule an action | **Command** |
| Same steps, different details | **Template Method** or **Strategy** |
| Business logic shouldn't know about the DB | **Repository** + **DI** |
| Need exactly one shared instance | **DI**, and only *then* consider Singleton |

---

## Common Interview Questions

- **Q: Why is Singleton considered an anti-pattern?**
  → It's global mutable state: dependencies become hidden (you can't see them in the
  constructor), tests leak state into each other, and it's not thread-safe by default.
  Dependency injection gives you the "one instance" benefit while keeping it explicit and mockable.

- **Q: Strategy vs Template Method?**
  → Both vary part of an algorithm. **Template Method uses inheritance** (subclass overrides
  steps, structure fixed at compile time); **Strategy uses composition** (object injected,
  swappable at runtime). Prefer Strategy — it's more flexible and avoids inheritance coupling.

- **Q: Have you used patterns without realising it?**
  → Almost certainly yes: Django middleware = Chain of Responsibility, Django signals =
  Observer, `@login_required` = Decorator, DRF serializers = DTO, class-based views =
  Template Method. Naming these is a strong answer.

---

**Related:** [principles.md](principles.md) · [architecture.md](architecture.md)
