"""AlgoVista — dependency-free local Python API serving a HTML/CSS/JS UI."""
from __future__ import annotations
import json, inspect, mimetypes, webbrowser, threading, argparse
from pathlib import Path
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlsplit, parse_qs, quote
from time import perf_counter_ns
from daa_app.algorithms import RUNNERS, LABELS, Trace
from daa_app.datasets import validate_data, load_dataset, execute
from daa_app.benchmark import verify, benchmark_one

ROOT = Path(__file__).resolve().parent
DATASETS = ROOT/'datasets'
WEB = ROOT/'web'
RESULTS = ROOT/'results'

DESCRIPTIONS = {
 'closest_pair': {
  'category':'Computational Geometry','one_liner':'Find the two closest points in a 2D plane.',
  'description':'Given a cloud of points, identify the pair with the smallest Euclidean distance. Instead of comparing every pair, the algorithm divides the plane, solves both halves, then checks a narrow middle strip.',
  'complexity':'O(n log n)','space':'O(n)','recurrence':'T(n) = 2T(n/2) + O(n)',
  'steps':['Sort points by x and by y coordinates.','Divide the points into a left and right half.','Recursively find the closest pair in each half.','Build a vertical strip near the split line, and compare only nearby y-neighbors.','Return the minimum-distance pair.'],
  'applications':['Collision detection','Spatial analysis','Geographic data'],'concept':'Divide → conquer both halves → merge using the strip.'},
 'integer_multiplication': {
  'category':'Number Theory','one_liner':'Multiply huge numbers with fewer recursive operations.',
  'description':'Karatsuba multiplication splits two large integers into high and low halves. It calculates three smaller products rather than the four required by schoolbook divide-and-conquer multiplication.',
  'complexity':'O(d^1.585)','space':'O(d log d) typical','recurrence':'T(d) = 3T(d/2) + O(d)',
  'steps':['Split each d-digit number into high and low parts.','Compute low×low and high×high recursively.','Compute (high+low)×(high+low) recursively.','Derive the cross product by subtracting the first two products.','Recombine all products using powers of ten.'],
  'applications':['Big integer arithmetic','Cryptography concepts','Computer algebra'],'concept':'Three recursive multiplications replace four.'},
 'inversions': {
  'category':'Array Analytics','one_liner':'Count all out-of-order pairs efficiently.',
  'description':'An inversion is a pair of positions i < j where A[i] > A[j]. A merge-sort approach counts inversions within each half and adds cross-half inversions during the sorted merge.',
  'complexity':'O(n log n)','space':'O(n)','recurrence':'T(n) = 2T(n/2) + O(n)',
  'steps':['Split the array into two halves.','Recursively sort and count inversions in the left half.','Repeat for the right half.','While merging, if the right number is smaller, count all remaining left numbers.','Return the sorted sequence and total inversion count.'],
  'applications':['Ranking comparisons','Sequence analysis','Measuring disorder'],'concept':'A merge step simultaneously sorts and counts.'},
 'minmax': {
  'category':'Array Algorithms','one_liner':'Find both extremes with a comparison-efficient recursion.',
  'description':'The tournament-style min/max algorithm splits an array, finds both extremes in the halves, and compares the two minima and two maxima. For powers of two, it makes 3n/2 − 2 comparisons.',
  'complexity':'O(n)','space':'O(log n)','recurrence':'T(n) = 2T(n/2) + O(1)',
  'steps':['Return the element twice if there is only one value.','Compare two values directly when the segment length is two.','Otherwise split the segment into halves.','Solve min/max recursively for each half.','Compare the two minima and two maxima to form the result.'],
  'applications':['Data profiling','Sensor extremes','Fast dataset summaries'],'concept':'Each merge uses just two comparisons.'}
}

FUNCTIONS = {'closest_pair':'closest_pair','integer_multiplication':'karatsuba_multiply','inversions':'count_inversions','minmax':'minmax'}

def file_for_name(name:str)->Path:
    if not name or '/' in name or '\\' in name or not name.endswith('.json'):
        raise ValueError('Invalid dataset filename.')
    matches = list(DATASETS.glob('*/'+name))
    if len(matches)!=1:raise ValueError('Dataset not found.')
    return matches[0]

def catalog():
    result=[]
    for folder in DATASETS.iterdir():
        if not folder.is_dir():continue
        for path in sorted(folder.glob('*.json')):
            data=load_dataset(path)
            result.append({'filename':path.name,'algorithm':data['algorithm'],'label':LABELS[data['algorithm']], 'size':data['size'],'seed':data.get('seed')})
    return sorted(result,key=lambda a:(a['algorithm'],a['size']))

class Handler(BaseHTTPRequestHandler):
    server_version='AlgoVista/2.0'
    def log_message(self, format, *args):
        if not self.path.startswith('/api/catalog'):super().log_message(format,*args)
    def reply(self,obj,status=200):
        body=json.dumps(obj,ensure_ascii=False,allow_nan=False,default=str).encode('utf-8')
        self.send_response(status);self.send_header('Content-Type','application/json; charset=utf-8')
        self.send_header('Cache-Control','no-store');self.send_header('Content-Length',str(len(body)))
        self.end_headers();self.wfile.write(body)
    def do_GET(self):
        try:
            req=urlsplit(self.path);q=parse_qs(req.query);path=req.path
            if path=='/api/catalog':return self.reply({'datasets':catalog(),'algorithms':LABELS})
            if path=='/api/info':
                infos={}
                for key,details in DESCRIPTIONS.items():
                    infos[key]={**details,'id':key,'label':LABELS[key],'source':inspect.getsource(RUNNERS[key]),'file':'daa_app/algorithms.py'}
                return self.reply({'algorithms':infos})
            if path=='/api/dataset':return self.reply({'data':load_dataset(file_for_name(q.get('file',[''])[0]))})
            if path=='/api/benchmarks':
                return self.reply({'results':json.loads((RESULTS/'benchmark_results.json').read_text(encoding='utf-8'))})
            if path=='/api/download':
                target=file_for_name(q.get('file',[''])[0]);content=target.read_bytes()
                self.send_response(200);self.send_header('Content-Type','application/json')
                self.send_header('Content-Disposition',f'attachment; filename="{target.name}"')
                self.send_header('Content-Length',str(len(content)));self.end_headers();return self.wfile.write(content)
            if path in ('/','/index.html'):target=WEB/'index.html'
            else:
                target=(WEB/path.lstrip('/')).resolve()
                if not target.is_relative_to(WEB.resolve()):raise ValueError('Invalid file path.')
            if not target.is_file():return self.reply({'error':'Not found'},404)
            content=target.read_bytes();kind=mimetypes.guess_type(str(target))[0] or 'application/octet-stream'
            self.send_response(200);self.send_header('Content-Type',kind+('; charset=utf-8' if kind.startswith('text/') or kind=='application/javascript' else ''))
            self.send_header('Content-Length',str(len(content)));self.end_headers();self.wfile.write(content)
        except (ValueError,KeyError,FileNotFoundError) as ex:self.reply({'error':str(ex)},400)
        except Exception as ex:self.reply({'error':f'Internal error: {ex}'},500)
    def do_POST(self):
        if urlsplit(self.path).path!='/api/run':return self.reply({'error':'Not found'},404)
        try:
            length=int(self.headers.get('Content-Length','0'))
            if length<1 or length>8_000_000:raise ValueError('Request too large or empty.')
            payload=json.loads(self.rfile.read(length))
            if 'filename' in payload:data=load_dataset(file_for_name(payload['filename']))
            elif 'data' in payload:data=validate_data(payload['data'])
            else:raise ValueError('Provide filename or data.')
            trace=Trace(limit=360)
            start=perf_counter_ns();result=execute(data,trace)
            elapsed=(perf_counter_ns()-start)/1e6
            ok=verify(data,result) if data['size']<=1000 else None
            return self.reply({'result':result,'verified':ok,'elapsed_ms':round(elapsed,5),
                               'steps':trace.steps,'trace_skipped':trace.skipped,'algorithm':data['algorithm'],'size':data['size']})
        except (ValueError,TypeError,KeyError,OverflowError) as ex:self.reply({'error':str(ex)},400)
        except Exception as ex:self.reply({'error':f'Execution failed: {ex}'},500)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--port',type=int,default=8765);p.add_argument('--no-browser',action='store_true');a=p.parse_args()
    server=ThreadingHTTPServer(('127.0.0.1',a.port),Handler)
    print(f'AlgoVista is available at http://127.0.0.1:{a.port}')
    if not a.no_browser:threading.Timer(.7,lambda:webbrowser.open(f'http://127.0.0.1:{a.port}')).start()
    try:server.serve_forever()
    except KeyboardInterrupt:print('\nExiting AlgoVista.')
    finally:server.server_close()
