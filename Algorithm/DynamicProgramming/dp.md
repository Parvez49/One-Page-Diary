### Dynamic Programming (DP):
 is a method used in mathematics and computer science to solve
    complex problems by breaking them down into simpler subproblems. By solving each
    subproblem only once and storing the results, it avoids redundant computations,
    leading to more efficient solutions for a wide range of problems.

### How Does Dynamic Programming (DP) Work?
 Identify Subproblems, Store Solutions, 
    Build Up Final Solutions, Avoid Redundancy. 

### When to Use Dynamic Programming (DP)?
    1. Optimal Substructure: Optimal substructure means that we combine the optimal results of subproblems to achieve the optimal result of the bigger problem.
    2. Overlapping Subproblems: The same subproblems are solved repeatedly in different parts of the problem.

### Approaches of Dynamic Programming (DP)
    1. Top-Down Approach (Memoization): start from the original (bigger) problem (the "top") and break it into smaller subproblems (going "down").
    2. Bottom-Up Approach (Tabulation): start from the simplest (smallest) subproblems (the "bottom") and build up to the original problem.
    
### Core Concept
- Overlapping Subproblems – The problem can be broken into smaller problems that repeat.
- Optimal Substructure – The optimal solution can be formed from optimal solutions of subproblems.
- Memoization – Top-down approach using recursion + cache.
- Tabulation – Bottom-up approach using iteration.

### How to classify a problem as a Dynamic Programming Problem? 
    - Typically, all the problems that require maximizing or minimizing certain quantities or counting problems
    - All dp problems satisfy the overlapping subproblems property and most of the classic dp problems also satisfy the optimal substructure property.

## DP Patterns:

### 1. Minimum (Maximum) Path to Reach a Target
routes[i] = min(routes[i-1], routes[i-2], ... , routes[i-k]) + cost[i]

### 0/1 Knapsack problem
- Problem Statement: A set of n items, Each item has: A weight w[i], A value v[i] and A knapsack with a maximum weight capacity W.
- Goal: Pick a subset of items to put in the knapsack so that: Total weight ≤ W, Total value is maximized, either take the whole item or none (hence 0/1)
#### Example
```
Items:       [weight, value]
Item 1:      [1, 1]
Item 2:      [3, 4]
Item 3:      [4, 5]
Capacity W:  7
```
```
from typing import List

def knapsack_bottom_up(weights: List[int], values: List[int], W: int) -> int:
    n = len(weights)
    # dp[i][w] = max value using first i items with capacity w
    dp = [[0] * (W + 1) for _ in range(n + 1)]

    for i in range(1, n + 1):
        wi, vi = weights[i - 1], values[i - 1]
        for w in range(0, W + 1):
            # don't take item i
            dp[i][w] = dp[i - 1][w]
            # take item i, if it fits
            if wi <= w:
                dp[i][w] = max(dp[i][w],
                               dp[i - 1][w - wi] + vi)
    return dp[n][W]

# top-down approach

from functools import lru_cache
from typing import List

def knapsack_top_down(weights: List[int], values: List[int], W: int) -> int:
    n = len(weights)

    @lru_cache(None)
    def dp(i: int, rem_w: int) -> int:
        # base case: no items left or no capacity
        if i == n or rem_w == 0:
            return 0

        wi, vi = weights[i], values[i]
        # option 1: skip this item
        res = dp(i + 1, rem_w)
        # option 2: take this item (if it fits)
        if wi <= rem_w:
            res = max(res, vi + dp(i + 1, rem_w - wi))
        return res

    return dp(0, W)

```


















