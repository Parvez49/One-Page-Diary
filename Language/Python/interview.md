# Python — Interview Questions

> Claim first, then the *why*. Depth lives in the linked files.

---

## 1. Language & execution

**Is Python compiled or interpreted?**
Both. Source is **compiled to bytecode** (cached in `__pycache__`), which the **CPython
VM interprets**. "Interpreted, not compiled" is the wrong answer.
→ [execution_model.md](execution_model.md)

**Is Python pass-by-value or pass-by-reference?**
Neither — **call by object reference**. The function gets a reference to the same object:
**mutating** it is visible to the caller, **rebinding** the parameter is not.

```python
def f(lst, n):
    lst.append(1)   # visible outside
    n += 1          # not visible
    lst = [99]      # not visible
```

**How does Python manage memory?**
**Reference counting** primarily — immediate, deterministic deallocation at count 0 — plus a
**generational cycle collector** for reference cycles, on top of pymalloc arenas.
⚠️ Freed memory often isn't returned to the OS, so RSS shows the high-water mark.

**What is the GIL? ⭐⭐**
A mutex allowing only one thread to execute Python **bytecode** at a time per interpreter.
It makes refcounting cheap and the C API simple. It's **released during blocking I/O and
inside C extensions** — which is why threads help I/O-bound work but not pure-Python CPU work.
⚠️ It does **not** make your code thread-safe: `x += 1` is three opcodes.

**`is` vs `==`?**
Identity vs value. Use `is` only for `None`/`True`/`False`/sentinels — small-int (−5..256) and
string interning make `is` deceptively appear to work on values.

**What is `UnboundLocalError`?**
Assigning to a name anywhere in a function makes it local for the *whole* function, so reading
it before assignment fails. Fix with `global`/`nonlocal` or by returning a value.

---

## 2. Data structures

**When would you use a set instead of a list? ⭐**
Membership tests and dedup: `in` is **O(1)** on a set, **O(n)** on a list. Converting a list
to a set before a membership loop is the most common real Python speedup.

**Are dicts ordered?**
Yes — insertion-ordered. An implementation detail in 3.6, a **language guarantee from 3.7**.

**How does a dict get O(1) lookup, and why must keys be immutable?**
Hash table with open addressing. The key's hash must stay stable for its lifetime — a mutated
key hashes to a different bucket and becomes unreachable.

**`list.pop(0)` vs `deque.popleft()`?**
O(n) vs O(1). Use `collections.deque` for queues.

**Why does `sort()` return `None`?**
It sorts in place. `sorted()` returns a new list. Same for `append`/`extend`/`reverse`.

**Is Python's sort stable?**
Yes — Timsort. Equal elements keep relative order, which makes multi-pass sorting work.

**List comprehension vs generator expression?**
Eager list in memory, re-iterable, indexable vs **lazy, O(1) memory, single-pass**.
→ [data_structures.md](data_structures.md)

---

## 3. Functions & decorators

**What is a closure?**
A nested function capturing variables from its enclosing scope, keeping them alive after that
scope returns. Inspect via `f.__closure__`.

**Why does `[lambda: i for i in range(3)]` give `[2,2,2]`? ⭐**
**Late binding** — the closure captures the *variable*, read at call time. Bind eagerly with
a default argument: `lambda i=i: i`.

**What is a decorator?**
A callable taking a function and returning a replacement; `@d` is `f = d(f)`.

**Why `functools.wraps`? ⭐**
It copies `__name__`, `__doc__`, `__wrapped__` etc. Without it you break `help()`, docs,
pickling, and any framework that dispatches on function name (pytest, Flask, Celery).

**In what order do stacked decorators apply?**
Bottom-up at definition (`@a @b def f` → `a(b(f))`); the top one is outermost at call time.

**Why is a mutable default argument dangerous? ⭐⭐**
Defaults are evaluated **once at `def` time** and shared by every call. Use `None` as the
sentinel.

**`@classmethod` vs `@staticmethod`?**
`cls` vs nothing. Classmethods are for **alternative constructors** and respect subclassing —
`cls(...)` returns the actual subclass.

---

## 4. OOP

**The four pillars, in Python terms?**
**Encapsulation** — convention (`_x`) plus `@property`, no real `private`.
**Abstraction** — ABCs / Protocols.
**Inheritance** — `super()` and the MRO.
**Polymorphism** — ⭐ **duck typing**; no common base class needed.

**Is `__x` private?**
No. It's **name mangling** to `_Class__x`, intended to prevent accidental subclass
collisions. `obj._Class__x` still works.

**What is the MRO? ⭐**
The linear attribute-search order, computed by **C3 linearisation** (`Cls.__mro__`). It
guarantees each class appears once, subclasses precede parents, and base order is preserved.

**What does `super()` actually do? ⭐⭐**
Delegates to the **next class in the instance's MRO** — not necessarily the parent. That's
what makes cooperative multiple inheritance and mixins work.

**Why did my class counter not increment?**
`self.count += 1` reads the class attribute then creates an **instance** attribute shadowing
it. Use `ClassName.count`.

**`__new__` vs `__init__`?**
`__new__` creates and returns the instance; `__init__` initialises it and returns `None`.
You need `__new__` for immutable subclasses and singletons.

**I defined `__eq__` and my object stopped working as a dict key. ⭐**
Defining `__eq__` sets `__hash__ = None`. Define `__hash__` over the same **immutable** fields.

**`__str__` vs `__repr__`?**
User-facing vs developer-facing. `str()` falls back to `__repr__`, not the reverse — and
`__repr__` is what appears in logs, tracebacks, and containers. Always implement it.

**Composition vs inheritance? ⭐**
Is-a vs has-a. *Inherit to be substitutable (Liskov); compose to reuse behaviour.* Composition
is loosely coupled, swappable at runtime, and far easier to test.

**How do you enforce an interface?**
ABC with `@abstractmethod` (fails at **instantiation**), or a `Protocol` for structural
typing on classes you don't own.
→ [oop.md](oop.md)

---

## 5. Iterators & generators

**Iterable vs iterator?**
Iterable defines `__iter__`; an **iterator** also defines `__next__`, holds position, and is
**single-use**.

**Why can I loop over a list twice but not a generator? ⭐**
`for` calls `iter()` on the list each time; a generator *is* its own iterator and exhausts
permanently — the second loop silently sees nothing.

**How would you process a file larger than RAM? ⭐⭐**
Iterate it lazily with a generator — one line in memory at a time — and chain generators into
a streaming pipeline.

**What does `yield` do?**
Suspends the function, returning a value while preserving **all local state** until the next
`next()`.

**How do you write a context manager, and what does `__exit__` returning `True` do? ⭐**
`__enter__`/`__exit__`, or `@contextmanager` with one `yield` inside try/finally. Returning
truthy from `__exit__` **suppresses the exception** — usually a bug.
→ [iterators.md](iterators.md)

---

## 6. Concurrency

**Threads vs processes vs asyncio — how do you choose? ⭐⭐**
CPU-bound → **multiprocessing** (real cores). I/O-bound → **threads**. Thousands of
concurrent I/O operations → **asyncio**. *"Threads for waiting, processes for computing,
asyncio for waiting at scale."*

**Why don't threads speed up CPU-bound Python?**
The GIL serialises bytecode; you pay switching overhead and gain no parallelism.

**Then why do threads help I/O?**
The GIL is **released** during blocking syscalls.

**What is a race condition and how do you prevent it?**
Unsynchronised concurrent access where the outcome depends on timing. Prevent with locks,
thread-safe queues, or by not sharing mutable state.

**How does a deadlock happen?**
Circular lock waits. Acquire locks in a consistent global order and use timeouts.

**Why is multiprocessing sometimes slower? ⭐**
Every argument and result is **pickled**, processes cost ~10–100 ms and tens of MB to start,
and large data gets duplicated per worker.

**Why does multiprocessing need `if __name__ == "__main__"`?**
With the `spawn` start method children re-import the module; without the guard they re-execute
the spawning code recursively.

**What's the fastest way to break an asyncio app? ⭐**
Any **blocking call** inside a coroutine (`time.sleep`, `requests`, a sync DB driver) — it
stalls the entire event loop. Offload with `asyncio.to_thread`.
→ [concurrency.md](concurrency.md)

---

## 7. Typing & tooling

**Are type hints enforced at runtime?**
No — metadata for static checkers and opt-in libraries (Pydantic, FastAPI, dataclasses).

**Static checking vs runtime validation? ⭐**
mypy verifies your code's internal consistency before it runs; Pydantic validates **untrusted
data at boundaries**. You need both — hints won't stop `{"age": "abc"}` from an API.

**ABC vs Protocol?**
Nominal (must inherit) vs **structural** (matching methods suffice) — Protocols let you type
duck-typed and third-party code.

**Why can't I pass `list[int]` where `list[float]` is expected?**
Mutable generics are **invariant**. Accept `Iterable[float]` instead — *accept the most
general type, return the most specific.*
→ [typing.md](typing.md)

---

## 8. Performance

**How do you approach "the app is slow"? ⭐**
Profile first (`cProfile` locally, **`py-spy`** on a live process), fix the **algorithm**,
and only then micro-optimise. Check **query counts** before Python CPU — an N+1 or a missing
index usually dominates.

**Why is `s += x` in a loop O(n²)?**
Strings are immutable; every concatenation copies. Use `"".join()`.

**Memory keeps growing — is it a leak?**
Not necessarily: Python retains freed arenas, so RSS reflects the peak. Confirm with
`tracemalloc`/`memray`; cap worker lifetime (`--max-requests`) for a high-water mark.

**How do you speed up CPU-bound Python?**
Better algorithm → **vectorise** (NumPy) → multiprocessing → native extension (Rust/Cython).
→ [performance.md](performance.md)

---

## 9. Rapid fire

| Question | Answer |
|---|---|
| `{}` creates a…? | **dict**. `set()` for an empty set. |
| `(1)` type? | `int`. A one-tuple is `(1,)`. |
| `0.1 + 0.2 == 0.3`? | **False** — binary floats. Use `Decimal` for money. |
| `-7 // 2`? | **−4** — floors toward −∞ (C gives −3). |
| Shallow vs deep copy | Shares children vs recursively copies. |
| `[[0]*3]*3` problem | Three references to **one** row. |
| `.keys()` returns? | A live **view**, supporting set operations. |
| `__slots__` does what? | Removes the per-instance `__dict__` — less memory, no dynamic attrs. |
| What's a descriptor? | An object controlling attribute access (`__get__`/`__set__`) — how `@property` and Django fields work. |
| Data vs non-data descriptor | Data (`__set__`) beats the instance `__dict__`; non-data loses to it. |
| EAFP vs LBYL | try/except vs check-first; EAFP is idiomatic and race-free. |
| `raise X from e` | Chains the cause and preserves the original traceback. |
| Module imported twice? | No — cached in `sys.modules`; top-level code runs **once**. |
| Pythonic singleton | **A module.** Import-cached and thread-safe by construction. |
| `strip(".txt")` removes? | Any of those **characters** from both ends. Use `removesuffix`. |
| `random` for a token? | ⚠️ No — use `secrets`. |
| `datetime.now()` | Naive. Use `datetime.now(timezone.utc)`. |
| `assert` for validation? | ⚠️ No — stripped by `python -O`. |
| `bool` and `int` | `bool` **subclasses** `int`; `True + True == 2`. |
| `lru_cache` on a method | Pins every `self` forever — a leak. |

---

## 10. The five traps to have ready

1. **Mutable default argument** — evaluated once at `def` time.
2. **Late binding closure** — captures the variable, not the value.
3. **`is` vs `==`** — small-int caching makes `is` look correct.
4. **`[[0]*3]*3`** — shared row references.
5. **The GIL** — released on I/O, and does *not* make `x += 1` atomic.

→ [pitfalls.md](pitfalls.md)
