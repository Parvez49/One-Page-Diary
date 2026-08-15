# Recursion & Backtracking

> Memoisation → **[DynamicProgramming/dp.md](DynamicProgramming/dp.md)** · Pattern triggers:
> **[patterns.md §10](patterns.md)**

---

## 1. Writing recursion that works ⭐

**Three parts, always:**

1. **Base case** — when to stop (⚠️ missing or unreachable → stack overflow).
2. **Recursive case** — solve a *strictly smaller* subproblem.
3. **Combine** — build this answer from the subproblem's.

```python
def solve(state):
    if is_base(state): return base_value       # ⭐ 1
    result = combine(solve(smaller(state)))    # ⭐ 2 + 3
    return result
```

⭐ **Trust the recursion.** The hardest habit is resisting the urge to trace every level.
Assume `solve(n-1)` is correct, then ask only: *"given that, how do I produce `solve(n)`?"*
Saying this out loud in an interview reads as fluency.

⚠️ **Every recursive call costs O(depth) stack space** — even with no data structures.
⚠️ **Python's default recursion limit is 1000**: a recursive DFS over 10⁵ nodes raises
`RecursionError`. Convert to an explicit stack, or raise the limit (⚠️ risking a real segfault).

**Recursion vs iteration:** recursion is clearer for tree/graph structure and divide-and-conquer;
iteration avoids stack cost. ⭐ **Tail recursion is *not* optimised in Python** — CPython
deliberately keeps full tracebacks, so a tail-recursive loop still grows the stack.

---

## 2. Divide and conquer

```python
def merge_sort(a):
    if len(a) <= 1: return a                   # base
    mid = len(a) // 2
    left, right = merge_sort(a[:mid]), merge_sort(a[mid:])   # ⭐ divide
    return merge(left, right)                                # ⭐ conquer
```

`T(n) = 2T(n/2) + O(n)` → **O(n log n)** by the master theorem
([complexity.md §3](complexity.md)).

**Family:** merge sort, quicksort, quickselect, binary search, "count inversions" (merge sort
with a counter), closest pair of points, and fast exponentiation:

```python
def power(x, n):                               # ⭐ O(log n), not O(n)
    if n == 0: return 1
    half = power(x, n // 2)
    return half * half * (x if n % 2 else 1)
```

---

## 3. Backtracking — the universal template ⭐⭐

**Systematic brute force with early abandonment.** Build a partial solution incrementally; the
moment it can't extend to a valid answer, undo and try something else.

```python
def backtrack(path, choices):
    if is_solution(path):
        result.append(path[:])                 # ⭐⭐ COPY — path keeps mutating
        return
    for choice in choices:
        if not is_valid(choice, path):
            continue                           # ⭐ PRUNE — where the speed comes from
        path.append(choice)                    # 1. choose
        backtrack(path, next_choices(choice))  # 2. explore
        path.pop()                             # 3. ⭐ UN-CHOOSE
```

⚠️⚠️ **The two bugs that account for nearly every failure:**
1. Forgetting `path.pop()` — state leaks into sibling branches.
2. Appending `path` instead of `path[:]` — every result is the *same list object*, and they all
   end up empty.

---

## 4. The four canonical shapes ⭐

**Subsets** — 2ⁿ, each element in or out:

```python
def subsets(nums):
    res = []
    def dfs(i, path):
        if i == len(nums):
            res.append(path[:]); return
        dfs(i + 1, path)                       # exclude
        path.append(nums[i]); dfs(i + 1, path); path.pop()   # include
    dfs(0, [])
    return res
```

**Combinations** — order doesn't matter, so pass a **start index** to prevent revisiting:

```python
def combine(n, k):
    res = []
    def dfs(start, path):
        if len(path) == k: res.append(path[:]); return
        for i in range(start, n + 1):          # ⭐ `start` forbids going backwards
            path.append(i); dfs(i + 1, path); path.pop()
    dfs(1, [])
    return res
```

**Permutations** — order matters, so use a `used` set instead of a start index:

```python
def permute(nums):
    res, used = [], [False] * len(nums)
    def dfs(path):
        if len(path) == len(nums): res.append(path[:]); return
        for i, x in enumerate(nums):
            if used[i]: continue
            used[i] = True;  path.append(x)
            dfs(path)
            path.pop();      used[i] = False   # ⭐ undo BOTH
        return
    dfs([])
    return res
```

⭐ **`start` index vs `used` array is the whole distinction between combinations and
permutations** — and a question interviewers ask directly.

**Handling duplicates** — sort first, then skip repeats at the same depth:

```python
nums.sort()
for i in range(start, len(nums)):
    if i > start and nums[i] == nums[i-1]: continue    # ⭐ skip duplicate SIBLINGS
```

⚠️ The condition is `i > start` (same level), not `i > 0` — the latter also blocks legitimate
reuse deeper in the tree.

---

## 5. Pruning — where the marks are ⭐

Backtracking without pruning is just brute force. **The pruning is the algorithm.**

```python
def combination_sum(candidates, target):
    candidates.sort()                          # ⭐ enables the break below
    res = []
    def dfs(start, remain, path):
        if remain == 0: res.append(path[:]); return
        for i in range(start, len(candidates)):
            if candidates[i] > remain:
                break                          # ⭐⭐ sorted → all later ones fail too
            path.append(candidates[i])
            dfs(i, remain - candidates[i], path)   # `i` not `i+1` → reuse allowed
            path.pop()
    dfs(0, target, [])
    return res
```

**Pruning strategies:** sort to enable early `break` · check feasibility before recursing
(remaining capacity, remaining items) · order choices most-constrained-first (N-Queens, sudoku)
· memoise repeated states (that's the bridge to DP) · keep a running best and abandon branches
that can't beat it (branch and bound).

**N-Queens** — the classic: track attacked columns and both diagonals in sets, so validity is
O(1) rather than O(n):

```python
cols, diag, anti = set(), set(), set()
if c in cols or (r - c) in diag or (r + c) in anti: continue   # ⭐ r-c and r+c identify diagonals
```

---

## 6. Complexity of backtracking

| Problem | Count | Total |
|---|---|---|
| Subsets | 2ⁿ | **O(2ⁿ · n)** (n to copy each) |
| Permutations | n! | **O(n! · n)** |
| Combinations C(n,k) | C(n,k) | O(C(n,k) · k) |
| N-Queens | — | ~O(n!) with pruning |

⭐ **Space is O(depth) for the stack plus O(size) for the current path** — the output itself is
usually excluded from "auxiliary space."

⭐ **This is why constraints tell you the approach**: `n ≤ 20` invites O(2ⁿ); `n ≤ 10` invites
O(n!) ([complexity.md §1](complexity.md)).

---

## 7. When recursion becomes DP ⭐

```python
def fib(n):                                    # ⚠️ O(2ⁿ) — recomputes the same subproblems
    return n if n < 2 else fib(n-1) + fib(n-2)

@functools.cache                               # ⭐ O(n) — memoisation, one line
def fib(n):
    return n if n < 2 else fib(n-1) + fib(n-2)
```

⭐ **The rule: if the recursion tree has *overlapping* subproblems, memoise it — that's
top-down DP.** If the branches are all distinct (subsets, permutations), memoisation buys
nothing and it stays backtracking.

⚠️ **Memoisation requires that a state's answer depend only on the state**, not on the path
taken to reach it. Backtracking problems that track a mutable path often violate this.

⚠️ `functools.cache` needs **hashable** arguments — convert lists to tuples, and beware caching
methods (it pins `self` forever;
[../Language/Python/functions.md](../Language/Python/functions.md)).

---

## 8. Interview points

- **What are the three parts of a recursive function?** Base case, smaller subproblem,
  combination step.
- **What's the space complexity of recursion? ⭐** O(depth) call stack, independent of any data
  structures.
- **Does Python optimise tail recursion?** ⭐ No — deliberately, to preserve tracebacks. Deep
  recursion needs an explicit stack.
- **Give the backtracking template. ⭐⭐** Choose → explore → un-choose, with pruning; copy the
  path when recording a result.
- **Combinations vs permutations in code? ⭐** A `start` index prevents revisiting earlier
  elements (order-insensitive); a `used` array allows any order (order-sensitive).
- **How do you avoid duplicate results?** Sort, then skip `nums[i] == nums[i-1]` when
  `i > start` — same-level siblings only.
- **Where does backtracking get its speed?** Pruning — abandoning branches that provably can't
  produce a solution.
- **When does backtracking become DP? ⭐** When subproblems overlap and depend only on the
  state — then memoise.
- **Why is naive Fibonacci O(2ⁿ)?** The tree recomputes the same subproblems exponentially
  often; caching makes it O(n).
- **Complexity of generating all subsets?** O(2ⁿ · n) — 2ⁿ subsets, O(n) to copy each.
- **Recursion or iteration?** Recursion for tree/graph and divide-and-conquer clarity;
  iteration when stack depth or performance matters.
