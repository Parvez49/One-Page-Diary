# Algorithms & Data Structures — Index

DSA for **senior/staff interviews**. The emphasis is on **recognising which technique applies**
and being able to justify it — not on memorising solutions.

**Conventions:** ⭐ = high interview value · ⚠️ = a trap that produces wrong answers ·
every file ends with an **Interview points** section. Code is Python 3.

---

## Files

| File | Covers | Interview weight |
|---|---|---|
| [patterns.md](patterns.md) | ⭐⭐ **The recognition table** — two pointers, sliding window, prefix sums, monotonic stack, binary search on the answer, intervals, heaps, backtracking | ⭐⭐⭐ |
| [complexity.md](complexity.md) | **Constraints → complexity**, Big-O, master theorem, amortisation, space, operation costs | ⭐⭐⭐ |
| [searching_sorting.md](searching_sorting.md) | **Binary search templates**, `bisect`, rotated arrays, sorting comparison, Timsort, quickselect | ⭐⭐⭐ |
| [arrays_strings.md](arrays_strings.md) | **Kadane's**, prefix/difference arrays, in-place tricks, palindromes, matrices, hash-map techniques | ⭐⭐⭐ |
| [DynamicProgramming/dp.md](DynamicProgramming/dp.md) | The 5-step method, memo vs tabulation, **knapsack & the reversed loop**, LCS, LIS, interval/bitmask/tree DP | ⭐⭐⭐ |
| [Graph/graph.md](Graph/graph.md) | Representation, **BFS vs DFS**, cycle detection (directed vs not), **topological sort**, **union-find**, bipartite | ⭐⭐⭐ |
| [Graph/shortest_path.md](Graph/shortest_path.md) | **Choosing the algorithm**, Dijkstra, Bellman–Ford, Floyd–Warshall, **Kruskal vs Prim** | ⭐⭐⭐ |
| [Tree/trees.md](Tree/trees.md) | Traversals **and what each is for**, BST validation, balancing, heaps, tries | ⭐⭐⭐ |
| [recursion_backtracking.md](recursion_backtracking.md) | Recursion, divide & conquer, the **backtracking template**, combinations vs permutations, pruning | ⭐⭐ |
| [math.md](math.md) | GCD/Euclid, primes & sieve, modular arithmetic, **bit manipulation** | ⭐⭐ |
| [Tree/binary_indexed_tree.md](Tree/binary_indexed_tree.md) | Fenwick tree, `i & -i`, inversions, **BIT vs segment tree** | ⭐ |
| [Tree/segment_tree.md](Tree/segment_tree.md) | Range query + update, **lazy propagation**, when not to use one | ⭐ |
| [interview.md](interview.md) | **The 7-step framework**, what to ask, edge cases, Q&A, communication | ⭐⭐⭐ |

**Runnable code:** `Graph/dijkstra.py`, `Graph/bellman_ford.py`, `Graph/floyd_warshall.py`,
`Graph/mst.py` — each self-verifies with assertions (`python3 <file>`).

---

## Suggested study order

1. **[patterns.md](patterns.md)** — the highest-leverage file. Most problems are one of ~15
   patterns in disguise; learn the *trigger*, not the problem.
2. **[complexity.md](complexity.md)** — reading the constraints tells you the required
   complexity before you write anything.
3. **[searching_sorting.md](searching_sorting.md)** + **[arrays_strings.md](arrays_strings.md)**
   — the bread and butter of screening rounds.
4. **[Graph/graph.md](Graph/graph.md)** — BFS/DFS, topological sort, and union-find cover a
   large share of medium/hard problems.
5. **[DynamicProgramming/dp.md](DynamicProgramming/dp.md)** — the most-feared topic; the 5-step
   method makes it mechanical.
6. **[Tree/trees.md](Tree/trees.md)** + **[recursion_backtracking.md](recursion_backtracking.md)**
   — traversal shapes and the choose/explore/un-choose template.
7. **[Graph/shortest_path.md](Graph/shortest_path.md)** + **[math.md](math.md)** — depth.
8. **[Tree/segment_tree.md](Tree/segment_tree.md)** +
   **[Tree/binary_indexed_tree.md](Tree/binary_indexed_tree.md)** — specialised; know *when*
   they apply more than how to write them.
9. **[interview.md](interview.md)** — the framework, the day before.

---

## The answers worth memorising

| Question | Short answer |
|---|---|
| How do you pick an approach? ⭐⭐ | From **n**: ≤20 → exponential · 10⁵ → O(n log n) · 10⁷ → O(n). |
| Sorted array, find a pair | Two pointers — O(n), O(1) space. |
| Contiguous subarray + constraint | Sliding window — ⚠️ **unless negatives** → prefix sum + hash map. |
| "Min/max X such that…" ⭐ | **Binary search on the answer** (needs a monotone predicate). |
| Next greater element | Monotonic stack — O(n) amortised. |
| k largest | **Min**-heap of size k, O(n log k); quickselect O(n) for a one-off. |
| Shortest path, unweighted | **BFS** — DFS finds *a* path, not the shortest. |
| Shortest path, negative weights ⭐ | Bellman–Ford — Dijkstra finalises on pop and can't revisit. |
| Cycle in a **directed** graph ⭐ | Node still on the **recursion stack**, not merely visited. |
| Can all courses be finished? | Topological sort; fewer than V nodes output ⇒ cycle. |
| Repeated connectivity queries | Union-find, O(α(n)) with **both** optimisations. |
| 0/1 knapsack inner loop ⭐⭐ | **Reversed** — forward iteration means unbounded knapsack. |
| DP or greedy? | Greedy commits locally; coins {1,3,4} for 6 is the counterexample. |
| `heapify` cost | ⭐ **O(n)**, not O(n log n). |
| Validate a BST | Pass a (lo, hi) range down — parent comparison alone is wrong. |
| BIT or segment tree? | Prefix sums (invertible) vs range min/max or range updates. |
| Recursion space | O(depth) stack — ⚠️ Python caps at ~1000 frames. |

---

## Related directories

`../Language/Python/` — Python performance, data structures, and the pitfalls that turn a
correct algorithm into a slow one · `../Database/` — B-trees and indexing in practice ·
`../SDLC/` — design principles · `../Web/` · `../linux/`
