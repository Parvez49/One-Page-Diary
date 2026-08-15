# Graphs — Representation & Traversal

> Shortest paths & MST: **[shortest_path.md](shortest_path.md)** · Patterns:
> **[../patterns.md](../patterns.md)**

---

## 1. Vocabulary ⭐

| Term | Meaning |
|---|---|
| **Directed / undirected** | edges one-way vs both ways |
| **Weighted** | edges carry a cost |
| **Sparse** | ⭐ E ≈ O(V) — use an **adjacency list** |
| **Dense** | E ≈ O(V²) — an adjacency matrix is competitive |
| **DAG** | directed **acyclic** graph — ⭐ enables topological sort and DP |
| **Connected component** | maximal set of mutually reachable vertices |
| **Strongly connected** | (directed) every vertex reaches every other |
| **Bipartite** | 2-colourable — ⭐ no odd-length cycle |
| **Tree** | connected, acyclic, exactly V−1 edges |
| **Hamiltonian path/cycle** | visits every **vertex** exactly once (⚠️ NP-complete) |
| **Eulerian path/cycle** | uses every **edge** exactly once (⭐ solvable in O(E)) |

⭐ **Hamiltonian vs Eulerian is a classic trap**: they sound symmetric but aren't.
Eulerian is easy — a connected graph has an Eulerian **cycle** iff every vertex has even
degree, and a **path** iff exactly zero or two vertices have odd degree. Hamiltonian is
NP-complete with no such characterisation.

---

## 2. Representation ⭐

```python
from collections import defaultdict, deque

# ⭐ Adjacency list — the default choice
adj = defaultdict(list)
for u, v in edges:
    adj[u].append(v)
    adj[v].append(u)              # ⚠️ omit for a directed graph

# Adjacency matrix — dense graphs, O(1) edge lookup
M = [[0] * V for _ in range(V)]
```

| | Adjacency list | Adjacency matrix |
|---|---|---|
| Space | ⭐ **O(V + E)** | ⚠️ **O(V²)** |
| Is u–v an edge? | O(deg u) | ⭐ **O(1)** |
| Iterate neighbours | ⭐ O(deg u) | O(V) |
| Best for | ⭐ sparse (most real graphs) | dense, or Floyd–Warshall |

⭐ **Adjacency list unless the graph is dense or you need O(1) edge lookup.** A social graph
with 10⁶ users and 10⁷ edges needs 10¹² matrix cells — obviously impossible.

⭐ **A grid is a graph** — cell `(r,c)` with 4 (or 8) implicit neighbours. Don't build an
adjacency list for it; compute neighbours on the fly
([../arrays_strings.md §5](../arrays_strings.md)).

---

## 3. BFS ⭐⭐

**Level by level, using a queue.** ⭐ **Finds the shortest path in an *unweighted* graph** —
because it reaches every vertex by the fewest edges first.

```python
def bfs(adj, src):
    visited = {src}                            # ⭐⭐ mark on ENQUEUE, not on dequeue
    q = deque([src])
    dist = {src: 0}
    while q:
        u = q.popleft()
        for v in adj[u]:
            if v not in visited:
                visited.add(v)
                dist[v] = dist[u] + 1
                q.append(v)
    return dist
```

⚠️⚠️ **Mark visited when you enqueue, not when you dequeue.** Marking on dequeue lets a vertex
be added multiple times before it's processed — the queue blows up to O(E) duplicates and
complexity degrades badly on dense graphs.

**Level-order variant** — when you need to know *which* level you're on:

```python
while q:
    for _ in range(len(q)):                    # ⭐ snapshot the level size FIRST
        u = q.popleft()
        ...
    depth += 1
```

**Multi-source BFS** ⭐ — seed the queue with *all* sources at distance 0. This is the elegant
answer to "rotting oranges", "walls and gates", and "nearest 0 in a matrix": one BFS instead of
one per source.

**0-1 BFS** — with edge weights of only 0 or 1, use a **deque**: `appendleft` for weight-0
edges, `append` for weight-1. O(V+E), no heap needed.

**Complexity:** O(V + E) time, O(V) space (queue width).

---

## 4. DFS ⭐

**Go deep first**, via recursion or an explicit stack.

```python
def dfs(adj, u, visited):
    visited.add(u)
    for v in adj[u]:
        if v not in visited:
            dfs(adj, v, visited)

def dfs_iterative(adj, src):                   # ⭐ avoids RecursionError on big graphs
    visited, stack = set(), [src]
    while stack:
        u = stack.pop()
        if u in visited: continue
        visited.add(u)
        stack.extend(adj[u])
```

⚠️ **Python's recursion limit is 1000** — a recursive DFS on a 10⁵-node graph (or a path-shaped
graph) raises `RecursionError`. Use the iterative form for large inputs
([../recursion_backtracking.md](../recursion_backtracking.md)).

**BFS or DFS?**

| Use BFS | Use DFS |
|---|---|
| ⭐ shortest path (unweighted) | ⭐ cycle detection |
| level-order / nearest-first | topological sort |
| minimum steps / moves | connected components, flood fill |
| when the target is likely shallow | path existence, backtracking |
| ⚠️ memory = O(width) — wide graphs hurt | ⚠️ memory = O(depth) — deep graphs hurt |

⭐ **DFS does *not* find shortest paths.** It finds *a* path. Using DFS for a
minimum-steps question is a common and costly mistake.

---

## 5. Cycle detection ⭐

**Undirected** — a visited neighbour that isn't your parent:

```python
def has_cycle_undirected(adj, u, parent, visited):
    visited.add(u)
    for v in adj[u]:
        if v not in visited:
            if has_cycle_undirected(adj, v, u, visited): return True
        elif v != parent:                      # ⭐ back edge to a non-parent
            return True
    return False
```

**Directed** — needs **three colours**, because a visited node isn't enough:

```python
WHITE, GRAY, BLACK = 0, 1, 2                   # unvisited / in progress / done

def has_cycle_directed(adj, u, color):
    color[u] = GRAY
    for v in adj[u]:
        if color[v] == GRAY: return True       # ⭐⭐ back edge to the CURRENT path
        if color[v] == WHITE and has_cycle_directed(adj, v, color): return True
    color[u] = BLACK
    return False
```

⭐⭐ **The distinction interviewers probe:** in a directed graph, meeting an already-visited node
does **not** imply a cycle — it may be a *cross edge* to a finished branch
(`A→B, A→C, B→C` has no cycle). Only a node still **on the current recursion stack** (GRAY)
means a cycle. A single `visited` set gives false positives.

---

## 6. Topological sort ⭐

**A linear ordering of a DAG where every edge points forwards.** Course schedules, build
systems, dependency resolution.

**Kahn's algorithm (BFS)** — ⭐ the one to write, since it detects cycles for free:

```python
def topo_sort(V, edges):
    adj = defaultdict(list)
    indeg = [0] * V
    for u, v in edges:
        adj[u].append(v); indeg[v] += 1

    q = deque(u for u in range(V) if indeg[u] == 0)     # ⭐ start with no dependencies
    order = []
    while q:
        u = q.popleft(); order.append(u)
        for v in adj[u]:
            indeg[v] -= 1
            if indeg[v] == 0: q.append(v)               # ⭐ all deps satisfied

    return order if len(order) == V else []             # ⭐⭐ short → CYCLE
```

⭐ **`len(order) < V` means a cycle** — that single check answers "can all courses be
finished?" without a separate cycle detector.

**DFS variant:** push each node onto a stack **after** exploring all its descendants, then
reverse. ⚠️ Doesn't detect cycles unless you add colouring.

⚠️ **The topological order isn't unique** — any valid ordering is correct. Use a heap instead
of a deque if the problem demands lexicographically smallest.

⭐ **DAG shortest path:** relax edges in topological order → **O(V+E)**, and it handles negative
weights (unlike Dijkstra).

---

## 7. Union-Find (Disjoint Set Union) ⭐⭐

**For connectivity questions**, especially dynamic ones.

```python
class DSU:
    def __init__(self, n):
        self.parent = list(range(n))
        self.rank = [0] * n
        self.count = n                          # ⭐ number of components

    def find(self, x):
        while self.parent[x] != x:
            self.parent[x] = self.parent[self.parent[x]]   # ⭐ path compression (halving)
            x = self.parent[x]
        return x

    def union(self, a, b):
        ra, rb = self.find(a), self.find(b)
        if ra == rb: return False               # ⭐ already connected → this edge is a CYCLE
        if self.rank[ra] < self.rank[rb]: ra, rb = rb, ra   # ⭐ union by rank
        self.parent[rb] = ra
        if self.rank[ra] == self.rank[rb]: self.rank[ra] += 1
        self.count -= 1
        return True
```

⭐ **With both path compression and union by rank, operations are O(α(n))** — the inverse
Ackermann function, below 5 for any conceivable n. Effectively constant.

⚠️ **Only one optimisation isn't enough**: path compression alone is O(log n) amortised, union
by rank alone is O(log n). You need both for α(n).

**Union-find or DFS?** ⭐ DFS answers connectivity **once** on a static graph in O(V+E).
Union-find handles **incremental** edges and repeated queries, which is why it powers
**Kruskal's MST**, "number of islands II", "redundant connection", and account-merging problems.

⚠️ Union-find can't easily be undone or applied to *directed* connectivity.

---

## 8. Bipartite check & colouring

```python
def is_bipartite(adj, n):
    color = [-1] * n
    for s in range(n):                          # ⚠️ loop all — the graph may be disconnected
        if color[s] != -1: continue
        color[s] = 0; q = deque([s])
        while q:
            u = q.popleft()
            for v in adj[u]:
                if color[v] == -1:
                    color[v] = color[u] ^ 1     # ⭐ opposite colour
                    q.append(v)
                elif color[v] == color[u]:
                    return False                # ⭐ odd cycle
    return True
```

⭐ **Bipartite ⟺ no odd-length cycle.** Used for "can these people be split into two groups",
scheduling conflicts, and as a precondition for bipartite matching.

⚠️ **Always loop over all vertices** for a disconnected graph — checking only from vertex 0 is
a recurring bug across all these algorithms.

---

## 9. Advanced (know the names)

| Algorithm | Solves | Cost |
|---|---|---|
| **Tarjan / Kosaraju** | strongly connected components | O(V+E) |
| **Tarjan bridges & articulation points** | critical edges/vertices | O(V+E) |
| **Kahn + DP on DAG** | longest path in a DAG | O(V+E) |
| **Hopcroft–Karp** | bipartite matching | O(E√V) |
| **Ford–Fulkerson / Dinic** | max flow, min cut | varies |
| **A\*** | heuristic shortest path | ⭐ Dijkstra + a heuristic |

⭐ **Max-flow min-cut** is worth one sentence: the maximum flow equals the minimum cut capacity,
which turns many partition/assignment problems into flow problems.

---

## 10. Interview points

- **Adjacency list vs matrix? ⭐** O(V+E) space and fast neighbour iteration vs O(V²) space and
  O(1) edge lookup. List unless the graph is dense.
- **BFS vs DFS — when each? ⭐** BFS for shortest paths in unweighted graphs and level order;
  DFS for cycles, topological order, and components.
- **Why does BFS give the shortest path?** It explores in order of edge count, so a vertex is
  first reached by a minimum-length path.
- **When do you mark a node visited in BFS? ⭐⭐** On **enqueue** — marking on dequeue allows
  duplicate queue entries.
- **What's multi-source BFS?** Seed the queue with all sources at distance 0 — one traversal
  instead of one per source.
- **Cycle detection: directed vs undirected? ⭐⭐** Undirected: a visited neighbour that isn't
  the parent. Directed: a node **still on the recursion stack** (GRAY) — a plain visited set
  gives false positives on cross edges.
- **Explain topological sort and how you detect a cycle.** Kahn's: repeatedly remove
  in-degree-0 nodes; if fewer than V are output, a cycle exists.
- **Is the topological order unique?** No — any ordering respecting the edges is valid.
- **What is union-find and its complexity? ⭐** Disjoint-set with path compression and union by
  rank — O(α(n)), effectively constant. Both optimisations are required.
- **Union-find vs DFS for connectivity?** DFS once on a static graph; union-find for
  incremental edges and repeated queries (and Kruskal's).
- **How do you test bipartiteness?** 2-colour via BFS; a conflict means an odd cycle.
- **Hamiltonian vs Eulerian? ⭐** Every vertex once (NP-complete) vs every edge once (O(E), via
  degree parity).
