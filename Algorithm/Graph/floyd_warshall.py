"""
Floyd-Warshall — all-pairs shortest paths via DP.

DP meaning of layer k:  dist[i][j] = shortest i->j path using only vertices
{0..k} as INTERMEDIATES.

    d_k(i,j) = min( d_{k-1}(i,j),               # path avoids k
                    d_{k-1}(i,k) + d_{k-1}(k,j) )   # path goes through k once

- Works for directed and undirected graphs
- Handles NEGATIVE edge weights (but not negative cycles — it detects them)
- O(V^3) time, O(V^2) space  -> practical up to V ~= 500

Two bugs to avoid (both are easy to write and produce silently wrong answers):
  1. The relaxation is a SUM: dist[i][k] + dist[k][j].
     NOT min(dist[i][j], dist[i][k], dist[k][j]) — that compares three
     unrelated path costs and is meaningless.
  2. `k` MUST be the OUTERMOST loop. The DP layer is defined by k, so every
     pair must be updated for a given k before moving to k+1.
"""

INF = float("inf")


class FloydWarshall:
    def __init__(self, vertices):
        self.V = vertices
        self.dist = [[INF] * vertices for _ in range(vertices)]
        for i in range(vertices):
            self.dist[i][i] = 0                      # zero-cost self loops

    def add_edge(self, u, v, w):
        # min() so parallel edges keep only the cheapest
        self.dist[u][v] = min(self.dist[u][v], w)

    def run(self):
        d, V = self.dist, self.V

        for k in range(V):                           # k OUTERMOST
            dk = d[k]
            for i in range(V):
                dik = d[i][k]
                if dik == INF:                       # no i->k path; skip the row
                    continue
                di = d[i]
                for j in range(V):
                    if dk[j] != INF and dik + dk[j] < di[j]:
                        di[j] = dik + dk[j]          # SUM, not min-of-three

        for i in range(V):                           # negative cycle detection
            if d[i][i] < 0:
                return None
        return d

    def path_exists(self, u, v):
        return self.dist[u][v] != INF


if __name__ == "__main__":
    g = FloydWarshall(4)
    for u, v, w in [(0, 1, 3), (0, 2, 7), (1, 2, -2), (1, 3, 2), (2, 3, 5), (3, 0, 1)]:
        g.add_edge(u, v, w)

    result = g.run()
    if result is None:
        print("Graph contains a negative weight cycle")
    else:
        print("All-pairs shortest paths:")
        for i, row in enumerate(result):
            print(i, ["INF" if x == INF else x for x in row])
        # 0->2 is 1 via 0->1->2 (3 + -2), NOT the direct edge of 7
        assert result[0][2] == 1
        assert result[0][3] == 5        # 0->1->3 = 3 + 2  (beats 0->1->2->3 = 1 + 5)
        assert result[1][2] == -2       # the direct negative edge
        print("OK")
