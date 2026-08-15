# Shortest Paths & Minimum Spanning Trees

> Traversal & representation: **[graph.md](graph.md)** · Runnable code:
> `bellman_ford.py`, `floyd_warshall.py`, `mst.py`

---

## 1. Choosing the algorithm ⭐⭐

**The decision table — this is the question, and the answer is "it depends on the weights."**

| Situation | Algorithm | Complexity |
|---|---|---|
| **Unweighted**, single source | ⭐ **BFS** | O(V+E) |
| Weights ∈ {0,1} | 0-1 BFS (deque) | O(V+E) |
| **Non-negative** weights, single source | ⭐⭐ **Dijkstra** | O(E log V) |
| **Negative** weights allowed | ⭐ **Bellman–Ford** | O(V·E) |
| **All pairs**, small V (≤ ~500) | ⭐ **Floyd–Warshall** | O(V³) |
| All pairs, sparse | Johnson's (Bellman–Ford + Dijkstra ×V) | O(V·E log V) |
| **DAG** (any weights) | ⭐ topological order + relax | **O(V+E)** |
| With a distance heuristic | **A\*** | ≤ Dijkstra |

⭐⭐ **The single most important fact: Dijkstra breaks on negative edges.** Once a vertex is
popped, Dijkstra assumes its distance is final — a later negative edge could improve it, but
it's never reconsidered. If a problem mentions negative costs (refunds, discounts, elevation
loss), that's the signal for Bellman–Ford.

⚠️ **Never use BFS for weighted shortest paths.** BFS minimises *edge count*, not *weight*.

---

## 2. Dijkstra ⭐⭐

```python
import heapq

def dijkstra(adj, src, V):                 # adj[u] = [(v, w), ...]
    dist = [float("inf")] * V
    dist[src] = 0
    pq = [(0, src)]                        # (distance, vertex)

    while pq:
        d, u = heapq.heappop(pq)
        if d > dist[u]:                    # ⭐⭐ STALE ENTRY — skip it
            continue
        for v, w in adj[u]:
            nd = d + w
            if nd < dist[v]:               # ⭐ relaxation
                dist[v] = nd
                heapq.heappush(pq, (nd, v))
    return dist
```

⭐⭐ **The `if d > dist[u]: continue` line is what most implementations omit** — including the
version previously in these notes. Python's `heapq` has no decrease-key, so the standard
technique is **lazy deletion**: push a new entry and skip outdated pops. Without that check
you re-expand vertices and the neighbour loop runs far more often than necessary. It's the
detail that shows you've actually written Dijkstra rather than copied it.

**Why it's correct (greedy invariant):** when the smallest-distance vertex is popped, no
unprocessed path can reach it more cheaply — any alternative route goes through a vertex with a
**larger** tentative distance, and adding non-negative weights can only increase it. ⭐ That
argument is exactly why negative edges break it.

**Complexity:** O((V+E) log V) ≈ **O(E log V)** with a binary heap; O(E + V log V) with a
Fibonacci heap (theoretical). ⚠️ Lazy deletion means the heap can hold O(E) entries.

**Variants:** track `parent[]` to reconstruct the path · stop early when the target is popped
(⭐ valid, since its distance is final) · maximise probability/capacity instead of minimising
sum (negate or use max-heap) · "cheapest flight within K stops" is Dijkstra with `(cost, node,
stops)` or, more simply, Bellman–Ford limited to K+1 rounds.

---

## 3. Bellman–Ford ⭐

**Handles negative edges and detects negative cycles.**

```python
def bellman_ford(V, edges, src):           # edges = [(u, v, w), ...]
    INF = float("inf")
    dist = [INF] * V
    dist[src] = 0

    for _ in range(V - 1):                 # ⭐ V-1 rounds is provably enough
        changed = False
        for u, v, w in edges:
            if dist[u] != INF and dist[u] + w < dist[v]:
                dist[v] = dist[u] + w
                changed = True
        if not changed:                    # ⭐ early exit — already converged
            break

    for u, v, w in edges:                  # ⭐⭐ one EXTRA pass
        if dist[u] != INF and dist[u] + w < dist[v]:
            return None                    # still improving → NEGATIVE CYCLE
    return dist
```

⭐ **Why exactly V−1 rounds:** a shortest path visits at most V vertices, so it has at most V−1
edges, and each round guarantees one more edge of every shortest path is correctly relaxed. If
anything still improves on round V, some path is getting shorter without bound — a **negative
cycle**.

⚠️ **The `dist[u] != INF` guard matters**: `inf + (-5) < inf` is `False` in Python so it happens
to be safe here, but in C++ it overflows. Keep the guard as a habit.

**Complexity:** O(V·E) — much slower than Dijkstra, so use it only when negatives exist.
**SPFA** (queue-based Bellman–Ford) is often faster in practice but still O(V·E) worst case.

⭐ **To find *which* vertices are affected by a negative cycle**, run V more rounds and mark
anything that keeps improving as `-inf`.

---

## 4. Floyd–Warshall ⭐

**All-pairs shortest paths via DP over "allowed intermediate vertices."**

```python
def floyd_warshall(V, edges):
    INF = float("inf")
    dist = [[INF] * V for _ in range(V)]
    for i in range(V):
        dist[i][i] = 0                     # ⭐ before adding edges
    for u, v, w in edges:
        dist[u][v] = min(dist[u][v], w)    # ⚠️ min — handles parallel edges

    for k in range(V):                     # ⭐⭐ k MUST be the OUTER loop
        for i in range(V):
            for j in range(V):
                if dist[i][k] + dist[k][j] < dist[i][j]:
                    dist[i][j] = dist[i][k] + dist[k][j]     # ⭐ SUM, not min of three

    for i in range(V):
        if dist[i][i] < 0:                 # ⭐ negative cycle
            return None
    return dist
```

⚠️⚠️ **Two bugs live here, and the version previously in these notes had one of them:**

1. **The relaxation is a *sum*.** It must be
   `dist[i][j] = min(dist[i][j], dist[i][k] + dist[k][j])` — the cost of going *i → k → j*.
   Writing `min(dist[i][j], dist[i][k], dist[k][j])` compares three unrelated path costs and
   produces silently wrong answers.
2. **`k` must be the outermost loop.** The DP meaning is "shortest i→j using only vertices
   `0..k` as intermediates," so all pairs must be updated for a given `k` before moving on.
   Putting `k` innermost gives wrong results on many graphs while looking plausible on small
   ones.

⭐ **The recurrence:** `d_k(i,j) = min(d_{k-1}(i,j), d_{k-1}(i,k) + d_{k-1}(k,j))` — either the
path avoids `k`, or it goes through `k` exactly once. The k-th layer can be written in place
because `d(i,k)` and `d(k,j)` don't change during round `k`.

**Complexity:** O(V³) time, O(V²) space → practical to about V ≈ 500.
⭐ **Also computes transitive closure** (replace min/+ with or/and) and detects negative cycles
via `dist[i][i] < 0`.

---

## 5. Minimum Spanning Tree ⭐

**A subset of edges connecting all V vertices with minimum total weight and no cycles** — always
exactly **V−1 edges**. Undirected, weighted, connected graphs only.

### Kruskal — sort edges, union-find

```python
def kruskal(V, edges):                     # edges = [(w, u, v), ...]
    dsu = DSU(V)                           # ⭐ see graph.md §7
    mst, total = [], 0
    for w, u, v in sorted(edges):          # ⭐ globally cheapest first
        if dsu.union(u, v):                # ⭐ False ⇒ same component ⇒ would form a cycle
            mst.append((u, v, w)); total += w
            if len(mst) == V - 1: break    # ⭐ early exit
    return mst, total
```

**O(E log E)** — dominated by the sort. ⭐ **Best for sparse graphs**, and the natural choice
when edges arrive as a list.

### Prim — grow one tree with a heap

```python
import heapq

def prim(adj, V, start=0):                 # adj[u] = [(w, v), ...]
    visited = set()
    heap = [(0, start)]
    total, edges = 0, 0

    while heap and len(visited) < V:
        w, u = heapq.heappop(heap)
        if u in visited:                   # ⭐ stale entry
            continue
        visited.add(u)
        total += w
        for nw, v in adj[u]:
            if v not in visited:
                heapq.heappush(heap, (nw, v))    # ⭐⭐ push neighbours — easily forgotten

    return total if len(visited) == V else None  # ⭐ None ⇒ graph is disconnected
```

⚠️ **The previous `mst.py` in these notes never pushed neighbours into the heap and had no
return** — so the loop popped the seed and then spun on an empty heap. The push inside the
neighbour loop is what makes it grow.

**O(E log V)** — ⭐ better for **dense** graphs (and O(V²) without a heap, which beats the heap
version when E ≈ V²).

| | **Kruskal** | **Prim** |
|---|---|---|
| Strategy | globally cheapest edge | cheapest edge leaving the current tree |
| Needs | ⭐ union-find | ⭐ priority queue |
| Best for | **sparse** graphs, edge lists | **dense** graphs, adjacency lists |
| Disconnected graph | ⭐ yields a spanning **forest** | ⚠️ only reaches one component |

⭐ **Both are greedy and both are optimal**, by the **cut property**: for any partition of the
vertices, the lightest edge crossing the cut belongs to some MST. That one sentence justifies
both algorithms — a strong thing to say.

⚠️ **The MST is unique only if all edge weights are distinct.** Equal weights allow several
valid MSTs (the total cost is still unique).

⚠️ **An MST is not a shortest-path tree.** It minimises *total* edge weight, not the distance
from a source — a very common confusion.

---

## 6. Interview points

- **Which shortest-path algorithm, and why? ⭐⭐** BFS if unweighted; Dijkstra for non-negative
  weights; Bellman–Ford if negatives are possible; Floyd–Warshall for all pairs with small V;
  topological relaxation for a DAG.
- **Why does Dijkstra fail on negative edges? ⭐⭐** It finalises a vertex when popped, assuming
  no cheaper route remains — a negative edge later can violate that, and it never revisits.
- **What's the `if d > dist[u]: continue` line for? ⭐** `heapq` has no decrease-key; you push
  duplicates and lazily skip stale ones.
- **Dijkstra's complexity?** O(E log V) with a binary heap.
- **Why V−1 rounds in Bellman–Ford? ⭐** A shortest path has at most V−1 edges; a V-th
  improvement proves a negative cycle.
- **How do you detect a negative cycle?** One extra Bellman–Ford pass that still relaxes, or
  `dist[i][i] < 0` after Floyd–Warshall.
- **Why is `k` the outer loop in Floyd–Warshall? ⭐⭐** The DP layer is "paths using only
  vertices ≤ k as intermediates" — all pairs must be updated per k.
- **Kruskal vs Prim? ⭐** Sort-and-union-find (sparse, edge lists) vs grow-with-a-heap (dense,
  adjacency lists); both O(E log V)-ish and both optimal.
- **Why are the greedy MST algorithms correct?** The cut property — the lightest edge crossing
  any cut is in some MST.
- **Is the MST unique?** Only with distinct edge weights; the total cost is always unique.
- **Is an MST also a shortest-path tree? ⭐** No — it minimises total weight, not
  source-to-vertex distance.
- **Shortest path in a DAG with negative weights?** Relax in topological order — O(V+E), no
  Bellman–Ford needed.
