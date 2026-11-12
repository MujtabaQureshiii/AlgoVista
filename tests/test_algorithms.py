import unittest, math, random
from daa_app.algorithms import closest_pair,karatsuba_multiply,count_inversions,minmax,Trace
from daa_app.datasets import build_dataset,validate_data,execute
from daa_app.benchmark import verify

class AlgorithmTests(unittest.TestCase):
    def test_closest_pair_duplicates(self):
        r=closest_pair([[1,1],[2,2],[1,1],[5,5]],Trace())
        self.assertEqual(r['distance'],0)
        self.assertEqual(set(r['point_indices']),{0,2})
    def test_closest_pair_random_oracle(self):
        rng=random.Random(11)
        for n in range(2,45):
            pts=[[rng.randint(-20,20),rng.randint(-20,20)] for _ in range(n)]
            r=closest_pair(pts)
            oracle=min(math.dist(pts[i],pts[j]) for i in range(n) for j in range(i+1,n))
            self.assertAlmostEqual(r['distance'],oracle)
    def test_karatsuba(self):
        rng=random.Random(8)
        for digits in (1,2,18,19,39,101,330):
            a=int(''.join(str(rng.randint(1,9)) for _ in range(digits)))
            b=int(''.join(str(rng.randint(1,9)) for _ in range(digits)))
            for sa in (1,-1):
                got=karatsuba_multiply(sa*a,b,Trace())
                self.assertEqual(int(got['product']),sa*a*b)
    def test_inversions(self):
        self.assertEqual(count_inversions([2,4,1,3,5])['inversions'],3)
        self.assertEqual(count_inversions([2,2,2])['inversions'],0)
        self.assertEqual(count_inversions([3,2,1])['inversions'],3)
    def test_minmax(self):
        for n in range(1,70):
            vals=[(i*17)%23 - 11 for i in range(n)]
            r=minmax(vals)
            self.assertEqual((r['minimum'],r['maximum']),(min(vals),max(vals)))
        self.assertEqual(minmax([8,3,11,-2,7,4,9,1])['comparisons'],10)
    def test_generated_datasets(self):
        for kind in ('closest_pair','integer_multiplication','inversions','minmax'):
            d=validate_data(build_dataset(kind,120,4))
            self.assertEqual(d['size'],120)
            self.assertTrue(verify(d,execute(d)))
if __name__=='__main__': unittest.main()
