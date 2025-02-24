"""
The Bellman-Ford algorithm is used to find the shortest path from a single source to all other
vertices in a graph. It is particularly useful when the graph contains negative weight edges,
which Dijkstra's algorithm cannot handle.

✅ Handles negative weight edges
✅ Detects negative weight cycles
✅ Uses O(VE) time complexity
✅ if there are no negative weight cycles, Bellman-Ford Always Give the Shortest Path.
"""


class BellmanFord:
    def __init__(self, vertices):
        self.V = vertices
        self.edge = list()

    def add_edge(self, u, v, weight):
        self.edge.append((u, v, weight))

    def run(self, src):
        INF = float('inf')
        distance = {v: INF for v in range(self.V)}

        distance[src] = 0

        # Relax all edges V-1 times
        for _ in range(self.V - 1):
            for u,v,weight in self.edge:
                if distance[u] != INF and distance[u] + weight < distance[v]:
                    distance[v] = distance[u] + weight

        for u,v, weight in self.edge:
            if distance[u] != INF and distance[u] + weight < distance[v]:
                print("Graph contains a negative weight cycle!")
                return None

        return distance


bellman = BellmanFord(5)
path = [(0,1,6), (0,2,7),(1,2,8),(1,3,-4),(2,4,9),(3,1,5),(3,4,7),(4,3,-2)]
for u,v,w in path:
    bellman.add_edge(u,v,w)

shortest_path = bellman.run(0)

if shortest_path:
    print(shortest_path)