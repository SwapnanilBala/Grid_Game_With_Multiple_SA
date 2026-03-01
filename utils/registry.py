from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Any

# This file is the "wiring hub" for the project.
# It exposes:
# - ALGOS: a name -> function mapping (so the launcher/CLI can pick algorithms by string)
# - discover_maps: helper to list available map files

from Maze_Game.algos.search.astar import astar
from Maze_Game.algos.search.dfs import dfs
from Maze_Game.algos.search.bfs import bfs
from Maze_Game.algos.search.ucs import ucs
from Maze_Game.algos.search.dls import dls
# If our bds file defines bds(...) we use that; if it defines bidirectional_search(...)
# we can import that instead:
from Maze_Game.algos.search.bds import bds  # OR: from Maze_Game.algos.search.bds import bidirectional_search as bds

# Generic type for "something callable" (we keep it loose because different algos take slightly different params).
AlgoFn = Callable[..., Any]

# The main registry used by main.py and the launcher.
# Add a new algorithm here and it'll automatically show up in the UI/CLI choices.
ALGOS: dict[str, AlgoFn] = {
    "astar": astar,
    "dfs": dfs,
    "bfs": bfs,
    "ucs": ucs,
    "dls": dls,
    "bds": bds,
}

# Grabs all map files from the assets/maps folder.
# The launcher uses this to let us swipe through maps.
def discover_maps(maps_dir: Path) -> list[Path]:
    return sorted(maps_dir.glob("*.txt"))

# Tiny container used when we want to bundle a (map, algo) pair together.
@dataclass
class RunConfig:
    map_path: Path
    algo_name: str