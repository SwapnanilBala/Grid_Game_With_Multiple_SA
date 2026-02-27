from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Any

from Maze_Game.algos.search.astar import astar
from Maze_Game.algos.search.dfs import dfs
from Maze_Game.algos.search.bfs import bfs
from Maze_Game.algos.search.ucs import ucs
from Maze_Game.algos.search.dls import dls
# If your bds file defines bds(...) use that; if it defines bidirectional_search(...) use that instead:
from Maze_Game.algos.search.bds import bds  # OR: from Maze_Game.algos.search.bds import bidirectional_search as bds

AlgoFn = Callable[..., Any]

ALGOS: dict[str, AlgoFn] = {
    "astar": astar,
    "dfs": dfs,
    "bfs": bfs,
    "ucs": ucs,
    "dls": dls,
    "bds": bds,
}

def discover_maps(maps_dir: Path) -> list[Path]:
    return sorted(maps_dir.glob("*.txt"))

@dataclass
class RunConfig:
    map_path: Path
    algo_name: str