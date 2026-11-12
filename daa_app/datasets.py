"""Reproducible input generation, schema validation, and secure JSON loading."""
from __future__ import annotations
import json, random
from pathlib import Path
from .algorithms import RUNNERS

SIZES = [120, 144, 168, 192, 216, 240, 280, 320, 384, 448]


def build_dataset(algorithm: str, n: int, seed: int) -> dict:
    if algorithm not in RUNNERS: raise ValueError(f'Unknown algorithm {algorithm}')
    if n <= 100: raise ValueError('Project datasets must have input size > 100.')
    rng=random.Random(seed)
    result={'version':1,'algorithm':algorithm,'size':n,'seed':seed}
    if algorithm=='closest_pair':
        # Jittered values, including negative coordinates; distinct positions by index.
        result['points']=[[round(rng.uniform(-1000,1000),4),round(rng.uniform(-1000,1000),4)] for _ in range(n)]
    elif algorithm=='integer_multiplication':
        def digits(k): return str(rng.randint(1,9))+''.join(str(rng.randrange(10)) for _ in range(k-1))
        result['a']=digits(n); result['b']=digits(n)
    else:
        result['values']=[rng.randint(-100000,100000) for _ in range(n)]
    return result


def generate_all(folder: str | Path) -> list[Path]:
    folder=Path(folder); folder.mkdir(parents=True, exist_ok=True)
    files=[]
    for group_i, kind in enumerate(RUNNERS):
        sub=folder/kind; sub.mkdir(exist_ok=True)
        for i, size in enumerate(SIZES, 1):
            data=build_dataset(kind,size,seed=302_2026 + group_i*1000 + i*13)
            path=sub/f'{kind}_{i:02d}_n{size}.json'
            path.write_text(json.dumps(data,indent=2),encoding='utf-8')
            files.append(path)
    return files


def validate_data(data: dict) -> dict:
    if not isinstance(data,dict): raise ValueError('Dataset must be a JSON object.')
    kind=data.get('algorithm')
    if kind not in RUNNERS: raise ValueError('Invalid algorithm type.')
    if kind=='closest_pair':
        points=data.get('points')
        if not isinstance(points,list) or len(points)<2 or any(not isinstance(p,list) or len(p)!=2 or any(type(v) not in (int,float) or abs(v)>1e100 for v in p) for p in points):
            raise ValueError('points must be an array of [x, y] finite numeric pairs.')
        import math
        if any(not math.isfinite(float(v)) for p in points for v in p): raise ValueError('Coordinates must be finite.')
        size=len(points)
    elif kind=='integer_multiplication':
        for key in ('a','b'):
            v=data.get(key)
            if not isinstance(v,str) or not v or not v.lstrip('+-').isdigit() or len(v)>3500:
                raise ValueError('a and b must be decimal integer strings (at most 3500 chars).')
        size=max(len(data['a'].lstrip('+-')),len(data['b'].lstrip('+-')))
    else:
        vals=data.get('values')
        if not isinstance(vals,list) or not vals or any(type(v) not in (int,float) for v in vals):
            raise ValueError('values must be a nonempty numeric array.')
        import math
        if any(not math.isfinite(float(v)) for v in vals): raise ValueError('Values must be finite.')
        size=len(vals)
    if size > 100000: raise ValueError('Dataset too large for interactive execution.')
    result=dict(data)
    result['size']=size
    return result


def load_dataset(path: str | Path) -> dict:
    path=Path(path)
    if path.stat().st_size>8_000_000: raise ValueError('Dataset file exceeds 8 MB limit.')
    return validate_data(json.loads(path.read_text(encoding='utf-8')))


def execute(data: dict, trace=None):
    kind=data['algorithm']
    if kind=='closest_pair': return RUNNERS[kind](data['points'],trace)
    if kind=='integer_multiplication': return RUNNERS[kind](data['a'],data['b'],trace)
    return RUNNERS[kind](data['values'],trace)
