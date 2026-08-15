# Pitfalls — The Traps That Get Asked

> A single page of the bugs that appear in interviews *and* in production.
> Deeper treatment lives in the linked files.

---

## 1. Mutable default arguments ⭐⭐⭐

```python
def add(item, target=[]):        # ⚠️ evaluated ONCE, at def time
    target.append(item)
    return target

add(1)   # [1]
add(2)   # [1, 2]   ← same list
```

**Why:** default values are evaluated when the `def` statement executes and stored in
`func.__defaults__` — one object shared by every call.

```python
def add(item, target=None):      # ⭐ the fix
    target = [] if target is None else target
    target.append(item)
    return target
```

Same trap: `def log(msg, ts=datetime.now())` freezes the timestamp at import time, and
`class Cart: items = []` shares one list across every instance
([oop.md](oop.md)).

---

## 2. Late binding in closures ⭐⭐

```python
fns = [lambda: i for i in range(3)]
[f() for f in fns]                  # ⚠️ [2, 2, 2]

fns = [lambda i=i: i for i in range(3)]    # ⭐ bind NOW via default arg
[f() for f in fns]                  # [0, 1, 2]
```

Closures capture the **variable**, not its value at creation. Bites when building callbacks,
event handlers, or registering tasks in a loop. See [functions.md](functions.md).

---

## 3. `is` vs `==`

```python
a = 256;  b = 256;  a is b      # True  ⚠️ small-int cache
a = 257;  b = 257;  a is b      # False
```

`==` compares **value** (`__eq__`), `is` compares **identity**. CPython interns ints −5..256
and some strings, so `is` appears to work on values — until it doesn't.

⭐ Use `is` only for `None`, `True`, `False`, and sentinel objects. `if x is None:` — never
`if x == None:`.

---

## 4. Truthiness vs `None`

```python
def f(items=None):
    if not items:       # ⚠️ also true for [] , 0 , "" , 0.0
        items = default
    if items is None:   # ⭐ means "not provided"
        items = default
```

`0`, `""`, `[]`, `{}`, `set()`, `0.0` are all falsy but **not** `None`. A valid `0` or empty
list silently becomes your default. See [data_model.md](data_model.md).

---

## 5. Mutating while iterating

```python
for x in li:
    if bad(x): li.remove(x)     # ⚠️ skips elements — indices shift

for k in d:
    del d[k]                    # ⚠️ RuntimeError: dictionary changed size
```

```python
li[:] = [x for x in li if not bad(x)]      # ⭐ rebuild in place
for k in list(d.keys()): del d[k]          # ⭐ iterate a snapshot
```

---

## 6. Shallow copy & shared references

```python
grid = [[0] * 3] * 3            # ⚠️ THREE references to ONE row
grid[0][0] = 1                  # [[1,0,0], [1,0,0], [1,0,0]]

grid = [[0] * 3 for _ in range(3)]        # ⭐

import copy
b = copy.copy(a)                # shallow: children shared
b = copy.deepcopy(a)            # ⭐ recursive
```

`list(x)`, `x[:]`, `dict(x)`, `x.copy()` are all **shallow**.

---

## 7. Exhausted iterators

```python
gen = (x for x in range(3))
list(gen)      # [0, 1, 2]
list(gen)      # ⚠️ [] — silently empty, no error
```

Applies to generators, `map`, `filter`, `zip`, file objects, `csv.reader`. Materialise with
`list()` if you need two passes. See [iterators.md](iterators.md).

---

## 8. `str.strip()` isn't a suffix remover

```python
"parvez.txt".strip(".txt")      # ⚠️ "parvez"  — by accident
"text.txt".strip(".txt")        # ⚠️ "e"       — strips t, x, . from BOTH ends
"text.txt".removesuffix(".txt") # ⭐ "text"    (3.9+)
```

`strip` removes any characters **in the set** you pass, from both ends.

---

## 9. Float arithmetic

```python
0.1 + 0.2 == 0.3          # ⚠️ False  →  0.30000000000000004
round(2.5), round(3.5)    # ⚠️ 2, 4 — banker's rounding, ties go to even

from decimal import Decimal
Decimal("0.1") + Decimal("0.2") == Decimal("0.3")     # ⭐ True
math.isclose(a, b, rel_tol=1e-9)                      # ⭐ float comparison
```

⭐ **Never use floats for money.** `Decimal` for currency, or store integer minor units
(cents). This is a standard fintech interview question.

---

## 10. Class vs instance attributes

```python
class Counter:
    count = 0
    def inc(self):
        self.count += 1          # ⚠️ creates an INSTANCE attribute, shadows the class one
        Counter.count += 1       # ⭐ actually updates the shared counter
```

Reading falls back to the class; **writing always targets the instance**.

---

## 11. Exception handling

```python
except:                     # ⚠️ catches KeyboardInterrupt, SystemExit
except Exception:           # ⚠️ still too broad — hides real bugs
except ValueError as e:     # ⭐ the narrowest thing you can handle

raise NewError(str(e))      # ⚠️ traceback lost
raise NewError(...) from e  # ⭐ chained cause preserved
```

⚠️ `try/except/pass` is where bugs go to hide. Log at minimum.

⚠️ **`finally` with `return` swallows exceptions:**

```python
def f():
    try:    raise ValueError()
    finally: return "ok"       # ⚠️ the exception silently disappears
```

---

## 12. Comparison chaining & operator surprises

```python
a = [1, 2]
b = a + [3]        # new list
a += [3]           # ⚠️ IN-PLACE (__iadd__) — mutates, visible to other names

t = (1, [2])
t[1] += [3]        # ⚠️ TypeError raised... AND the list IS modified
```

```python
if 0 < x < 10:     # ⭐ chaining works and is idiomatic
if x == 1 or 2:    # ⚠️ always truthy — `2` is truthy. Use: x in (1, 2)
```

---

## 13. Integer division & modulo

```python
-7 // 2          # -4  (⭐ floors toward -∞, unlike C's -3)
-7 % 2           #  1  (⭐ sign follows the DIVISOR, unlike C's -1)
7 / 2            # 3.5 — `/` is always float in Python 3
```

---

## 14. Scope surprises

```python
count = 0
def f():
    count += 1        # ⚠️ UnboundLocalError — assignment makes it local everywhere
```

Fix with `global`/`nonlocal`, or (better) return a value. See
[execution_model.md](execution_model.md).

---

## 15. Performance traps

```python
s = ""
for x in items: s += x           # ⚠️ O(n²) — strings are immutable
s = "".join(items)               # ⭐ O(n)

if x in big_list:                # ⚠️ O(n) per check
if x in big_set:                 # ⭐ O(1)

li.pop(0)                        # ⚠️ O(n)
deque.popleft()                  # ⭐ O(1)

any([expensive(x) for x in xs])  # ⚠️ evaluates ALL of them
any(expensive(x) for x in xs)    # ⭐ short-circuits
```

---

## 16. `lru_cache` on methods

```python
class Service:
    @functools.lru_cache          # ⚠️ caches `self` → instances never freed
    def get(self, key): ...
```

The cache keys on `(self, key)`, keeping every instance alive forever. Use
`@cached_property`, or cache a module-level function.

---

## 17. Rapid fire

| Trap | One-line fix |
|---|---|
| `{}` is an empty **dict** | `set()` for an empty set |
| `(1)` is an int | `(1,)` for a one-tuple |
| `sort()` returns `None` | `sorted()` returns a new list |
| `open()` without `with` | ⭐ use `with` — guaranteed close |
| `assert` for validation | stripped by `python -O`; raise real exceptions |
| `datetime.now()` (naive) | ⭐ `datetime.now(timezone.utc)` — always tz-aware |
| `dict.keys()` is a view | it reflects later mutations |
| `except Exception as e: print(e)` | `log.exception(...)` keeps the traceback |
| `input()` returns `str` | cast explicitly |
| local file named `random.py` | shadows stdlib for the whole project |
| `del` on a list index inside a loop | shifts remaining indices |
| `bool` is a subclass of `int` | `True + True == 2`; `isinstance(True, int)` is `True` |

---

## 18. Interview points

The five that come up most often, with the one-sentence answer:

1. **Mutable default argument** — evaluated once at `def` time; use `None`.
2. **Late binding closure** — captures the variable, not the value; bind with a default arg.
3. **`is` vs `==`** — identity vs equality; small-int caching makes `is` look correct.
4. **Shallow vs deep copy** — `[[0]*3]*3` shares one row; use a comprehension or `deepcopy`.
5. **The GIL** — serialises bytecode, released during I/O, and does **not** make `x += 1`
   atomic.
