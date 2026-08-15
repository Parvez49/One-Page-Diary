# The Data Model — Dunders, Protocols, Descriptors

> *"Python's data model is the API you implement to make your objects behave like built-ins."*
> Classes & inheritance: **[oop.md](oop.md)** · Iteration protocol: **[iterators.md](iterators.md)**

---

## 1. Everything is an object

```python
isinstance(42, object)        # True
isinstance(int, object)       # True — even TYPES are objects
type(42), type(int)           # (<class 'int'>, <class 'type'>)

def f(): pass
f.custom = "attributes on a function"    # ⭐ functions are objects too
```

**Every object has three things:** an **identity** (`id()`, never changes), a **type**
(`type()`, effectively fixed), and a **value** (mutable or not).

⭐ **The core idea of the data model:** built-in syntax dispatches to dunder methods.
`a + b` calls `a.__add__(b)`, `len(x)` calls `x.__len__()`, `x[k]` calls `x.__getitem__(k)`.
So *"how do I make my class work with `len()`/`in`/`with`/`for`?"* always has the same
answer — implement the protocol.

---

## 2. The dunders that matter

### Construction & representation

```python
class Point:
    __slots__ = ("x", "y")                    # see §6

    def __init__(self, x, y):                 # initialise an ALREADY-created object
        self.x, self.y = x, y

    def __repr__(self):                       # ⭐ unambiguous, for DEVELOPERS
        return f"Point(x={self.x!r}, y={self.y!r})"

    def __str__(self):                        # readable, for USERS
        return f"({self.x}, {self.y})"
```

⭐⭐ **Always implement `__repr__`; `__str__` is optional.** `str()` falls back to `__repr__`,
but not the reverse — and `__repr__` is what you see in logs, tracebacks, debuggers, and
inside container displays (`[Point(x=1, y=2)]`). A class with only `__str__` shows
`<__main__.Point object at 0x7f...>` in every stack trace you'll ever have to read.

**Aim for `repr()` to be valid Python that reconstructs the object** — hence `!r` on the
fields.

⚠️ **`__new__` vs `__init__`:** `__new__` **creates and returns** the instance (a static
method receiving `cls`); `__init__` only **initialises** it and must return `None`. You need
`__new__` for immutable types (`int`, `str`, `tuple` subclasses) and singletons — you cannot
change an immutable's value in `__init__` because it already exists.

```python
class UpperStr(str):
    def __new__(cls, value):
        return super().__new__(cls, value.upper())   # ⭐ must happen at CREATION
```

### Equality & hashing ⭐⭐

```python
class Point:
    def __init__(self, x, y):
        self.x, self.y = x, y

    def __eq__(self, other):
        if not isinstance(other, Point):
            return NotImplemented          # ⭐ NOT False — lets the other side try
        return (self.x, self.y) == (other.x, other.y)

    def __hash__(self):
        return hash((self.x, self.y))      # ⭐ hash the same fields as __eq__
```

⚠️⚠️ **Defining `__eq__` sets `__hash__ = None`** — your class becomes unhashable and can no
longer go in a `set` or be a `dict` key. You must define `__hash__` too.

**The hash/eq contract, which interviewers do probe:**

1. `a == b` ⟹ `hash(a) == hash(b)`. (The converse need not hold — collisions are fine.)
2. Hash must **not change** during the object's lifetime → hash only **immutable** fields.
3. Unequal objects *may* share a hash; that's just a collision.

⭐ **Never hash mutable state.** Mutate a field after inserting into a dict and the object
lands in the wrong bucket — you get a "lost" key that `in` reports as absent while it's
visibly present in the dict.

**Ordering:** implement `__lt__` and add `@functools.total_ordering` to derive the rest.

### Containers, calling, truthiness

| Dunder | Enables |
|---|---|
| `__len__` | `len(x)` — ⭐ also used for truthiness if `__bool__` is absent |
| `__getitem__` / `__setitem__` / `__delitem__` | `x[k]`, `x[k] = v`, `del x[k]` |
| `__contains__` | `k in x` (falls back to iteration) |
| `__iter__` / `__next__` | `for` loops — see [iterators.md](iterators.md) |
| `__call__` | `x()` — makes the instance callable |
| `__bool__` | `if x:` |
| `__enter__` / `__exit__` | `with x:` |
| `__getattr__` / `__setattr__` / `__getattribute__` | attribute access |

⭐ **Truthiness order:** `__bool__` → else `__len__` → else always `True`. This is why an
empty list, dict, string, and `0` are falsy, and why a custom class with `__len__` returning
0 is unexpectedly falsy.

⚠️ **`if not x:` vs `if x is None:`** — an empty DataFrame, list, or `0` is falsy but *not*
`None`. Use `is None` when you mean "missing."

### `__getattr__` vs `__getattribute__`

```python
class Proxy:
    def __getattr__(self, name):        # ⭐ called ONLY when normal lookup FAILS
        return f"dynamic:{name}"

    # def __getattribute__(self, name): # ⚠️ called on EVERY access — easy infinite recursion
```

`__getattr__` is the safe hook (fallback); `__getattribute__` intercepts everything and must
delegate via `super().__getattribute__(name)` or it recurses forever.

---

## 3. Mutability ⭐

| Immutable | Mutable |
|---|---|
| `int`, `float`, `bool`, `str`, `bytes`, `tuple`, `frozenset`, `range` | `list`, `dict`, `set`, `bytearray`, most custom classes |

**Only immutable objects are reliably hashable** — hence dict keys and set members are
strings, numbers, and tuples.

```python
t = (1, [2, 3])
hash(t)          # ⚠️ TypeError — a tuple is only hashable if ALL its items are
t[1].append(4)   # ⭐ the TUPLE is immutable, but the LIST inside it is not
```

⭐ **Immutability in Python is shallow.** A tuple guarantees its *references* never change,
not that the referenced objects are frozen.

```python
s = "hello"
s += " world"    # ⚠️ builds a NEW string — O(n) each time
"".join(parts)   # ⭐ O(n) total for the whole loop
```

⚠️ **String concatenation in a loop is O(n²).** Use `join()` or `io.StringIO`.

**Copying:**

```python
import copy
shallow = copy.copy(obj)      #  or list(x), x[:], dict(x), x.copy()
deep    = copy.deepcopy(obj)  # ⭐ recursive; handles cycles; SLOW
```

```python
grid = [[0] * 3] * 3          # ⚠️⚠️ THREE REFERENCES TO ONE ROW
grid[0][0] = 1
print(grid)                   # [[1,0,0], [1,0,0], [1,0,0]]

grid = [[0] * 3 for _ in range(3)]     # ⭐ correct: three distinct rows
```

---

## 4. Operator overloading

```python
class Money:
    def __init__(self, amount, currency="USD"):
        self.amount, self.currency = amount, currency

    def __add__(self, other):
        if not isinstance(other, Money) or other.currency != self.currency:
            return NotImplemented              # ⭐ Python then tries other.__radd__
        return Money(self.amount + other.amount, self.currency)

    def __radd__(self, other):                 # ⭐ enables sum([...]) which starts at 0
        if other == 0:
            return self
        return NotImplemented

    def __mul__(self, k):  return Money(self.amount * k, self.currency)
    def __neg__(self):     return Money(-self.amount, self.currency)
    def __format__(self, spec): return f"{self.amount:{spec}} {self.currency}"
```

⭐ **Return `NotImplemented`, don't raise.** Python then tries the **reflected** operation on
the right operand (`__radd__`, `__rmul__`) and only raises `TypeError` if that also declines.
Raising immediately breaks interoperability with types that *could* have handled it.

⚠️ `NotImplemented` (a singleton value) ≠ `NotImplementedError` (an exception you raise in
abstract methods).

---

## 5. Descriptors ⭐⭐

**A descriptor is an object implementing `__get__`, `__set__`, or `__delete__`, used as a
class attribute to control access to an instance attribute.**

They are how `@property`, `@classmethod`, `@staticmethod`, and *every* method in Python
actually work — functions are non-data descriptors, which is what binds `self`.

```python
class PositiveNumber:
    def __set_name__(self, owner, name):        # ⭐ 3.6+: learns its own attribute name
        self._name = f"_{name}"

    def __get__(self, instance, owner):
        if instance is None:
            return self                          # ⭐ accessed on the CLASS, not an instance
        return getattr(instance, self._name)

    def __set__(self, instance, value):
        if value < 0:
            raise ValueError(f"{self._name} must be positive, got {value}")
        setattr(instance, self._name, value)


class BankAccount:
    balance = PositiveNumber()                   # validation defined ONCE...

class Product:
    price = PositiveNumber()                     # ...reused everywhere

acct = BankAccount()
acct.balance = 200      # ok
acct.balance = -50      # ValueError
```

⭐ **Descriptor vs `@property`:** a property's logic lives in *one* class and must be
rewritten for every attribute; a descriptor is a **reusable, composable** validator you can
drop into any class. This is exactly how Django model fields, SQLAlchemy columns, and
Pydantic validation are implemented — a great thing to say out loud.

**Data vs non-data descriptors — this determines lookup priority:**

| Kind | Defines | Priority |
|---|---|---|
| **Data descriptor** | `__set__` or `__delete__` | ⭐ **wins over** the instance `__dict__` |
| **Non-data descriptor** | only `__get__` | instance `__dict__` **wins over** it |

```
attribute lookup order:
  type(obj).__mro__ data descriptor  →  obj.__dict__  →  non-data descriptor
  →  class attribute  →  __getattr__
```

⚠️ **This is why a `@property` can't be shadowed by an instance attribute** (it defines
`__set__`, so it's a data descriptor and always wins), while a method *can* be overwritten
per-instance (`obj.method = something`).

---

## 6. `__slots__`

```python
class Point:
    __slots__ = ("x", "y")            # ⭐ no per-instance __dict__
    def __init__(self, x, y):
        self.x, self.y = x, y

p = Point(1, 2)
p.z = 3          # ⚠️ AttributeError — the point of slots
```

**Wins:** ~40–50% less memory per instance and slightly faster attribute access — meaningful
at millions of objects (records, graph nodes, ORM rows).

⚠️ **Costs:** no dynamic attributes, no `__dict__` (breaks some libraries, `vars()`, and
naive pickling), and inheritance needs every class in the chain to declare `__slots__` or a
`__dict__` reappears. **Use it when profiling says memory matters, not by default.**

---

## 7. Interview points

- **`__str__` vs `__repr__`?** User-facing vs developer-facing. `repr` is the fallback and
  what appears in logs/tracebacks/containers — always implement it.
- **`__new__` vs `__init__`?** Creates/returns the instance vs initialises it. Needed for
  immutable subclasses and singletons.
- **I defined `__eq__` and my object broke as a dict key.** Defining `__eq__` sets
  `__hash__ = None`; define `__hash__` over the same immutable fields.
- **What's the hash/eq contract?** Equal ⟹ equal hashes; hash must be stable for the
  object's lifetime; collisions are allowed.
- **Why return `NotImplemented` from `__add__`?** It lets Python try the reflected operation
  on the other operand instead of failing outright.
- **What is a descriptor, and where have you seen one?** An object controlling attribute
  access via `__get__`/`__set__`; `@property` and methods are descriptors, and it's the
  mechanism behind Django/SQLAlchemy/Pydantic fields.
- **Data vs non-data descriptor?** Data descriptors (with `__set__`) take precedence over the
  instance `__dict__`; non-data descriptors do not.
- **What does `__slots__` do and what does it cost?** Removes the per-instance dict — less
  memory, no dynamic attributes.
- **Is a tuple immutable?** Its *references* are; a mutable object inside it can still change,
  which is why such a tuple is unhashable.
- **Shallow vs deep copy?** Shallow copies the container and shares the children; deep
  recursively copies everything (and handles cycles).
