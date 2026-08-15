"""
Dijkstra — single-source shortest paths, NON-NEGATIVE weights only.

  O((V + E) log V) ~= O(E log V) with a binary heap.

Why it needs non-negative weights:
  When a vertex is popped it is treated as FINAL. That is justified only
  because every alternative route goes through a vertex with a larger
  tentative distance, and adding non-negative weights can only increase it.
  A negative edge breaks the argument -> use Bellman-Ford instead.

The lazy-deletion detail most implementations omit:
  Python's heapq has no decrease-key. Instead of updating an existing entry
  we push a NEW one and skip outdated pops with `if d > dist[u]: continue`.
  Without that guard, vertices get re-expanded and the neighbour loop runs
  far more often than necessary.
"""

import heapq

INF = float("inf")


class Graph:
    def __init__(self, vertices, directed=False):
        self.V = vertices
        self.directed = directed
        self.adj = [[] for _ in range(vertices)]

    def add_edge(self, u, v, w):
        if w < 0:
            raise ValueError("Dijkstra requires non-negative weights; use Bellman-Ford")
        self.adj[u].append((v, w))
        if not self.directed:
            self.adj[v].append((u, w))

    def shortest_paths(self, src, target=None):
        """Return (dist, parent). Stops early if `target` is given and popped."""
        dist = [INF] * self.V
        parent = [-1] * self.V
        dist[src] = 0
        pq = [(0, src)]

        while pq:
            d, u = heapq.heappop(pq)
            if d > dist[u]:                  # stale entry from before an improvement
                continue
            if u == target:                  # its distance is final — safe to stop
                break

            for v, w in self.adj[u]:
                nd = d + w
                if nd < dist[v]:             # relaxation
                    dist[v] = nd
                    parent[v] = u
                    heapq.heappush(pq, (nd, v))

        return dist, parent

    @staticmethod
    def reconstruct(parent, src, dst):
        path, cur = [], dst
        while cur != -1:
            path.append(cur)
            if cur == src:
                break
            cur = parent[cur]
        path.reverse()
        return path if path and path[0] == src else []


if __name__ == "__main__":
    g = Graph(6)
    for u, v, w in [(0, 1, 4), (0, 2, 1), (2, 1, 2), (1, 3, 5),
                    (2, 3, 8), (3, 4, 3), (4, 5, 1), (3, 5, 6)]:
        g.add_edge(u, v, w)

    dist, parent = g.shortest_paths(0)
    print("distances from 0:", dist)
    print("path 0 -> 5    :", Graph.reconstruct(parent, 0, 5))

    # 0->2 = 1;  0->2->1 = 3 (beats the direct edge of 4);  0->2->1->3 = 8
    assert dist[1] == 3
    assert dist[2] == 1
    assert dist[3] == 8
    assert dist[5] == 12          # via 4: 11 + 1  (beats the direct 3->5 edge: 8 + 6 = 14)
    print("OK")
