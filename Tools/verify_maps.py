"""Temporary script to verify all 60x60 maps load and all algorithms find a path."""

from Maze_Game.main import run_once, ASSETS_DIR

maps = [
    "A-Star.txt", "BDS.txt", "BFS.txt", "BFS_Alternate.txt",
    "DFS.txt", "DLS.txt", "UCS.txt", "UCS_Weighted_01.txt",
    "UCS_Weighted_02.txt", "Maze_Challenge.txt",
]
algos = ["astar", "bds", "bfs", "dfs", "dls", "ucs"]

for m in maps:
    for a in algos:
        _, r, _ = run_once(ASSETS_DIR / "maps" / m, a)
        tag = "OK" if r.found else "FAIL"
        print(f"  {m:25s} {a:6s} {tag}  cost={r.cost}")

print("\nDone.")
