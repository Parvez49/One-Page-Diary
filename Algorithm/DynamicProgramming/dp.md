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

### Minimum (Maximum) Path to Reach a Target
