# Patterns — Recognising the Technique

> **The highest-value file here.** Most interview problems are one of ~15 patterns wearing a
> costume. Learn the *trigger*, not the problem.
> Complexity budgets: **[complexity.md](complexity.md)**

---

## 1. The recognition table ⭐⭐

| The problem says… | Reach for | Cost |
|---|---|---|
| sorted array, find a pair/triplet | ⭐ **two pointers** | O(n) |
| "contiguous subarray/substring", "at most k" | ⭐⭐ **sliding window** | O(n) |
| linked list cycle, find the middle | **fast & slow pointers** | O(n), O(1) space |
| repeated range-sum queries | ⭐ **prefix sum** | O(n) build, O(1) query |
| subarray **sums to k** (with negatives) | ⭐ **prefix sum + hash map** | O(n) |
| "next greater/smaller element", histogram | ⭐ **monotonic stack** | O(n) |
| max/min **in every window** | **monotonic deque** | O(n) |
| top-K, "k largest", merge k lists | ⭐ **heap** | O(n log k) |
| "minimum/maximum value such that…" | ⭐⭐ **binary search on the answer** | O(n log range) |
| all combinations/permutations/subsets | **backtracking** | O(2ⁿ) / O(n!) |
| overlapping/merging **intervals** | ⭐ **sort by start + sweep** | O(n log n) |
| grid/maze **shortest path**, unweighted | ⭐ **BFS** | O(V+E) |
| connectivity, "are these connected?" | ⭐ **union-find** | ~O(1) |
| count/optimise with overlapping subproblems | ⭐ **DP** | varies |
| "kth smallest" in a stream | two heaps / quickselect | O(log n) |
| anagram/frequency matching | hash map counter | O(n) |
| prefix matching, autocomplete | **trie** | O(len) |
| detect cycle / ordering with dependencies | **topological sort** | O(V+E) |

⭐ **Say the trigger out loud in an interview**: *"The array is sorted and I need a pair, so
two pointers gets this to O(n) without extra space."* That sentence is worth more than the code.

---

## 2. Two pointers

**Trigger:** sorted array · pair/triplet with a target · in-place partition/reversal.

```python
def two_sum_sorted(a, target):          # ⭐ O(n) time, O(1) space
    lo, hi = 0, len(a) - 1
    while lo < hi:
        s = a[lo] + a[hi]
        if s == target: return (lo, hi)
        if s < target:  lo += 1         # need bigger → move left pointer right
        else:           hi -= 1         # need smaller
    return None
```

⭐ **Why it's correct:** at each step one candidate is provably eliminated — if `a[lo]+a[hi]` is
too small, `a[lo]` can't pair with anything ≤ `a[hi]`, so discarding it loses no solution.
Being able to state that invariant is what separates memorised code from understanding.

**3Sum** = sort, fix one element, two-pointer the rest → O(n²). ⚠️ Skip duplicates at *both*
the fixed index and the moving pointers or you emit repeat triplets.

**Variants:** in-place `remove duplicates` (slow/fast write pointer), `reverse`, Dutch national
flag (3-way partition), `merge two sorted arrays` **backwards** to avoid a temp array.

---

## 3. Sliding window ⭐⭐

**Trigger:** *contiguous* subarray/substring + longest/shortest/count + a constraint.

```python
def longest_unique(s):                        # ⭐ variable-size window
    seen, left, best = {}, 0, 0
    for right, ch in enumerate(s):
        if ch in seen and seen[ch] >= left:
            left = seen[ch] + 1               # shrink past the previous occurrence
        seen[ch] = right
        best = max(best, right - left + 1)
    return best
```

```python
def min_subarray_len(target, nums):           # ⭐ shrink-while pattern
    left = total = 0
    best = float("inf")
    for right, v in enumerate(nums):
        total += v
        while total >= target:                # ⭐ shrink WHILE valid
            best = min(best, right - left + 1)
            total -= nums[left]; left += 1
    return 0 if best == float("inf") else best
```

⭐ **The template:** expand `right` always; move `left` only while the window is
invalid (for *longest*) or valid (for *shortest*). Each index enters and leaves once → **O(n)**,
even though there's a nested `while`.

⚠️⚠️ **Sliding window requires monotonicity** — adding an element must move the constraint in
one direction only. It **breaks with negative numbers**: "subarray sum = k" with negatives is
*not* a window problem, because growing the window can decrease the sum. Use prefix sums + a
hash map instead. This is the trap interviewers set.

**Fixed-size window:** add `nums[right]`, subtract `nums[right-k]` — no inner loop.

---

## 4. Fast & slow pointers (Floyd)

**Trigger:** linked list cycle, middle node, "find the duplicate number".

```python
def has_cycle(head):
    slow = fast = head
    while fast and fast.next:
        slow, fast = slow.next, fast.next.next
        if slow is fast: return True          # ⭐ they must meet inside a cycle
    return False
```

⭐ **Finding the cycle *start*:** after they meet, reset one pointer to the head and advance
both one step at a time — they meet at the entry. (The distance from head to entry equals the
distance from the meeting point to the entry, mod the cycle length.)

⭐ **"Find the duplicate in [1..n]"** is this problem in disguise: treat `i → nums[i]` as a
linked list; the duplicate forces a cycle. O(n) time, **O(1) space**, no array modification.

---

## 5. Prefix sums ⭐

**Trigger:** repeated range queries, or "subarray summing to k."

```python
pre = [0]
for x in nums: pre.append(pre[-1] + x)
range_sum = pre[j+1] - pre[i]                 # ⭐ O(1) per query
```

```python
def subarrays_with_sum_k(nums, k):            # ⭐⭐ works WITH negatives
    count, running = 0, 0
    seen = {0: 1}                             # ⭐ empty prefix — needed for exact matches
    for x in nums:
        running += x
        count += seen.get(running - k, 0)     # a previous prefix that closes the gap
        seen[running] = seen.get(running, 0) + 1
    return count
```

⭐ **This is the answer whenever sliding window fails on negatives.** The insight: a subarray
sums to k iff two prefix sums differ by k.

**Relatives:** 2-D prefix sums (submatrix sums via inclusion–exclusion), **difference arrays**
(range update O(1), then one pass to materialise), prefix XOR, prefix product.

---

## 6. Monotonic stack ⭐

**Trigger:** "next/previous greater or smaller element", histograms, temperatures, rain water.

```python
def next_greater(nums):                       # ⭐ O(n) despite the nested while
    res, stack = [-1] * len(nums), []         # stack holds INDICES, decreasing values
    for i, v in enumerate(nums):
        while stack and nums[stack[-1]] < v:
            res[stack.pop()] = v              # v is the next greater for that index
        stack.append(i)
    return res
```

⭐ **Why O(n):** every index is pushed once and popped at most once — 2n operations total. That
amortised argument is the follow-up question ([complexity.md §4](complexity.md)).

**Largest rectangle in a histogram** is the canonical hard case: maintain an increasing stack;
when a shorter bar arrives, pop and compute the area with the popped bar as the height.
**Trapping rain water** is solvable this way or with two pointers in O(1) space.

**Monotonic deque** — sliding window maximum: keep indices in decreasing order, pop from the
back while smaller, pop from the front when out of window → O(n).

---

## 7. Binary search on the answer ⭐⭐

**The most under-recognised pattern, and a strong senior signal.**

**Trigger:** *"minimum X such that a condition holds"* / *"maximum X that still fits"* — where
checking a candidate X is easy but computing the optimum directly is not.

```python
def min_capacity(weights, days):
    def feasible(cap):                        # ⭐ monotone: bigger cap is never worse
        need, cur = 1, 0
        for w in weights:
            if cur + w > cap: need, cur = need + 1, 0
            cur += w
        return need <= days

    lo, hi = max(weights), sum(weights)       # ⭐ bounds must bracket the answer
    while lo < hi:
        mid = (lo + hi) // 2
        if feasible(mid): hi = mid            # ⭐ keep mid — it might be the answer
        else:             lo = mid + 1
    return lo
```

⭐ **The requirement is monotonicity**: the predicate must be `False…False True…True` over the
search space. Then you're finding the boundary.

**Recognisable instances:** ship capacity in D days, Koko eating bananas, split array largest
sum, minimum time to complete jobs, "smallest divisor". They all look different and are all
this.

⚠️ The loop shape matters — `lo < hi` with `hi = mid` / `lo = mid + 1` converges on the first
`True` without an infinite loop. See [searching_sorting.md](searching_sorting.md).

---

## 8. Intervals & line sweep ⭐

**Trigger:** meetings, bookings, merging ranges, "maximum overlap".

```python
def merge(intervals):
    intervals.sort(key=lambda x: x[0])         # ⭐ sort by START — almost always step 1
    out = []
    for s, e in intervals:
        if out and s <= out[-1][1]:
            out[-1][1] = max(out[-1][1], e)    # overlap → extend
        else:
            out.append([s, e])
    return out
```

**Line sweep** — process sorted *events*, not intervals. Sweep a conceptual line across the
axis and maintain a running state:

```python
def min_meeting_rooms(intervals):              # ⭐ max concurrent overlap
    events = []
    for s, e in intervals:
        events.append((s, 1))                  # start: +1
        events.append((e, -1))                 # end:   -1
    events.sort()                              # ⚠️ ends before starts at equal time
    cur = best = 0
    for _, delta in events:
        cur += delta
        best = max(best, cur)
    return best
```

⭐ **The line-sweep insight:** you never need the intervals themselves, only the *transition
points*. It generalises to skyline problems, rectangle union area, and closest-pair-of-points.

⚠️ **Tie-breaking at equal coordinates decides the answer**: if a meeting ends exactly when
another starts, `(t, -1)` must sort before `(t, +1)` or you over-count rooms.

Alternative for "rooms": a **min-heap of end times** — pop while the earliest end ≤ current
start.

---

## 9. Heaps / top-K

**Trigger:** "k largest/smallest/most frequent", merge k sorted lists, running median.

```python
import heapq
heapq.nlargest(k, nums)                       # or:
h = []
for x in nums:                                # ⭐ O(n log k), not O(n log n)
    heapq.heappush(h, x)
    if len(h) > k: heapq.heappop(h)           # keep a MIN-heap of size k
```

⭐ **Counter-intuitive but standard: use a *min*-heap for the k *largest*.** The root is the
weakest survivor, so it's the cheapest thing to evict.

⚠️ Python's `heapq` is a **min-heap only** — negate values for a max-heap.

**Two heaps** (max-heap of the lower half + min-heap of the upper half) gives the **running
median** in O(log n) per insert.

⭐ **Quickselect** finds the kth element in **O(n) average** without a heap — worth naming as the
better answer when you only need one k.

---

## 10. Backtracking

**Trigger:** "all combinations/permutations/subsets", N-Queens, sudoku, word search.

```python
def subsets(nums):
    res, path = [], []
    def dfs(i):
        if i == len(nums):
            res.append(path[:])                # ⭐ COPY — path is mutated
            return
        dfs(i + 1)                             # exclude
        path.append(nums[i]); dfs(i + 1); path.pop()   # ⭐ choose → recurse → UNDO
    dfs(0)
    return res
```

⭐ **The shape is always: choose → explore → un-choose.** Forgetting the undo is the classic
bug; forgetting `path[:]` appends the same list object n times.

⭐ **Pruning is where the marks are** — abandon a branch as soon as it can't lead to a solution
(sorted input + `if remaining < 0: break`). Full detail in
[recursion_backtracking.md](recursion_backtracking.md).

---

## 11. Cyclic sort & in-place index tricks

**Trigger:** array contains numbers **1..n** (or 0..n−1); find missing/duplicate in O(1) space.

```python
def find_duplicates(nums):                     # ⭐ use the SIGN as a visited marker
    out = []
    for x in nums:
        i = abs(x) - 1
        if nums[i] < 0: out.append(abs(x))
        else:           nums[i] = -nums[i]
    return out
```

⭐ **The insight: the values *are* valid indices**, so the array can store its own visited set.
This is the O(1)-space follow-up when your hash-set answer is "correct but can you do better?"

---

## 12. Choosing under pressure ⭐

```
Sorted input?          → binary search / two pointers
Contiguous + constraint? → sliding window   (⚠️ unless negatives → prefix sum + map)
"All possible …"?      → backtracking
"Count/optimal ways"?  → DP
Grid/graph shortest?   → BFS (unweighted) · Dijkstra (weighted)
"Top k"?               → heap  ·  "kth once"? → quickselect
"Next greater"?        → monotonic stack
"Min/max X such that"? → ⭐ binary search on the answer
Intervals?             → sort by start, sweep
Connectivity?          → union-find
```

⭐ **If nothing matches: state the brute force, give its complexity, then find what's
recomputed.** Every optimisation is either "remember it" (hash map/DP), "keep it sorted"
(binary search/heap), or "avoid re-scanning" (two pointers/window).

---

## 13. Interview points

- **How do you choose an approach? ⭐⭐** From the constraints (n bounds the complexity) plus
  the keyword triggers — sorted, contiguous, all-combinations, top-k, min-such-that.
- **When does sliding window not work? ⭐** With negative numbers, or any non-monotone
  constraint — use prefix sums with a hash map.
- **Why is a monotonic stack O(n) with a nested loop?** Each element is pushed and popped at
  most once — amortised O(1) per element.
- **Min-heap or max-heap for the k largest?** ⭐ **Min**-heap of size k — the root is the
  easiest element to evict.
- **What makes binary search on the answer valid?** The feasibility predicate must be monotone
  across the search space.
- **How do you find a cycle's start in a linked list?** Floyd's — after they meet, restart one
  pointer at the head and step both by one.
- **Two pointers vs hash map for two-sum?** Sorted input → two pointers, O(1) space;
  unsorted → hash map, O(n) space but no sort.
- **Which pattern handles "subarray sums to k" with negatives?** Prefix sum + hash map of
  counts, seeded with `{0: 1}`.
- **What's the backtracking template?** Choose → recurse → un-choose, with pruning; copy the
  path when recording a solution.
- **When would you use union-find over DFS?** Incremental/dynamic connectivity queries, or
  Kruskal's MST — DFS answers connectivity once, union-find answers it repeatedly.
