# Trees, Heaps & Tries

> Range queries: **[segment_tree.md](segment_tree.md)**, **[binary_indexed_tree.md](binary_indexed_tree.md)** ·
> Graph traversal: **[../Graph/graph.md](../Graph/graph.md)**

---

## 1. Definitions ⭐

A **tree** is a connected acyclic graph: V vertices, exactly **V−1 edges**, and a unique path
between any two nodes.

| Term | Meaning |
|---|---|
| **Height** | edges on the longest root→leaf path (⚠️ a single node = 0 or 1 by convention — *state yours*) |
| **Depth** | edges from the root to this node |
| **Full** | every node has 0 or 2 children |
| **Complete** | all levels filled except possibly the last, filled left to right — ⭐ how heaps are stored |
| **Perfect** | all levels completely filled — 2^h+1 − 1 nodes |
| **Balanced** | height O(log n) — ⭐ what makes BST operations fast |

```python
class Node:
    def __init__(self, val):
        self.val, self.left, self.right = val, None, None
```

⚠️ **A "binary tree" question is usually really a recursion question.** The structure gives you
the base case (`if not node: return ...`) for free.

---

## 2. Traversals ⭐⭐

```python
def inorder(node):                       # ⭐ Left → Node → Right
    if not node: return
    inorder(node.left); visit(node); inorder(node.right)

def preorder(node):                      # Node → Left → Right
    if not node: return
    visit(node); preorder(node.left); preorder(node.right)

def postorder(node):                     # Left → Right → Node
    if not node: return
    postorder(node.left); postorder(node.right); visit(node)
```

⭐⭐ **What each one is *for* — this is the actual question:**

| Traversal | Use |
|---|---|
| **Inorder** | ⭐ **sorted order in a BST** — the defining property |
| **Preorder** | ⭐ **serialise / copy a tree** (root first, so you can rebuild top-down) |
| **Postorder** | ⭐ **delete a tree**, or compute anything needing children first (height, subtree sums) |
| **Level-order (BFS)** | level-by-level, shortest path, right-side view |

⭐ **Postorder is the "bottom-up DP" traversal** — height, diameter, "is balanced", and
max-path-sum all need the children's answers before the parent's.

**Iterative inorder** (when recursion depth is a concern):

```python
def inorder_iter(root):
    stack, cur, out = [], root, []
    while stack or cur:
        while cur:                       # ⭐ dive left, pushing as you go
            stack.append(cur); cur = cur.left
        cur = stack.pop()
        out.append(cur.val)              # visit
        cur = cur.right
    return out
```

**Level-order:**

```python
def level_order(root):
    if not root: return []
    out, q = [], deque([root])
    while q:
        level = []
        for _ in range(len(q)):          # ⭐ snapshot the level size FIRST
            n = q.popleft()
            level.append(n.val)
            if n.left:  q.append(n.left)
            if n.right: q.append(n.right)
        out.append(level)
    return out
```

⭐ **Morris traversal** does inorder in **O(1) space** by temporarily threading `right`
pointers to the successor — worth naming when asked for constant space.

---

## 3. Common tree recursions ⭐

```python
def height(node):
    return 0 if not node else 1 + max(height(node.left), height(node.right))

def is_balanced(root):                   # ⭐ O(n) — return height AND validity together
    def check(n):
        if not n: return 0
        lh = check(n.left)
        if lh == -1: return -1           # ⭐ propagate failure, don't recompute
        rh = check(n.right)
        if rh == -1 or abs(lh - rh) > 1: return -1
        return 1 + max(lh, rh)
    return check(root) != -1
```

⚠️ **The naive `is_balanced` calling `height()` at every node is O(n²).** Returning height and
the balance verdict in one pass is the expected optimisation.

```python
def diameter(root):                      # ⭐ longest path between ANY two nodes
    best = 0
    def depth(n):
        nonlocal best
        if not n: return 0
        l, r = depth(n.left), depth(n.right)
        best = max(best, l + r)          # ⭐ the path THROUGH n — not returned upward
        return 1 + max(l, r)             # ⭐ what the parent can use: one side only
    depth(root)
    return best
```

⭐ **The diameter pattern generalises**: compute a value *at* each node (path through it) while
returning a *different* value upward (best single branch). Max-path-sum is the same shape with
`max(0, …)` to drop negative branches.

**LCA (lowest common ancestor):**

```python
def lca(root, p, q):
    if not root or root is p or root is q: return root
    l, r = lca(root.left, p, q), lca(root.right, p, q)
    return root if (l and r) else (l or r)     # ⭐ both sides found → this IS the LCA
```

⭐ In a **BST** it's simpler: descend while both targets are on the same side — O(h).

---

## 4. Binary Search Tree ⭐

**Invariant: everything in the left subtree < node < everything in the right subtree.**

```python
def search(node, key):                   # O(h)
    while node and node.val != key:
        node = node.left if key < node.val else node.right
    return node
```

⚠️⚠️ **Validating a BST needs a *range*, not a parent comparison:**

```python
def is_valid_bst(node, lo=float("-inf"), hi=float("inf")):
    if not node: return True
    if not (lo < node.val < hi): return False
    return (is_valid_bst(node.left,  lo, node.val) and     # ⭐ tighten the bound
            is_valid_bst(node.right, node.val, hi))
```

Checking only `left.val < node.val < right.val` passes trees that are **not** BSTs — a value
deep in the left subtree can exceed the root. ⭐ Alternative: an inorder traversal must be
strictly increasing.

**Deletion — three cases:** no children (remove) · one child (splice it in) · ⭐ **two children
(replace with the inorder successor — the leftmost node of the right subtree — then delete
that)**.

⚠️⚠️ **A BST degenerates to a linked list on sorted insertion** — `1,2,3,4,5` gives height n
and O(n) operations. That's why self-balancing trees exist:

| Tree | Balance |
|---|---|
| **AVL** | strictly balanced (height diff ≤ 1) — ⭐ faster lookups, more rotations |
| **Red-Black** | loosely balanced — ⭐ fewer rotations, faster inserts; used by most stdlibs |
| **B-Tree / B+Tree** | ⭐ high fan-out for disk — **database and filesystem indexes** |
| Treap / Skip list | randomised, simpler to implement |

⭐ **B-trees are the database answer**: nodes hold many keys to match a disk page, so height
stays ~3–4 even for billions of rows — see [../../Database/](../../Database/).

⚠️ **Python has no built-in balanced BST.** Use `sortedcontainers.SortedList` (O(log n)) or
keep a sorted list with `bisect` (O(log n) search, ⚠️ O(n) insert).

---

## 5. Heaps ⭐

**A complete binary tree stored in an array**, with `heap[0]` the min (or max).

```
parent(i) = (i-1)//2     left(i) = 2i+1     right(i) = 2i+2
```

```python
import heapq
heapq.heapify(a)                 # ⭐ O(n) — NOT O(n log n)
heapq.heappush(h, x)             # O(log n)
heapq.heappop(h)                 # O(log n) — smallest
h[0]                             # ⭐ O(1) peek
heapq.heappushpop(h, x)          # ⭐ cheaper than push then pop
heapq.nlargest(k, a)
```

⭐⭐ **`heapify` is O(n)** — the classic follow-up. Most nodes are near the bottom and sink only
a short distance; the sum ∑ n/2^h · h converges to O(n).

⚠️ **`heapq` is min-only** — negate for a max-heap (`-x`), or push `(-priority, item)`.
⚠️ Ties on the first tuple element compare the second — push a counter to avoid comparing
unorderable objects: `(priority, counter, item)`.

**Use for:** top-K, merge k sorted lists, running median (two heaps), Dijkstra, Prim, task
scheduling ([../patterns.md §9](../patterns.md)).

---

## 6. Trie (prefix tree) ⭐

```python
class Trie:
    def __init__(self):
        self.root = {}

    def insert(self, word):
        node = self.root
        for ch in word:
            node = node.setdefault(ch, {})
        node["$"] = True                 # ⭐ end-of-word marker

    def search(self, word):
        node = self._walk(word)
        return node is not None and "$" in node

    def starts_with(self, prefix):
        return self._walk(prefix) is not None

    def _walk(self, s):
        node = self.root
        for ch in s:
            if ch not in node: return None
            node = node[ch]
        return node
```

⭐ **O(L) per operation — independent of how many words are stored.** A hash set matches whole
words equally fast, but only a trie answers **prefix** queries: autocomplete, word search on a
board, IP routing, and "longest common prefix."

⚠️ Memory-hungry (a dict per node). A **radix/compressed trie** merges single-child chains.

⭐ **Word Search II** is the canonical use: build a trie of the dictionary, then DFS the board
once while walking the trie — instead of searching for each word separately.

---

## 7. Interview points

- **When do you use each traversal? ⭐⭐** Inorder → sorted order in a BST; preorder →
  serialise/copy; postorder → delete or compute from children up; level-order → BFS by level.
- **How do you validate a BST? ⭐** Pass down a (lo, hi) range — comparing only with the
  immediate parent is wrong.
- **What's the complexity of BST search?** O(h) — O(log n) balanced, **O(n) degenerate**.
- **Why do balanced trees exist?** Sorted insertions degenerate a plain BST into a linked list.
- **AVL vs Red-Black?** Stricter balance and faster lookups vs fewer rotations and faster
  inserts — stdlibs pick red-black.
- **Why do databases use B-trees? ⭐** High fan-out matches disk pages, keeping height ~3–4 for
  billions of rows, so lookups cost few I/Os.
- **How do you delete a node with two children?** Replace it with its inorder successor, then
  delete that node.
- **Is `heapify` O(n log n)? ⭐** No — **O(n)**.
- **How do you get a max-heap in Python?** Negate values — `heapq` is min-only.
- **Compute the diameter of a binary tree. ⭐** Postorder: track `left + right` through each
  node while returning `1 + max(left, right)` upward.
- **Why is the naive `is_balanced` O(n²)?** It recomputes height at every node; return height
  and validity in one pass.
- **Trie vs hash set?** Both O(L) for exact lookup, but only a trie supports prefix queries.
- **How do you do inorder traversal in O(1) space?** Morris traversal — thread right pointers
  to successors.
