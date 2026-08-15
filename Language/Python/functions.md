# Functions, Closures & Decorators

> Scope rules (LEGB): **[execution_model.md](execution_model.md)** · Traps: **[pitfalls.md](pitfalls.md)**

---

## 1. Functions are first-class objects ⭐

```python
def greet(name): return f"hi {name}"

f = greet                      # assign
[greet, str.upper]             # store in containers
def apply(fn, x): return fn(x) # pass as an argument
def make(): return greet       # return from a function
greet.calls = 0                # ⭐ attach attributes — they're objects
greet.__name__, greet.__doc__, greet.__defaults__, greet.__closure__
```

This is what makes decorators, callbacks, and higher-order functions possible at all.

---

## 2. Parameters — the full signature grammar

```python
def f(pos_only, /, standard, *args, kw_only, **kwargs):
    ...
#            ▲                ▲
#            │                └─ everything AFTER * is KEYWORD-ONLY
#            └─ everything BEFORE / is POSITIONAL-ONLY (3.8+)
```

```python
def connect(host, port=5432, *, timeout=30, retries=3):
    ...
connect("db")                        # ok
connect("db", 5433, timeout=5)       # ok
connect("db", 5433, 5)               # ⚠️ TypeError — timeout is keyword-only
```

⭐ **Force keyword-only arguments with a bare `*`.** `resize(img, 100, 200, True, False)` is
unreadable and breaks silently when you reorder parameters; `resize(img, w=100, h=200,
crop=True)` cannot. Do this for any function with more than ~2 flags.

**Unpacking at the call site:**

```python
args = (1, 2);  kw = {"timeout": 5}
f(*args, **kw)
```

⚠️⚠️ **Mutable default arguments — the #1 Python interview trap:**

```python
def add(item, target=[]):        # ⚠️ the list is created ONCE, at def time
    target.append(item)
    return target

add(1)   # [1]
add(2)   # [1, 2]  ← the SAME list

def add(item, target=None):      # ⭐ the fix
    if target is None:
        target = []
    target.append(item)
    return target
```

**Defaults are evaluated once, when the `def` executes** — not per call. The same applies to
`datetime.now()` as a default (frozen at import time).

---

## 3. Closures ⭐⭐

A closure is a **function that captures variables from its enclosing scope and keeps them
alive after that scope has returned.**

```python
def make_counter():
    count = 0                     # enclosing scope
    def increment():
        nonlocal count            # ⭐ rebind, don't shadow
        count += 1
        return count
    return increment              # the enclosing frame is gone...

c = make_counter()
c(); c()          # 1, 2         # ...but `count` survives in the closure

c.__closure__[0].cell_contents    # 2 — you can inspect the captured cell
```

Requirements: a nested function, a reference to an enclosing local, and the outer function
returning the inner one.

⚠️⚠️ **Late binding — closures capture the *variable*, not its value:**

```python
fns = [lambda: i for i in range(3)]
[f() for f in fns]                     # ⚠️ [2, 2, 2] — all see the final i

fns = [lambda i=i: i for i in range(3)]   # ⭐ default arg captures NOW
# or: functools.partial(lambda i: i, i)
[f() for f in fns]                     # [0, 1, 2]
```

This bites hardest in loops that build callbacks, event handlers, or Django/Celery task
registrations.

**Closure vs class:** a closure is a lightweight object with one method. Reach for a class
when you need several methods or introspectable state; a closure when you need one behaviour
with captured config.

---

## 4. Decorators ⭐⭐⭐

A decorator is **a callable that takes a function and returns a replacement**.
`@deco` is exactly `func = deco(func)`.

```python
import functools, time

def timer(func):
    @functools.wraps(func)                  # ⭐⭐ see below
    def wrapper(*args, **kwargs):
        start = time.perf_counter()
        try:
            return func(*args, **kwargs)    # ⭐ return the value!
        finally:
            print(f"{func.__name__}: {time.perf_counter() - start:.3f}s")
    return wrapper

@timer
def slow(n): return sum(range(n))
```

⭐⭐ **Always use `functools.wraps`.** Without it the wrapper replaces the function's
`__name__`, `__doc__`, `__module__`, `__qualname__`, and `__wrapped__` — which breaks
`help()`, Sphinx docs, pickling, and **any framework that dispatches on function name**
(pytest fixtures, Flask routes registering every view as `"wrapper"`, Celery task names).

⚠️ Forgetting `return func(...)` inside the wrapper makes every decorated function return
`None` — a silent, maddening bug.

### Decorator with arguments — three levels

```python
def retry(times=3, delay=1, exceptions=(Exception,)):
    def decorator(func):                       # ← receives the function
        @functools.wraps(func)
        def wrapper(*args, **kwargs):          # ← receives the call
            for attempt in range(times):
                try:
                    return func(*args, **kwargs)
                except exceptions:
                    if attempt == times - 1:
                        raise
                    time.sleep(delay * 2 ** attempt)   # exponential backoff
        return wrapper
    return decorator

@retry(times=5, exceptions=(ConnectionError,))
def fetch(url): ...
```

⭐ **`@retry` and `@retry()` are different** — a parameterised decorator *must* be called.
Supporting both requires a `func=None` check; be explicit unless you have a reason.

### Class-based decorators & decorating classes

```python
class CountCalls:
    def __init__(self, func):
        functools.update_wrapper(self, func)
        self.func, self.count = func, 0
    def __call__(self, *a, **kw):
        self.count += 1
        return self.func(*a, **kw)
```

⚠️ **A class-based decorator on a *method* breaks `self` binding** — the instance isn't a
descriptor-aware function. Use a function-based decorator for methods, or implement
`__get__`.

### Stacking

```python
@a
@b
def f(): ...        # ⭐ f = a(b(f)) — BOTTOM-UP application, top-down execution
```

So the topmost decorator is the outermost wrapper: it runs first on the way in and last on
the way out. This matters for `@app.route` + `@login_required` ordering.

### Decorators worth knowing from the stdlib

```python
@functools.cache                 # ⭐ 3.9+, unbounded memoisation
@functools.lru_cache(maxsize=128)
@functools.cached_property       # ⭐ compute once per instance, store in __dict__
@functools.singledispatch        # type-based overloading
@staticmethod / @classmethod / @property
@contextlib.contextmanager       # see iterators.md
@dataclasses.dataclass
```

⚠️ **`lru_cache` on a method keeps every `self` alive forever** — a real memory leak in
long-running services. Cache a module-level function instead, or use `cached_property`.
Arguments must also be **hashable** (no list/dict arguments).

---

## 5. `functools` & friends

```python
from functools import partial, reduce, wraps, cache, cached_property, total_ordering

connect_local = partial(connect, host="localhost")   # ⭐ pre-bind arguments
reduce(operator.mul, nums, 1)                        # rarely clearer than a loop

@total_ordering                                       # ⭐ define __eq__ + __lt__,
class Version:                                        #    get <= > >= free
    def __eq__(self, o): ...
    def __lt__(self, o): ...
```

```python
class Dataset:
    @cached_property                # ⭐ expensive, computed once per instance
    def summary(self):
        return heavy_computation(self.rows)
```

⚠️ `cached_property` needs a `__dict__`, so it's incompatible with `__slots__`, and it never
invalidates — `del obj.summary` is the manual reset.

---

## 6. Lambdas

```python
sorted(users, key=lambda u: u.age)
```

A lambda is a **single-expression** anonymous function. No statements, no annotations, no
docstring, and it shows as `<lambda>` in tracebacks.

⭐ Use lambdas only as throwaway `key=`/callback arguments. Assigning one to a name
(`f = lambda x: x*2`) is worse than `def` in every way — PEP 8 says so explicitly, and you
lose the useful name in stack traces. For attribute/item access prefer
`operator.attrgetter`/`itemgetter`, which are faster and clearer.

---

## 7. Error handling in functions

```python
try:
    result = risky()
except (ValueError, KeyError) as e:
    log.warning("recoverable: %s", e)
    raise                                 # ⭐ bare raise preserves the traceback
except Exception as e:
    raise ProcessingError("context") from e   # ⭐ chains: "direct cause"
else:
    commit()                              # ⭐ runs only if NO exception
finally:
    cleanup()                             # always runs
```

⚠️ **`except:` / `except Exception:` bare** swallows `KeyboardInterrupt` and `SystemExit`
(the bare form) and hides real bugs (both). Catch the narrowest exception you can actually
handle.

⚠️ **`raise NewError(str(e))` destroys the original traceback.** Use `raise ... from e`.

⭐ **EAFP over LBYL** — the Pythonic idiom is *"easier to ask forgiveness than permission"*:

```python
try:                       # ⭐ EAFP — one dict lookup, no race
    value = d[key]
except KeyError:
    value = default

if key in d:               # LBYL — two lookups, and racy on shared state
    value = d[key]
```

Exceptions are cheap to *set up* in Python and only costly when raised, so EAFP wins when the
error case is rare.

---

## 8. Interview points

- **What is a closure?** A nested function that captures and keeps alive variables from its
  enclosing scope after that scope has exited.
- **Why does `[lambda: i for i in range(3)]` return `[2,2,2]`?** Late binding — the closure
  captures the *variable*, read at call time. Bind with a default argument.
- **What is a decorator?** A callable that takes a function and returns a replacement;
  `@d` is `f = d(f)`.
- **Why `functools.wraps`?** It copies `__name__`/`__doc__`/`__wrapped__` so introspection,
  docs, and name-based frameworks keep working.
- **How do you write a decorator that takes arguments?** Three nested levels — the outer
  factory returns the decorator, which returns the wrapper.
- **In what order do stacked decorators apply?** Bottom-up at definition; the top one is the
  outermost at call time.
- **Why is a mutable default argument dangerous?** It's evaluated once at `def` time and
  shared across all calls. Use `None` as the sentinel.
- **`*args` / `**kwargs`?** Collect extra positional / keyword arguments; `*` and `**` at a
  call site unpack them.
- **How do you force keyword-only arguments?** A bare `*` in the signature.
- **`lru_cache` risks?** Unbounded growth, hashable-args-only, and on methods it pins every
  `self` in memory.
- **EAFP vs LBYL?** Try and handle the exception vs check first; EAFP is idiomatic and
  race-free.
- **How do you re-raise while adding context?** `raise NewError(...) from e`, or a bare
  `raise` to preserve the original traceback exactly.
