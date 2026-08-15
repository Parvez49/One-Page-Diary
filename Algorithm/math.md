# Math & Bit Manipulation

> Complexity budgets: **[complexity.md](complexity.md)**

---

## 1. GCD & LCM ⭐

**GCD** — the largest number dividing both without remainder. `gcd(12, 18) = 6`.

```python
def gcd(a, b):                    # ⭐ Euclidean algorithm — O(log min(a,b))
    while b:
        a, b = b, a % b
    return a

import math
math.gcd(12, 18)                  # ⭐ use the stdlib; variadic in 3.9+
math.lcm(4, 6)                    # 12
```

⭐ **Why it's O(log n):** each step replaces `(a, b)` with `(b, a mod b)`, and `a mod b < a/2`
whenever `b ≤ a/2` — so the pair at least halves every two steps. That's the follow-up
question.

```python
lcm(a, b) = a * b // gcd(a, b)    # ⭐ divide FIRST in other languages to avoid overflow
```

**Extended Euclid** — finds `x, y` with `ax + by = gcd(a,b)`; the basis of the **modular
inverse**:

```python
def ext_gcd(a, b):
    if b == 0: return a, 1, 0
    g, x1, y1 = ext_gcd(b, a % b)
    return g, y1, x1 - (a // b) * y1
```

**Where GCD shows up:** reducing fractions, "water jug" reachability (achievable iff the target
is a multiple of the gcd), grid problems (lattice points on a line segment =
`gcd(dx, dy)`), and cycle/rotation problems.

---

## 2. Primes ⭐

**Primality test — trial division to √n:**

```python
def is_prime(n):
    if n < 2: return False
    if n < 4: return True                     # 2, 3
    if n % 2 == 0 or n % 3 == 0: return False
    i = 5
    while i * i <= n:                         # ⭐ only up to √n
        if n % i == 0 or n % (i + 2) == 0: return False
        i += 6                                # ⭐ all primes > 3 are 6k ± 1
    return True
```

⭐ **Why √n suffices:** if `n = a·b` with both factors > √n, then `a·b > n` — a contradiction.
So any composite has a factor ≤ √n. **O(√n)**.

**Sieve of Eratosthenes — all primes up to n in O(n log log n):**

```python
def sieve(n):
    is_p = bytearray([1]) * (n + 1)
    is_p[0] = is_p[1] = 0
    for i in range(2, int(n**0.5) + 1):       # ⭐ stop at √n
        if is_p[i]:
            is_p[i*i::i] = bytearray(len(is_p[i*i::i]))   # ⭐ start at i², not 2i
    return [i for i, p in enumerate(is_p) if p]
```

⭐ **Two optimisations worth naming:** start marking at **i²** (smaller multiples were already
marked by smaller primes), and stop the outer loop at **√n**.

⭐ **Sieve vs trial division:** one number → trial division O(√n). *Many* numbers up to n →
sieve, which amortises to nearly O(1) each. Choosing correctly is the actual question.

**Linear sieve** (O(n)) also gives the **smallest prime factor** per number, making
factorisation O(log n) per query:

```python
def factorize(n):                             # ⭐ O(√n) trial division
    f = {}
    d = 2
    while d * d <= n:
        while n % d == 0: f[d] = f.get(d, 0) + 1; n //= d
        d += 1
    if n > 1: f[n] = f.get(n, 0) + 1          # ⚠️ the remaining prime factor
    return f
```

⚠️ Forgetting the final `if n > 1` drops the largest prime factor — a very common bug.

**Miller–Rabin** for huge n (probabilistic, deterministic below 3.3×10²⁴ with fixed witnesses)
— know the name.

---

## 3. Modular arithmetic ⭐

Competitive and interview problems use `MOD = 10**9 + 7` (prime, fits in 32 bits when doubled).

```
(a + b) % m == ((a % m) + (b % m)) % m
(a * b) % m == ((a % m) * (b % m)) % m
(a - b) % m == ((a % m) - (b % m) + m) % m     # ⚠️ +m keeps it non-negative in C/Java
```

⚠️⚠️ **Division does not distribute over mod.** `(a / b) % m ≠ (a%m) / (b%m)`. You need the
**modular inverse**:

```python
pow(b, m - 2, m)                  # ⭐ Fermat's little theorem — m must be PRIME
pow(b, -1, m)                     # ⭐ Python 3.8+ — works for any coprime m
```

```python
pow(2, 100, MOD)                  # ⭐ fast modular exponentiation, O(log n), built in
```

⭐ **Python has arbitrary-precision integers**, so overflow never happens — which is exactly why
you should *say* "in C++ this would overflow, so I'd take the mod at each step." That shows
language-independent understanding.

---

## 4. Bit manipulation ⭐⭐

```python
x & 1          # odd?                       x >> 1     # ⭐ divide by 2
x | (1 << i)   # ⭐ SET bit i               x & ~(1<<i)  # CLEAR bit i
x ^ (1 << i)   # TOGGLE bit i               (x >> i) & 1 # ⭐ TEST bit i
x & (x - 1)    # ⭐⭐ clear the LOWEST set bit
x & (-x)       # ⭐⭐ ISOLATE the lowest set bit
x.bit_count()  # popcount (3.10+)           bin(x).count("1")
```

⭐ **`x & (x-1)` and `x & (-x)` are the two to memorise.** `x-1` flips the lowest set bit and
everything below it, so `&` clears exactly that bit. `-x` is the two's complement (`~x + 1`),
which leaves only the lowest set bit in common.

```python
n > 0 and n & (n - 1) == 0        # ⭐ power of two: exactly one set bit
```

**Classic uses:**

```python
functools.reduce(operator.xor, nums)         # ⭐ single number — pairs cancel (a^a==0)
```

⭐ **XOR properties do the work:** `a ^ a = 0`, `a ^ 0 = a`, commutative and associative. So
XOR-ing an array where every element appears twice except one leaves that one. Two singles?
Split by any differing bit — `x & (-x)` gives you one.

**Bitmask as a set** — subsets of ≤ 20 elements:

```python
for mask in range(1 << n):                    # ⭐ all 2ⁿ subsets
    subset = [nums[i] for i in range(n) if mask >> i & 1]

sub = mask
while sub:                                    # ⭐ enumerate SUBMASKS of mask — O(3ⁿ) total
    sub = (sub - 1) & mask
```

This is the foundation of **bitmask DP** (travelling salesman, assignment problems) — see
[DynamicProgramming/dp.md](DynamicProgramming/dp.md).

⚠️ **Python's `>>` on negatives is an arithmetic shift on infinite-precision integers** —
`-1 >> 1 == -1`, and there's no `>>>`. Mask explicitly (`& 0xFFFFFFFF`) when emulating 32-bit
behaviour.

---

## 5. Combinatorics

```python
math.comb(n, k)        # ⭐ C(n,k) — 3.8+
math.perm(n, k)        # P(n,k)
math.factorial(n)
```

```
C(n,k) = n! / (k!(n-k)!)          C(n,k) = C(n-1,k-1) + C(n-1,k)   ⭐ Pascal's rule → DP
```

**Counting rules:** product rule (independent choices multiply) · sum rule (disjoint cases add)
· **inclusion–exclusion** (|A∪B| = |A|+|B|−|A∩B|) · **pigeonhole** (n+1 items in n boxes force a
repeat — the basis of many "prove a duplicate exists" arguments) · **stars and bars**
(distributing k identical items into n bins = C(k+n−1, n−1)).

⭐ **Under a modulus**, precompute factorials and inverse factorials once, then each C(n,k) is
O(1).

---

## 6. Number-theory quick hits

```python
n & 1                              # parity without %
divmod(a, b)                       # ⭐ quotient and remainder in one call
-7 // 2 == -4                      # ⚠️ Python floors toward -∞ (C truncates → -3)
-7 %  2 == 1                       # ⚠️ sign follows the DIVISOR
int(math.isqrt(n))                 # ⭐ exact integer sqrt — no float error
```

⚠️ **Never use `int(n ** 0.5)` for integer square roots** — floating-point error makes
`isqrt(10**18)` off by one. `math.isqrt` is exact.

**Digit manipulation:**

```python
while n: n, d = divmod(n, 10)      # ⭐ extract digits right to left
sum(int(c) for c in str(n))        # digit sum — readable, fine for interviews
```

**Base conversion:** `int("ff", 16)`, `bin(x)`, `oct(x)`, `hex(x)`; general base via repeated
`divmod`.

⭐ **Floats are not exact**: `0.1 + 0.2 != 0.3`. Use `math.isclose`, integers scaled by a
constant, or `Decimal` for money
([../Language/Python/pitfalls.md](../Language/Python/pitfalls.md)).

---

## 7. Interview points

- **Explain the Euclidean algorithm and its complexity. ⭐** Repeatedly replace `(a,b)` with
  `(b, a mod b)`; O(log min(a,b)) because the values at least halve every two steps.
- **How do you compute LCM?** `a*b // gcd(a,b)` — divide before multiplying in fixed-width
  languages.
- **Why only check up to √n for primality? ⭐** Any composite has a factor ≤ √n, since two
  factors both above √n would exceed n.
- **Sieve or trial division?** One query → trial division O(√n); many queries up to n → sieve,
  O(n log log n) total.
- **Why does the sieve start marking at i²?** Smaller multiples of i were already marked by
  smaller prime factors.
- **How do you divide under a modulus? ⭐** Multiply by the modular inverse — `pow(b, m-2, m)`
  when m is prime (Fermat), or `pow(b, -1, m)`.
- **What does `x & (x-1)` do? ⭐⭐** Clears the lowest set bit — so `x & (x-1) == 0` tests for a
  power of two, and repeated application counts set bits.
- **What does `x & (-x)` do?** Isolates the lowest set bit (two's complement).
- **Find the number appearing once when all others appear twice.** XOR everything — equal values
  cancel.
- **How do you enumerate all subsets of n ≤ 20 items?** Bitmask from `0` to `1 << n`.
- **Why is `int(n ** 0.5)` unsafe?** Floating-point error on large n — use `math.isqrt`.
- **What's `-7 // 2` in Python?** −4 — floor division toward −∞, unlike C's truncation.
