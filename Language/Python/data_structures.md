# Data Structures — Internals & Complexity

> Mutability & hashing: **[data_model.md](data_model.md)** · Lazy sequences: **[iterators.md](iterators.md)**

---

## 1. Choosing — the decision table ⭐

| Need | Use | Why |
|---|---|---|
| Ordered, mutable sequence | `list` | O(1) append/index |
| Fixed record, hashable | `tuple` | immutable → usable as a dict key |
| Key → value | `dict` | ⭐ O(1) average lookup, **insertion-ordered** since 3.7 |
| Membership / dedup | `set` | ⭐ O(1) `in` vs list's **O(n)** |
| Queue / both ends | `collections.deque` | ⭐ O(1) `popleft()`; list's `pop(0)` is **O(n)** |
| Counting | `collections.Counter` | `most_common()` built in |
| Grouping | `defaultdict(list)` | no `setdefault` boilerplate |
| Top-K / priority | `heapq` | O(log n) push/pop |
| Sorted insertion | `bisect` | binary search into a sorted list |
| Named record | `NamedTuple` / `dataclass` | readable fields, cheap |

⭐⭐ **The single highest-value fact here:** `x in some_list` is **O(n)**; `x in some_set` is
**O(1)**. Converting a list to a set before a membership loop turns O(n·m) into O(n) — the
most common real-world Python performance fix there is.

```python
# ⚠️ O(n × m) — quietly quadratic
dupes = [x for x in items if x in known_list]

# ⭐ O(n + m)
known = set(known_list)
dupes = [x for x in items if x in known]
```

---

## 2. Complexity cheat sheet

| Operation | list | deque | dict | set |
|---|---|---|---|---|
| index `x[i]` | **O(1)** | O(n) | — | — |
| `x[k]` lookup | — | — | **O(1)** avg | — |
| `in` | ⚠️ **O(n)** | O(n) | **O(1)** | **O(1)** |
| append / add | O(1)* | **O(1)** | O(1)* | O(1)* |
| `insert(0, v)` / `pop(0)` | ⚠️ **O(n)** | **O(1)** | — | — |
| `pop()` (end) | O(1) | O(1) | — | — |
| `remove(v)` | O(n) | O(n) | O(1) by key | O(1) |
| sort | O(n log n) | — | — | — |

\* amortised — occasional resize/rehash.

---

## 3. list

**Internals:** a dynamic array of **pointers** (not values), over-allocated so appends are
**amortised O(1)**. Growth is roughly 1.125×, and the list never shrinks on delete.

```python
li = [3, 1, 2]
li.append(4)              # end
li.extend([5, 6])         # ⭐ extend([x]) ≠ append([x])
li.insert(0, 0)           # ⚠️ O(n) — shifts everything
li.pop()                  # last (O(1))
li.pop(0)                 # ⚠️ O(n) — use deque
li.remove(3)              # by VALUE, first match, O(n)
li.index(2)               # position, raises ValueError if absent
li.count(2)
li.sort(key=len, reverse=True)   # ⭐ IN PLACE, returns None
li.reverse()
li.copy()                 # shallow — same as li[:]
```

⚠️ **`sort()` returns `None`** — `x = li.sort()` gives `None`. Use `sorted(li)` for a new
list. Same trap with `reverse()`, `append()`, `extend()`.

**Slicing:**

```python
li[2:5]      li[:3]      li[-3:]      li[::2]      li[::-1]   # ⭐ reversed copy
li[1:3] = [9, 9, 9]      # slice assignment can change length
del li[::2]
```

⭐ Slicing always produces a **shallow copy** — the outer list is new, the elements are shared.

**Sorting properly:**

```python
sorted(people, key=lambda p: (p.dept, -p.salary))   # ⭐ tuple key = multi-level sort
sorted(words, key=str.lower)
from operator import itemgetter, attrgetter
sorted(rows, key=itemgetter(2))                     # ⭐ faster than lambda
```

Python's **Timsort** is stable — equal elements keep their relative order, which is why
sorting by secondary key first then primary key works.

⚠️ **Mutating a list while iterating it skips elements:**

```python
for x in li:
    if cond(x): li.remove(x)      # ⚠️ silently skips

li = [x for x in li if not cond(x)]    # ⭐ rebuild instead
li[:] = [x for x in li if not cond(x)] # ⭐ in place, if other names reference it
```

---

## 4. dict ⭐⭐

**Internals:** an open-addressing hash table. Since **3.6/3.7** it's split into a compact
**index array** plus a dense **entries array** — which made dicts ~20% smaller *and* made
**insertion order a language guarantee** (3.7+).

```python
d = {"a": 1}
d["b"] = 2
d.get("z")                    # None — no KeyError
d.get("z", 0)                 # ⭐ default
d.setdefault("c", []).append(1)
d.pop("a", None)
d |= {"e": 5}                 # ⭐ 3.9+ merge   ({**a, **b} on older)
d.keys() / .values() / .items()      # ⭐ live VIEWS, not copies

for k, v in d.items(): ...
{v: k for k, v in d.items()}         # invert
```

⭐ **`.items()` returns a view** that reflects later changes and supports set operations
(`d1.keys() & d2.keys()` = shared keys). It's not a snapshot.

⚠️ **Changing dict size during iteration raises `RuntimeError`.** Iterate over
`list(d.keys())` if you must delete.

**Keys must be hashable** → immutable. A list key raises `TypeError`; a tuple works
(if its contents are hashable too).

```python
from collections import defaultdict, Counter, OrderedDict, ChainMap

groups = defaultdict(list)
for u in users:
    groups[u.dept].append(u)              # ⭐ no key-exists check

Counter(words).most_common(3)             # ⭐ top-3 in one line
ChainMap(cli_args, env_vars, defaults)    # ⭐ layered config lookup
```

⚠️ `defaultdict` **creates the key on read** — `d[missing]` inserts an empty list rather than
raising. Convenient, and a real source of quietly growing dicts.

`OrderedDict` is still useful for `move_to_end()` (LRU caches) and order-sensitive equality.

---

## 5. set

Hash table without values. Unordered, no duplicates, members must be hashable.

```python
s = {1, 2, 3}
empty = set()             # ⚠️ {} is an empty DICT
s.add(4);  s.discard(9)   # discard won't raise; remove() will

a | b    a.union(b)
a & b    a.intersection(b)
a - b    a.difference(b)
a ^ b    a.symmetric_difference(b)
a <= b   a.issubset(b)
```

⭐ **Set algebra replaces loops.** "Which users are in A but not B?" is `set_a - set_b` —
O(n) and one line instead of a nested loop.

`frozenset` is the immutable, **hashable** variant — usable as a dict key or set member.

---

## 6. tuple & records

```python
t = (1, 2)
x, y = t                 # unpacking
a, *rest = [1,2,3,4]     # ⭐ star unpacking
```

⚠️ **A single-element tuple needs the comma:** `(1,)`. `(1)` is just `1`.

```python
from typing import NamedTuple
from dataclasses import dataclass, field

class Point(NamedTuple):          # ⭐ immutable, tuple-compatible, tiny
    x: float
    y: float = 0.0

@dataclass(slots=True, frozen=True)    # ⭐ 3.10+: slots=True for memory
class User:
    name: str
    tags: list[str] = field(default_factory=list)   # ⭐⭐ NOT `= []`
```

⚠️⚠️ **Mutable default arguments** — the canonical Python trap, see
[pitfalls.md](pitfalls.md). In dataclasses, `field(default_factory=list)` is enforced;
in plain functions nothing stops you.

| Use | When |
|---|---|
| `NamedTuple` | immutable, indexable, lowest memory, tuple-compatible APIs |
| `@dataclass` | mutable records with methods, `__eq__`/`__repr__` generated free |
| `frozen=True` dataclass | immutable **and** hashable |
| `TypedDict` | you're stuck with real dicts (JSON) but want type checking |
| Pydantic | you need **runtime validation** and coercion at a boundary |

---

## 7. Comprehensions

```python
[x**2 for x in range(10) if x % 2]           # list
{x: x**2 for x in range(5)}                  # dict
{c for c in text if c.isalpha()}             # set
(x**2 for x in big)                          # ⭐ GENERATOR — lazy, O(1) memory
[y for row in matrix for y in row]           # ⭐ flatten: loops in for-statement order
```

⭐ **Use a generator expression when you only iterate once** — `sum(x*x for x in nums)`
never materialises a list. Inside `sum`/`any`/`max` the extra brackets are pure waste.

⭐ **`any()`/`all()` short-circuit:** `any(is_bad(x) for x in huge)` stops at the first hit.
`any([...])` with a list comp evaluates *everything* first — a real performance bug.

⚠️ Comprehensions have their **own scope** (3.x) — the loop variable doesn't leak. But
`:=` (walrus) inside one *does* bind outward, which is occasionally useful and often
confusing.

⚠️ Nested comprehensions past two levels are write-only code — use a loop.

---

## 8. Strings

```python
s.strip() / .lstrip() / .rstrip()     # ⭐ strips a SET OF CHARS, not a prefix
s.removeprefix("api_")                # ⭐ 3.9+ — what people wrongly expect strip to do
s.split(",")  / s.split()             # ⚠️ split() with no arg collapses ALL whitespace
",".join(parts)                       # ⭐ O(n) — never += in a loop
s.replace(a, b)  s.startswith(p)  s.casefold()
f"{value:>10.2f}"  f"{obj!r}"  f"{x=}"    # ⭐ f"{x=}" prints "x=5" — debugging gold
```

⚠️⚠️ **`"parvez.txt".strip(".txt")` returns `"parvez"` — by accident.** `strip` removes any
*characters* in the argument from both ends, so `strip(".txt")` also eats leading/trailing
`t`, `x`, `.`. Use **`removesuffix(".txt")`**.

**`str` vs `bytes`:** `str` is Unicode text; `bytes` is raw. `.encode()` / `.decode()`
convert. ⭐ `len("héllo")` counts **characters**, `len("héllo".encode())` counts **bytes** —
the source of most encoding bugs at I/O boundaries.

---

## 9. Interview points

- **When would you use a set over a list?** Membership tests and deduplication — O(1) vs O(n).
- **Are dicts ordered?** Yes, insertion-ordered — an implementation detail in 3.6, a
  **language guarantee** from 3.7.
- **How does a dict achieve O(1) lookup?** Hash table: hash the key to a slot, open addressing
  for collisions, resize when load factor is exceeded. Worst case is O(n).
- **Why must dict keys be immutable?** The hash must stay stable; a mutated key lands in the
  wrong bucket and becomes unreachable.
- **`list.pop(0)` vs `deque.popleft()`?** O(n) vs O(1) — use `deque` for queues.
- **`append` vs `extend`?** Adds one element vs adds every element of an iterable.
- **Why is `sort()` returning `None`?** It sorts in place; `sorted()` returns a new list.
- **Is Python's sort stable?** Yes (Timsort) — equal elements retain relative order, which
  enables multi-pass sorting.
- **List comprehension vs generator expression?** Eager list in memory vs lazy one-at-a-time
  — generators for large or single-pass data.
- **`[[0]*3]*3` — what's wrong?** All three rows are the *same* list object. Use a
  comprehension.
- **Why is string `+=` in a loop slow?** Strings are immutable, so each concat copies —
  O(n²). Use `join()`.
- **`strip(".txt")` didn't do what I expected.** It strips characters, not a suffix — use
  `removesuffix()`.
