"""
Bellman-Ford — single-source shortest paths WITH negative edge weights.

  - Handles negative weights (Dijkstra cannot: it finalises a vertex on pop,
    so a later negative edge would never be reconsidered)
  - DETECTS negative weight cycles
  - O(V * E) time, O(V) space

Why exactly V-1 rounds:
  A shortest path visits at most V vertices, so it uses at most V-1 edges.
  Each full round guarantees one more edge of every shortest path is
  correctly relaxed. If anything STILL improves on an extra pass, some path
  is getting shorter without bound -> a negative cycle is reachable.
"""

INF = float("inf")


class BellmanFord:
    def __init__(self, vertices):
        self.V = vertices
        self.edges = []                      # (u, v, weight) — directed

    def add_edge(self, u, v, weight):
        self.edges.append((u, v, weight))

    def run(self, src):
        """Return distances from src, or None if a negative cycle is reachable."""
        dist = [INF] * self.V
        dist[src] = 0

        for _ in range(self.V - 1):
            changed = False
            for u, v, w in self.edges:
                # the INF guard matters in fixed-width languages (overflow)
                if dist[u] != INF and dist[u] + w < dist[v]:
                    dist[v] = dist[u] + w
                    changed = True
            if not changed:                  # converged early
                break

        for u, v, w in self.edges:           # one EXTRA pass: still improving?
            if dist[u] != INF and dist[u] + w < dist[v]:
                return None                  # negative cycle
        return dist

    def negative_cycle_nodes(self, src):
        """Vertices whose distance is -inf (affected by a negative cycle)."""
        dist = [INF] * self.V
        dist[src] = 0
        for _ in range(self.V - 1):
            for u, v, w in self.edges:
                if dist[u] != INF and dist[u] + w < dist[v]:
                    dist[v] = dist[u] + w

        affected = set()
        for _ in range(self.V):              # propagate -inf outward
            for u, v, w in self.edges:
                if dist[u] != INF and dist[u] + w < dist[v]:
                    dist[v] = -INF
                    affected.add(v)
        return affected


if __name__ == "__main__":
    g = BellmanFord(5)
    for u, v, w in [(0, 1, 6), (0, 2, 7), (1, 2, 8), (1, 3, -4),
                    (2, 4, 9), (3, 1, 5), (3, 4, 7), (4, 3, -2)]:
        g.add_edge(u, v, w)

    dist = g.run(0)
    if dist is None:
        print("Graph contains a negative weight cycle")
    else:
        print("Shortest distances from 0:", dist)
        # 0->1 = 6;  0->2 = 7;  0->1->3 = 6-4 = 2;  0->1->3->4 = 2+7 = 9
        assert dist == [0, 6, 7, 2, 9]
        print("OK")

    # A graph that DOES contain a negative cycle: 1 -> 2 -> 1 costs -1
    bad = BellmanFord(3)
    for u, v, w in [(0, 1, 1), (1, 2, -2), (2, 1, 1)]:
        bad.add_edge(u, v, w)
    assert bad.run(0) is None
    print("negative cycle detected OK")
