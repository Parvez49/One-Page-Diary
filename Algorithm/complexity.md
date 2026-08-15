# Complexity — Big-O, Amortisation, Space

> Pattern selection: **[patterns.md](patterns.md)** · Python-specific costs:
> **[../Language/Python/data_structures.md](../Language/Python/data_structures.md)**

---

## 1. Reading the constraints ⭐⭐

**Before writing code, look at `n` — it tells you the required complexity.** This is the single
most useful trick in an algorithm interview: it turns "what approach?" into a lookup.

| n (max) | Required | Typical approach |
|---|---|---|
| ≤ 10–12 | **O(n!)**, O(2ⁿ·n) | permutations, brute-force backtracking |
| ≤ 20–25 | **O(2ⁿ)** | subsets, bitmask DP |
| ≤ 100 | O(n⁴) | 4 nested loops, Floyd–Warshall on 100 nodes |
| ≤ 500 | **O(n³)** | Floyd–Warshall, interval DP |
| ≤ 5,000 | **O(n²)** | ⭐ 2-D DP, all pairs |
| ≤ 10⁵–10⁶ | ⭐ **O(n log n)** | sort, heap, binary search, divide & conquer |
| ≤ 10⁷–10⁸ | **O(n)** | ⭐ two pointers, sliding window, hash map, prefix sum |
| ≥ 10⁹ | **O(log n)** / O(1) | binary search, math, bit tricks |

⭐ **Rule of thumb: ~10⁸ simple operations per second in C++, ~10⁶–10⁷ in Python.** So `n = 10⁵`
with an O(n²) solution is 10¹⁰ operations — hopeless. Saying *"n is 10⁵, so I need at worst
O(n log n), which rules out the nested-loop approach"* immediately signals you think about cost
before coding.

---

## 2. Big-O, Θ, Ω

- **O(f)** — upper bound ("at most"). What everyone means in interviews.
- **Ω(f)** — lower bound ("at least").
- **Θ(f)** — tight bound (both).

⭐ **Big-O describes growth as n → ∞, dropping constants and lower-order terms.** `O(3n² + 5n)`
is `O(n²)`. That's why an O(n log n) algorithm can lose to O(n²) on small inputs — Python's
`sort` switches to insertion sort for small runs for exactly this reason.

**Best / average / worst** are separate from O/Θ/Ω — quicksort is O(n log n) average and
**O(n²) worst**; a hash table is O(1) average and **O(n) worst** (all keys collide).

**Growth, slowest to fastest:**

```
O(1) < O(log n) < O(√n) < O(n) < O(n log n) < O(n²) < O(n³) < O(2ⁿ) < O(n!)
```

⚠️ **Common mis-statements to avoid:**
- "Binary search is O(log n) **because it halves**" — right idea; the point is that the number
  of halvings to reach 1 is log₂n.
- Nested loops are **not** automatically O(n²): `for i in range(n): for j in range(i, n)` is
  n(n+1)/2 = **O(n²)**, but `while j < n: j *= 2` inside a loop over n is **O(n log n)**.
- Recursion cost = (number of calls) × (work per call), **plus stack space**.

---

## 3. Analysing recursion — the Master Theorem ⭐

For `T(n) = a·T(n/b) + O(n^d)` (a subproblems of size n/b, plus O(n^d) to combine):

| Case | Result | Example |
|---|---|---|
| `d > log_b a` | **O(n^d)** — combining dominates | — |
| `d = log_b a` | ⭐ **O(n^d log n)** | **merge sort**: a=2, b=2, d=1 → O(n log n) |
| `d < log_b a` | **O(n^log_b a)** — recursion dominates | naive matrix mult |

**Worked examples:**

```
Binary search    T(n) = T(n/2) + O(1)     → a=1,b=2,d=0 → O(log n)
Merge sort       T(n) = 2T(n/2) + O(n)    → ⭐ O(n log n)
Fibonacci naive  T(n) = T(n-1) + T(n-2)   → ⚠️ O(φⁿ) ≈ O(1.618ⁿ)  — not master-theorem shaped
```

⭐ **When the theorem doesn't apply, count the recursion tree**: branching factor ^ depth.
Subsets = 2 choices × n items = **O(2ⁿ)**; permutations = **O(n!)**.

---

## 4. Amortised analysis ⭐

**The average cost per operation over a worst-case sequence** — not the average case.

```python
lst.append(x)     # ⭐ amortised O(1)
```

A Python list occasionally reallocates and copies (O(n)), but it over-allocates geometrically,
so n appends cost O(n) total → **O(1) amortised**. The individual slow operation is real, but
it's paid for by all the cheap ones before it.

⚠️ **Amortised ≠ average.** Quicksort is O(n log n) *average* (over random inputs); a dynamic
array append is O(1) *amortised* (guaranteed over any sequence). The amortised bound is a
worst-case guarantee for the sequence; the average-case bound is a probabilistic claim.

Other amortised results worth knowing: **union-find with path compression + union by rank** is
O(α(n)) ≈ O(1); **monotonic stack** loops look O(n²) but each element is pushed and popped at
most once → **O(n)** ([patterns.md](patterns.md)).

---

## 5. Space complexity ⭐

**Count auxiliary space** — extra memory beyond the input — and **don't forget the call stack**.

```python
def rec(n):
    if n == 0: return
    rec(n - 1)          # ⚠️ O(n) STACK space, even with no data structures
```

| Structure | Space |
|---|---|
| in-place two pointers | ⭐ O(1) |
| hash map / set of n items | O(n) |
| recursion depth d | ⭐ **O(d) stack** |
| 2-D DP table | O(n·m) — ⭐ often reducible to O(m) |
| merge sort | O(n) · **quicksort** O(log n) stack |
| BFS queue | O(width) · **DFS** O(depth) |

⭐ **The rolling-array trick**: when `dp[i]` depends only on `dp[i-1]`, keep two rows instead of
the whole table — O(n·m) → O(m). Interviewers ask for this as the follow-up
([DynamicProgramming/dp.md](DynamicProgramming/dp.md)).

⚠️ **Python's recursion limit is 1000** by default — a recursive DFS on a 10⁵-node graph
raises `RecursionError`. Convert to an explicit stack, or `sys.setrecursionlimit()` (⚠️ which
risks a real segfault).

---

## 6. The costs you're expected to know

| Operation | Complexity |
|---|---|
| array index | O(1) |
| ⭐ `x in list` | **O(n)** — the most common accidental O(n²) |
| ⭐ `x in set` / `dict[k]` | **O(1)** average, O(n) worst |
| `list.append` / `pop()` | O(1) amortised |
| ⚠️ `list.insert(0,x)` / `pop(0)` | **O(n)** — use `deque` |
| sort | O(n log n) |
| heap push/pop | O(log n) · **heapify O(n)** |
| ⭐ string concat in a loop | **O(n²)** — use `join` |
| slicing `a[i:j]` | O(j−i) — ⚠️ copies |
| BST search (balanced) | O(log n) · ⚠️ **O(n) if degenerate** |
| BFS/DFS | O(V + E) |
| Dijkstra (binary heap) | O(E log V) |

⚠️ **`heapify` is O(n), not O(n log n)** — a classic follow-up. Building a heap from a list is
linear because most nodes sink only a short distance.

---

## 7. Common trade-offs ⭐

- **Time vs space** — a hash map turns O(n²) two-sum into O(n) by spending O(n) memory. Say the
  trade aloud; it's the point of the question.
- **Preprocess vs query** — sorting costs O(n log n) once but makes every later query O(log n).
  Worth it above ~log n queries.
- **Read vs write** — an index speeds reads and slows writes ([../Database/](../Database/)).
- ⭐ **Amortised vs worst case** — a real-time system may prefer guaranteed O(log n) over
  amortised O(1) with occasional O(n) spikes.

---

## 8. Interview points

- **How do you pick an approach from the constraints? ⭐⭐** `n ≤ 20` → exponential is fine;
  `n = 10⁵` → O(n log n) at worst; `n = 10⁷` → O(n) only.
- **What does Big-O actually describe?** Asymptotic growth with constants dropped — not
  real-world runtime on small inputs.
- **Best vs average vs worst vs amortised?** Input-dependent bounds vs the guaranteed average
  over a *sequence* of operations.
- **Why is `list.append` O(1) if it sometimes reallocates?** Geometric over-allocation makes n
  appends O(n) total.
- **Is `heapify` O(n log n)?** ⭐ No — **O(n)**.
- **What's the complexity of `x in my_list`?** O(n) — convert to a set for O(1) membership.
- **Does recursion use space?** Yes — O(depth) call stack, even with no data structures.
- **Quicksort vs merge sort complexity?** Both O(n log n) average; quicksort is **O(n²) worst**
  but O(log n) space, merge sort is stable and O(n) space.
- **When is O(n²) acceptable?** When n is small and bounded, or when the constant factor and
  simplicity beat an asymptotically better algorithm.
- **How do you analyse `T(n) = 2T(n/2) + O(n)`?** Master theorem case 2 → **O(n log n)** (merge
  sort).
