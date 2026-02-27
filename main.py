from __future__ import annotations

import argparse
from pathlib import Path

from Maze_Game.env.gridworld import GridWorld
from Maze_Game.utils.registry import ALGOS, discover_maps
from Maze_Game.visualization.gridworld_viz import save_gridworld_png
from Maze_Game.visualization.pygame_viz import run_launcher, run_trace_viewer

PROJECT_ROOT = Path(__file__).resolve().parent
ASSETS_DIR = PROJECT_ROOT / "assets"
RESULTS_DIR = PROJECT_ROOT / "results"
CONFIGS_DIR = PROJECT_ROOT / "configs"


def run_once(map_path: Path, algo_name: str):
    """
    Runs one algorithm on one map and returns (env, result, trace).
    """
    env = GridWorld.from_file(map_path)
    trace: list[tuple[int, int]] = []

    kwargs = dict(
        start=env.start,
        is_goal=env.is_goal,
        neighbors=env.neighbors4,
        h=env.manhattan,
        trace=trace,
    )

    # BDS needs the explicit goal state
    if algo_name == "bds":
        kwargs["goal"] = env.goal

    result = ALGOS[algo_name](**kwargs)

    return env, result, trace


def main() -> None:
    parser = argparse.ArgumentParser(description="Run search algorithms on GridWorld.")
    parser.add_argument(
        "--mode",
        choices=["launcher", "single"],
        default="launcher",
        help="launcher = swipe UI, single = run one map/algo from args",
    )
    parser.add_argument("--map", default="map01.txt", help="Map filename inside assets/maps/")
    parser.add_argument(
        "--algo",
        choices=list(ALGOS.keys()),
        default="astar",
        help="Search algorithm to run (single mode).",
    )
    parser.add_argument("--out", default=None, help="PNG filename inside results/figures/ (single mode)")
    parser.add_argument("--cell", type=int, default=30, help="Cell size for Pygame viewer.")
    parser.add_argument("--fps", type=int, default=20, help="Start FPS for Pygame viewer.")
    args = parser.parse_args()

    # folders
    RESULTS_DIR.mkdir(exist_ok=True)
    figures_dir = RESULTS_DIR / "figures"
    figures_dir.mkdir(parents=True, exist_ok=True)

    print("Project root:", PROJECT_ROOT)
    print("Assets:", ASSETS_DIR.exists(), ASSETS_DIR)
    print("Configs:", CONFIGS_DIR.exists(), CONFIGS_DIR)
    print("Results:", RESULTS_DIR.exists(), RESULTS_DIR)

    # --- LAUNCHER MODE ---
    if args.mode == "launcher":
        maps = discover_maps(ASSETS_DIR / "maps")
        algos = list(ALGOS.keys())

        if not maps:
            raise FileNotFoundError(f"No map files found in: {ASSETS_DIR / 'maps'}")

        run_launcher(
            maps=maps,
            algos=algos,
            run_once=run_once,
            cell_size=args.cell,
            start_fps=args.fps,
        )
        return

    # --- SINGLE MODE ---
    map_path = ASSETS_DIR / "maps" / args.map
    if not map_path.exists():
        raise FileNotFoundError(f"Map file not found: {map_path}")

    env, result, trace = run_once(map_path, args.algo)

    print(
        f"\n{args.algo.upper()} => found={result.found} cost={result.cost} "
        f"expanded={result.expanded} frontier_max={result.frontier_max}"
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

    # Save PNG (single mode)
    out_name = args.out or f"{args.algo}_{map_path.stem}.png"
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
