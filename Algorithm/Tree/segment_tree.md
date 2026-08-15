# Segment Tree

> Simpler alternative for prefix sums: **[binary_indexed_tree.md](binary_indexed_tree.md)** ·
> Trees: **[trees.md](trees.md)**

---

## 1. What and why ⭐

**A binary tree where each node stores an aggregate over a *segment* of the array.** Leaves are
single elements; each internal node combines its two children.

```
                 [0..5] sum=17
             /                    \
      [0..2] sum=11          [3..5] sum=6
       /       \              /       \
  [0..1]=6   [2..2]=5    [3..4]=5   [5..5]=1
   /    \                  /   \
[0]=2  [1]=4           [3]=2  [4]=3
```

| Operation | Naive array | ⭐ Segment tree |
|---|---|---|
| range query | O(n) | **O(log n)** |
| point update | O(1) | **O(log n)** |
| range update (lazy) | O(n) | **O(log n)** |

⭐ **The trade to state:** a plain array has O(1) updates but O(n) queries; a prefix-sum array
flips that to O(1) queries but O(n) updates. A segment tree makes **both** O(log n) — the right
structure when reads *and* writes are frequent.

---

## 2. Implementation

```python
class SegmentTree:
    def __init__(self, arr, func=lambda a, b: a + b, identity=0):
        self.n, self.func, self.identity = len(arr), func, identity
        self.tree = [identity] * (2 * self.n)          # ⭐ iterative, size 2n

        for i, v in enumerate(arr):                    # leaves in [n, 2n)
            self.tree[self.n + i] = v
        for i in range(self.n - 1, 0, -1):             # ⭐ build parents bottom-up, O(n)
            self.tree[i] = func(self.tree[2 * i], self.tree[2 * i + 1])

    def update(self, i, value):                        # point update — O(log n)
        i += self.n
        self.tree[i] = value
        while i > 1:
            i //= 2
            self.tree[i] = self.func(self.tree[2 * i], self.tree[2 * i + 1])

    def query(self, lo, hi):                           # ⭐ [lo, hi) half-open — O(log n)
        res_l = res_r = self.identity
        lo += self.n; hi += self.n
        while lo < hi:
            if lo & 1:                                 # lo is a RIGHT child → take it
                res_l = self.func(res_l, self.tree[lo]); lo += 1
            if hi & 1:                                 # hi is a right child → take hi-1
                hi -= 1; res_r = self.func(self.tree[hi], res_r)
            lo //= 2; hi //= 2
        return self.func(res_l, res_r)
```

```python
st = SegmentTree([2, 4, 5, 2, 3, 1])
st.query(1, 4)      # 4 + 5 + 2 = 11
st.update(2, 10)
st.query(1, 4)      # 4 + 10 + 2 = 16
st = SegmentTree(arr, min, float("inf"))    # ⭐ range MINIMUM — same code
```

⭐ **Keeping `res_l` and `res_r` separate matters for non-commutative operations** (matrix
product, string concatenation) — the left fragments must combine before the right ones. For sum
or min it makes no difference, but the habit is free.

⚠️ **The recursive version needs `4n` space**, not `2n`, because the tree isn't perfect. The
iterative version above is exactly `2n` and is usually the one to write.

---

## 3. Lazy propagation ⭐

**Range updates in O(log n)** — without it, "add 5 to every element in [l, r]" is O(n).

**The idea:** when an update covers a node's whole segment, record it as a *pending* value on
that node and stop. Push the pending value down only when a later query needs to descend
through it.

```python
def update_range(self, node, seg_lo, seg_hi, lo, hi, delta):
    self._push(node, seg_lo, seg_hi)                  # ⭐ apply any pending update first
    if seg_hi < lo or hi < seg_lo:                    # no overlap
        return
    if lo <= seg_lo and seg_hi <= hi:                 # ⭐ FULL cover → mark lazy, stop here
        self.lazy[node] += delta
        self._push(node, seg_lo, seg_hi)
        return
    mid = (seg_lo + seg_hi) // 2                      # partial → recurse both sides
    self.update_range(2*node,   seg_lo, mid,     lo, hi, delta)
    self.update_range(2*node+1, mid+1,  seg_hi,  lo, hi, delta)
    self.tree[node] = self.tree[2*node] + self.tree[2*node+1]
```

⭐ **"Full cover → stop and mark" is the entire trick.** The O(log n) bound comes from the fact
that any range decomposes into at most O(log n) fully-covered nodes.

⚠️ For **sum**, a pending `+delta` contributes `delta × segment_length`; for **min/max** it's
just `+delta`. Getting that multiplication wrong is the classic lazy-propagation bug.

---

## 4. Segment tree vs Fenwick (BIT) ⭐

| | **Fenwick / BIT** | **Segment tree** |
|---|---|---|
| Code size | ⭐ ~10 lines | ~50 lines |
| Memory | ⭐ n | 2n (4n recursive) |
| Speed | ⭐ faster constant | slower constant |
| Operations | ⚠️ **invertible only** (sum, xor) | ⭐ **any associative** (min, max, gcd, sum) |
| Range update | needs two BITs | ⭐ lazy propagation |
| Search on the tree | awkward | ⭐ "first index where prefix ≥ x" in O(log n) |

⭐⭐ **The decision rule: prefix sums only → Fenwick. Range min/max/gcd or range updates →
segment tree.** A BIT works by subtracting prefixes, which requires an **invertible** operation
— you cannot recover a range minimum that way, because min has no inverse. That single sentence
answers the comparison question.

---

## 5. Variants worth naming

- **Merge-sort tree** — each node stores its segment sorted → "count elements < x in range."
- **Persistent segment tree** — keep every historical version (path copying) → "kth smallest in
  a range."
- **2-D segment tree** — matrix range queries, O(log² n).
- **Sparse table** — ⭐ O(1) range min/max after O(n log n) build, but **immutable**: the right
  choice when there are no updates.
- **Sqrt decomposition** — O(√n) per operation, far simpler; often enough.

⚠️ **Don't reach for a segment tree by default.** If the array never changes, a prefix-sum array
(O(1)) or sparse table beats it. The segment tree earns its complexity only with interleaved
updates and queries.

---

## 6. Interview points

- **What problem does a segment tree solve? ⭐** Range queries *and* point/range updates both in
  O(log n), when a prefix-sum array would make one of them O(n).
- **Build complexity?** O(n) — each node combines its children once.
- **When is a Fenwick tree enough? ⭐⭐** Prefix sums (or any invertible operation). Range
  min/max needs a segment tree, because you can't subtract a minimum.
- **What is lazy propagation?** Deferring a range update at a fully-covered node and pushing it
  down only when a query descends — turning O(n) range updates into O(log n).
- **Why 4n memory in the recursive version?** The implicit tree isn't perfect, so indices can
  exceed 2n; the iterative bottom-up form needs exactly 2n.
- **What operations can a segment tree support?** Any **associative** one — sum, min, max, gcd,
  matrix product, string concat.
- **What if the array never changes?** Prefix sums (O(1) sums) or a sparse table (O(1) range
  min) — no tree needed.
- **How would you find the first index whose prefix sum ≥ x?** Descend the tree in O(log n),
  choosing left or right by the child's aggregate.
