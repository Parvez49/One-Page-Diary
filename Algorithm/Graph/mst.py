"""
Minimum Spanning Tree — Prim's and Kruskal's.

An MST is a subset of edges of a weighted, connected, UNDIRECTED graph that:
  - connects all V vertices
  - has minimum total weight
  - contains no cycles -> exactly V-1 edges

Both algorithms are greedy and both are optimal, by the CUT PROPERTY:
for any partition of the vertices, the lightest edge crossing the cut
belongs to some MST.

  Kruskal  O(E log E)  sort edges + union-find   -> better for SPARSE graphs
  Prim     O(E log V)  grow one tree with a heap -> better for DENSE graphs

Note: the MST is unique only when all edge weights are distinct (the total
cost is always unique). An MST is NOT a shortest-path tree.
"""

import heapq


# --------------------------------------------------------------------------
# Prim — grow a single tree, always taking the cheapest edge leaving it
# --------------------------------------------------------------------------
class PrimMST:
    def __init__(self, vertices):
        self.V = vertices
        self.graph = {i: [] for i in range(vertices)}

    def add_edge(self, u, v, weight):
        """Undirected edge; store as (weight, neighbour) so the heap sorts by weight."""
        self.graph[u].append((weight, v))
        self.graph[v].append((weight, u))

    def run(self, start=0):
        """Return (mst_edges, total_cost), or (None, None) if disconnected."""
        visited = set()
        mst_edges = []
        total_cost = 0
        heap = [(0, start, -1)]                  # (weight, vertex, parent)

        while heap and len(visited) < self.V:
            weight, u, parent = heapq.heappop(heap)
            if u in visited:                     # stale entry — already in the tree
                continue

            visited.add(u)
            if parent != -1:
                mst_edges.append((parent, u, weight))
                total_cost += weight

            # THE STEP THAT MAKES IT GROW: push every edge leaving u.
            for w, v in self.graph[u]:
                if v not in visited:
                    heapq.heappush(heap, (w, v, u))

        if len(visited) != self.V:               # never reached every vertex
            return None, None
        return mst_edges, total_cost


# --------------------------------------------------------------------------
# Kruskal — sort all edges, add one unless it closes a cycle
# --------------------------------------------------------------------------
class DSU:
    def __init__(self, n):
        self.parent = list(range(n))
        self.rank = [0] * n

    def find(self, x):
        while self.parent[x] != x:
            self.parent[x] = self.parent[self.parent[x]]   # path compression
            x = self.parent[x]
        return x

    def union(self, a, b):
        ra, rb = self.find(a), self.find(b)
        if ra == rb:
            return False                          # same component -> would make a cycle
        if self.rank[ra] < self.rank[rb]:         # union by rank
            ra, rb = rb, ra
        self.parent[rb] = ra
        if self.rank[ra] == self.rank[rb]:
            self.rank[ra] += 1
        return True


def kruskal(vertices, edges):
    """edges = [(u, v, weight), ...] -> (mst_edges, total_cost)."""
    dsu = DSU(vertices)
    mst_edges, total_cost = [], 0

    for u, v, w in sorted(edges, key=lambda e: e[2]):      # cheapest first
        if dsu.union(u, v):
            mst_edges.append((u, v, w))
            total_cost += w
            if len(mst_edges) == vertices - 1:             # done early
                break

    if len(mst_edges) != vertices - 1:            # disconnected -> spanning FOREST
        return None, None
    return mst_edges, total_cost


if __name__ == "__main__":
    edges = [(0, 1, 4), (0, 2, 8), (1, 2, 11), (1, 3, 8),
             (2, 4, 7), (3, 4, 2), (3, 5, 9), (4, 5, 6)]

    prim = PrimMST(6)
    for u, v, w in edges:
        prim.add_edge(u, v, w)
    p_edges, p_cost = prim.run()

    k_edges, k_cost = kruskal(6, edges)

    print("Prim   :", p_cost, p_edges)
    print("Kruskal:", k_cost, k_edges)

    # Different edge sets are possible, but the total cost is always the same.
    assert p_cost == k_cost == 27
    assert len(p_edges) == len(k_edges) == 5      # V - 1
    print("OK")
