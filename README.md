# GridWorld Search Visualizer (Maze_Game)

A modular **pathfinding + search algorithm playground** that lets you **run, compare, and visually replay** classical AI search strategies on custom GridWorld maps.

This project models a 2D grid environment as a **state space** (each cell is a state; valid moves define transitions) and applies multiple **graph search paradigms** to compute a route from **Start (`S`)** to **Goal (`G`)** while avoiding **Obstacles (`O`)**.

The key feature is that you can **watch the search happen** in real time: node expansions appear live, followed by an overlay of the final path.

---

## Overview

- **Grid as a graph**
  - State = `(row, col)`
  - 4-direction movement (up/down/left/right)
- **Unified algorithm interface** so new search strategies plug in cleanly
- **Standard `SearchResult` output** to capture performance statistics

---

## Features

- **Modular design**: easy to add new algorithms and maps
- **Real-time visualization**: watch the search process unfold
- **Performance metrics**: track expanded nodes, frontier size, and more
- **Customizable maps**: create and load your own GridWorld maps

---

## Algorithms implemented

### Uninformed search

- **BFS** — shortest path in *steps* on uniform-cost grids (great baseline)
- **DFS** — explores deep paths quickly with low memory usage, not optimal
- **DLS (Depth-Limited Search)** — DFS with a depth cap (useful for demonstrating “too shallow fails vs deeper succeeds”)

### Cost / optimal search

- **UCS (Uniform Cost Search / Dijkstra)** — optimal when step costs are non-negative (equivalent to BFS when all costs are 1)

### Heuristic search

- **A\*** — guided search using **Manhattan distance** (typically expands far fewer nodes than BFS)

### Meet-in-the-middle

- **BDS (Bidirectional Search / Bidirectional BFS)** — searches from start and goal simultaneously and meets in the middle (efficient on unweighted maps)

---

## Metrics and instrumentation

Every run returns a `SearchResult` with:

- `found`: whether a path exists
- `path`: the final route (sequence of states)
- `cost`: path cost (for uniform grids, this is effectively steps)
- `expanded`: number of expanded nodes (time proxy)
- `frontier_max`: maximum frontier size (memory proxy)

---

## Visualization

- **Interactive launcher (Pygame)**
  - Select a map and algorithm
  - Watch expanded nodes and the final path overlay
- **PNG export (matplotlib)**
  - Single-run mode supports saving a PNG summary into `results/figures/`

---

## Map format (`S` / `G` / `O` / `F`)

Maps are plain `.txt` files located in `assets/maps/`.

Legend:

- `S` = Start
- `G` = Goal
- `O` = Obstacle
- `F` = Free space

Important:

- All rows must be the same width (rectangular grid).

Example:

```txt
OOOOOOOOOOOO
OSFFFFFOFFFO
OFFOOOFFFGOO
OOOOOOOOOOOO
```

If you add a custom map and run into sizing/format issues:

```bash
python tools/fix_maps.py
```

This script automatically:

- strips trailing whitespace
- removes empty lines
- normalizes row lengths (pads with `F` / truncates when needed)

---

## Setup

- Python 3.10+ recommended
- `pygame`
- `matplotlib`

Note:

- The existing `requirements` may include extra packages that aren’t used.

---

## Running

Launcher mode:

```bash
python main.py --mode launcher
```

You can also run `main.py` directly from your IDE.

---

## Controls (launcher UI)

- Left / Right: switch map
- Up / Down: switch algorithm
- Enter: run visualization
- Esc: exit viewer / quit

---

## Project structure

```text
Maze_Game/
├─ algos/
│  └─ search/                # BFS, DFS, DLS, UCS, A*, BDS
├─ env/                      # GridWorld parsing + transition rules
├─ visualization/            # pygame replay + png export
├─ assets/maps/              # map text files
├─ results/figures/          # saved PNG outputs
├─ tools/                    # map fixer/validator scripts
└─ main.py                   # entry point (launcher + single run)
```

---

## Why this project is useful

This is a compact platform to demonstrate and compare search behavior:

- Visually (trace replay)
- Quantitatively (expanded/frontier stats)
- Structurally (clean separation of env / algos / visualization)

It’s a good fit for:

- AI search coursework
- Algorithm comparisons
- Anyone who wants to literally watch algorithms “think”