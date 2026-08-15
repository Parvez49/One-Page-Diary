# Searching & Sorting

> Binary search on the answer: **[patterns.md §7](patterns.md)** · Costs: **[complexity.md](complexity.md)**

---

## 1. Binary search — get the template right ⭐⭐

**Precondition: the search space must be monotone** (sorted, or a `False…True` predicate).

```python
def binary_search(a, target):                 # ⭐ the safe template
    lo, hi = 0, len(a) - 1
    while lo <= hi:                           # ⭐ <=  with an INCLUSIVE hi
        mid = lo + (hi - lo) // 2             # ⭐ overflow-safe idiom (matters in C++/Java)
        if a[mid] == target: return mid
        if a[mid] < target:  lo = mid + 1
        else:                hi = mid - 1
    return -1                                 # ⭐ lo is now the insertion point
```

⚠️⚠️ **The three ways people break binary search:**

1. **`while lo < hi` with `hi = len(a)-1`** — misses the last element.
2. **`lo = mid` instead of `lo = mid + 1`** — infinite loop when `hi = lo + 1`.
3. **Inconsistent bounds** — mixing an exclusive `hi = len(a)` with `hi = mid - 1`.

⭐ **Pick one template and never deviate.** Either `lo <= hi` with inclusive `hi = len(a)-1`
and `±1` on both sides, **or** the boundary form below. Don't mix them.

### The boundary form — what you actually need most ⭐

Finding the *first element satisfying a predicate* is more common than exact match:

```python
def first_true(lo, hi, pred):                 # ⭐ FFFF TTTT → returns the first T
    while lo < hi:                            # ⭐ <  with EXCLUSIVE hi
        mid = (lo + hi) // 2
        if pred(mid): hi = mid                # ⭐ keep mid — it may be the answer
        else:         lo = mid + 1
    return lo
```

This one template gives you: lower/upper bound, insertion point, rotated-array search, and
**binary search on the answer** ([patterns.md](patterns.md)).

---

## 2. `bisect` — use the stdlib ⭐

```python
import bisect

a = [1, 3, 3, 3, 5, 7]
bisect.bisect_left(a, 3)     # ⭐ 1 — leftmost insertion point (first ≥ x)
bisect.bisect_right(a, 3)    # ⭐ 4 — rightmost insertion point (first > x)
bisect.insort(a, 4)          # insert keeping order — ⚠️ O(n) due to the list shift
```

**The distinction that matters:**

| Need | Call |
|---|---|
| index of the first element **≥ x** | `bisect_left(a, x)` |
| index of the first element **> x** | `bisect_right(a, x)` |
| ⭐ **count of x** | `bisect_right(a,x) - bisect_left(a,x)` |
| does x exist? | `i = bisect_left(a,x); i < len(a) and a[i] == x` |

```python
bisect.bisect_left(a, x, key=lambda r: r.score)    # ⭐ 3.10+ key argument
```

**The implementations** (worth being able to write — the only difference is `<` vs `<=`):

```python
def bisect_left(a, x, lo=0, hi=None):
    hi = len(a) if hi is None else hi
    while lo < hi:
        mid = (lo + hi) // 2
        if a[mid] < x: lo = mid + 1           # ⭐  <   → skips past smaller only
        else:          hi = mid
    return lo

def bisect_right(a, x, lo=0, hi=None):
    hi = len(a) if hi is None else hi
    while lo < hi:
        mid = (lo + hi) // 2
        if a[mid] <= x: lo = mid + 1          # ⭐  <=  → also skips past equals
        else:           hi = mid
    return lo
```

---

## 3. Binary search variants ⭐

**Rotated sorted array** — one half is always sorted:

```python
def search_rotated(a, target):
    lo, hi = 0, len(a) - 1
    while lo <= hi:
        mid = (lo + hi) // 2
        if a[mid] == target: return mid
        if a[lo] <= a[mid]:                        # ⭐ LEFT half is sorted
            if a[lo] <= target < a[mid]: hi = mid - 1
            else:                        lo = mid + 1
        else:                                       # right half is sorted
            if a[mid] < target <= a[hi]: lo = mid + 1
            else:                        hi = mid - 1
    return -1
```

⚠️ With **duplicates** (`[3,1,3,3,3]`) you can't tell which half is sorted when
`a[lo] == a[mid]` — shrink with `lo += 1`, degrading to **O(n)** worst case.

**Other variants:** peak element (compare to the neighbour, no sorted array needed), median of
two sorted arrays (binary search the partition — O(log min(m,n))), search a 2-D matrix (treat
as one flat sorted array), and `√x` / "find the boundary" problems.

---

## 4. Sorting algorithms ⭐

| Algorithm | Avg | Worst | Space | Stable | Note |
|---|---|---|---|---|---|
| **Merge sort** | O(n log n) | ⭐ **O(n log n)** | O(n) | ⭐ **yes** | predictable; external/linked lists |
| **Quicksort** | O(n log n) | ⚠️ **O(n²)** | O(log n) | no | ⭐ fastest in practice (cache-friendly) |
| **Heapsort** | O(n log n) | O(n log n) | ⭐ **O(1)** | no | guaranteed + in-place, poor locality |
| **Insertion** | O(n²) | O(n²) | O(1) | yes | ⭐ **best for small/nearly-sorted** |
| **Counting/Radix** | ⭐ **O(n+k)** | O(n+k) | O(k) | yes | ⚠️ integers/bounded range only |
| Bubble/Selection | O(n²) | O(n²) | O(1) | yes/no | teaching only |

⭐ **The lower bound: comparison sorting cannot beat Ω(n log n)** — there are n! orderings and
each comparison yields one bit, so you need ≥ log₂(n!) ≈ n log n comparisons. Counting/radix
sort beat it only by *not comparing*.

**Quicksort partition:**

```python
def quicksort(a, lo, hi):
    if lo >= hi: return
    p = partition(a, lo, hi)                  # ⭐ pivot lands in its final position
    quicksort(a, lo, p - 1)
    quicksort(a, p + 1, hi)
```

⚠️ **Quicksort's O(n²)** hits when the pivot is always extreme — e.g. first-element pivot on
already-sorted input. Fixes: **random pivot**, median-of-three, or introsort (switch to
heapsort after a depth limit) — which is what C++'s `std::sort` does.

**Stability** — equal elements keep their input order. ⭐ It matters when you sort by multiple
keys in passes: sort by secondary key, then by primary, and stability preserves the secondary
order within ties.

---

## 5. Sorting in Python ⭐

```python
sorted(a)                                     # new list  — ⭐ Timsort
a.sort()                                      # in place, returns None ⚠️
sorted(people, key=lambda p: (p.dept, -p.age))   # ⭐ tuple key = multi-level sort
sorted(words, key=str.lower, reverse=True)
from operator import itemgetter
sorted(rows, key=itemgetter(2))               # ⭐ faster than a lambda
```

⭐ **Timsort** (Python, Java objects) is a hybrid merge/insertion sort that detects existing
sorted "runs" — **O(n) on already-sorted input**, O(n log n) worst, and **stable**.

⭐ **`key=` is evaluated once per element** (Schwartzian transform), unlike a comparator called
O(n log n) times. For a custom comparison, `functools.cmp_to_key` — but a key function is
almost always expressible and faster.

⚠️ `a.sort()` returns `None` — `x = a.sort()` is the classic bug
([../Language/Python/data_structures.md](../Language/Python/data_structures.md)).

---

## 6. Quickselect — kth element in O(n) ⭐

```python
import random

def quickselect(a, k):                        # ⭐ k-th smallest, 0-indexed
    lo, hi = 0, len(a) - 1
    while True:
        p = partition(a, lo, hi, random.randint(lo, hi))
        if   p == k: return a[p]
        elif p < k:  lo = p + 1               # ⭐ recurse into ONE side only
        else:        hi = p - 1
```

⭐ **O(n) average** — unlike quicksort, only one partition is explored, so the work is
n + n/2 + n/4 + … = 2n. ⚠️ O(n²) worst case; median-of-medians makes it O(n) worst but with a
constant nobody wants.

**When to prefer it over a heap:** one-shot "kth largest" on a static array. **Heap wins** for
streaming data or when you need all k elements in order
([patterns.md §9](patterns.md)).

---

## 7. Interview points

- **Write binary search.** ⭐ Then state the invariant and why `lo = mid + 1` (not `mid`)
  guarantees termination.
- **`bisect_left` vs `bisect_right`?** First index ≥ x vs first index > x; their difference is
  the count of x.
- **What breaks binary search?** Unsorted/non-monotone input, mixed bound conventions, and
  `lo = mid` causing an infinite loop.
- **Can you binary search something unsorted? ⭐** Yes — anything with a monotone predicate
  (peak finding, binary search on the answer).
- **Merge sort vs quicksort? ⭐** Both O(n log n) average; quicksort is faster in practice and
  O(log n) space but **O(n²) worst**; merge sort is stable with guaranteed bounds and O(n)
  space.
- **When is quicksort O(n²), and how do you avoid it?** Consistently extreme pivots — use
  random/median-of-three pivots or introsort.
- **What is stability and when does it matter?** Equal elements keep relative order — essential
  for multi-key sorting in passes.
- **Can any sort beat O(n log n)? ⭐** Not by comparison (information-theoretic bound); counting
  and radix sort can, for bounded integer keys.
- **What sort does Python use?** Timsort — stable, adaptive, O(n) on sorted input.
- **kth largest — heap or quickselect?** Quickselect for a one-off O(n) average; heap for
  streaming or when k results are needed, at O(n log k).
- **How do you sort by two keys?** A tuple `key=`, or two stable passes (secondary first).
