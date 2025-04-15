# Binary Indexed Tree

A Binary Indexed Tree (BIT), also known as a Fenwick Tree, is a data structure that provides efficient methods for:
- Prefix sum queries (sum of elements from index 1 to i)
- Point updates (updating a single element)
  
Both operations can be done in O(log n) time, which is faster than a naive O(n) approach and simpler to implement than a Segment Tree in some scenarios.

### When to Use BIT
We have an array of numbers.
We want to:
- Frequently update single elements (arr[i] += delta)
- Frequently get prefix sums (sum of arr[1..i])

 We don't need range updates (for that, Segment Tree is better).

### The tree is built in a way where:
- Jump to parent node using index -= index & -index
- Jump to child node using index += index & -index

