from __future__ import annotations

import argparse
from pathlib import Path

from algos.search.astar import astar
from algos.search.dfs import dfs
from env.gridworld import GridWorld
from visualization.gridworld_viz import save_gridworld_png
from visualization.pygame_viz import run_trace_viewer

PROJECT_ROOT = Path(__file__).resolve().parent
ASSETS_DIR = PROJECT_ROOT / "assets"
RESULTS_DIR = PROJECT_ROOT / "results"
CONFIGS_DIR = PROJECT_ROOT / "configs"


def main() -> None:
    parser = argparse.ArgumentParser(description="Run search algorithms on GridWorld.")
    parser.add_argument("--map", default="map01.txt", help="Map filename inside assets/maps/")
    parser.add_argument(
        "--algo",
        choices=["astar", "dfs"],
        default="astar",
        help="Search algorithm to run.",
    )
    parser.add_argument("--out", default=None, help="PNG filename inside results/figures/ (optional)")
    parser.add_argument("--cell", type=int, default=30, help="Cell size for Pygame viewer.")
    parser.add_argument("--fps", type=int, default=20, help="Start FPS for Pygame viewer.")
    args = parser.parse_args()

    RESULTS_DIR.mkdir(exist_ok=True)
    figures_dir = RESULTS_DIR / "figures"
    figures_dir.mkdir(parents=True, exist_ok=True)

    print("Project root:", PROJECT_ROOT)
    print("Assets:", ASSETS_DIR.exists(), ASSETS_DIR)
    print("Configs:", CONFIGS_DIR.exists(), CONFIGS_DIR)
    print("Results:", RESULTS_DIR.exists(), RESULTS_DIR)

    map_path = ASSETS_DIR / "maps" / args.map
    if not map_path.exists():
        raise FileNotFoundError(f"Map file not found: {map_path}")

    env = GridWorld.from_file(map_path)

    trace: list[tuple[int, int]] = []

    if args.algo == "astar":
        result = astar(
            start=env.start,
            is_goal=env.is_goal,
            neighbors=env.neighbors4,
            h=env.manhattan,
            trace=trace,
        )
    else:  # dfs
        result = dfs(
            start=env.start,
            is_goal=env.is_goal,
            neighbors=env.neighbors4,
            trace=trace,
        )

    print(
        f"\n{args.algo.upper()} => found={result.found} cost={result.cost} expanded={result.expanded} frontier_max={result.frontier_max}"
    )

    if result.found:
        print(f"path_len={len(result.path)}")
        print(env.render_with_path(result.path))
    else:
        print("No path found.")

    # Live replay (Pygame)
    run_trace_viewer(
        grid=env.grid,
        trace=trace,
        path=result.path if result.found else None,
        cell_size=args.cell,
        start_fps=args.fps,
    )

    # Save PNG (optional)
    out_name = args.out or f"{args.algo}_{Path(args.map).stem}.png"
    out_path = figures_dir / out_name
    title = f"{args.algo.upper()} | found={result.found} | cost={result.cost} | expanded={result.expanded}"
    save_gridworld_png(
        grid=env.grid,
        path=result.path if result.found else None,
        out_path=out_path,
        title=title,
    )
    print(f"\nSaved: {out_path}")


if __name__ == "__main__":
    main()
