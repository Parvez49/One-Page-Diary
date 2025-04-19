
### bisect_left and bisect_right
- bisect.bisect_left(a, x): Returns the leftmost index at which x can be inserted to keep list a sorted.
- bisect.bisect_right(a, x)(bisect.bisect(a, x)): Returns the rightmost index at which x can be inserted to keep list a sorted.
- bisect.bisect() is the same as bisect.bisect_right()

```
import bisect

a = [1, 3, 3, 3, 5, 7]
x = 3
print(bisect.bisect_left(a, x))   # Output: 1
print(bisect.bisect_right(a, x))  # Output: 4
```

### bisect_left implementation:
```
def bisect_left(a, x, lo=0, hi=None):
    if hi is None:
        hi = len(a)
    while lo < hi:
        mid = (lo + hi) // 2
        if a[mid] < x:
            lo = mid + 1
        else:
            hi = mid
    return lo
```

### bisect_right implementation:
```
def bisect_right(a, x, lo=0, hi=None):
    if hi is None:
        hi = len(a)
    while lo < hi:
        mid = (lo + hi) // 2
        if a[mid] <= x:
            lo = mid + 1
        else:
            hi = mid
    return lo
```
