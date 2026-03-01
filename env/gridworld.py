# env/gridworld.py
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

State = tuple[int, int]  # (row, col)

# Tile legend used by the text map files in assets/maps/.
# - O = wall (blocked)
# - F = free floor (normal cost)
# - S = start
# - G = goal
# - M/W/R = optional weighted terrain (see step_cost)
WALL = "O"      # was "#"
START = "S"
GOAL = "G"


@dataclass(slots=True)
class GridWorld:
    # Simple grid-based environment.
    # The searches don't know about files or characters; they only see:
    # - a start state
    # - a goal test
    # - a neighbors(...) function that yields (next_state, step_cost)
    grid: list[list[str]]
    start: State
    goal: State

    @classmethod
    def from_file(cls, path: str | Path) -> "GridWorld":
        path = Path(path)
        # Important: don't strip trailing spaces.
        # Some maps use spaces as real walkable tiles, and removing them can make the map
        # look "non-rectangular" even if the file is correct.
        lines = path.read_text(encoding="utf-8").splitlines()
        # remove empty lines
        lines = [ln for ln in lines if ln.strip() != ""]

        # Convert each line into a list of characters so we can index as grid[r][c].
        grid: list[list[str]] = [list(ln) for ln in lines]
        rows = len(grid)
        cols = len(grid[0]) if rows else 0
        if rows == 0 or cols == 0:
            raise ValueError("Map is empty.")

        # Ensure rectangular
        # (All rows must be the same width, otherwise coordinate math breaks.)
        for r in range(rows):
            if len(grid[r]) != cols:
                bad_line = "".join(grid[r])
                raise ValueError(
                    f"Non-rectangular map at row {r} (line {r + 1}): expected {cols}, got {len(grid[r])}. "
                    f"Row repr: {bad_line!r}"
                )

        start: State | None = None
        goal: State | None = None

        for r in range(rows):
            for c in range(cols):
                if grid[r][c] == START:
                    start = (r, c)
                elif grid[r][c] == GOAL:
                    goal = (r, c)

        if start is None:
            raise ValueError("Map missing 'S' (start).")
        if goal is None:
            raise ValueError("Map missing 'G' (goal).")

        return cls(grid=grid, start=start, goal=goal)

    @property
    def rows(self) -> int:
        return len(self.grid)

    @property
    def cols(self) -> int:
        return len(self.grid[0])

    def in_bounds(self, s: State) -> bool:
        # Basic bounds check so we don't walk off the edge of the grid.
        r, c = s
        return 0 <= r < self.rows and 0 <= c < self.cols

    def passable(self, s: State) -> bool:
        # Only walls are blocked.
        r, c = s
        return self.grid[r][c] != WALL

    def step_cost(self, s: State) -> float:
        r, c = s
        ch = self.grid[r][c]
        # This is where "weighted maps" happen.
        # The search algorithms (UCS/A*) don't know about tiles at all — they just add up
        # the step costs we provide here.
        #
        # Default behavior (keeps all existing maps working):
        # - F / S / G / space all cost 1.
        #
        # Extra terrain for weighted maps (Option B - letters):
        # - R = road  (cheap-ish)
        # - M = mud   (kinda expensive)
        # - W = water (very expensive)
        if ch in ("F", START, GOAL, " "):
            return 1.0

        if ch == "R":
            return 1.0
        if ch == "M":
            return 5.0
        if ch == "W":
            return 10.0

        # Unknown tile? Treat it like normal floor so we don't crash on new symbols.
        return 1.0

    def neighbors4(self, s: State) -> Iterable[tuple[State, float]]:
        # 4-way movement (up/down/left/right).
        # We yield (next_state, step_cost) so weighted algorithms can do the right thing.
        r, c = s
        for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
            nxt = (r + dr, c + dc)
            if self.in_bounds(nxt) and self.passable(nxt):
                yield nxt, self.step_cost(nxt)

    def is_goal(self, s: State) -> bool:
        # Goal test function used by the search algorithms.
        return s == self.goal

    def manhattan(self, s: State) -> float:
        # Heuristic used by A*: Manhattan distance on a grid.
        # (This assumes the cheapest step cost is 1. If we ever add cheaper-than-1 tiles,
        # we should scale this by the min step cost to keep it admissible.)
        (r1, c1) = s
        (r2, c2) = self.goal
        return float(abs(r1 - r2) + abs(c1 - c2))

    def render_with_path(self, path: list[State]) -> str:
        # Text-only helper to print the grid, with the final path drawn on top.
        # We keep walls/start/goal intact and mark the rest of the path with a dot.
        g = [row[:] for row in self.grid]
        for (r, c) in path:
            if g[r][c] in (START, GOAL, WALL):
                continue
            g[r][c] = "•"
        return "\n".join("".join(row) for row in g)
