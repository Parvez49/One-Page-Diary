# Iterators, Generators & Context Managers

> Protocols: **[data_model.md](data_model.md)** · Async generators: **[concurrency.md](concurrency.md)**

---

## 1. The iteration protocol ⭐

```python
for x in obj: ...
```

is really:

```python
it = iter(obj)              # → obj.__iter__()
while True:
    try:    x = next(it)    # → it.__next__()
    except StopIteration:
        break
```

| Term | Defines | Note |
|---|---|---|
| **Iterable** | `__iter__` | can be looped over; `list`, `dict`, `str`, file |
| **Iterator** | `__iter__` **and** `__next__` | ⭐ stateful, **single-use**, `__iter__` returns `self` |
| **Generator** | (produced by `yield`) | an iterator Python writes for you |

```python
li = [1, 2, 3]
it = iter(li)
next(it), next(it), next(it)    # 1, 2, 3
next(it)                        # ⚠️ StopIteration
```

⭐ **A list is iterable but not an iterator** — that's why you can loop over a list twice
(each `for` calls `iter()` afresh) but **a generator or file object exhausts**:

```python
gen = (x for x in range(3))
list(gen)      # [0, 1, 2]
list(gen)      # ⚠️ [] — already consumed, silently empty
```

This "second loop sees nothing" bug is extremely common with `map`, `filter`, `zip`,
`csv.reader`, and generator expressions. If you need it twice, materialise: `data = list(gen)`.

**Custom iterator:**

```python
class Countdown:
    def __init__(self, n): self.n = n
    def __iter__(self): return self          # ⭐ iterator returns itself
    def __next__(self):
        if self.n <= 0: raise StopIteration
        self.n -= 1
        return self.n + 1
```

⭐ If `__iter__` returns a **new** object each time, the container is re-iterable (like a
list). If it returns `self`, it's a one-shot iterator. That choice is the whole design.

---

## 2. Generators ⭐⭐

`yield` turns a function into a **generator function** — calling it runs **no code** and
returns a generator object. Execution starts on the first `next()` and **suspends at each
`yield`, preserving all local state**.

```python
def read_large_file(path):
    with open(path) as f:
        for line in f:
            yield line.rstrip()        # ⭐ one line in memory at a time

for line in read_large_file("system.log"):
    if "ERROR" in line:
        print(line)
```

⭐⭐ **The killer argument: memory.** Reading a 10 GB log with `f.readlines()` needs 10 GB of
RAM; the generator above needs one line. This is *the* reason to know generators, and the
answer to "how would you process a file bigger than memory?"

```python
sum(x*x for x in range(10_000_000))    # ⭐ O(1) memory
sum([x*x for x in range(10_000_000)])  # ⚠️ ~400 MB list built first
```

| | list | generator |
|---|---|---|
| Memory | all items | ⭐ one at a time |
| Available immediately | yes | computed lazily |
| Re-iterable | ✅ | ❌ **single pass** |
| `len()` / indexing | ✅ | ❌ |
| Infinite sequences | ❌ | ⭐ ✅ |

```python
def naturals():                 # ⭐ infinite — impossible with a list
    n = 0
    while True:
        yield n; n += 1
```

**`yield from`** delegates to a sub-iterable (and forwards `send`/`throw`):

```python
def flatten(items):
    for x in items:
        if isinstance(x, list):
            yield from flatten(x)      # ⭐ recursive delegation
        else:
            yield x
```

**Generators as coroutines** — `send()` pushes a value *in*:

```python
def accumulator():
    total = 0
    while True:
        value = yield total            # ⭐ yield is an EXPRESSION here
        total += value

acc = accumulator()
next(acc)          # prime it — run to the first yield
acc.send(10)       # 10
acc.send(5)        # 15
```

This is the mechanism `asyncio` was originally built on (`yield from` → `await`).

⚠️ **`return` inside a generator** sets `StopIteration.value` rather than returning normally —
`yield from` captures it, a plain `for` loop discards it silently.

⚠️ Generators holding an open file/connection may not run their `finally`/`with` cleanup
promptly if abandoned mid-iteration — call `.close()` or wrap in `contextlib.closing`.

---

## 3. Pipelines with `itertools` ⭐

Chained generators = a streaming pipeline, constant memory:

```python
lines   = (l.rstrip() for l in open("access.log"))
errors  = (l for l in lines if " 500 " in l)
parsed  = (parse(l) for l in errors)
for record in parsed: ...      # ⭐ nothing executes until this line
```

```python
import itertools as it

it.chain(a, b)                    # concatenate iterables
it.islice(gen, 10)                # ⭐ take 10 — slicing for generators
it.groupby(sorted(rows, key=k), key=k)   # ⚠️ requires PRE-SORTED input
it.count(1), it.cycle(x), it.repeat(x)   # infinite
it.product(a, b), it.permutations(x, 2), it.combinations(x, 2)
it.takewhile(pred, x), it.dropwhile(pred, x)
it.tee(gen, 2)                    # ⭐ two independent copies of one generator
it.batched(iterable, 5)           # ⭐ 3.12+ fixed-size chunks
zip(a, b, strict=True)            # ⭐ 3.10+: raise if lengths differ
```

⚠️ **`groupby` only groups *consecutive* equal keys** — unsorted input silently yields
fragmented groups. Sort by the same key first.

⚠️ `tee` buffers whatever one branch reads ahead of the other; two branches consumed at very
different rates can hold most of the stream in memory.

---

## 4. Context managers ⭐⭐

`with` guarantees setup/teardown **even when an exception is raised** — the reason it exists.

```python
with open("f.txt") as f:      # __enter__ → f
    data = f.read()
# __exit__ runs here, on success OR exception
```

**Class-based:**

```python
class Timer:
    def __enter__(self):
        self.start = time.perf_counter()
        return self                              # ⭐ what `as x` binds

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.elapsed = time.perf_counter() - self.start
        return False        # ⭐⭐ False/None → propagate; True → SUPPRESS the exception
```

⚠️⚠️ **Returning a truthy value from `__exit__` swallows the exception.** Accidentally
returning `True` makes errors vanish silently — one of the nastiest bugs in this area. Return
`False` (or nothing) unless suppression is the explicit purpose.

**Generator-based — usually shorter:**

```python
from contextlib import contextmanager

@contextmanager
def transaction(conn):
    tx = conn.begin()
    try:
        yield tx                # ⭐ everything before = __enter__, after = __exit__
        tx.commit()
    except Exception:
        tx.rollback()
        raise                   # ⭐ re-raise: don't silently swallow
    finally:
        tx.close()
```

⚠️ Exactly **one** `yield`, and it must be inside `try`/`finally` if cleanup must survive an
exception in the body.

```python
from contextlib import suppress, closing, nullcontext, ExitStack

with suppress(FileNotFoundError):        # ⭐ cleaner than try/except/pass
    os.remove(path)

with ExitStack() as stack:               # ⭐ a DYNAMIC number of context managers
    files = [stack.enter_context(open(p)) for p in paths]

cm = open(p) if p else nullcontext()     # ⭐ conditional context manager

with open("a") as a, open("b") as b:     # multiple in one statement
    ...
```

**Where you'll actually use them:** DB transactions and connection pools, file handles, locks
(`with lock:`), temporary directories, `unittest.mock.patch`, `torch.no_grad()`,
`pytest.raises`, timing/profiling blocks.

---

## 5. Interview points

- **Iterable vs iterator?** Iterable has `__iter__`; an iterator also has `__next__`, holds
  position, and is single-use.
- **Why can I loop over a list twice but not a generator?** `for` calls `iter()` on the list
  each time; a generator *is* the iterator and exhausts permanently.
- **What does `yield` do?** Suspends the function, returning a value and preserving all local
  state until the next `next()`.
- **Generator vs list comprehension?** Lazy, O(1) memory, single-pass vs eager, indexable,
  re-iterable.
- **How do you process a file larger than RAM?** Iterate the file object / a generator
  pipeline — one line at a time.
- **What is `yield from`?** Delegate to a sub-iterator, forwarding values, `send`, and
  exceptions.
- **How do you write a context manager?** `__enter__`/`__exit__`, or `@contextmanager` with a
  single `yield` inside try/finally.
- **What happens if `__exit__` returns `True`?** The exception is **suppressed** — usually a
  bug.
- **Why use `with` instead of try/finally?** It's the same guarantee, less code, and the
  resource's lifetime is visible in one line.
- **What is `StopIteration`?** The signal an iterator is exhausted; `for` catches it. Inside a
  generator, `return` sets its `.value`.
