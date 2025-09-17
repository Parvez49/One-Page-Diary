### Kadane's algorithm
Given an integer array nums, find the subarray with the largest sum, and return its sum.
```
Example 1:
  
  Input: nums = [-2,1,-3,4,-1,2,1,-5,4]
  Output: 6
  Explanation: The subarray [4,-1,2,1] has the largest sum 6.

Example 2:
  
  Input: nums = [5,4,-1,7,8]
  Output: 23
  Explanation: The subarray [5,4,-1,7,8] has the largest sum 23.

Sotution:

        # current_sum: the maximum sum ending at the current index
        # max_sum: the maximum sum we have found so far

        max_sum=float('-inf')
        current_sum=0
        for i in nums:
            current_sum+=i
            if max_sum<current_sum:
                max_sum=current_sum
            
            if current_sum<0:
                current_sum=0
        print(res)
```

### GCD
  GCD (Greatest Common Divisor) of two numbers is the largest number that divides both without leaving a remainder.
- GCD(12, 18) = 6
- Much faster because it reduces the size quickly.
- Complexity: O(log(min(a, b))) — very efficient.
```
def gcd_euclidean(a, b):
    while b:
        a, b = b, a % b
    return a
```


