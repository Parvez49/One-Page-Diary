"""
Floyd-Warshall algorithm is a dynamic programming algorithm that finds the shortest
paths between all pairs of nodes in a graph.

✅ Works for both directed and undirected graphs
✅ Handles negative weight edges (but not negative weight cycles)
✅ Time Complexity: O(V³) → Suitable for small to medium-sized graphs

"""

class FloydWarshall:
    def __init__(self, vertices):
        self.V = vertices
        self.INF = float('inf')
        self.dist = [[self.INF]*self.V for _ in range(self.V)]

    def add_edge(self, u,v,w):
        self.dist[u][v] = w

    def run(self):
        for i in range(self.V):
            self.dist[i][i] = 0

        for k in range(self.V):
            for i in range(self.V):
                for j in range(self.V):
                    if self.dist[i][k] != self.INF and self.dist[k][j] != self.INF:
                        self.dist[i][j] = min(self.dist[i][j], self.dist[i][k], self.dist[k][j])

        for i in range(self.V):
            if self.dist[i][i] < 0:
                print('Graph contain a negative weight cycle')
                return None

        return self.dist


graph = FloydWarshall(4)
graph.add_edge(0, 1, 3)
graph.add_edge(0, 2, 7)
graph.add_edge(1, 2, -2)
graph.add_edge(1, 3, 2)
graph.add_edge(2, 3, 5)
graph.add_edge(3, 0, 1)

shortest_paths = graph.run()

if shortest_paths:
    print("All-Pairs Shortest Paths:")
    for row in shortest_paths:
        print(row)
