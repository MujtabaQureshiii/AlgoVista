"""Execute/validate datasets and save machine-readable benchmark results."""
from __future__ import annotations
import csv, json, math, time
from pathlib import Path
from .datasets import load_dataset, execute


def verify(data, result):
    kind=data['algorithm']
    if kind=='closest_pair':
        ids=result['point_indices']; p=data['points']
        if ids[0]==ids[1]: return False
        d=math.dist(p[ids[0]],p[ids[1]])
        if not math.isclose(d,result['distance'],rel_tol=1e-9,abs_tol=1e-8): return False
        # Full O(n²) correctness oracle for the provided sample sizes.
        expected=min((p[i][0]-p[j][0])**2+(p[i][1]-p[j][1])**2
                     for i in range(len(p)) for j in range(i+1,len(p)))
        return math.isclose(result['distance_squared'],expected,rel_tol=1e-9,abs_tol=1e-8)
    if kind=='integer_multiplication': return int(result['product'])==int(data['a'])*int(data['b'])
    if kind=='inversions':
        a=data['values']; expected=sum(a[i]>a[j] for i in range(len(a)) for j in range(i+1,len(a)))
        return result['inversions']==expected
    if kind=='minmax': return result['minimum']==min(data['values']) and result['maximum']==max(data['values'])
    return False


def benchmark_one(path):
    data=load_dataset(path)
    started=time.perf_counter_ns()
    result=execute(data)
    elapsed=(time.perf_counter_ns()-started)/1_000_000
    ok=verify(data,result)
    field=({'closest_pair': 'distance','integer_multiplication':'digits',
             'inversions':'inversions','minmax':'minimum'}[data['algorithm']])
    summary=str(result[field]); summary=summary[:90]
    return {'dataset':Path(path).name,'algorithm':data['algorithm'],'size':data['size'],
            'time_ms':round(elapsed,4),'verified':ok,'result_summary':summary,
            'comparisons':result.get('comparisons',''),'recursive_calls':result.get('recursive_calls','')}


def benchmark_all(folder, output_folder):
    folder=Path(folder); output_folder=Path(output_folder)
    output_folder.mkdir(parents=True,exist_ok=True)
    files=sorted(folder.rglob('*.json'))
    if not files: raise ValueError(f'No JSON datasets in {folder}')
    records=[benchmark_one(p) for p in files]
    fields=['dataset','algorithm','size','time_ms','verified','result_summary','comparisons','recursive_calls']
    with (output_folder/'benchmark_results.csv').open('w',newline='',encoding='utf-8') as f:
        writer=csv.DictWriter(f,fieldnames=fields); writer.writeheader();writer.writerows(records)
    (output_folder/'benchmark_results.json').write_text(json.dumps(records,indent=2),encoding='utf-8')
    return records
