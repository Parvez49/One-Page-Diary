## Breadth First Search (BFS)

It begins with a node, then first traverses all its adjacent. Once all adjacent are visited, then their adjacent are traversed.

### Algorithm

```
 Initialization: Enqueue the given source vertex into a queue and mark it as visited.

    Exploration: While the queue is not empty:
        Dequeue a node from the queue and visit it (e.g., print its value).
        For each unvisited neighbor of the dequeued node:
            Enqueue the neighbor into the queue.
            Mark the neighbor as visited.
    Termination: Repeat step 2 until the queue is empty.
```

### Implementation

```
def bfs(adj, s):
    q = deque()
    visited = [False] * len(adj);
    visited[s] = True
    q.append(s)

    while q:
        curr = q.popleft()
        print(curr, end=" ")

        for x in adj[curr]:
            if not visited[x]:
                visited[x] = True
                q.append(x)

```

## Dijkstra’s Algorithm

using Adjacency List in O(E logV)

```
import heapq

class Graph:
    def __init__(self, V: int):
        self.V = V
        self.adj = [[] for _ in range(V)]

    def addEdge(self, u: int, v: int, w: int):
        self.adj[u].append((v, w))
        self.adj[v].append((u, w))

    # Prints shortest paths from src to all other vertices
    def shortestPath(self, src: int):
        # Create a priority queue to store vertices that
        # are being preprocessed
        pq = []
        heapq.heappush(pq, (0, src))

        # Create a vector for distances and initialize all
        # distances as infinite (INF)
        dist = [float('inf')] * self.V
        dist[src] = 0

        while pq:
            # The first vertex in pair is the minimum distance
            # vertex, extract it from priority queue.
            # vertex label is stored in second of pair
            d, u = heapq.heappop(pq)

            for v, weight in self.adj[u]:
                if dist[v] > dist[u] + weight:
                    # Updating distance of v
                    dist[v] = dist[u] + weight
                    heapq.heappush(pq, (dist[v], v))

        # Print shortest distances stored in dist[]
        for i in range(self.V):
            print(f"{i} \t\t {dist[i]}")

```
