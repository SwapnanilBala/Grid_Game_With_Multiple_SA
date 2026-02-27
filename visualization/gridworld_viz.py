# visualization/gridworld_viz.py
from __future__ import annotations

from pathlib import Path
from typing import Iterable

import matplotlib.pyplot as plt

State = tuple[int, int]


def save_gridworld_png(
    grid: list[list[str]],
    path: Iterable[State] | None,
    out_path: str | Path,
    title: str | None = None,
) -> None:
    """
    Saves a PNG visualization of the grid + optional path.
    Uses default matplotlib colors (no custom styling).
    """
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    rows = len(grid)
    cols = len(grid[0]) if rows else 0

    # Encode tiles into numbers for imshow
    # 0 free, 1 wall, 2 start, 3 goal, 4 weighted
    img = [[0] * cols for _ in range(rows)]
    for r in range(rows):
        for c in range(cols):
            ch = grid[r][c]
            if ch == "O":
                img[r][c] = 1
            elif ch == "S":
                img[r][c] = 2
            elif ch == "G":
                img[r][c] = 3
            else:
                img[r][c] = 0

    fig, ax = plt.subplots()
    ax.imshow(img)  # default colormap

    # Light gridlines so cells are visible
    ax.set_xticks(range(cols))
    ax.set_yticks(range(rows))
    ax.set_xticklabels([])
    ax.set_yticklabels([])
    ax.grid(True)

    if title:
        ax.set_title(title)

    # Overlay path (if any)
    if path is not None:
        pr = []
        pc = []
        for (r, c) in path:
            pr.append(r)
            pc.append(c)
        ax.plot(pc, pr)  # default line style/color

    fig.tight_layout()
    fig.savefig(out_path, dpi=200)
    plt.close(fig)
