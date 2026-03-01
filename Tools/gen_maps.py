"""
Temporary script to generate 60x60 maze maps for all algorithms.
Uses a recursive-backtracker maze generator with extra loop openings
to create complex, interesting mazes.
"""

import random
import sys
from pathlib import Path

sys.setrecursionlimit(10000)

MAPS_DIR = Path(__file__).resolve().parent.parent / "assets" / "maps"


def generate_maze(rows, cols, start, goal, weighted_tiles=None, extra_loops_frac=8):
    # Initialize all walls
    grid = [["O"] * cols for _ in range(rows)]

    def in_bounds(r, c):
        return 1 <= r < rows - 1 and 1 <= c < cols - 1

    # Carve passages using recursive backtracker (iterative stack version)
    sr, sc = 1, 1
    grid[sr][sc] = "F"
    stack = [(sr, sc)]
    visited = {(sr, sc)}

    while stack:
        r, c = stack[-1]
        neighbors = []
        for dr, dc in [(-2, 0), (2, 0), (0, -2), (0, 2)]:
            nr, nc = r + dr, c + dc
            if in_bounds(nr, nc) and (nr, nc) not in visited:
                neighbors.append((nr, nc, r + dr // 2, c + dc // 2))

        if neighbors:
            nr, nc, wr, wc = random.choice(neighbors)
            grid[wr][wc] = "F"
            grid[nr][nc] = "F"
            visited.add((nr, nc))
            stack.append((nr, nc))
        else:
            stack.pop()

    # Open extra random walls to create loops (makes it more interesting for search)
    for _ in range(rows * cols // extra_loops_frac):
        r = random.randint(1, rows - 2)
        c = random.randint(1, cols - 2)
        if grid[r][c] == "O":
            adj_floors = 0
            for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                nr2, nc2 = r + dr, c + dc
                if 0 <= nr2 < rows and 0 <= nc2 < cols and grid[nr2][nc2] != "O":
                    adj_floors += 1
            if adj_floors >= 2:
                grid[r][c] = "F"

    # Place start and goal
    grid[start[0]][start[1]] = "S"
    grid[goal[0]][goal[1]] = "G"

    # Ensure cells around S and G are passable
    for pos in [start, goal]:
        for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            nr, nc = pos[0] + dr, pos[1] + dc
            if 0 < nr < rows - 1 and 0 < nc < cols - 1 and grid[nr][nc] == "O":
                grid[nr][nc] = "F"

    # Scatter weighted terrain tiles on free floor cells
    if weighted_tiles:
        for tile_char, count in weighted_tiles.items():
            placed = 0
            attempts = 0
            while placed < count and attempts < count * 30:
                r = random.randint(1, rows - 2)
                c = random.randint(1, cols - 2)
                attempts += 1
                if grid[r][c] == "F":
                    grid[r][c] = tile_char
                    placed += 1

    return ["".join(row) for row in grid]


# Map dimensions tuned so the viewer almost fills a 1920x1080 screen at cell_size=30
# without any shrinking:  59 cols x 29 rows  -->  window ~1786 x 968 px.
ROWS = 29
COLS = 59
LAST_R = ROWS - 2   # 27
LAST_C = COLS - 2   # 57

# (filename, seed, start, goal, weighted_tiles, extra_loops_frac)
CONFIGS = [
    ("A-Star.txt",          100, (1, 1), (LAST_R, LAST_C), None, 6),
    ("BDS.txt",             200, (1, 1), (1, LAST_C),      None, 6),
    ("BFS.txt",             300, (1, 1), (LAST_R, LAST_C), None, 7),
    ("BFS_Alternate.txt",   400, (1, 1), (LAST_R, LAST_C), None, 5),
    ("DFS.txt",             450, (1, 1), (LAST_R, LAST_C), None, 7),
    ("DLS.txt",             500, (1, 1), (LAST_R, LAST_C), None, 8),
    ("UCS.txt",             600, (1, 1), (LAST_R, LAST_C), None, 6),
    ("UCS_Weighted_01.txt", 700, (1, 1), (LAST_R, LAST_C), {"W": 60, "M": 45}, 6),
    ("UCS_Weighted_02.txt", 800, (1, 1), (LAST_R, LAST_C), {"W": 30, "M": 50, "R": 25}, 6),
    ("Maze_Challenge.txt",  900, (1, 1), (LAST_R, LAST_C), {"W": 25, "M": 35}, 10),
]


def main():
    MAPS_DIR.mkdir(parents=True, exist_ok=True)
    for name, seed, start, goal, wt, loops in CONFIGS:
        random.seed(seed)
        lines = generate_maze(ROWS, COLS, start, goal, wt, loops)

        # Validate
        lens = set(len(ln) for ln in lines)
        assert lens == {COLS}, f"{name} not rectangular: {lens}"
        assert len(lines) == ROWS, f"{name} wrong row count: {len(lines)}"
        assert lines[start[0]][start[1]] == "S", f"{name} missing S"
        assert lines[goal[0]][goal[1]] == "G", f"{name} missing G"

        p = MAPS_DIR / name
        p.write_text("\n".join(lines) + "\n", encoding="utf-8")
        print(f"  {name}: {len(lines)}x{len(lines[0])} OK")

    print(f"\nAll {len(CONFIGS)} maps generated as {ROWS}x{COLS}.")


if __name__ == "__main__":
    main()
