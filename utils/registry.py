from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Any

from Maze_Game.algos.search.astar import astar
from Maze_Game.algos.search.dfs import dfs

AlgoFn = Callable[..., Any]

ALGOS: dict[str, AlgoFn] = {
    "astar": astar,
    "dfs": dfs,
}

def discover_maps(maps_dir: Path) -> list[Path]:
    return sorted(maps_dir.glob("*.txt"))

@dataclass
class RunConfig:
    map_path: Path
    algo_name: str
