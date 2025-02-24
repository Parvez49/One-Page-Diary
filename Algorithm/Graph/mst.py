"""
🔹 Minimum Spanning Tree (MST) Algorithms

A Minimum Spanning Tree (MST) is a subset of edges in a weighted, connected, undirected graph that:
✅ Connects all vertices with minimum total edge weight
✅ No cycles (forms a tree)
✅ Used in network design, clustering, and approximation algorithms
"""


"""
🔹 Prim’s Algorithm (Efficient for Dense Graphs)

✅ Uses a priority queue (min-heap)
✅ Grows the MST one vertex at a time, always adding the smallest edge that connects to the MST
✅ Works best with adjacency list representation
"""

import heapq

class PrimMST:
    def __init__(self, vertices):
        self.V = vertices
        self.graph = {i: [] for i in range(self.V)}

    def add_edge(self, u,v, weight):
        """Add an undirected edge"""
        self.graph[u].append((weight, v))
        self.graph[v].append((weight, u))

    def run(self):
        """Execute Prim's algorithm and return the MST edge and cost"""

        INF = float('inf')
        mst_edge = []
        total_cost = 0
        visited = set()
        min_heap = [(0,0,-1)]

        while len(visited) < self.V:
            weight, u, parent = heapq.heappop(min_heap)
            if u in visited:
                continue
            visited.add(u)
            if parent != -1:
                mst_edge.append((parent, u, weight))
                total_cost += weight


