# 🧭✨ GridWorld Search Visualizer (Maze_Game) — Watch Algorithms Think in Real Time

A modular **pathfinding + search algorithm playground** that lets you **run, compare, and visually replay** classical AI search strategies on custom GridWorld maps.  
This project models a 2D grid environment as a **state space** (each cell is a state; valid moves define transitions) and applies multiple **graph search paradigms** to compute a route from **Start (S)** to **Goal (G)** while avoiding **Obstacles (O)**.  

🔥 The fun part: you can **see the search happen**—node expansions appear live, then the final path gets overlaid so you can instantly compare algorithm behavior.

---

## 🚀 What this project includes (everything in one place)

### 🎯 Core Idea
- Treat the grid as a graph: **State = (row, col)**  
- Use **4-direction movement** (up/down/left/right)  
- Run search algorithms under a **unified contract** so new algorithms plug in cleanly  
- Capture performance data automatically via a standard `SearchResult`

### 🧠 Algorithms Implemented
**Uninformed Search**
- **BFS** — shortest path in *steps* on uniform-cost grids (great baseline)
- **DFS** — explores deep paths fast, low memory, not optimal
- **DLS (Depth-Limited Search)** — DFS with a depth cap (great for demonstrating “too shallow fails vs deeper succeeds”)

**Cost / Optimal Search**
- **UCS (Uniform Cost Search / Dijkstra)** — optimal when step costs are non-negative (acts like BFS when all costs are 1)

**Heuristic Search**
- **A\*** — guided search using **Manhattan distance** (typically expands far fewer nodes than BFS)

**Meet-in-the-middle**
- **BDS (Bidirectional Search / Bidirectional BFS)** — searches from start and goal simultaneously and “meets” in the middle (efficient on unweighted maps)

### 📊 Metrics + Instrumentation (built-in)
Every run returns a `SearchResult` with:
- `found` → whether a path exists
- `path` → the final route (sequence of states)
- `cost` → path cost (for uniform grids, this is basically steps)
- `expanded` → number of expanded nodes (**time proxy**)
- `frontier_max` → maximum frontier size (**memory proxy**)

### 🎮 Visualization (Pygame Replay + PNG Export)
- **Interactive Launcher UI (Pygame)**  
  Pick a map + algorithm, run it, then watch:
  - expanded nodes (blue)
  - final path overlay (red)
  - start (green) + goal (red/pink)

- **Single-run mode** also supports saving a **PNG** summary (matplotlib) into `results/figures/`.

---

## 🗺️ Map Format (S/G/O/F Legend)
Maps are plain `.txt` files inside:


Legend:
- `S` = Start  
- `G` = Goal  
- `O` = Obstacle  
- `F` = Free space  

✅ Important: **All rows must be the same width** (rectangular grid).

Example map:
```txt
OOOOOOOOOOOO
OSFFFFFOFFFO
OFFOOOFFFGOO
OOOOOOOOOOOO 
```

### Run this if you add your custom map and it has some sort of size issue: python tools/fix_maps.py 

This here Automatically :
- strips trailing whitespace
- removes empty lines
- normalizes row lengths (pads with F / truncates when needed)

## Let's talk about how to actually run this thing

-> python main.py --mode launcher 

Or you can just run the main.py file

### These are the controls after you see the UI popping up: 

- ← / → : switch map

- ↑ / ↓ : switch algorithm

- Enter : run visualization

- Esc : exit viewer / quit

## Project Structure 

Maze_Game/
├─ algos/
│  └─ search/                # BFS, DFS, DLS, UCS, A*, BDS
├─ env/                      # GridWorld parsing + transition rules
├─ visualization/            # pygame replay + png export
├─ assets/maps/              # map text files
├─ results/figures/          # saved PNG outputs
├─ tools/                    # map fixer/validator scripts
└─ main.py                   # entry point (launcher + single run)

### The Requirements 

- Python 3.10+ recommended

- pygame

- matplotlib

* A short note:  ignore the requirements as it includes a lot of packages that we really haven't used.


🌟 Why this project is not miserable and actually so cool:

* This is a compact platform to demonstrate and compare search behavior:

- Visually (trace replay)

- Quantitatively (expanded/frontier stats)

- Structurally (clean separation of env / algos / visualization)

* Perfect for:

- `AI search` coursework

- Algorithm comparisons


* A BIG FAT YESSS: Anyone who wants to literally `watch` algorithms “think”