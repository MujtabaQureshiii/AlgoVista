# AlgoVista — Interactive Divide & Conquer Studio

An original **HTML/CSS/JavaScript web UI with a local Python algorithm engine** for CS302 Design & Analysis of Algorithms, Parts 2–4.

## Start on Windows
Double-click `START_WINDOWS.bat`. A browser window opens at http://127.0.0.1:8765. If necessary, install Python 3.10+ and ensure it is added to PATH. No pip packages are required.

## Start on macOS/Linux
Run `./START_MAC_LINUX.sh` from this folder, or `python3 server.py`. Open http://127.0.0.1:8765 if the browser does not open automatically.

## Screens
1. **Welcome** — AlgoVista logo, hero animation, and Start Exploring button.
2. **Workspace Hub** — three major options: Run Algorithms, Learn Algorithms, Dataset Explorer.
3. **Run Algorithms** — select algorithm and dataset, run the real Python implementation, inspect result, pass/fail verification, visualization, and animated trace playback. Export execution JSON. You can load custom JSON inputs.
4. **Learn Algorithms** — the concept, purpose, time/space complexity, recurrence, five-step explanation, applications and the **actual Python function source** used by the engine.
5. **Dataset Explorer** — search/filter 40 reproducible JSON datasets, view their full content, download or execute one, and inspect benchmark charts; export CSV.

## Algorithms
- 2D Closest Pair of Points — O(n log n)
- Karatsuba Integer Multiplication — O(d^1.585), where d is the number of decimal digits
- Merge-sort Ordinary Inversion Counting — O(n log n)
- Tournament-Style Minimum and Maximum — O(n)

The 40 JSON datasets are under `datasets/`, 10 per algorithm, with sizes 120, 144, 168, 192, 216, 240, 280, 320, 384, 448. Integer multiplication uses operand digit counts as its input size. The project preserves independent correctness verification and the benchmark outputs from the earlier Python version.

## Project folders
- `web/index.html`, `web/styles.css`, `web/app.js` — original frontend, screen design, animations and visualizations
- `server.py` — Python's standard-library local HTTP server and API endpoints
- `daa_app/algorithms.py` — computational implementations (unchanged from the previous project)
- `daa_app/datasets.py`, `daa_app/benchmark.py` — input and independent verification
- `datasets/` — 40 example inputs
- `results/` — CSV + JSON verification and timing results
- `tests/` — automated algorithm tests
- `generate_datasets.py`, `run_benchmarks.py` — regenerate datasets and benchmarks

## Optional commands
`python -m unittest discover -s tests -v` — automated tests
`python run_benchmarks.py` — recompute all 40 benchmarks on your own computer
`python generate_datasets.py` — regenerate seeded data
`python server.py --port 8999` — use a different port
`python server.py --no-browser` — do not launch a browser automatically

## Notes
This is a local browser-based desktop experience. The Python server binds only to `127.0.0.1` (your own computer). Keep the terminal window open while using AlgoVista. HTML/CSS/JS control the presentation; the Python functions perform all computations. An internet connection is not required, though an optional Google Fonts stylesheet may be loaded if available; safe local font fallbacks are provided. Benchmark timings depend on your system.

Design direction was informed by the polished layout/graphics marketplace aesthetic of GraphicRiver; **no third-party GraphicRiver template, asset, logo or code is copied or redistributed**.

The Learn Algorithms screen also includes a **Pseudocode** tab that gives a language-independent outline for every algorithm.
