# Performance — Profiling & Optimisation

> Complexity table: **[data_structures.md](data_structures.md)** · Parallelism: **[concurrency.md](concurrency.md)** ·
> System-level triage: **[../../linux/performance.md](../../linux/performance.md)**

---

## 1. Measure first ⭐⭐

**The order that actually works:** measure → find the hot spot → fix the *algorithm* → only
then micro-optimise. Most "slow Python" is an O(n²) loop or an N+1 query, not the
interpreter.

```bash
python -m cProfile -s cumtime app.py | head -30     # ⭐ where time goes, by function
python -m cProfile -o prof.out app.py               # then: snakeviz prof.out
py-spy top --pid 1234                               # ⭐⭐ sample a RUNNING process, no restart
py-spy record -o flame.svg --pid 1234               # flame graph
```

```python
import timeit
timeit.timeit("'-'.join(map(str, range(100)))", number=10_000)   # ⭐ micro-benchmarks

import cProfile, pstats
with cProfile.Profile() as pr:
    main()
pstats.Stats(pr).sort_stats("cumtime").print_stats(20)
```

⭐ **`py-spy` is the production tool** — it attaches to a live process with no code changes,
no restart, and negligible overhead. `cProfile` adds significant overhead and needs you to
run the code yourself.

**Line-level and memory:**

```bash
pip install line_profiler memray
kernprof -lv script.py          # @profile decorator → per-line timings
memray run script.py && memray flamegraph memray-*.bin    # ⭐ memory allocations
```

```python
tracemalloc.start(); ...; tracemalloc.get_traced_memory()   # stdlib memory snapshots
sys.getsizeof(obj)              # ⚠️ SHALLOW — a list of lists reports only the pointers
```

⚠️ **Never optimise from intuition.** The classic waste is rewriting a function that
accounts for 2% of runtime while an accidental O(n²) `in list` check next to it accounts for
90%.

---

## 2. Algorithmic wins — the big ones ⭐

```python
# ⚠️ O(n × m)                        # ⭐ O(n + m)
[x for x in a if x in b_list]        known = set(b_list)
                                     [x for x in a if x in known]

# ⚠️ O(n²) string building           # ⭐ O(n)
for x in items: s += x               s = "".join(items)

# ⚠️ O(n) per op                     # ⭐ O(1)
li.pop(0) / li.insert(0, x)          deque.popleft() / appendleft()

# ⚠️ repeated sorting                # ⭐ O(n log k)
sorted(data)[:10]                    heapq.nsmallest(10, data)

# ⚠️ recomputing in a loop           # ⭐ hoist / cache
for x in xs: f(config())             cfg = config(); for x in xs: f(cfg)
```

⭐ **The single most valuable habit: know which operations are O(n).** `x in list`,
`list.pop(0)`, `list.insert(0, …)`, `del list[0]`, and string `+=` are the five that silently
turn linear code quadratic.

**Caching:**

```python
@functools.cache                       # ⭐ pure functions, deterministic, hashable args
def fib(n): return n if n < 2 else fib(n-1) + fib(n-2)

@functools.lru_cache(maxsize=1024)     # bounded
@functools.cached_property             # per instance, computed once
```

⚠️ `lru_cache` on a **method** pins every `self` in memory forever
([pitfalls.md](pitfalls.md)).

---

## 3. Interpreter-level costs

**What's actually expensive in CPython:** attribute lookup, function calls, and creating
objects — each is a dict lookup or an allocation, not a machine instruction.

```python
# ⭐ Hoist attribute lookups out of hot loops
append = result.append          # bind ONCE
for x in items: append(f(x))    # vs result.append(x) — a lookup per iteration

# ⭐ Push the loop into C
total = sum(x * x for x in nums)                # C-level loop
squares = list(map(str, nums))                  # map with a builtin beats a comprehension
data = [row for row in rows if row.ok]          # comprehension beats append-in-loop

# ⭐ Local variables are faster than globals (array index vs dict lookup)
def hot(n, _len=len): ...
```

⭐ **The general principle: do less work *in Python*.** Every operation you push into a C
builtin (`sum`, `map`, `join`, `sorted`, `any`, set operations) or a C library (NumPy,
Polars, `re`) skips the interpreter loop entirely — typically 10–100×.

⚠️ These micro-optimisations buy percentages; the algorithmic fixes in §2 buy orders of
magnitude. Apply them only inside a profiler-confirmed hot loop, and never at the cost of
readability elsewhere.

---

## 4. Memory

```python
__slots__ = ("x", "y")          # ⭐ ~40-50% less per instance — see data_model.md
(x for x in big)                # generator: O(1) instead of O(n)
array.array("i", nums)          # compact numeric storage
np.array(nums)                  # ⭐ contiguous, typed, vectorised
sys.intern(s)                   # dedupe millions of repeated strings
```

⭐ **Streaming beats loading.** Process a 10 GB file line by line
([iterators.md](iterators.md)); read a large query with `yield_per`/server-side cursors
instead of `fetchall()`.

⚠️ **Python rarely returns freed memory to the OS** — RSS reflects the *peak*
([execution_model.md](execution_model.md)). For long-lived workers, cap lifetime
(gunicorn `--max-requests 1000 --max-requests-jitter 100`) rather than hunting a phantom leak.

**Real leaks** come from: unbounded caches/dicts, `lru_cache` on methods, accumulating
lists/logs, un-cancelled asyncio tasks, and reference cycles involving C extensions. Confirm
with `tracemalloc` snapshots or `memray` before theorising.

---

## 5. I/O — usually the real bottleneck ⭐

In a typical web service, Python CPU time is a small fraction; the database and network
dominate.

```python
# ⚠️ N+1 queries — the most common performance bug in Django/SQLAlchemy apps
for order in Order.objects.all():
    print(order.customer.name)          # one query PER ROW

# ⭐ one or two queries
Order.objects.select_related("customer")        # SQL JOIN (FK / one-to-one)
Order.objects.prefetch_related("items")         # second query + join in Python (M2M)
```

```python
Model.objects.bulk_create(objs, batch_size=1000)      # ⭐ not a save() per row
Model.objects.only("id", "name")                      # don't fetch unused columns
session.execute(stmt.execution_options(yield_per=1000))
requests.Session()                                     # ⭐ connection reuse + keep-alive
```

⭐ **Check the query count before the Python profiler** — `django-debug-toolbar`,
`EXPLAIN ANALYZE`, or an APM trace. A missing index or an N+1 is worth more than every
micro-optimisation in this file combined. See
[../../Database/](../../Database/).

**Then caching layers:** Redis for computed results, HTTP caching headers, and materialised
views — reducing work beats speeding it up.

---

## 6. When Python isn't enough

| Approach | Use when |
|---|---|
| **NumPy / Polars / DuckDB** | ⭐ array or tabular math — vectorise, don't loop |
| **`multiprocessing`** | CPU-bound and parallelisable across cores |
| **PyPy** | long-running pure-Python workloads (JIT, often 3–10×) |
| **Cython / mypyc** | a profiled hot function you can annotate and compile |
| **Rust (PyO3/maturin)** | ⭐ the modern choice for a new native extension |
| **C extension** | existing C library to wrap |

⭐ **Vectorising is usually the win.** A NumPy operation over a million elements runs one C
loop; the Python equivalent runs a million interpreter iterations. Reach for a native
extension only after the algorithm, the queries, and vectorisation are all exhausted.

---

## 7. Interview points

- **How do you find a performance problem?** Profile first — `cProfile` locally, `py-spy` in
  production — then fix the algorithm before micro-optimising.
- **Why is `x in list` slow?** Linear scan; a `set` is O(1) hashed lookup.
- **Why is `s += x` in a loop O(n²)?** Strings are immutable, so each concatenation copies.
  Use `join`.
- **How would you process a 50 GB file?** Stream it with a generator — constant memory — and
  parallelise by chunk if CPU-bound.
- **Your service's memory keeps growing — leak or not?** Check whether it plateaus. Python
  retains freed arenas, so a high-water mark isn't a leak; confirm with `tracemalloc`/`memray`
  and cap worker lifetime.
- **How do you speed up CPU-bound Python?** Better algorithm → vectorise (NumPy) →
  multiprocessing → native extension. Threads don't help (GIL).
- **What's an N+1 query and how do you fix it?** One query per row from lazy relations; fix
  with `select_related`/`prefetch_related` or an explicit join.
- **Is `functools.cache` always safe?** Only for pure functions with hashable args; it's
  unbounded, and on methods it leaks instances.
- **`sys.getsizeof` on a list of lists?** Shallow — it counts pointers, not the contents.
- **When would you rewrite in another language?** After profiling shows an irreducible
  CPU-bound hot spot that vectorisation and parallelism can't address.
