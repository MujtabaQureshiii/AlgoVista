"""AlgoVista — an interactive, multi-screen algorithm visualization platform.

Uses standard Tkinter widgets with hand-drawn Canvas visuals, a worker thread,
and step playback. No external graphics libraries or web connection required.
"""
from __future__ import annotations
import csv, json, math, queue, threading, time, inspect
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from pathlib import Path
from .algorithms import LABELS, RUNNERS, Trace
from .datasets import load_dataset, execute
from .benchmark import verify, benchmark_all

ROOT=Path(__file__).resolve().parents[1]
COLORS={'bg':'#0B1220','side':'#101C2F','panel':'#142239','panel2':'#192A43',
        'stroke':'#29415D','fg':'#E9F2FC','muted':'#92A8C2','accent':'#4FDEBD',
        'blue':'#5C93FF','amber':'#FFCB70','pink':'#FB789A','good':'#5CDFB0','danger':'#FC8292'}
FNT='Segoe UI'

ALGORITHM_GUIDES={
'closest_pair':{
'about':'''WHAT IT SOLVES\nGiven n points in two-dimensional space, find two distinct input points with the smallest Euclidean distance.\n\nTECHNIQUE\nDivide and Conquer — spatial partition by x-coordinate.\n\nTIME COMPLEXITY\nO(n log n)\n\nSPACE COMPLEXITY\nO(n) auxiliary storage for ordered point lists.\n\nOUTPUT\nClosest point coordinates, original input indices, Euclidean distance, squared distance, number of point comparisons, and correctness check.\n\nWHY IT MATTERS\nThis is one of the two mandatory implementation tasks in the CS302 project.''',
'method':'''1. Sort points once by x-coordinate and once by y-coordinate.\n\n2. Divide the x-sorted points into left and right halves. Maintain both halves in y-sorted order.\n\n3. Recursively solve the left and right subproblems. For 2 or 3 points, check all pairs directly.\n\n4. Let delta be the best distance found in either half. Build a y-sorted strip containing points within delta of the vertical dividing line.\n\n5. For each strip point, compare only the next at most seven strip points (stopping early when y-separation exceeds delta).\n\n6. Keep the globally best pair; return its coordinates and distance.\n\nVISUALIZATION\nBlue dots show the input points; the amber line and mint rings identify the final closest pair. The trace reveals recursive division, base cases and strip checks.\n\nRECURRENCE\nT(n) = 2T(n/2) + O(n) = O(n log n).'''
},
'integer_multiplication':{
'about':'''WHAT IT SOLVES\nMultiply two potentially very large integers using Karatsuba's divide-and-conquer method.\n\nTECHNIQUE\nSplit operands into high and low decimal halves, then use three recursive multiplications rather than four.\n\nTIME COMPLEXITY\nO(d^log₂3) ≈ O(d^1.585), where d is the number of digits.\n\nOUTPUT\nThe exact product, output digit count, recursive call count, base multiplication count, and verification status.\n\nWHY IT MATTERS\nInteger Multiplication is the second mandatory implementation task in the CS302 project.''',
'method':'''1. Let the operands be x and y, with around d digits. Set B = 10^m, where m = floor(d/2).\n\n2. Split x = xH·B + xL and y = yH·B + yL.\n\n3. Recursively compute z0 = xL·yL and z2 = xH·yH.\n\n4. Compute z1 = (xL+xH)(yL+yH) − z0 − z2 using the third recursive multiplication.\n\n5. Reconstruct xy = z2·B² + z1·B + z0.\n\n6. When numbers are small (18 digits or fewer), multiply directly as a base case. The final sign is restored separately.\n\nVISUALIZATION\nThree outlined panels show z2, z0, and z1; the execution trace records splits, base cases and combinations.\n\nRECURRENCE\nT(d) = 3T(d/2) + O(d).'''
},
'inversions':{
'about':'''WHAT IT SOLVES\nCount all pairs (i, j) in an array with i < j but A[i] > A[j]. These out-of-order pairs are called inversions.\n\nTECHNIQUE\nDivide and Conquer, based on merge sort.\n\nTIME COMPLEXITY\nO(n log n)\n\nSPACE COMPLEXITY\nO(n) auxiliary array storage.\n\nOUTPUT\nNumber of inversions, merge comparison count, sorted prefix, and correctness status.\n\nPROJECT CONNECTION\nThis extends the inversion-counting work from your Part 1 Section C.''',
'method':'''1. Split the array into two nearly equal halves.\n\n2. Recursively count the inversions inside each half.\n\n3. Merge the two sorted halves. If L[i] <= R[j], append L[i].\n\n4. Otherwise L[i] > R[j], which means each remaining element in L from index i forms an inversion with R[j]. Add len(L) − i to the cross-inversion count.\n\n5. Return left inversions + right inversions + cross inversions.\n\nVISUALIZATION\nThe bar chart displays a representative prefix of the input array. The trace shows divide and merge operations.\n\nRECURRENCE\nT(n) = 2T(n/2) + O(n) = O(n log n).'''
},
'minmax':{
'about':'''WHAT IT SOLVES\nFind both the smallest and the largest number in an input array efficiently.\n\nTECHNIQUE\nPairwise divide and conquer; compare outcomes from the two halves.\n\nTIME COMPLEXITY\nO(n)\n\nSPACE COMPLEXITY\nO(log n) recursion stack for balanced recursion.\n\nOUTPUT\nMinimum, maximum, and exact number of key comparisons.\n\nPROJECT CONNECTION\nThis implements the approach from Part 1 Section A.''',
'method':'''1. If the subarray has only one item, that value is both its minimum and maximum.\n\n2. If it has two values, perform exactly one comparison and return them in min/max order.\n\n3. Otherwise split into two nearly equal subarrays and recursively find each half's minimum and maximum.\n\n4. Combine results with two comparisons: compare the local minima, and compare the local maxima.\n\n5. Return the overall minimum and maximum.\n\nVISUALIZATION\nThe bar chart shows a representative input prefix. Mint bars identify extrema appearing in the visible prefix.\n\nCOMPARISON COUNT\nFor n = 2^k, C(n) = 3n/2 − 2, compared with 2(n−1) for a basic brute-force scan.'''
}}

class Studio(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title('AlgoVista  |  Divide & Conquer Algorithm Explorer')
        self.geometry('1510x900')
        self.minsize(1100,720)
        self.configure(bg=COLORS['bg'])
        self.data=None; self.current_path=None; self.result=None; self.trace=[]
        self.step_index=0; self.playing=False; self.busy=False; self.progress_phase=0
        self.playback_speed=1.0; self.last_tick=time.monotonic(); self.guide_open=False; self.guide_moving=False; self.guide_x=0
        self.active_screen='welcome'; self.screen_layer=None; self.guide_frame=None
        self.messages=queue.Queue()
        self.all_files=[]
        self._setup_style()
        self._layout()
        self._discover_files()
        self._choose_first()
        self._show_welcome()
        self.after(80,self._poll)
        self.after(60,self._animate)

    def _setup_style(self):
        style=ttk.Style(self)
        style.theme_use('clam')
        style.configure('Dark.Treeview',background=COLORS['panel'],foreground=COLORS['fg'],
                        fieldbackground=COLORS['panel'],rowheight=27,borderwidth=0,font=(FNT,10))
        style.map('Dark.Treeview',background=[('selected',COLORS['blue'])], foreground=[('selected','#06111F')])
        style.configure('Dark.Treeview.Heading',background=COLORS['panel2'],foreground=COLORS['muted'],
                        padding=(8,8),font=(FNT,9,'bold'),relief='flat')
        style.configure('Dark.TCombobox',fieldbackground=COLORS['panel2'],background=COLORS['panel2'],foreground=COLORS['fg'])
        style.configure('Vista.TNotebook',background=COLORS['panel'],borderwidth=0)
        style.configure('Vista.TNotebook.Tab',background=COLORS['panel2'],foreground=COLORS['muted'],padding=(15,11),font=(FNT,9,'bold'),borderwidth=0)
        style.map('Vista.TNotebook.Tab',background=[('selected',COLORS['side'])],foreground=[('selected',COLORS['accent'])])

    def _label(self,parent,text,size=10,color='fg',bold=False,**kw):
        return tk.Label(parent,text=text,bg=parent.cget('bg'),fg=COLORS.get(color,color),
                        font=(FNT,size,'bold' if bold else 'normal'),**kw)

    def _button(self,parent,label,command,color='panel2',fg='fg',pad=10):
        b=tk.Button(parent,text=label,command=command,relief='flat',borderwidth=0,cursor='hand2',
                    bg=COLORS.get(color,color),fg=COLORS.get(fg,fg),activebackground=COLORS['blue'],
                    activeforeground='#071324',font=(FNT,10,'bold'),padx=17,pady=pad)
        return b

    def _panel(self,parent,**kw):
        return tk.Frame(parent,bg=COLORS['panel'],highlightbackground=COLORS['stroke'],highlightthickness=1,**kw)

    def _layout(self):
        # Sidebar
        self.sidebar=tk.Frame(self,bg=COLORS['side'],width=252)
        self.sidebar.pack(side='left',fill='y'); self.sidebar.pack_propagate(False)
        brand=tk.Frame(self.sidebar,bg=COLORS['side']);brand.pack(fill='x',padx=22,pady=(25,14))
        self._label(brand,'◈  ALGOVISTA',19,'accent',True).pack(anchor='w')
        self._label(brand,'DIVIDE  /  CONQUER  /  VISUALIZE',8,'muted',True).pack(anchor='w',pady=(7,0))
        tk.Frame(self.sidebar,bg=COLORS['stroke'],height=1).pack(fill='x',padx=20,pady=12)
        self._button(self.sidebar,'⌂   Home / Dashboard',self._show_dashboard,color='panel2').pack(fill='x',padx=14,pady=(6,8))
        self._label(self.sidebar,'ALGORITHMS',9,'muted',True).pack(anchor='w',padx=22,pady=(12,9))
        self.alg_buttons={}
        for kind,label in LABELS.items():
            readable={'closest_pair':'01   Closest Pair (2D)','integer_multiplication':'02   Karatsuba Multiply',
                      'inversions':'03   Inversion Count','minmax':'04   Min & Max'}[kind]
            b=self._button(self.sidebar,readable,lambda k=kind:self._open_algorithm(k),color='side',pad=13)
            b.configure(anchor='w',font=(FNT,10),padx=20)
            b.pack(fill='x',padx=10,pady=2)
            self.alg_buttons[kind]=b
        tk.Frame(self.sidebar,bg=COLORS['stroke'],height=1).pack(fill='x',padx=20,pady=23)
        self._label(self.sidebar,'WORKSPACE',9,'muted',True).pack(anchor='w',padx=22,pady=(1,12))
        self._button(self.sidebar,'＋  Open JSON dataset',self._open_file).pack(fill='x',padx=16,pady=5)
        self._button(self.sidebar,'↻  Refresh datasets',self._discover_files).pack(fill='x',padx=16,pady=5)
        self._button(self.sidebar,'▣  Benchmark all 40',self._open_benchmarks,color='blue',fg='#071324').pack(fill='x',padx=16,pady=5)
        self._button(self.sidebar,'ⓘ  Algorithm Guide',self._open_guide,color='panel2').pack(fill='x',padx=16,pady=5)
        tk.Frame(self.sidebar,bg=COLORS['side']).pack(expand=True)
        self._label(self.sidebar,'CS302  •  FALL 2026',9,'muted',True).pack(anchor='w',padx=22)
        self._label(self.sidebar,'Parts 2 / 3 / 4  •  Python',9,'muted').pack(anchor='w',padx=22,pady=(4,24))

        # Main content
        outer=tk.Frame(self,bg=COLORS['bg']);outer.pack(side='left',fill='both',expand=True)
        head=tk.Frame(outer,bg=COLORS['bg']);head.pack(fill='x',padx=24,pady=(23,16))
        self._label(head,'Algorithm Execution Lab',23,'fg',True).pack(side='left')
        self._button(head,'ⓘ  HOW IT WORKS + CODE',self._open_guide,color='blue',fg='#071324',pad=7).pack(side='right',padx=12)
        self.status=self._label(head,'●  READY',10,'accent',True);self.status.pack(side='right',padx=12)
        self._label(outer,'Explore data, execute divide-and-conquer algorithms, and inspect verified results.',10,'muted').pack(anchor='w',padx=24,pady=(0,15))
        metrics=tk.Frame(outer,bg=COLORS['bg']);metrics.pack(fill='x',padx=24,pady=(0,16))
        self.metrics={}
        for i,(key,title) in enumerate([('algorithm','ACTIVE ALGORITHM'),('size','INPUT SIZE'),('runtime','EXECUTION TIME'),('verified','VERIFICATION')]):
            block=self._panel(metrics);block.grid(row=0,column=i,sticky='ew',padx=(0,10) if i<3 else 0)
            metrics.grid_columnconfigure(i,weight=1)
            self._label(block,title,9,'muted',True).pack(anchor='w',padx=15,pady=(12,5))
            label=self._label(block,'—',14,'fg',True,anchor='w');label.pack(fill='x',padx=15,pady=(0,14))
            self.metrics[key]=label
        core=tk.PanedWindow(outer,orient='horizontal',bg=COLORS['bg'],sashwidth=8,borderwidth=0,relief='flat')
        core.pack(fill='both',expand=True,padx=24,pady=(0,19))
        left=self._panel(core);right=self._panel(core)
        core.add(left,minsize=260,width=335);core.add(right,minsize=470)
        self._label(left,'DATASET LIBRARY',11,'fg',True).pack(anchor='w',padx=15,pady=(15,3))
        self.files_sub=self._label(left,'40 reproducible samples',9,'muted');self.files_sub.pack(anchor='w',padx=15,pady=(0,12))
        tree_wrap=tk.Frame(left,bg=COLORS['panel']);tree_wrap.pack(fill='both',expand=True,padx=12,pady=(0,12))
        self.tree=ttk.Treeview(tree_wrap,columns=('size','type'),show='tree headings',style='Dark.Treeview',selectmode='browse')
        self.tree.heading('#0',text='DATASET');self.tree.heading('size',text='N');self.tree.heading('type',text='TYPE')
        self.tree.column('#0',width=155,stretch=True);self.tree.column('size',width=52,anchor='center',stretch=False)
        self.tree.column('type',width=49,anchor='center',stretch=False)
        tree_scroll=ttk.Scrollbar(tree_wrap,command=self.tree.yview);self.tree.configure(yscrollcommand=tree_scroll.set)
        self.tree.pack(side='left',fill='both',expand=True);tree_scroll.pack(side='right',fill='y')
        self.tree.bind('<<TreeviewSelect>>',self._on_tree)
        self._label(left,'SELECTED INPUT',9,'muted',True).pack(anchor='w',padx=15,pady=(0,6))
        self.preview=tk.Text(left,height=7,bg=COLORS['panel2'],fg=COLORS['muted'],borderwidth=0,
                             relief='flat',wrap='word',font=('Consolas',9),padx=10,pady=9)
        self.preview.pack(fill='x',padx=12,pady=(0,10));self.preview.configure(state='disabled')
        self._button(left,'▶   RUN SELECTED DATASET',self._execute,color='accent',fg='#071C24').pack(fill='x',padx=12,pady=(0,14))

        toolbar=tk.Frame(right,bg=COLORS['panel']);toolbar.pack(fill='x',padx=16,pady=(14,8))
        self._label(toolbar,'EXECUTION INSPECTOR',11,'fg',True).pack(side='left')
        self._button(toolbar,'Export result',self._export_result,pad=6).pack(side='right')
        self._button(toolbar,'ⓘ  View algorithm & Python',self._open_guide,pad=6).pack(side='right',padx=8)
        visual=self._panel(right);visual.pack(fill='both',expand=True,padx=14,pady=(2,10))
        vhead=tk.Frame(visual,bg=COLORS['panel']);vhead.pack(fill='x',padx=12,pady=(10,3))
        self._label(vhead,'LIVE VISUALIZATION',9,'muted',True).pack(side='left')
        self.visual_sub=self._label(vhead,'Choose a dataset to begin',9,'muted');self.visual_sub.pack(side='right')
        self.canvas=tk.Canvas(visual,bg=COLORS['panel'],highlightthickness=0,height=245)
        self.canvas.pack(fill='both',expand=True,padx=8,pady=(0,8))
        self.canvas.bind('<Configure>',lambda event:self._render_visual())

        lower=tk.PanedWindow(right,orient='vertical',bg=COLORS['panel'],sashwidth=7,borderwidth=0)
        lower.pack(fill='both',expand=True,padx=14,pady=(0,13))
        outframe=self._panel(lower);stepsframe=self._panel(lower)
        lower.add(outframe,minsize=105,height=150);lower.add(stepsframe,minsize=130,height=235)
        self._label(outframe,'RESULT SUMMARY',9,'muted',True).pack(anchor='w',padx=12,pady=(10,5))
        self.output=tk.Text(outframe,bg=COLORS['panel'],fg=COLORS['fg'],wrap='word',height=4,
                            borderwidth=0,font=('Consolas',10),padx=12,pady=3)
        self.output.pack(fill='both',expand=True,pady=(0,6));self.output.configure(state='disabled')
        stepsheader=tk.Frame(stepsframe,bg=COLORS['panel']);stepsheader.pack(fill='x',padx=10,pady=(8,5))
        self._label(stepsheader,'DIVIDE & CONQUER TRACE',9,'muted',True).pack(side='left')
        self._button(stepsheader,'◀',self._prev_step,pad=4).pack(side='right',padx=2)
        self._button(stepsheader,'▶ / ❚❚',self._toggle_play,pad=4).pack(side='right',padx=2)
        self._button(stepsheader,'▶',self._next_step,pad=4).pack(side='right',padx=2)
        stepwrap=tk.Frame(stepsframe,bg=COLORS['panel']);stepwrap.pack(fill='both',expand=True,padx=11,pady=(0,8))
        self.step_list=tk.Listbox(stepwrap,bg=COLORS['panel'],fg=COLORS['fg'],selectbackground=COLORS['blue'],
                                   selectforeground='#081827',highlightthickness=0,borderwidth=0,
                                   activestyle='none',font=('Consolas',9))
        stepbar=tk.Scrollbar(stepwrap,command=self.step_list.yview,bg=COLORS['panel'])
        self.step_list.configure(yscrollcommand=stepbar.set)
        self.step_list.pack(side='left',fill='both',expand=True);stepbar.pack(side='right',fill='y')
        self.step_list.bind('<<ListboxSelect>>',self._step_selected)
        playback=tk.Frame(stepsframe,bg=COLORS['panel']);playback.pack(fill='x',padx=12,pady=(0,10))
        self.step_progress=tk.Canvas(playback,height=7,bg=COLORS['panel2'],highlightthickness=0)
        self.step_progress.pack(fill='x',pady=(0,7));self.step_progress.bind('<Button-1>',self._scrub_trace)
        self._label(playback,'PLAYBACK SPEED',8,'muted',True).pack(side='left')
        self.speed_control=ttk.Scale(playback,from_=0.4,to=3.5,orient='horizontal',command=lambda v:setattr(self,'playback_speed',float(v)))
        self.speed_control.set(1.0);self.speed_control.pack(side='right',fill='x',expand=True,padx=(15,3))

    def _discover_files(self):
        self.all_files=sorted((ROOT/'datasets').rglob('*.json'))
        self._filter(getattr(self,'active_filter','closest_pair'))

    def _filter(self,kind):
        self.active_filter=kind
        for k,b in self.alg_buttons.items():
            b.configure(bg=COLORS['panel2'] if kind==k else COLORS['side'],fg=COLORS['accent'] if kind==k else COLORS['fg'])
        for item in self.tree.get_children():self.tree.delete(item)
        items=[p for p in self.all_files if p.parent.name==kind]
        for p in items:
            try:
                name=p.stem
                size=int(name.rsplit('_n',1)[-1])
                self.tree.insert('', 'end',iid=str(p),text=name.split('_n')[0][-19:],values=(size,'JSON'))
            except (ValueError,tk.TclError):pass
        self.files_sub.configure(text=f'{len(items)} bundled datasets  •  n > 100')
        self.metrics['algorithm'].configure(text={'closest_pair':'Closest Pair','integer_multiplication':'Karatsuba',
                                                  'inversions':'Inversions','minmax':'Min & Max'}[kind])
        if items:self.tree.selection_set(str(items[0]));self.tree.see(str(items[0]))

    def _choose_first(self):
        items=self.tree.get_children()
        if items:self.tree.selection_set(items[0]);self._on_tree()

    def _open_file(self):
        path=filedialog.askopenfilename(title='Open a CS302 JSON dataset',filetypes=[('JSON dataset','*.json')])
        if path:self._load_path(Path(path))

    def _on_tree(self,event=None):
        items=self.tree.selection()
        if items:self._load_path(Path(items[0]))

    def _load_path(self,path):
        if self.busy:return
        try:data=load_dataset(path)
        except Exception as exc:
            messagebox.showerror('Invalid dataset',str(exc));return
        self.current_path=path;self.data=data;self.result=None;self.trace=[];self.step_index=0;self.playing=False
        self.metrics['size'].configure(text=f'{data["size"]:,}')
        self.metrics['runtime'].configure(text='—')
        self.metrics['verified'].configure(text='NOT RUN',fg=COLORS['muted'])
        self.metrics['algorithm'].configure(text={'closest_pair':'Closest Pair','integer_multiplication':'Karatsuba',
                                                  'inversions':'Inversions','minmax':'Min & Max'}[data['algorithm']])
        if data['algorithm']=='closest_pair':sample=str(data['points'][:7])
        elif data['algorithm']=='integer_multiplication':sample=f'a = {data["a"][:85]}...\nb = {data["b"][:85]}...'
        else:sample=str(data['values'][:22])
        self._set_text(self.preview,f'FILE: {path.name}\nALGORITHM: {LABELS[data["algorithm"]]}\nINPUT: {sample}')
        self._set_text(self.output,'Press RUN SELECTED DATASET to calculate the result and produce a step-by-step trace.')
        self.step_list.delete(0,'end');self.visual_sub.configure(text='INPUT PREVIEW')
        self._render_visual()
        self._refresh_guide_if_open()

    def _execute(self):
        if self.busy or not self.data:return
        self.busy=True;self.playing=False;self._set_status('●  COMPUTING...',COLORS['amber'])
        data=self.data;path=self.current_path
        self._set_text(self.output,'Computing divide-and-conquer solution and validating against a reference result...')
        def worker():
            try:
                t=Trace(limit=260)
                start=time.perf_counter_ns();r=execute(data,t)
                elapsed=(time.perf_counter_ns()-start)/1_000_000
                verified=verify(data,r)
                self.messages.put(('executed',path,r,t,elapsed,verified))
            except Exception as exc:self.messages.put(('error',str(exc)))
        threading.Thread(target=worker,daemon=True).start()

    def _run_benchmarks(self):
        if self.busy:return
        self.busy=True;self._set_status('●  BENCHMARKING...',COLORS['amber'])
        def worker():
            try:
                records=benchmark_all(ROOT/'datasets',ROOT/'results')
                self.messages.put(('benchmarks',records))
            except Exception as exc:self.messages.put(('error',str(exc)))
        threading.Thread(target=worker,daemon=True).start()

    def _poll(self):
        try:
            while True:
                item=self.messages.get_nowait();what=item[0];self.busy=False
                if what=='executed':
                    _,path,r,t,elapsed,verified=item
                    if path!=self.current_path:continue
                    self.result=r;self.trace=t.steps
                    self.metrics['runtime'].configure(text=f'{elapsed:.3f} ms')
                    self.metrics['verified'].configure(text='PASS ✓' if verified else 'FAILED',
                                                       fg=COLORS['good'] if verified else COLORS['danger'])
                    self._set_status('●  COMPLETE' if verified else '●  CHECK FAILED',COLORS['good'] if verified else COLORS['danger'])
                    self._show_result(elapsed,t.skipped)
                    self._set_trace(t.steps,t.skipped)
                    self.playing=bool(t.steps);self.last_tick=time.monotonic()
                    self.visual_sub.configure(text=f'{len(t.steps)} recorded steps')
                    self._render_visual()
                elif what=='benchmarks':
                    recs=item[1];passed=sum(r['verified'] for r in recs)
                    self._set_status('●  BENCHMARK COMPLETE',COLORS['good'])
                    self._show_benchmarks(recs)
                    self._refresh_benchmark_screen()
                    messagebox.showinfo('Benchmark completed',f'{passed} / {len(recs)} datasets verified.\n\nResults saved to:\n{ROOT / "results" / "benchmark_results.csv"}\nand benchmark_results.json')
                elif what=='error':
                    self._set_status('●  ERROR',COLORS['danger'])
                    messagebox.showerror('Execution error',item[1])
        except queue.Empty:pass
        self.after(90,self._poll)

    def _show_result(self,elapsed,skipped):
        r=self.result; kind=r['algorithm']
        if kind=='closest_pair':
            details=f'Nearest points: #{r["point_indices"][0]} {r["points"][0]} and #{r["point_indices"][1]} {r["points"][1]}\nDistance = {r["distance"]:.10f}  |  point comparisons = {r["comparisons"]}'
        elif kind=='integer_multiplication':
            p=r['product'];preview=p if len(p)<=160 else p[:85]+' ... '+p[-55:]
            details=f'Product ({r["digits"]} digits): {preview}\nKaratsuba recursive calls: {r["recursive_calls"]} | base multiplications: {r["base_multiplications"]}'
        elif kind=='inversions':
            details=f'Inversion count = {r["inversions"]:,}\nMerge comparisons = {r["comparisons"]:,} | Sorted prefix = {r["sorted_preview"][:12]}'
        else:
            details=f'Minimum = {r["minimum"]:,}  |  Maximum = {r["maximum"]:,}\nKey comparisons = {r["comparisons"]:,}'
        self._set_text(self.output,f'{details}\nTime: {elapsed:.4f} ms  |  {r["complexity"]}\nTrace: first {len(self.trace)} events; {skipped} additional events condensed.')

    def _set_trace(self,steps,skipped):
        self.step_list.delete(0,'end')
        for i,step in enumerate(steps,1):
            self.step_list.insert('end',f'{i:03d}  {"·"*min(6,step["depth"])}[{step["stage"]:<7}] {step["detail"]}')
        if skipped:self.step_list.insert('end',f'... {skipped} more events omitted to preserve GUI responsiveness')
        self.step_index=0
        self._update_step_progress()
        if steps:self.step_list.selection_set(0);self.step_list.see(0)

    def _step_selected(self,event=None):
        selected=self.step_list.curselection()
        if selected:self.step_index=min(selected[0],max(0,len(self.trace)-1));self._render_visual()

    def _prev_step(self):self._goto_step(self.step_index-1)
    def _next_step(self):self._goto_step(self.step_index+1)
    def _goto_step(self,index):
        if not self.trace:return
        self.step_index=max(0,min(len(self.trace)-1,index))
        self.step_list.selection_clear(0,'end');self.step_list.selection_set(self.step_index)
        self.step_list.see(self.step_index);self._render_visual();self._update_step_progress()

    def _toggle_play(self):
        if self.trace:
            self.playing=not self.playing
            if self.playing and self.step_index>=len(self.trace)-1:self._goto_step(0)
            self.last_tick=time.monotonic()

    def _animate(self):
        self.progress_phase=(self.progress_phase+1)%6
        if self.playing and self.trace and time.monotonic()-self.last_tick >= 0.44/max(0.4,self.playback_speed):
            self.last_tick=time.monotonic()
            if self.step_index>=len(self.trace)-1:self.playing=False
            else:self._goto_step(self.step_index+1)
        self.after(55,self._animate)

    def _show_benchmarks(self,recs):
        lines=['FULL DATASET BENCHMARK RESULTS (40 SAMPLES)','']
        for kind,label in LABELS.items():
            subset=[r for r in recs if r['algorithm']==kind]
            if not subset:continue
            lines.append(f'{label}: {sum(r["verified"] for r in subset)}/{len(subset)} passed')
            lines.append(f'  sizes: {min(r["size"] for r in subset)}–{max(r["size"] for r in subset)}  |  avg runtime: {sum(r["time_ms"] for r in subset)/len(subset):.4f} ms')
        lines.extend(['','Full row-by-row times and results are in results/benchmark_results.csv.'])
        self._set_text(self.output,'\n'.join(lines))

    def _export_result(self):
        if self.result is None:
            messagebox.showinfo('Nothing to export','Run a dataset first.');return
        path=filedialog.asksaveasfilename(defaultextension='.json',filetypes=[('JSON','*.json')],
                                          initialfile='daa_result.json')
        if path:
            payload={'source_file':str(self.current_path),'algorithm':self.data['algorithm'],
                     'input_size':self.data['size'],'result':self.result,'trace':self.trace}
            Path(path).write_text(json.dumps(payload,indent=2),encoding='utf-8')
            messagebox.showinfo('Result exported',f'Saved:\n{path}')

    def _set_text(self,widget,value):
        widget.configure(state='normal');widget.delete('1.0','end');widget.insert('end',value);widget.configure(state='disabled')

    def _set_status(self,value,color):self.status.configure(text=value,fg=color)

    def _render_visual(self):
        c=self.canvas;c.delete('all')
        w=max(c.winfo_width(),320);h=max(c.winfo_height(),190)
        # Subtle dashboard grid
        for x in range(26,w,42):c.create_line(x,0,x,h,fill='#1B2B43')
        for y in range(18,h,42):c.create_line(0,y,w,y,fill='#1B2B43')
        if not self.data:
            c.create_text(w/2,h/2,text='LOAD A DATASET',fill=COLORS['muted'],font=(FNT,15,'bold'));return
        kind=self.data['algorithm']
        if kind=='closest_pair':
            pts=self.data['points'];xs=[p[0] for p in pts];ys=[p[1] for p in pts]
            xmin,xmax=min(xs),max(xs);ymin,ymax=min(ys),max(ys)
            def pos(pt):
                return 25+(pt[0]-xmin)/max(1e-9,xmax-xmin)*(w-50), h-22-(pt[1]-ymin)/max(1e-9,ymax-ymin)*(h-44)
            for p in pts:
                x,y=pos(p);c.create_oval(x-2.4,y-2.4,x+2.4,y+2.4,fill=COLORS['blue'],outline='')
            if self.result:
                p,q=self.result['points'];x1,y1=pos(p);x2,y2=pos(q)
                c.create_line(x1,y1,x2,y2,fill=COLORS['amber'],width=3)
                for x,y in ((x1,y1),(x2,y2)):
                    c.create_oval(x-7,y-7,x+7,y+7,outline=COLORS['accent'],width=3)
            c.create_text(w-14,15,text=f'{len(pts)} XY POINTS',anchor='ne',fill=COLORS['muted'],font=(FNT,9,'bold'))
        elif kind in ('minmax','inversions'):
            vals=self.data['values'];subset=vals[:min(72,len(vals))]
            lo=min(subset);hi=max(subset);step=(w-42)/len(subset)
            for i,v in enumerate(subset):
                height=12+(v-lo)/max(1e-9,hi-lo)*(h-57)
                x=20+i*step
                color=COLORS['accent'] if kind=='minmax' and self.result and v in (self.result['minimum'],self.result['maximum']) else COLORS['blue']
                c.create_rectangle(x,h-22-height,x+max(2,step-2),h-22,fill=color,outline='')
            c.create_text(w-14,15,text=f'FIRST {len(subset)} / {len(vals)} VALUES',anchor='ne',fill=COLORS['muted'],font=(FNT,9,'bold'))
        else:
            a=self.data['a'];b=self.data['b'];half=max(len(a),len(b))//2
            x=w/2
            c.create_text(x,32,text='KARATSUBA: THREE RECURSIVE PRODUCTS',fill=COLORS['fg'],font=(FNT,13,'bold'))
            c.create_text(x,72,text=f'{len(a)}-digit × {len(b)}-digit input operands',fill=COLORS['muted'],font=(FNT,11))
            for i,(label,color) in enumerate((('z₂: high × high',COLORS['blue']),('z₀: low × low',COLORS['accent']),('z₁: (high+low)² − z₂ − z₀',COLORS['amber']))):
                bx=22+i*(w-44)/3;bw=(w-60)/3
                c.create_rectangle(bx,110,bx+bw,min(h-45,162),fill=COLORS['panel2'],outline=color,width=2)
                c.create_text(bx+bw/2,min(h-69,133),text=label,fill=color,font=(FNT,9,'bold'),width=bw-8)
            c.create_text(x,h-18,text=f'SPLIT ~ {half} DECIMAL DIGITS   •   T(d) = 3T(d/2) + O(d)',fill=COLORS['muted'],font=(FNT,9))
        if self.trace:
            step=self.trace[min(self.step_index,len(self.trace)-1)]
            c.create_rectangle(8,h-38,w-8,h-5,fill=COLORS['side'],outline=COLORS['stroke'])
            detail=f'STEP {self.step_index+1:03d}/{len(self.trace):03d}  •  {step["stage"]}: {step["detail"]}'
            c.create_text(16,h-22,text=detail[:120],anchor='w',fill=COLORS['accent'],font=(FNT,9,'bold'),width=w-40)


    # ---- Screen transitions and welcome/dashboard experiences ----
    def _clear_screen_layer(self):
        if self.guide_frame is not None:
            self.guide_frame.destroy();self.guide_frame=None;self.guide_open=False
        if self.screen_layer is not None:
            self.screen_layer.destroy();self.screen_layer=None

    def _show_welcome(self):
        self._clear_screen_layer()
        self.active_screen='welcome'
        layer=tk.Frame(self,bg=COLORS['bg'])
        layer.place(relx=0,rely=0,relwidth=1,relheight=1)
        self.screen_layer=layer
        art=tk.Canvas(layer,bg=COLORS['bg'],highlightthickness=0)
        art.pack(fill='both',expand=True)
        self.welcome_art=art
        self._welcome_frame=0
        def draw(event=None):
            if not art.winfo_exists():return
            art.delete('all');w=art.winfo_width();h=art.winfo_height()
            art.create_rectangle(0,0,w,h,fill=COLORS['bg'],outline='')
            for i in range(18):
                x=(i*191+30)%max(1,w);y=(i*107+55)%max(1,h)
                r=2+((i*3)%4)
                art.create_oval(x-r,y-r,x+r,y+r,fill=COLORS['stroke'],outline='')
            shift=self._welcome_frame*2.8
            for i in range(5):
                x=w*.72+i*33;y=h*.47-160+i*58
                art.create_line(x-220,y+90,x+60,y-70,fill=COLORS['stroke'],width=2)
                art.create_oval(x+math.sin(shift/32+i)*35-9,y-9,x+math.sin(shift/32+i)*35+9,y+9,fill=COLORS['accent'] if i%2 else COLORS['blue'],outline='')
            for j in range(4):
                bx=w*.74+j*48;by=h*.60-j*54
                art.create_rectangle(bx-12,by-12,bx+12,by+12,fill=COLORS['panel2'],outline=COLORS['accent'],width=2)
            art.create_text(w*.09,h*.28,text='◈  ALGOVISTA',anchor='w',fill=COLORS['accent'],font=(FNT,26,'bold'))
            art.create_text(w*.09,h*.42,text='DIVIDE. CONQUER.\nUNDERSTAND.',anchor='w',fill=COLORS['fg'],font=(FNT,39,'bold'))
            art.create_text(w*.09,h*.60,text='An interactive algorithm visualization and analysis platform.\nFour divide-and-conquer algorithms · Forty verified datasets.\nExplore the actual Python code and follow every recorded step.',anchor='w',fill=COLORS['muted'],font=(FNT,12),width=w*.58)
            art.create_rectangle(w*.09,h*.73,w*.09+240,h*.73+57,fill=COLORS['accent'],outline='')
            art.create_text(w*.09+120,h*.73+28,text='START EXPLORING  →',fill='#071C24',font=(FNT,12,'bold'))
            art.create_text(w*.09,h*.89,text='CS302  •  DESIGN AND ANALYSIS OF ALGORITHMS  •  FALL 2026',anchor='w',fill=COLORS['muted'],font=(FNT,10,'bold'))
            self.start_rect=(w*.09,h*.73,w*.09+240,h*.73+57)
        def click(ev):
            x1,y1,x2,y2=getattr(self,'start_rect',(0,0,0,0))
            if x1<=ev.x<=x2 and y1<=ev.y<=y2:self._show_dashboard()
        art.bind('<Configure>',draw);art.bind('<Button-1>',click)
        def tick():
            if self.active_screen!='welcome' or not art.winfo_exists():return
            self._welcome_frame+=1;draw();self.after(65,tick)
        self.after(130,tick)

    def _show_dashboard(self):
        self._clear_screen_layer();self.active_screen='dashboard'
        layer=tk.Frame(self,bg=COLORS['bg']);layer.place(relx=0,rely=0,relwidth=1,relheight=1);self.screen_layer=layer
        top=tk.Frame(layer,bg=COLORS['bg']);top.pack(fill='x',padx=65,pady=(45,27))
        self._label(top,'◈  ALGOVISTA',25,'accent',True).pack(side='left')
        self._button(top,'Return to welcome',self._show_welcome).pack(side='right')
        center=tk.Frame(layer,bg=COLORS['bg']);center.pack(fill='both',expand=True,padx=65,pady=(42,20))
        self._label(center,'YOUR ALGORITHM WORKSPACE',10,'accent',True).pack(anchor='w')
        self._label(center,'Choose what to explore.',34,'fg',True).pack(anchor='w',pady=(8,7))
        self._label(center,'A complete workflow for running algorithms, inspecting their Python code, and comparing performance.',12,'muted').pack(anchor='w',pady=(0,36))
        cards=tk.Frame(center,bg=COLORS['bg']);cards.pack(fill='x')
        info=[('01  /  EXECUTE','Algorithm Execution Lab','Select JSON inputs, launch verified calculations, view visual plots and replay each recursion trace.','OPEN EXECUTION LAB',self._show_lab),
              ('02  /  LEARN','Algorithm Guide & Source','Learn each algorithm, see its complexity and read the exact Python function that powers its execution.','EXPLORE ALGORITHMS',self._open_guide_from_dashboard),
              ('03  /  MEASURE','Benchmark Center','Compare all 40 saved input datasets and generate fresh timings and correctness verification reports.','OPEN BENCHMARKS',self._open_benchmarks)]
        for ix,(eyebrow,title,description,action,callback) in enumerate(info):
            tile=self._panel(cards);tile.grid(row=0,column=ix,sticky='nsew',padx=(0,18) if ix<2 else 0,ipady=15)
            cards.grid_columnconfigure(ix,weight=1,uniform='tile')
            self._label(tile,eyebrow,10,'accent',True).pack(anchor='w',padx=22,pady=(22,12))
            self._label(tile,title,17,'fg',True,wraplength=280,justify='left').pack(anchor='w',padx=22,pady=(0,15))
            self._label(tile,description,11,'muted',wraplength=275,justify='left').pack(anchor='w',padx=22,pady=(0,28))
            self._button(tile,action,callback,color='blue',fg='#071324').pack(anchor='w',padx=22,pady=(0,15))
        stats=tk.Frame(center,bg=COLORS['bg']);stats.pack(fill='x',pady=(50,0))
        self._label(stats,'4 ALGORITHMS    /    40 INPUT FILES    /    n = 120–448    /    PYTHON 3',11,'accent',True).pack(anchor='w')

    def _show_lab(self):
        self._clear_screen_layer();self.active_screen='lab'

    def _open_algorithm(self,kind):
        self._show_lab();self._filter(kind)

    def _open_guide_from_dashboard(self):
        self._show_lab();self._open_guide()

    def _open_benchmarks(self):
        self._clear_screen_layer();self.active_screen='benchmarks'
        layer=tk.Frame(self,bg=COLORS['bg']);layer.place(relx=0,rely=0,relwidth=1,relheight=1);self.screen_layer=layer
        head=tk.Frame(layer,bg=COLORS['bg']);head.pack(fill='x',padx=45,pady=(40,15))
        self._label(head,'Benchmark Center',28,'fg',True).pack(side='left')
        self._button(head,'← Back to Lab',self._show_lab).pack(side='right')
        self._label(layer,'Run independent checks on every dataset. Exact timings depend on your machine.',11,'muted').pack(anchor='w',padx=45,pady=(0,16))
        tools=tk.Frame(layer,bg=COLORS['bg']);tools.pack(fill='x',padx=45,pady=(0,18))
        self._button(tools,'▶  RUN ALL 40 BENCHMARKS',self._run_benchmarks,color='accent',fg='#071324').pack(side='left',padx=(0,9))
        self._button(tools,'Open results CSV',lambda:self._open_csv()).pack(side='left')
        columns=('algorithm','dataset','size','time_ms','verified')
        holder=self._panel(layer);holder.pack(fill='both',expand=True,padx=45,pady=(0,32))
        self.benchmark_tree=ttk.Treeview(holder,columns=columns,show='headings',style='Dark.Treeview')
        for col,label,width in [('algorithm','ALGORITHM',200),('dataset','DATASET',250),('size','INPUT SIZE',110),('time_ms','TIME (MS)',130),('verified','VERIFIED',120)]:
            self.benchmark_tree.heading(col,text=label);self.benchmark_tree.column(col,width=width,stretch=True)
        scroll=ttk.Scrollbar(holder,command=self.benchmark_tree.yview)
        self.benchmark_tree.configure(yscrollcommand=scroll.set)
        self.benchmark_tree.pack(side='left',fill='both',expand=True,padx=(10,0),pady=10)
        scroll.pack(side='right',fill='y',pady=10)
        self._refresh_benchmark_screen()

    def _refresh_benchmark_screen(self):
        if self.active_screen!='benchmarks' or not hasattr(self,'benchmark_tree') or not self.benchmark_tree.winfo_exists():return
        for item in self.benchmark_tree.get_children():self.benchmark_tree.delete(item)
        path=ROOT/'results'/'benchmark_results.json'
        if not path.exists():return
        try:
            content=json.loads(path.read_text(encoding='utf-8'))
            if isinstance(content,dict):content=content.get('records',[])
            for entry in content:
                self.benchmark_tree.insert('','end',values=(LABELS.get(entry['algorithm'],entry['algorithm']),entry.get('dataset',entry.get('file','')),entry['size'],f"{entry['time_ms']:.4f}",'PASS' if entry['verified'] else 'FAIL'))
        except Exception:pass

    def _open_csv(self):
        import os,subprocess,sys
        p=ROOT/'results'/'benchmark_results.csv'
        if not p.exists():messagebox.showinfo('No CSV','Run the benchmark first.');return
        try:
            if sys.platform=='win32':os.startfile(p)
            elif sys.platform=='darwin':subprocess.Popen(['open',str(p)])
            else:subprocess.Popen(['xdg-open',str(p)])
        except Exception:messagebox.showinfo('Results CSV',str(p))

    # ---- Right-side guide drawer: explanatory content + actual source code ----
    def _open_guide(self):
        self._show_lab()
        if self.guide_frame is not None and self.guide_frame.winfo_exists():
            self._refresh_guide_if_open();return
        self.guide_open=True;self.guide_moving=False
        drawer=tk.Frame(self,bg=COLORS['panel'],highlightthickness=2,highlightbackground=COLORS['blue'])
        self.guide_frame=drawer
        width=min(650,max(470,int(self.winfo_width()*.45)))
        self.guide_width=width;self.guide_x=self.winfo_width()
        drawer.place(x=self.guide_x,y=0,width=width,relheight=1)
        header=tk.Frame(drawer,bg=COLORS['side']);header.pack(fill='x')
        self._label(header,'ⓘ  ALGORITHM INSIGHT',15,'accent',True).pack(side='left',padx=20,pady=18)
        self._button(header,'✕  Close',self._close_guide,pad=6).pack(side='right',padx=14)
        self.guide_name=self._label(drawer,'',19,'fg',True,wraplength=580,justify='left')
        self.guide_name.pack(anchor='w',padx=20,pady=(22,6))
        selector=tk.Frame(drawer,bg=COLORS['panel']);selector.pack(fill='x',padx=20,pady=(6,17))
        self.guide_choice=tk.StringVar(value=(self.data or {}).get('algorithm','closest_pair'))
        options=ttk.Combobox(selector,textvariable=self.guide_choice,values=list(LABELS),state='readonly',width=25,font=(FNT,10),style='Dark.TCombobox')
        options.pack(side='left');options.bind('<<ComboboxSelected>>',lambda e:self._fill_guide())
        self._label(selector,'Change algorithm',9,'muted').pack(side='left',padx=12)
        tabs=ttk.Notebook(drawer,style='Vista.TNotebook');tabs.pack(fill='both',expand=True,padx=18,pady=(0,17));self.guide_tabs=tabs
        for key,name in [('about','OVERVIEW'),('method','HOW IT WORKS'),('code','PYTHON SOURCE')]:
            page=tk.Frame(tabs,bg=COLORS['panel']);tabs.add(page,text='  '+name+'  ')
            view=tk.Text(page,bg=COLORS['panel'],fg=COLORS['fg'],wrap='word' if key!='code' else 'none',font=('Consolas',10) if key=='code' else (FNT,11),borderwidth=0,padx=16,pady=18,spacing3=7)
            sy=ttk.Scrollbar(page,command=view.yview);view.configure(yscrollcommand=sy.set)
            sy.pack(side='right',fill='y');view.pack(side='left',fill='both',expand=True)
            if key=='code':
                view.tag_configure('keyword',foreground=COLORS['accent']);view.tag_configure('comment',foreground=COLORS['muted'])
            setattr(self,'guide_'+key,view)
        foot=tk.Frame(drawer,bg=COLORS['side']);foot.pack(fill='x')
        self._button(foot,'▶  RUN THIS ALGORITHM',self._guide_run,color='accent',fg='#071C24').pack(side='right',padx=18,pady=14)
        self._label(foot,'Source displayed is the actual Python function used by the app.',9,'muted').pack(side='left',padx=18)
        self._fill_guide()
        self._slide_guide(opening=True)

    def _guide_run(self):
        choice=self.guide_choice.get();self._filter(choice);self._close_guide();self.after(300,self._execute)

    def _fill_guide(self):
        kind=self.guide_choice.get()
        self.guide_name.configure(text=LABELS[kind])
        self._set_text(self.guide_about,ALGORITHM_GUIDES[kind]['about'])
        self._set_text(self.guide_method,ALGORITHM_GUIDES[kind]['method'])
        code=inspect.getsource(RUNNERS[kind])
        view=self.guide_code;self._set_text(view,code)
        view.configure(state='normal')
        import re
        for m in re.finditer(r'\b(def|return|if|else|elif|while|for|in|not|and|or|nonlocal|raise|None)\b',code):
            view.tag_add('keyword',f'1.0+{m.start()}c',f'1.0+{m.end()}c')
        for no,line in enumerate(code.splitlines(),1):
            if '#' in line:view.tag_add('comment',f'{no}.{line.index("#")}',f'{no}.end')
        view.configure(state='disabled')

    def _refresh_guide_if_open(self):
        if self.guide_open and self.guide_frame is not None and self.guide_frame.winfo_exists():
            if self.data:self.guide_choice.set(self.data['algorithm']);self._fill_guide()

    def _slide_guide(self,opening):
        if self.guide_frame is None or not self.guide_frame.winfo_exists():return
        target=self.winfo_width()-self.guide_width if opening else self.winfo_width()
        delta=target-self.guide_x
        if abs(delta)<3:
            self.guide_x=target;self.guide_frame.place_configure(x=target)
            if not opening:self.guide_frame.destroy();self.guide_frame=None;self.guide_open=False
            return
        self.guide_x+=delta*.28
        self.guide_frame.place_configure(x=int(self.guide_x))
        self.after(17,lambda:self._slide_guide(opening))

    def _close_guide(self):
        if self.guide_frame is not None:self._slide_guide(opening=False)

    def _update_step_progress(self):
        if not hasattr(self,'step_progress') or not self.step_progress.winfo_exists():return
        c=self.step_progress;c.delete('all');w=max(10,c.winfo_width())
        n=len(self.trace)
        fraction=(self.step_index+1)/n if n else 0
        c.create_rectangle(0,0,w*fraction,7,fill=COLORS['accent'],outline='')

    def _scrub_trace(self,event):
        if self.trace:
            self.playing=False
            self._goto_step(round((event.x/max(1,self.step_progress.winfo_width()))*(len(self.trace)-1)))

def main():
    app=Studio();app.mainloop()

if __name__=='__main__':main()
