from pathlib import Path
from daa_app.benchmark import benchmark_all
if __name__=='__main__':
    base=Path(__file__).resolve().parent
    rows=benchmark_all(base/'datasets',base/'results')
    for r in rows:
        print(f"{r['algorithm']:<24} n={r['size']:>4}   {r['time_ms']:>9.4f} ms   {'PASS' if r['verified'] else 'FAIL'}")
    print(f'\nVerified {sum(r["verified"] for r in rows)} / {len(rows)} datasets. Saved CSV and JSON in results/.')
