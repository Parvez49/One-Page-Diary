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
- index & -index: the lowest set bit in the binary representation of index,
- -index is the two's complement of index.
  ```
  Take index = 6, which is 110 in binary:
  index     =  110 (6)
  -index    =  010 (2) → two's complement of 6
  index & -index = 010 (2)
  ```

### Implementation:
```
class BIT:
    def __init__(self, size):
        self.n = size
        self.tree = [0] * (self.n + 1)

    def update(self, index, delta):
        while index <= self.n:
            self.tree[index] += delta
            index += index & -index

    def query(self, index):
        result = 0
        while index > 0:
            result += self.tree[index]
            index -= index & -index
        return result

arr = [0, 2, 4, 5, 5, 6]  # index 0 is dummy to match 1-based BIT indexing
bit = BIT(len(arr) - 1)

# Build BIT
for i in range(1, len(arr)):
    bit.update(i, arr[i])

# Query sum from 1 to 3
print(bit.query(3))  # Output: 2 + 4 + 5 = 11

# Update index 2 by +1 (i.e., arr[2] = 4 -> 5)
bit.update(2, 1)

print(bit.query(3))  # Output: 2 + 5 + 5 = 12

```
