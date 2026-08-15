# Algorithm Interviews — Method & Q&A

> Pattern triggers: **[patterns.md](patterns.md)** · Complexity budgets: **[complexity.md](complexity.md)**

---

## 1. The framework ⭐⭐

**How you get to the answer is graded as heavily as the answer.** A candidate who narrates this
sequence and writes a good-not-perfect solution usually beats one who silently types the optimal
one.

```
1. CLARIFY   (2 min)  — repeat the problem back; ask about inputs and edge cases
2. EXAMPLE   (2 min)  — walk a small case BY HAND; include an edge case
3. BRUTE     (2 min)  — state the naive approach and its complexity out loud
4. OPTIMISE  (5 min)  — what's recomputed? which pattern fits? get AGREEMENT before coding
5. CODE     (10 min)  — clean, named variables, narrate as you go
6. TEST      (5 min)  — trace your example; then the edge cases
7. ANALYSE   (2 min)  — time and space, and what you'd improve with more time
```

⚠️⚠️ **Coding before step 4 is the most common failure.** Fifteen minutes into the wrong
approach is unrecoverable; two minutes of agreement isn't.

**Questions to ask in step 1:**
- Input size? (⭐ this dictates the required complexity)
- Sorted? Duplicates? Negative numbers? Empty input?
- Can I modify the input? Is extra space allowed?
- Are the values bounded? Integers or floats?
- Is there always a valid answer, or do I return a sentinel?

⭐ **"What's the maximum n?"** is the highest-value question you can ask — it converts an open
design problem into a complexity target ([complexity.md §1](complexity.md)).

---

## 2. If you're stuck ⭐

In order — each is a legitimate, visible move:

1. **Say what you're thinking.** Silence is scored as being stuck; reasoning aloud is scored as
   problem-solving.
2. **Work a small example by hand** and look for the repeated work.
3. **Solve a simpler version** — smaller n, one dimension, no duplicates.
4. **Run the pattern list** — sorted? contiguous? all-combinations? top-k? min-such-that?
   ([patterns.md §1](patterns.md))
5. **Ask what's recomputed.** Every optimisation is *remember it* (hash map/DP), *keep it
   sorted* (binary search/heap), or *avoid re-scanning* (two pointers/window).
6. **Write the brute force anyway.** A working O(n²) beats an unfinished O(n).
7. **Take the hint.** Interviewers hint deliberately; ignoring one is a negative signal.

---

## 3. Edge cases to test every time ⭐

| Category | Cases |
|---|---|
| **Empty / tiny** | `[]`, `[x]`, `""`, single node, `n = 0` |
| **Boundaries** | first/last element, `k = 0`, `k = n`, `k > n` |
| **Duplicates** | all identical, repeated targets |
| **Signs** | ⭐ all negative, zeros, mixed |
| **Structure** | already sorted, reverse sorted, one long chain (⭐ degenerate BST) |
| **Overflow** | huge values (⭐ irrelevant in Python — *say so*) |
| **Not found** | target absent, disconnected graph, no valid answer |

⭐ **All-negative input** breaks naive Kadane's; **duplicates** break naive rotated binary
search and 3Sum; **empty input** breaks almost everything. Test those three unprompted.

---

## 4. Core Q&A

**How do you decide the approach? ⭐⭐**
From the constraints plus the keyword triggers. `n ≤ 20` → exponential is acceptable;
`n = 10⁵` → O(n log n) at worst; `n = 10⁷` → O(n). Then: sorted → two pointers/binary search;
contiguous → sliding window; all-combinations → backtracking; count/optimum → DP.

**What is Big-O actually measuring?**
Asymptotic growth with constants and lower-order terms dropped — not real runtime on small
inputs.

**Amortised vs average case? ⭐**
Amortised is a **guarantee over a sequence** (list append is O(1) amortised); average is
probabilistic over inputs (quicksort is O(n log n) average, O(n²) worst).

**When does sliding window fail? ⭐**
With negative numbers, or any non-monotone constraint — growing the window must move the
condition in one direction only. Use prefix sums + a hash map instead.

**Why is a monotonic stack O(n) when it contains a nested loop?**
Each element is pushed once and popped at most once — 2n operations total.

**Min-heap or max-heap for the k largest? ⭐**
A **min**-heap of size k: the root is the weakest survivor, so it's the cheapest to evict.
O(n log k).

**BFS or DFS for a shortest path? ⭐**
BFS — it explores by edge count, so a vertex is first reached by a minimum-length path. DFS
finds *a* path, not the shortest.

**Why does Dijkstra fail on negative edges? ⭐⭐**
It finalises a vertex when popped, assuming no cheaper route remains. A negative edge can
invalidate that, and it never revisits. Use Bellman–Ford.

**Directed vs undirected cycle detection? ⭐⭐**
Undirected: a visited neighbour that isn't the parent. Directed: a node still **on the current
recursion stack** — a plain visited set gives false positives on cross edges.

**What is union-find's complexity?**
O(α(n)) ≈ constant, **with both** path compression and union by rank; either alone is
O(log n).

**Why is 0/1 knapsack's inner loop reversed? ⭐⭐**
So `dp[w - wi]` still holds the previous item's row, preventing reuse. Forward iteration is
unbounded knapsack.

**What are the two requirements for DP?**
Optimal substructure and overlapping subproblems.

**DP vs greedy? ⭐**
Greedy commits to a local choice; DP evaluates all. Coin change with {1,3,4} for 6 — greedy
gives 3 coins, DP gives 2.

**Is `heapify` O(n log n)?**
⭐ No — **O(n)**.

**Can anything beat O(n log n) sorting?**
Not by comparison (log₂(n!) lower bound). Counting/radix sort can, for bounded integer keys.

**BIT or segment tree? ⭐**
BIT for prefix sums (invertible operations) — smaller and faster. Segment tree for range
min/max/gcd or range updates, since you can't subtract a minimum.

**What's the space complexity of recursion?**
O(depth) call stack, even with no data structures. ⚠️ Python's limit is ~1000 frames.

---

## 5. Python-specific answers ⭐

| Question | Answer |
|---|---|
| `x in list` complexity | ⭐ **O(n)** — convert to a set for O(1) |
| `list.pop(0)` | ⚠️ O(n) — use `collections.deque` |
| String `+=` in a loop | ⚠️ **O(n²)** — strings are immutable; use `join` |
| Max-heap? | ⭐ Negate values — `heapq` is min-only |
| Recursion limit | ~1000 — use an iterative stack for large graphs |
| `-7 // 2` | **−4** (floors toward −∞, unlike C) |
| Integer overflow | ⭐ None — arbitrary precision. *Mention it would matter in C++* |
| `sort()` returns | `None` — it sorts in place |
| Sort stability | ⭐ Timsort is stable, and O(n) on sorted input |
| Integer sqrt | `math.isqrt` — ⚠️ not `int(n**0.5)` |
| Memoise a function | `@functools.cache` — ⚠️ needs hashable arguments |

---

## 6. Communication ⭐

**Do:**
- Narrate the *why*: *"the array is sorted, so two pointers gets O(n) without extra space."*
- State complexity **before** coding, and confirm it after.
- Name your variables properly — `left/right`, not `i/j/k` everywhere.
- Say "let me test this" and actually trace it.
- Flag known weaknesses yourself: *"this doesn't handle duplicates yet — shall I add that?"*

**Don't:**
- Code in silence.
- Claim a complexity you haven't verified.
- Say "this is easy" (it ages badly).
- Argue with a hint.
- Pretend to know an algorithm you don't — ⭐ *"I know Manacher's solves this in O(n) but I'd
  need to look it up; here's the O(n²) centre-expansion version"* is a **good** answer.

⭐ **The strongest closing move:** state what you'd do with more time — *"I'd add the
`assertNumQueries`-style tests for the edge cases, and this could drop to O(n) space with a
rolling array."* It signals engineering judgement beyond the puzzle.

---

## 7. The ten that come up most

1. **Two Sum** → hash map, O(n).
2. **Maximum subarray (Kadane's)** → ⚠️ handle all-negative.
3. **Merge intervals** → sort by start, then sweep.
4. **Valid parentheses** → stack.
5. **Binary search + first/last occurrence** → the boundary template.
6. **Number of islands** → BFS/DFS/union-find on a grid.
7. **LRU cache** → ⭐ hash map + doubly linked list (or `OrderedDict`).
8. **Merge k sorted lists** → heap, O(n log k).
9. **Course schedule** → topological sort; short output means a cycle.
10. **Coin change / knapsack** → DP, and know the loop-direction rule.

⭐ **Know these ten cold** — not because they'll be asked verbatim, but because each is the
canonical instance of a pattern, and recognising the pattern is the actual skill.
