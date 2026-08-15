# Arrays & Strings

> Which technique to use: **[patterns.md](patterns.md)** · Python costs:
> **[../Language/Python/data_structures.md](../Language/Python/data_structures.md)**

---

## 1. Kadane's algorithm — maximum subarray ⭐⭐

Find the contiguous subarray with the largest sum.

```
[-2, 1, -3, 4, -1, 2, 1, -5, 4]  →  6   (the subarray [4,-1,2,1])
```

```python
def max_subarray(nums):
    best = float("-inf")      # ⭐ the answer so far
    cur  = 0                  # ⭐ best sum ENDING at the current index
    for x in nums:
        cur = max(x, cur + x)     # ⭐ extend the previous run, or start fresh at x
        best = max(best, cur)
    return best
```

⭐ **The insight (and the DP framing interviewers want):** at each index you make one decision —
*extend the previous subarray or start a new one here*. If the running sum has gone negative it
can only hurt whatever follows, so you drop it. That's `dp[i] = max(nums[i], dp[i-1] + nums[i])`
with O(1) space.

⚠️⚠️ **The all-negative case is the standard bug.** Initialising `best = 0` returns 0 for
`[-3,-1,-2]` instead of −1. Start `best` at `-inf` (or `nums[0]`), and **update `best` before**
resetting the running sum. Your earlier version reset `cur` to 0 *after* comparing, which is
correct — but only because the comparison came first; the `max(x, cur+x)` form makes it
unambiguous.

**Variants:** return the **indices** (track where `cur` restarted), maximum **product**
subarray (⭐ track both max *and* min, since a negative flips them), circular maximum subarray
(answer = max(normal Kadane, total − minimum subarray)), and 2-D maximum submatrix (fix a
column pair, Kadane the row sums → O(n³)).

---

## 2. Prefix sums & difference arrays ⭐

```python
pre = [0]
for x in nums: pre.append(pre[-1] + x)
# sum(nums[i..j]) == pre[j+1] - pre[i]        ⭐ O(1) per query after O(n) build
```

**Difference array** — many range updates, one final read:

```python
diff = [0] * (n + 1)
for l, r, v in updates:                        # ⭐ O(1) per range update
    diff[l] += v
    diff[r + 1] -= v
arr = list(itertools.accumulate(diff[:n]))     # materialise once, O(n)
```

⭐ **The duality worth stating:** prefix sums make *queries* O(1) with O(n) preprocessing;
difference arrays make *updates* O(1) with O(n) finalisation. Need both to be fast and dynamic?
That's a **Fenwick tree** ([Tree/binary_indexed_tree.md](Tree/binary_indexed_tree.md)).

**2-D prefix sum** (submatrix sum by inclusion–exclusion):

```python
S[i][j] = M[i][j] + S[i-1][j] + S[i][j-1] - S[i-1][j-1]
sum(r1..r2, c1..c2) = S[r2][c2] - S[r1-1][c2] - S[r2][c1-1] + S[r1-1][c1-1]
```

Also: **prefix XOR** (`xor(i..j) = pre[j+1] ^ pre[i]`) and prefix products for
"product of array except self" (prefix × suffix, O(1) extra space).

---

## 3. In-place array manipulation

```python
def remove_duplicates(a):                     # sorted; return new length
    write = 1                                 # ⭐ slow pointer = write position
    for read in range(1, len(a)):
        if a[read] != a[write - 1]:
            a[write] = a[read]; write += 1
    return write
```

```python
def rotate(a, k):                             # ⭐ reverse three times — O(1) space
    k %= len(a)
    a.reverse(); a[:k] = reversed(a[:k]); a[k:] = reversed(a[k:])
```

⭐ **The reverse-thrice rotation is a classic** — reverse everything, then reverse each part.
No extra array, no modular index juggling.

**Dutch national flag** (sort 0s/1s/2s in one pass):

```python
lo = mid = 0; hi = len(a) - 1
while mid <= hi:
    if   a[mid] == 0: a[lo], a[mid] = a[mid], a[lo]; lo += 1; mid += 1
    elif a[mid] == 2: a[hi], a[mid] = a[mid], a[hi]; hi -= 1     # ⚠️ don't advance mid
    else: mid += 1
```

⚠️ After swapping with `hi` you must **not** advance `mid` — the value swapped in is unexamined.

**Index-as-storage tricks** (values are 1..n): negate `a[abs(x)-1]` to mark visited, or cyclic
sort to place each value at its index — both give O(1)-space missing/duplicate detection
([patterns.md §11](patterns.md)).

---

## 4. Strings ⭐

⚠️⚠️ **Strings are immutable in Python** — every `s += x` copies, making a loop **O(n²)**.
Build a list and `"".join(parts)` (O(n)), or use `io.StringIO`.

```python
from collections import Counter, defaultdict

Counter(s) == Counter(t)                      # ⭐ anagram check, O(n)
sorted(s) == sorted(t)                        # O(n log n) — worse

groups = defaultdict(list)                    # ⭐ group anagrams
for w in words:
    groups[tuple(sorted(w))].append(w)        # or a 26-length count tuple → O(n·k)
```

**Palindromes:**

```python
def longest_palindrome(s):                    # ⭐ expand around centre — O(n²), O(1) space
    def expand(l, r):
        while l >= 0 and r < len(s) and s[l] == s[r]: l -= 1; r += 1
        return s[l+1:r]
    best = ""
    for i in range(len(s)):
        for cand in (expand(i, i), expand(i, i + 1)):   # ⭐ odd AND even centres
            if len(cand) > len(best): best = cand
    return best
```

⚠️ **Forgetting even-length centres** misses `"abba"` — the most common bug here. Manacher's
algorithm does it in O(n) but is rarely required; know it exists.

**Pattern matching:** naive is O(n·m). **KMP** is O(n+m) using a prefix-function table that
tells you how far to shift on a mismatch instead of restarting. **Rabin–Karp** uses a rolling
hash — ⭐ the right answer for *multiple* pattern searches or "find repeated substrings",
with the caveat of hash collisions.

⭐ **Encoding matters:** `len("héllo")` counts **characters**; `len("héllo".encode())` counts
**bytes**. Interview problems assume ASCII; production code doesn't get to.

---

## 5. Matrix problems

```python
zip(*matrix)                                  # ⭐ transpose
[list(r) for r in zip(*matrix[::-1])]         # ⭐ rotate 90° clockwise
```

⭐ **In-place rotation = transpose, then reverse each row.** Stating that decomposition is worth
more than nested index arithmetic.

**Spiral traversal** — maintain four boundaries (`top, bottom, left, right`) and shrink after
each pass; ⚠️ check `top <= bottom` and `left <= right` *between* passes or you double-traverse
the middle row of an odd-sized matrix.

**Set matrix zeroes in O(1) space:** use the first row and column as the marker storage, with
two extra flags for the first row/column themselves.

**Grid traversal** is graph traversal — BFS for shortest path, DFS/union-find for connected
components ([Graph/graph.md](Graph/graph.md)):

```python
DIRS = ((0,1), (1,0), (0,-1), (-1,0))
for dr, dc in DIRS:
    nr, nc = r + dr, c + dc
    if 0 <= nr < rows and 0 <= nc < cols and grid[nr][nc] == "1":
        ...
```

---

## 6. Hash-map techniques ⭐

```python
seen = {}                                     # ⭐ two-sum: value → index, one pass
for i, x in enumerate(nums):
    if target - x in seen: return [seen[target - x], i]
    seen[x] = i
```

⭐ **The general move: trade O(n) space for O(n) time** by remembering what you've seen instead
of re-scanning. Two-sum, subarray-sum-k, longest consecutive sequence, and first-unique-character
are all the same idea.

**Longest consecutive sequence** in O(n): put everything in a set, then only start counting from
`x` when `x-1 ∉ set` — each element is visited O(1) times overall.

⚠️ Hash operations are O(1) **average**, O(n) worst case; and dict keys must be hashable, so a
list must become a tuple ([../Language/Python/data_model.md](../Language/Python/data_model.md)).

---

## 7. Interview points

- **Explain Kadane's algorithm. ⭐⭐** At each index, extend the previous subarray or restart —
  `dp[i] = max(x, dp[i-1] + x)` — because a negative running sum can only hurt what follows.
- **What breaks Kadane's?** All-negative input if you initialise the answer to 0.
- **Maximum product subarray — why is it harder?** A negative flips max and min, so you must
  track both running extremes.
- **When do you use prefix sums? ⭐** Repeated range queries, or subarray-sum problems where
  sliding window fails because of negatives.
- **Prefix sum vs difference array?** Fast queries with static data vs fast range updates with
  one final read.
- **Why is `s += x` in a loop O(n²)?** Strings are immutable — each concatenation copies. Use
  `join`.
- **How do you check for anagrams?** Character counts, O(n) — better than sorting's O(n log n).
- **Find the longest palindromic substring.** Expand around each centre — remembering **even**
  centres too; O(n²) time, O(1) space (Manacher's is O(n)).
- **Rotate a matrix in place. ⭐** Transpose, then reverse each row.
- **Find the duplicate in 1..n with O(1) space?** Sign-marking at `abs(x)-1`, or Floyd's cycle
  detection if the array must stay unmodified.
- **When is a hash map the answer?** Whenever you'd otherwise re-scan for something you've
  already seen — spend O(n) space to remove an O(n) inner loop.
