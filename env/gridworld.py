# env/gridworld.py
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

State = tuple[int, int]  # (row, col)

WALL = "#"
START = "S"
GOAL = "G"


@dataclass(slots=True)
class GridWorld:
    grid: list[list[str]]
    start: State
    goal: State

    @classmethod
    def from_file(cls, path: str | Path) -> "GridWorld":
        path = Path(path)
        lines = [line.rstrip("\n") for line in path.read_text(encoding="utf-8").splitlines()]
        # remove empty lines
        lines = [ln for ln in lines if ln.strip() != ""]

        grid: list[list[str]] = [list(ln) for ln in lines]
        rows = len(grid)
        cols = len(grid[0]) if rows else 0
        if rows == 0 or cols == 0:
            raise ValueError("Map is empty.")

        # Ensure rectangular
        for r in range(rows):
            if len(grid[r]) != cols:
                raise ValueError(f"Non-rectangular map at row {r}: expected {cols}, got {len(grid[r])}")

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
        r, c = s
        return 0 <= r < self.rows and 0 <= c < self.cols

    def passable(self, s: State) -> bool:
        r, c = s
        return self.grid[r][c] != WALL

    def step_cost(self, s: State) -> float:
        """
        Cost to ENTER cell s.
        - '.' / 'S' / 'G' => 1
        - digits '1'..'9' => that digit (weighted terrain)
        """
        r, c = s
        ch = self.grid[r][c]
        if ch.isdigit():
            return float(int(ch))
        return 1.0

    def neighbors4(self, s: State) -> Iterable[tuple[State, float]]:
        r, c = s
        for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
            nxt = (r + dr, c + dc)
            if self.in_bounds(nxt) and self.passable(nxt):
                yield nxt, self.step_cost(nxt)

    def is_goal(self, s: State) -> bool:
        return s == self.goal

    def manhattan(self, s: State) -> float:
        (r1, c1) = s
        (r2, c2) = self.goal
        return float(abs(r1 - r2) + abs(c1 - c2))

    def render_with_path(self, path: list[State]) -> str:
        g = [row[:] for row in self.grid]
        for (r, c) in path:
            if g[r][c] in (START, GOAL, WALL):
                continue
            g[r][c] = "•"
        return "\n".join("".join(row) for row in g)
