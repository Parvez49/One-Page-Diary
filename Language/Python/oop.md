# OOP — Classes, MRO, ABCs, Composition

> Dunders & descriptors: **[data_model.md](data_model.md)** · Design patterns:
> **[../../SDLC/design_patterns.md](../../SDLC/design_patterns.md)**

---

## 1. Class anatomy

```python
class Book(LibraryItem):
    total_books = 0                       # ⭐ CLASS attribute — shared by all instances

    def __init__(self, title: str, copies: int) -> None:
        self.title = title                # instance attribute — per object
        self.copies = copies
        Book.total_books += copies        # ⭐ Book., not self. — see below

    def borrow(self) -> bool:             # instance method — gets `self`
        if self.copies == 0:
            return False
        self.copies -= 1
        return True

    @classmethod                          # gets `cls` — alternative constructor
    def from_dict(cls, data: dict) -> "Book":
        return cls(data["title"], data["copies"])     # ⭐ cls, so subclasses work

    @staticmethod                         # gets nothing — just namespaced
    def is_valid(data: dict) -> bool:
        return {"title", "copies"} <= data.keys()

    @property                             # computed attribute, no parentheses at use
    def available(self) -> bool:
        return self.copies > 0
```

⚠️⚠️ **`self.total_books += 1` does NOT update the class attribute** — it reads the class
value, then creates a *new instance attribute* shadowing it. Write `Book.total_books` or
`type(self).total_books`.

⚠️ **A mutable class attribute is shared by every instance** — the class-level version of the
mutable-default trap:

```python
class Cart:
    items = []              # ⚠️ ONE list for ALL carts
    def add(self, x): self.items.append(x)

class Cart:
    def __init__(self):
        self.items = []     # ⭐ per instance
```

### instance vs class vs static ⭐

| | Receives | Use for | Sees subclass? |
|---|---|---|---|
| **instance method** | `self` | per-object behaviour | — |
| **`@classmethod`** | `cls` | ⭐ **alternative constructors**, class-level state | ✅ yes |
| **`@staticmethod`** | nothing | a related utility, grouped for namespacing | ❌ no |

⭐ **The `classmethod` argument to make:** `from_dict` written as a classmethod returns the
*actual subclass* when called as `EBook.from_dict(...)`, because `cls` is bound at call time.
Hard-coding `Book(...)` or using a staticmethod breaks inheritance. This is the **factory
method** pattern, and it's why `dict.fromkeys` and `datetime.fromtimestamp` are classmethods.

---

## 2. Encapsulation — there is no `private`

```python
class Account:
    def __init__(self):
        self.balance = 0        # public
        self._internal = 0      # ⭐ convention: "internal, don't touch"
        self.__mangled = 0      # name mangling → self._Account__mangled
```

⭐ **Python has no access control — it has conventions.** A single `_` is a *social* contract
(and excludes the name from `from x import *`). **Double `__` is not privacy either** — it's
**name mangling**, designed to stop *accidental attribute collisions in subclasses*, not to
stop access. `obj._Account__mangled` works fine.

**Use `__` sparingly** — it breaks subclass overriding and confuses debugging. `_single` is
the right default.

### `@property` — the reason Python doesn't need getters/setters ⭐

```python
class Circle:
    def __init__(self, radius):
        self.radius = radius              # ⭐ goes through the setter → validated

    @property
    def radius(self):
        return self._radius

    @radius.setter
    def radius(self, value):
        if value <= 0:
            raise ValueError("radius must be positive")
        self._radius = value

    @property
    def area(self):                       # ⭐ computed, read-only
        return math.pi * self._radius ** 2
```

⭐ **The interview point:** in Java you write getters up front because switching a public
field to a method later breaks the caller's API. In Python `@property` lets you **start with
a plain attribute and add validation later without changing a single caller** — `c.radius`
looks identical. So writing `get_x()/set_x()` in Python is a Java accent, not good design.

`@x.deleter` handles `del obj.x`. And `@property` is a **data descriptor**, which is why it
can't be shadowed by an instance attribute ([data_model.md §5](data_model.md)).

---

## 3. Inheritance & MRO(Method Resolution Order) ⭐⭐

```python
class Animal:
    def speak(self): raise NotImplementedError

class Dog(Animal):
    def speak(self): return "woof"
    def __init__(self, name):
        super().__init__()                # ⭐ always call it
        self.name = name
```

### The diamond problem

```python
class A:
    def greet(self): print("A")
class B(A):
    def greet(self): print("B")
class C(A):
    def greet(self): print("C")
class D(B, C):
    pass

D().greet()          # "B"
D.__mro__            # ⭐ D → B → C → A → object
```

```
      A
     / \
    B   C
     \ /
      D
```

**Python resolves this with the MRO, computed by the C3 linearisation algorithm.** The
guarantees: a class always precedes its parents, the order of bases is preserved
left-to-right, and each class appears **once**. If no consistent order exists, the `class`
statement raises `TypeError` at definition time.

⭐⭐ **`super()` does not mean "my parent" — it means "the next class in the MRO of the actual
instance."** That's the whole point:

```python
class B(A):
    def greet(self):
        print("B"); super().greet()      # in D()'s MRO this calls C, NOT A

D().greet()          # B → C → A   ⭐ cooperative multiple inheritance
```

This is why every class in a cooperative hierarchy must call `super()` — one link that
skips it silently drops the rest of the chain. It's also why `super().__init__(**kwargs)`
with `**kwargs` pass-through is the standard mixin pattern.

⚠️ Never call `A.greet(self)` explicitly in a multiple-inheritance tree — it hard-codes a
path, breaks the MRO chain, and can call the same class twice.

---

## 4. Abstract Base Classes

```python
from abc import ABC, abstractmethod

class Shape(ABC):
    @property
    @abstractmethod                       # ⭐ order matters: @property OUTERMOST
    def area(self) -> float: ...

    @abstractmethod
    def scale(self, factor: float) -> "Shape": ...

    def describe(self) -> str:            # ⭐ ABCs CAN have concrete methods
        return f"{type(self).__name__} with area {self.area:.2f}"

class Circle(Shape):
    def __init__(self, r): self.r = r
    @property
    def area(self): return math.pi * self.r ** 2
    def scale(self, f): return Circle(self.r * f)

Shape()          # ⚠️ TypeError: Can't instantiate abstract class
```

⭐ **The enforcement is at instantiation, not definition** — a subclass missing an abstract
method fails loudly the first time someone constructs it, which is far better than a
`NotImplementedError` in production six months later.

**ABC vs Protocol** — the modern distinction worth knowing:

| | **ABC** (nominal) | **Protocol** (structural, 3.8+) |
|---|---|---|
| Relationship | must **explicitly inherit** | ⭐ **any class with the right methods** |
| Checking | runtime, at instantiation | static (mypy); runtime with `@runtime_checkable` |
| Use when | you own the hierarchy and want enforcement | duck typing across code you don't own |

See [typing.md](typing.md). `collections.abc` (`Iterable`, `Sequence`, `Mapping`) also gives
you free mixin methods — subclass `Sequence`, implement `__len__` + `__getitem__`, and get
`__contains__`, `__iter__`, `__reversed__`, `index`, `count` for free.

---

## 5. Mixins

A **mixin** adds one reusable behaviour and is never instantiated alone.

```python
class TimestampMixin:
    def touch(self):
        self.updated_at = datetime.now(timezone.utc)

class SerializerMixin:
    def to_dict(self):
        return {k: v for k, v in vars(self).items() if not k.startswith("_")}

class User(TimestampMixin, SerializerMixin, Base):     # ⭐ mixins FIRST
    ...
```

⭐ **Mixins go to the left of the base class** so their methods come earlier in the MRO and
can override the base. Django (`LoginRequiredMixin`) and DRF are built on this.

**Rules that keep mixins sane:** one responsibility each, no `__init__` if avoidable (or
strict `super().__init__(**kwargs)` cooperation), and name them `...Mixin`. ⚠️ More than
three mixins deep and MRO debugging costs more than the reuse saves — that's the point to
switch to composition.

---

## 6. Composition over inheritance ⭐⭐

```python
# Inheritance — "is-a"
class Car(Vehicle): ...

# Composition — "has-a"
class Car:
    def __init__(self, engine: Engine, wheels: Wheels):
        self.engine, self.wheels = engine, wheels     # ⭐ injected → testable
    def drive(self):
        return f"{self.engine.start()} and {self.wheels.rotate()}"
```

| | Inheritance | Composition |
|---|---|---|
| Relationship | **is-a** | **has-a** |
| Coupling | ⚠️ tight — subclass depends on parent internals | loose — only the interface |
| Change at runtime | ❌ fixed at definition | ✅ swap the component |
| Testing | must construct the whole hierarchy | ⭐ inject a fake |
| Failure mode | fragile base class; deep chains | slightly more wiring |

⭐ **The senior answer:** *"Inherit to be substitutable for a type (Liskov); compose to reuse
behaviour."* Reaching for inheritance purely for code reuse is what produces 6-level
hierarchies where changing a base class breaks unrelated subclasses. Composition + dependency
injection also makes unit tests trivial — pass a stub engine.

See [../../SDLC/principles.md](../../SDLC/principles.md) for SOLID.

---

## 7. Singleton in Python

```python
class Config:
    _instance = None
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

a, b = Config(), Config()
assert a is b
```

⚠️ **This naive version is not thread-safe** — two threads can both pass the `is None` check.
Double-checked locking is required:

```python
import threading
_lock = threading.Lock()

class Config:
    _instance = None
    def __new__(cls):
        if cls._instance is None:              # fast path, no lock
            with _lock:
                if cls._instance is None:      # ⭐ re-check inside the lock
                    cls._instance = super().__new__(cls)
        return cls._instance
```

⚠️ Also note `__init__` **runs on every call** even though `__new__` returns the same object —
re-initialising your singleton's state each time. Guard it, or use one of these instead:

⭐ **The Pythonic singletons — prefer these:**

```python
# 1. A MODULE. Imported once, cached in sys.modules, thread-safe by import lock.
#    config.py:  settings = Settings()      →  from config import settings

# 2. functools.cache on a factory
@functools.cache
def get_client(): return ExpensiveClient()
```

Django's `django.conf.settings` and the app registry are module-level singletons; DB
connections are *thread-local* singletons, because a connection isn't thread-safe.

---

## 8. Modern class tooling

```python
from dataclasses import dataclass, field

@dataclass(frozen=True, slots=True, kw_only=True)     # ⭐ 3.10+
class User:
    name: str
    email: str
    tags: list[str] = field(default_factory=list)     # ⭐⭐ never `= []`
    _cache: dict = field(default_factory=dict, repr=False, compare=False)

    def __post_init__(self):                          # validation hook
        if "@" not in self.email:
            raise ValueError("invalid email")
```

Generates `__init__`, `__repr__`, `__eq__` (and `__hash__` when `frozen=True`).
`slots=True` for memory; `kw_only=True` prevents positional-argument mistakes.

**Which record type?** `dataclass` for internal models · `NamedTuple` for immutable
tuple-compatible records · **Pydantic** when data crosses a boundary and needs *runtime
validation* (API payloads, config) · plain class when behaviour dominates over data.

---

## 9. Interview points

- **The four pillars, in Python terms?** **Encapsulation** (convention + `@property`, no
  `private`), **Abstraction** (ABCs/Protocols), **Inheritance** (`super()` + MRO),
  **Polymorphism** (⭐ duck typing — no common base class required).
- **`@classmethod` vs `@staticmethod`?** `cls` vs nothing. Classmethods are for alternative
  constructors and respect subclassing.
- **Why did my class counter not increment?** `self.attr += 1` creates an instance attribute
  shadowing the class one; use `ClassName.attr`.
- **What is the MRO and which algorithm?** The linear order Python searches for attributes,
  computed by **C3 linearisation**; inspect with `Cls.__mro__`.
- **What does `super()` actually do?** Delegates to the **next class in the instance's MRO** —
  not necessarily the parent. That's what makes cooperative multiple inheritance work.
- **Is `__x` private?** No — it's name mangling to `_Class__x`, meant to avoid subclass
  collisions.
- **How do you enforce an interface?** ABC with `@abstractmethod` (fails at instantiation), or
  a `Protocol` for structural typing.
- **Composition vs inheritance?** Is-a vs has-a; prefer composition for reuse, inherit for
  substitutability.
- **Is your singleton thread-safe?** The `__new__` version isn't without double-checked
  locking — and a module is the idiomatic singleton anyway.
- **Duck typing?** If it implements the methods you call, it works — no shared base class or
  declaration required. `hasattr` / try-it-and-catch beats `isinstance`.
