# Dynamic Programming

> Recursion first: **[../recursion_backtracking.md](../recursion_backtracking.md)** ·
> Pattern triggers: **[../patterns.md](../patterns.md)**

---

## 1. What DP is ⭐

**Breaking a problem into overlapping subproblems, solving each once, and reusing the answers.**

**Two conditions must both hold:**

1. ⭐ **Optimal substructure** — the optimal answer is built from optimal answers to
   subproblems. (⚠️ *Not* universal: longest *simple* path in a general graph has no optimal
   substructure, which is why it's NP-hard while shortest path is easy.)
2. ⭐ **Overlapping subproblems** — the same subproblem recurs. Without this it's just
   divide-and-conquer (merge sort has optimal substructure but *no* overlap, so caching buys
   nothing).

⭐ **How to recognise a DP problem:** it asks for a **count**, a **maximum/minimum**, or
**whether something is achievable**, and a greedy choice can be shown to fail. Words like
"how many ways", "minimum cost", "longest/largest", "can you reach".

---

## 2. Memoisation vs tabulation ⭐

| | **Top-down (memoisation)** | **Bottom-up (tabulation)** |
|---|---|---|
| Direction | big problem → subproblems | smallest → up |
| Form | recursion + cache | loops + table |
| Writes | ⭐ **easier — mirrors the recurrence** | needs an explicit ordering |
| Computes | ⭐ **only reachable states** | every state |
| Space | ⚠️ **O(depth) call stack** | ⭐ no stack; **rolling arrays** possible |
| Debugging | harder (deep stacks) | easier |

```python
from functools import cache

@cache                                    # ⭐ top-down in one line
def fib(n):
    return n if n < 2 else fib(n - 1) + fib(n - 2)
```

```python
def fib(n):                               # ⭐ bottom-up, O(1) space
    a, b = 0, 1
    for _ in range(n):
        a, b = b, a + b
    return a
```

⭐ **Strategy that works under pressure: write the brute-force recursion first, add `@cache`,
then convert to a table only if space or stack depth demands it.** Say that out loud — it shows
method rather than a memorised table.

⚠️ `@cache` needs **hashable** arguments — convert lists to tuples
([../../Language/Python/functions.md](../../Language/Python/functions.md)).
⚠️ Deep recursion hits Python's 1000-frame limit — that alone can force tabulation.

---

## 3. The five-step method ⭐⭐

**Use this framework aloud in an interview; it's worth more than the final code.**

1. **State** — what identifies a subproblem? *"`dp[i][w]` = max value using the first `i` items
   with capacity `w`."* ⭐ Getting the state right is 80% of the work.
2. **Recurrence** — how does this state build from smaller ones? Usually a *choice*:
   take it or skip it.
3. **Base cases** — the smallest states, and be careful with empty/zero.
4. **Order** — iterate so dependencies are ready (⚠️ this is where knapsack's reversed loop
   comes from).
5. **Answer** — which cell holds it? ⚠️ Sometimes it's `max(dp)`, not `dp[n]` (LIS).

---

## 4. The patterns ⭐

### 4.1 Linear — `dp[i]` from a fixed window

```
dp[i] = f(dp[i-1], dp[i-2], ..., dp[i-k])
```

**Climbing stairs / house robber / min cost path:**

```python
def rob(nums):                            # ⭐ O(1) space — only two states needed
    prev, cur = 0, 0
    for x in nums:
        prev, cur = cur, max(cur, prev + x)   # skip this house, or rob it + prev
    return cur
```

**Kadane's** is this pattern with `dp[i] = max(x, dp[i-1] + x)`
([../arrays_strings.md](../arrays_strings.md)).

### 4.2 Knapsack ⭐⭐

**The most important DP family** — pick a subset under a capacity constraint.

```python
def knapsack_01(weights, values, W):      # ⭐ each item AT MOST ONCE
    n = len(weights)
    dp = [[0] * (W + 1) for _ in range(n + 1)]
    for i in range(1, n + 1):
        wi, vi = weights[i - 1], values[i - 1]
        for w in range(W + 1):
            dp[i][w] = dp[i - 1][w]                       # skip item i
            if wi <= w:                                   # or take it
                dp[i][w] = max(dp[i][w], dp[i - 1][w - wi] + vi)
    return dp[n][W]
```

```python
def knapsack_01_1d(weights, values, W):   # ⭐ rolling array: O(n·W) → O(W)
    dp = [0] * (W + 1)
    for wi, vi in zip(weights, values):
        for w in range(W, wi - 1, -1):    # ⭐⭐ REVERSED — see below
            dp[w] = max(dp[w], dp[w - wi] + vi)
    return dp[W]
```

⭐⭐ **The reversed inner loop is the single most-asked DP detail.** Iterating `w` downward
means `dp[w - wi]` still holds the *previous* item's value — so each item is used at most once.
Iterate **forward** and you read an already-updated cell, allowing the item to be reused — which
is exactly **unbounded knapsack**:

```python
for w in range(wi, W + 1):                # ⭐ FORWARD → unlimited copies (coin change)
    dp[w] = max(dp[w], dp[w - wi] + vi)
```

**Coin change** (min coins) and **partition equal subset sum** (boolean knapsack) are the same
machinery.

⚠️ **Coin change: loop order changes the meaning.** Items outer / capacity inner counts
**combinations**; capacity outer / items inner counts **permutations**. Interviewers test this.

### 4.3 Two sequences — a 2-D grid ⭐

```python
def lcs(a, b):                            # longest common subsequence
    m, n = len(a), len(b)
    dp = [[0] * (n + 1) for _ in range(m + 1)]
    for i in range(1, m + 1):
        for j in range(1, n + 1):
            if a[i-1] == b[j-1]:
                dp[i][j] = dp[i-1][j-1] + 1               # ⭐ match → extend the diagonal
            else:
                dp[i][j] = max(dp[i-1][j], dp[i][j-1])    # skip one character
    return dp[m][n]
```

**Same shape:** edit distance (3 choices — insert/delete/replace), regex/wildcard matching,
distinct subsequences, shortest common supersequence.

⭐ **Longest common *substring*** differs: reset to 0 on a mismatch and track the running
maximum, because a substring must be contiguous.

### 4.4 Subsequence on one array

```python
def lis(nums):                            # ⭐ O(n log n) — patience sorting
    import bisect
    tails = []                            # tails[k] = smallest tail of a length-k+1 subsequence
    for x in nums:
        i = bisect.bisect_left(tails, x)  # ⚠️ bisect_right for NON-decreasing
        if i == len(tails): tails.append(x)
        else:               tails[i] = x
    return len(tails)
```

⭐ The O(n²) DP (`dp[i] = 1 + max(dp[j] for j < i if nums[j] < nums[i])`) is the expected first
answer; the O(n log n) version is the follow-up. ⚠️ `tails` is **not** a valid LIS — only its
length is meaningful.

### 4.5 Interval DP

```
dp[i][j] = best over the subarray i..j, combining dp[i][k] and dp[k+1][j]
```

⭐ **Iterate by increasing length**, not by index — smaller intervals must be ready first.
Matrix chain multiplication, burst balloons, longest palindromic subsequence. Usually O(n³).

### 4.6 DP on grids

```python
dp[i][j] = grid[i][j] + min(dp[i-1][j], dp[i][j-1])       # min path sum
```

⭐ Reducible to O(cols) with a rolling row. Unique paths, minimum path sum, maximal square.

### 4.7 DP on trees / DAGs

⭐ **Postorder traversal is tree DP**: compute children first, combine at the parent — house
robber III, tree diameter, max path sum ([../Tree/trees.md](../Tree/trees.md)).
On a DAG, relax in **topological order** ([../Graph/graph.md](../Graph/graph.md)).

### 4.8 Bitmask DP

`dp[mask][i]` — `mask` is the set of visited items, `i` the current one. For **n ≤ 20**:
travelling salesman, assignment problems, "minimum sessions". O(2ⁿ · n²)
([../math.md §4](../math.md)).

### 4.9 Digit DP

Count numbers ≤ N with a property. State: `(position, tight, started, extra)` — where `tight`
tracks whether the prefix still matches N's.

---

## 5. Space optimisation ⭐

```python
dp = [[0] * (W + 1) for _ in range(n + 1)]   # O(n·W)
dp = [0] * (W + 1)                            # ⭐ O(W) — when dp[i] needs only dp[i-1]
```

⭐ **The standard follow-up is "can you reduce the space?"** If `dp[i]` depends only on
`dp[i-1]`, keep one or two rows. ⚠️ The cost: you lose the full table, so **path
reconstruction becomes impossible** — keep the 2-D table if the problem asks *which* items were
chosen, not just the optimum.

---

## 6. Recognising the type ⭐

```
Choose items under a capacity?          → knapsack   (⚠️ reversed loop for 0/1)
Two strings/arrays compared?            → 2-D grid DP (LCS/edit distance)
"How many ways to reach"?               → counting DP, dp[i] = sum of predecessors
"Min/max cost to reach the end"?        → linear or grid DP
Subsequence within one array?           → LIS family
Splitting/merging a range?              → interval DP, iterate by length
n ≤ 20 with a set of used items?        → bitmask DP
On a tree?                              → postorder DP
Greedy seems right but has a counterexample? → ⭐ that's the DP tell
```

⭐ **DP vs greedy:** greedy makes a locally optimal choice and never revisits it; DP considers
every choice and keeps the best. **Coin change with coins {1, 3, 4} and target 6** — greedy
gives 4+1+1 = 3 coins, DP finds 3+3 = 2. If you can construct such a counterexample, it's DP.

---

## 7. Interview points

- **What are the two requirements for DP? ⭐** Optimal substructure and overlapping
  subproblems — both, or it's divide-and-conquer/greedy.
- **Memoisation vs tabulation?** Top-down recursion with a cache (easier, computes only what's
  reached, uses stack) vs bottom-up loops (no stack, allows rolling-array space reduction).
- **How do you approach a DP problem? ⭐⭐** Define the state, write the recurrence, set base
  cases, choose an iteration order, identify the answer cell — after starting from brute-force
  recursion.
- **Why does 0/1 knapsack iterate capacity in reverse? ⭐⭐** So `dp[w - wi]` still holds the
  previous item's row, preventing the item from being reused. Forward iteration gives
  *unbounded* knapsack.
- **0/1 vs unbounded knapsack in code?** Only the direction of the inner loop.
- **In coin change, does loop order matter? ⭐** Yes — items-outer counts combinations,
  capacity-outer counts permutations.
- **How do you optimise DP space?** Rolling arrays when `dp[i]` depends only on `dp[i-1]` —
  ⚠️ at the cost of path reconstruction.
- **LIS in better than O(n²)?** Patience sorting with binary search — O(n log n).
- **DP vs greedy? ⭐** Greedy commits to a local choice; DP explores all. Coin change {1,3,4}
  for 6 is the standard counterexample.
- **Is Dijkstra DP?** Arguably — it's a greedy algorithm with optimal substructure.
  **Floyd–Warshall** and **Bellman–Ford** are unambiguously DP.
- **How would you recover *which* items were chosen?** Keep the full table and walk backwards
  from the answer cell, or store parent pointers.
