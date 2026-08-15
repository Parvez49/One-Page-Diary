# Binary Indexed Tree (Fenwick Tree)

> More general alternative: **[segment_tree.md](segment_tree.md)** · Bit tricks:
> **[../math.md §4](../math.md)**

---

## 1. What it's for ⭐

A **Fenwick tree** gives you both of these in **O(log n)**:

- **prefix sum** — sum of `arr[1..i]`
- **point update** — `arr[i] += delta`

| Approach | Prefix sum | Point update |
|---|---|---|
| plain array | ⚠️ O(n) | O(1) |
| prefix-sum array | O(1) | ⚠️ O(n) |
| ⭐ **Fenwick tree** | **O(log n)** | **O(log n)** |

⭐ **Use it when updates and queries are interleaved.** A static array should just use prefix
sums; the BIT earns its keep only when the data keeps changing
([../arrays_strings.md §2](../arrays_strings.md)).

⚠️ **It requires an *invertible* operation** — sum, XOR, count. A range is computed as
`query(r) − query(l−1)`, and you cannot subtract a **minimum**, so range-min needs a segment
tree.

---

## 2. The trick: `index & -index` ⭐⭐

Each node `i` stores the sum of the **`i & -i` elements ending at `i`**.

`i & -i` isolates the **lowest set bit**, because `-i` is the two's complement (`~i + 1`):

```
i        = 6  = 110
-i       =      010     (two's complement)
i & -i   =      010  = 2      ⭐ tree[6] covers 2 elements: arr[5..6]
```

```
index:   1     2     3     4     5     6     7     8
covers: [1]  [1-2]  [3]  [1-4]  [5]  [5-6]  [7]  [1-8]
lowbit:  1     2     1     4     1     2     1     8
```

⭐ **Two movements, and they're opposites:**
- **`i -= i & -i`** → jump to the previous disjoint block (**query**, walking down)
- **`i += i & -i`** → jump to the next node covering `i` (**update**, walking up)

Each step clears or adds one bit, so at most log n steps.

---

## 3. Implementation

```python
class BIT:
    def __init__(self, size):
        self.n = size
        self.tree = [0] * (size + 1)            # ⭐⭐ 1-INDEXED — index 0 is unused

    def update(self, i, delta):                 # arr[i] += delta   — O(log n)
        while i <= self.n:
            self.tree[i] += delta
            i += i & -i                         # ⭐ walk UP to covering nodes

    def query(self, i):                         # sum of arr[1..i]  — O(log n)
        total = 0
        while i > 0:
            total += self.tree[i]
            i -= i & -i                         # ⭐ walk DOWN over disjoint blocks
        return total

    def range_query(self, l, r):                # ⭐ sum of arr[l..r]
        return self.query(r) - self.query(l - 1)

    @classmethod
    def build(cls, arr):                        # ⭐ O(n) instead of n × O(log n)
        bit = cls(len(arr))
        bit.tree[1:] = arr[:]                   # arr is 1-indexed, arr[0] a dummy
        for i in range(1, bit.n + 1):
            parent = i + (i & -i)
            if parent <= bit.n:
                bit.tree[parent] += bit.tree[i]
        return bit
```

```python
arr = [0, 2, 4, 5, 5, 6]          # index 0 is a dummy for 1-based indexing
bit = BIT(len(arr) - 1)
for i in range(1, len(arr)):
    bit.update(i, arr[i])

bit.query(3)          # 2 + 4 + 5 = 11
bit.update(2, 1)      # arr[2]: 4 -> 5
bit.query(3)          # 2 + 5 + 5 = 12
bit.range_query(2, 4) # 5 + 5 + 5 = 15
```

⚠️⚠️ **1-indexing is not a style choice.** `i & -i` is `0` when `i == 0`, so `i -= i & -i`
never terminates and `i += i & -i` never advances. Keep index 0 unused and translate at the API
boundary if your data is 0-indexed.

⭐ **The O(n) build** (each node pushes its total to its parent once) beats n separate
`update()` calls — worth knowing when constructing from a large array.

---

## 4. Variants ⭐

**Range update, point query** — store a *difference array* in the BIT:

```python
def range_add(bit, l, r, delta):
    bit.update(l, delta)
    bit.update(r + 1, -delta)          # ⭐ then query(i) IS the value at i
```

**Range update + range query** needs **two BITs** (a standard trick worth naming):
maintain `B1` and `B2` such that
`prefix(i) = query(B1, i) * i − query(B2, i)`.

**Other uses:**

- ⭐ **Counting inversions** — sweep right to left, `query(value − 1)` counts smaller elements
  already seen. O(n log n), the BIT alternative to merge sort.
- **"Count of smaller numbers after self"** — the same sweep.
- ⭐ **Coordinate compression** first when values are large or sparse: map values to ranks
  1..k, then the BIT is size k.
- **2-D BIT** — matrix prefix sums in O(log² n).
- **`find_kth`** — descend the tree bit by bit to locate the smallest index with prefix ≥ k, in
  O(log n) rather than O(log² n) with binary search.

---

## 5. BIT vs Segment Tree ⭐⭐

| | **Fenwick / BIT** | **Segment tree** |
|---|---|---|
| Code | ⭐ ~10 lines | ~50 lines |
| Memory | ⭐ n | 2n (4n recursive) |
| Constant factor | ⭐ faster | slower |
| Operations | ⚠️ **invertible only** (sum, xor) | ⭐ **any associative** (min, max, gcd) |
| Range updates | needs two BITs | ⭐ lazy propagation |

⭐ **The one-sentence rule: prefix sums → BIT; range min/max or range updates → segment tree.**
The BIT computes a range as `query(r) − query(l−1)`, which is only valid for an operation with
an inverse — minimum has none.

---

## 6. Interview points

- **What does a Fenwick tree do? ⭐** Prefix sums and point updates both in O(log n), when a
  plain array or prefix-sum array makes one of them O(n).
- **How does `i & -i` work? ⭐⭐** It isolates the lowest set bit via two's complement; that bit
  is the size of the range the node covers.
- **Why is it 1-indexed?** `0 & -0 == 0`, so the update and query loops would never progress.
- **BIT vs segment tree? ⭐⭐** BIT is smaller, faster, and simpler but needs an **invertible**
  operation; segment trees handle any associative operation and support lazy range updates.
- **Can a BIT do range minimum?** Not directly — you can't subtract a minimum. Use a segment
  tree (or a sparse table if the data is static).
- **How do you support range updates with a BIT?** A difference array for range-update/
  point-query, or two BITs for range-update/range-query.
- **Where is a BIT the elegant answer? ⭐** Counting inversions and "smaller elements after
  self" — sweep and query, O(n log n).
- **What if values are huge or sparse?** Coordinate-compress to ranks first.
- **Build complexity?** O(n) with the parent-accumulation build, versus O(n log n) for n
  separate updates.
