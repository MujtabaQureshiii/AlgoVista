"""Pure-Python divide-and-conquer algorithms and bounded explanatory traces."""
from __future__ import annotations
from dataclasses import dataclass, field
from math import sqrt
from typing import Any

@dataclass
class Trace:
    limit: int = 260
    steps: list[dict[str, Any]] = field(default_factory=list)
    skipped: int = 0

    def add(self, stage: str, detail: str, depth: int = 0, **extra: Any) -> None:
        if len(self.steps) < self.limit:
            self.steps.append({'stage': stage, 'detail': detail, 'depth': depth, **extra})
        else:
            self.skipped += 1


def closest_pair(points: list[list[float]], trace: Trace | None = None) -> dict[str, Any]:
    """O(n log n) 2D closest pair, robust to duplicate coordinates."""
    if len(points) < 2:
        raise ValueError('Closest pair requires at least two points.')
    nodes = [(float(x), float(y), i) for i, (x, y) in enumerate(points)]
    px = sorted(nodes, key=lambda p: (p[0], p[1], p[2]))
    py = sorted(nodes, key=lambda p: (p[1], p[0], p[2]))
    comparisons = 0

    def dist2(a, b):
        nonlocal comparisons
        comparisons += 1
        return (a[0]-b[0])**2 + (a[1]-b[1])**2

    def better(x, y):
        if x is None: return y
        if y is None: return x
        if y[0] < x[0]: return y
        if y[0] > x[0]: return x
        return y if tuple(sorted((y[1][2], y[2][2]))) < tuple(sorted((x[1][2], x[2][2]))) else x

    def rec(xs, ys, depth):
        n = len(xs)
        if n <= 3:
            best = None
            for i in range(n):
                for j in range(i+1, n):
                    best = better(best, (dist2(xs[i], xs[j]), xs[i], xs[j]))
            if trace:
                trace.add('BASE', f'Brute-check {n} point(s): {"no pair" if best is None else f"best gap = {sqrt(best[0]):.6g}"}', depth)
            return best
        m = n // 2
        mid_x = xs[m][0]
        left = xs[:m]; right = xs[m:]
        ids = {p[2] for p in left}
        yl = [p for p in ys if p[2] in ids]
        yr = [p for p in ys if p[2] not in ids]
        if trace: trace.add('DIVIDE', f'{n} points → {len(left)} left / {len(right)} right; dividing x = {mid_x:.5g}', depth)
        best = better(rec(left, yl, depth+1), rec(right, yr, depth+1))
        delta2 = best[0] if best is not None else float('inf')
        strip = [p for p in ys if (p[0]-mid_x)**2 <= delta2]
        # Because strip is y-sorted, at most 7 successors are necessary.
        for i in range(len(strip)):
            for j in range(i+1, min(i+8, len(strip))):
                if (strip[j][1]-strip[i][1])**2 > delta2:
                    break
                candidate = (dist2(strip[i], strip[j]), strip[i], strip[j])
                new_best = better(best, candidate)
                if new_best is candidate and candidate[0] < delta2 and trace:
                    trace.add('STRIP', f'Cross-region closer pair: distance {sqrt(candidate[0]):.6g}', depth)
                best = new_best
                delta2 = best[0]
        if trace: trace.add('COMBINE', f'Combined {n} points; strip size {len(strip)}; minimum {sqrt(best[0]):.6g}', depth)
        return best

    d2, p, q = rec(px, py, 0)
    p, q = sorted((p, q), key=lambda k:k[2])
    return {'algorithm': 'closest_pair', 'distance': sqrt(d2), 'distance_squared': d2,
            'point_indices': [p[2], q[2]], 'points': [[p[0],p[1]], [q[0],q[1]]],
            'comparisons': comparisons, 'complexity': 'O(n log n) time; O(n) auxiliary space'}


def karatsuba_multiply(a: str | int, b: str | int, trace: Trace | None = None) -> dict[str, Any]:
    """Divide-and-conquer integer multiplication, 3 recursive multiplications per split."""
    sa, sb = str(a).strip(), str(b).strip()
    if not sa or not sb or not sa.lstrip('+-').isdigit() or not sb.lstrip('+-').isdigit():
        raise ValueError('Operands must be valid decimal integers.')
    x, y = int(sa), int(sb)
    calls = 0
    leaves = 0

    def rec(u, v, depth):
        nonlocal calls, leaves
        calls += 1
        n = max(len(str(u)), len(str(v)))
        if u == 0 or v == 0 or n <= 18:
            leaves += 1
            if trace: trace.add('BASE', f'Base multiplication of {len(str(u))} × {len(str(v))} digits', depth)
            return u*v
        half = n // 2
        base = 10**half
        high_u, low_u = divmod(u, base)
        high_v, low_v = divmod(v, base)
        if trace: trace.add('DIVIDE', f'Split {n}-digit operands at {half} digits', depth)
        z0 = rec(low_u, low_v, depth+1)
        z2 = rec(high_u, high_v, depth+1)
        z1 = rec(low_u+high_u, low_v+high_v, depth+1) - z0 - z2
        if trace: trace.add('COMBINE', f'Combine z2·10^{2*half} + z1·10^{half} + z0', depth)
        return z2 * 10**(2*half) + z1*base + z0

    sign = -1 if (x < 0) ^ (y < 0) else 1
    result = sign*rec(abs(x), abs(y), 0)
    return {'algorithm': 'integer_multiplication', 'product': str(result), 'digits': len(str(abs(result))),
            'recursive_calls': calls, 'base_multiplications': leaves,
            'complexity': 'O(d^log2(3)) ≈ O(d^1.585) time; d = operand digits'}


def count_inversions(values: list[int | float], trace: Trace | None = None) -> dict[str, Any]:
    """Count A[i] > A[j] for i<j using merge-sort decomposition."""
    comparisons = 0
    def rec(arr, depth):
        nonlocal comparisons
        if len(arr) <= 1: return arr[:], 0
        middle = len(arr)//2
        if trace: trace.add('DIVIDE', f'Split {len(arr)} values into {middle} and {len(arr)-middle}', depth)
        l, a = rec(arr[:middle], depth+1)
        r, b = rec(arr[middle:], depth+1)
        i=j=0; merged=[]; cross=0
        while i<len(l) and j<len(r):
            comparisons += 1
            if l[i] <= r[j]: merged.append(l[i]); i+=1
            else:
                merged.append(r[j]); cross+=len(l)-i; j+=1
        merged.extend(l[i:]); merged.extend(r[j:])
        if trace: trace.add('COMBINE', f'Merged {len(arr)} values; {cross} cross inversions', depth)
        return merged,a+b+cross
    ordered, total = rec(values, 0)
    return {'algorithm':'inversions','inversions':total,'comparisons':comparisons,
            'sorted_preview':ordered[:25], 'complexity':'O(n log n) time; O(n) auxiliary space'}


def minmax(values: list[int | float], trace: Trace | None = None) -> dict[str, Any]:
    """Tournament-style min/max with 3n/2-2 comparisons when n is power of 2."""
    if not values: raise ValueError('Input cannot be empty.')
    comparisons=0
    def rec(lo, hi, depth):
        nonlocal comparisons
        n=hi-lo
        if n==1: return values[lo],values[lo]
        if n==2:
            comparisons+=1
            if trace: trace.add('BASE', f'Pair {values[lo]}, {values[lo+1]}', depth)
            return (values[lo],values[lo+1]) if values[lo]<=values[lo+1] else (values[lo+1],values[lo])
        mid=(lo+hi)//2
        if trace: trace.add('DIVIDE', f'Split {n} values into {mid-lo} and {hi-mid}', depth)
        a,b=rec(lo,mid,depth+1); c,d=rec(mid,hi,depth+1)
        comparisons+=2
        if trace: trace.add('COMBINE', f'Min={min(a,c)}; max={max(b,d)}',depth)
        return min(a,c),max(b,d)
    low,high=rec(0,len(values),0)
    return {'algorithm':'minmax','minimum':low,'maximum':high,'comparisons':comparisons,
            'complexity':'O(n) time; O(log n) recursion stack'}

RUNNERS = {'closest_pair':closest_pair, 'integer_multiplication':karatsuba_multiply,
           'inversions':count_inversions,'minmax':minmax}
LABELS = {'closest_pair':'Closest Pair of Points (2D)', 'integer_multiplication':'Karatsuba Integer Multiplication',
          'inversions':'Counting Ordinary Inversions','minmax':'Minimum & Maximum'}
