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
    # This is a lightweight "export" visualizer.
    # The Pygame viewer is for interactive replay; this one is for saving a static image.
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
                # Anything that's not a wall/start/goal is treated as walkable.
                # (That includes weighted terrain like M/W/R.)
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
        # Plot the path as a simple line over the grid.
        pr = []
        pc = []
        for (r, c) in path:
            pr.append(r)
            pc.append(c)
        ax.plot(pc, pr)  # default line style/color

    fig.tight_layout()
    fig.savefig(out_path, dpi=200)
    plt.close(fig)


from datetime import datetime


def save_comparison_jpg(
    algo1_name: str,
    result1,          # SearchResult
    algo2_name: str,
    result2,          # SearchResult
    map_name: str,
    out_path: "str | Path",
) -> None:
    """
    Saves a side-by-side algorithm comparison figure as a JPEG.
    Top row: 4 bar charts (expanded, frontier_max, cost, path_len).
    Bottom row: summary table with a winner row.
    """
    import matplotlib.pyplot as plt
    import matplotlib.gridspec as gridspec
    from matplotlib.patches import FancyBboxPatch
    from pathlib import Path as _Path

    out_path = _Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    # ── Palette ──────────────────────────────────────────────────────────────
    BG       = "#0f1117"
    TEXT_COL = "#e8eaf0"
    DIM_COL  = "#8890a4"
    COL1     = "#6482ff"   # blue-violet  (algo 1)
    COL2     = "#ffa03c"   # amber        (algo 2)
    COL_WIN  = "#50ff8c"   # lime green   (winner highlight)
    COL_FAIL = "#ff4060"   # red          (not found)

    # ── Data ─────────────────────────────────────────────────────────────────
    def _val(result, attr):
        if not result.found and attr in ("cost", "path_len"):
            return None
        if attr == "path_len":
            return len(result.path)
        return getattr(result, attr)

    metrics = [
        ("Nodes\nExpanded",  "expanded"),
        ("Max\nFrontier",    "frontier_max"),
        ("Path\nCost",       "cost"),
        ("Path\nLength",     "path_len"),
    ]

    v1 = [_val(result1, m[1]) for m in metrics]
    v2 = [_val(result2, m[1]) for m in metrics]

    # ── Figure ───────────────────────────────────────────────────────────────
    fig = plt.figure(figsize=(14, 8), facecolor=BG)
    gs  = gridspec.GridSpec(2, 4, figure=fig, hspace=0.55, wspace=0.45,
                            top=0.88, bottom=0.12, left=0.06, right=0.97)

    fig.suptitle(
        f"Algorithm Comparison  —  {map_name}",
        color=TEXT_COL, fontsize=14, fontweight="bold", y=0.97,
    )

    # ── Bar charts (top row) ─────────────────────────────────────────────────
    for col_idx, (label, attr) in enumerate(metrics):
        ax = fig.add_subplot(gs[0, col_idx])
        ax.set_facecolor(BG)
        ax.spines[:].set_color("#2a3040")
        ax.tick_params(colors=DIM_COL, labelsize=8)
        ax.yaxis.label.set_color(DIM_COL)

        a1 = v1[col_idx]
        a2 = v2[col_idx]

        bars_x  = [0.35, 1.15]
        heights = [a1 if a1 is not None else 0,
                   a2 if a2 is not None else 0]
        colors  = [COL1, COL2]

        bars = ax.bar(bars_x, heights, width=0.55, color=colors,
                      edgecolor="none", zorder=3)
        ax.set_xticks(bars_x)
        ax.set_xticklabels(
            [algo1_name.upper(), algo2_name.upper()],
            fontsize=7, color=TEXT_COL,
        )
        ax.set_title(label, color=TEXT_COL, fontsize=8.5, pad=4)
        ax.set_xlim(-0.1, 1.65)
        ax.yaxis.set_tick_params(labelsize=7)
        ax.grid(axis="y", color="#1e2435", linewidth=0.6, zorder=0)

        for bar, val, is_none in zip(bars, [a1, a2], [a1 is None, a2 is None]):
            if is_none:
                ax.text(bar.get_x() + bar.get_width() / 2, 0.5,
                        "N/A", ha="center", va="bottom",
                        fontsize=7, color=COL_FAIL, fontweight="bold")
            else:
                ax.text(bar.get_x() + bar.get_width() / 2,
                        bar.get_height() * 1.02,
                        f"{val:.1f}" if isinstance(val, float) and val != int(val) else str(int(val)) if val is not None else "N/A",
                        ha="center", va="bottom",
                        fontsize=7.5, color=TEXT_COL, fontweight="bold")

    # ── Table (bottom row, full width) ───────────────────────────────────────
    ax_tbl = fig.add_subplot(gs[1, :])
    ax_tbl.set_facecolor(BG)
    ax_tbl.axis("off")

    def _fmt(val, attr):
        if val is None:
            return "—"
        if attr == "cost":
            return f"{val:.2f}"
        return str(int(val))

    def _winner_char(v1, v2):
        """Return (w1_wins, w2_wins) bool tuple. Lower is better for all metrics."""
        if v1 is None and v2 is None:
            return False, False
        if v1 is None:
            return False, True
        if v2 is None:
            return True, False
        return v1 < v2, v2 < v1

    row_labels  = ["Found", "Path Cost", "Path Length",
                   "Nodes Expanded", "Max Frontier", "Winner (↓ better)"]
    row_attrs   = ["found", "cost", "path_len", "expanded", "frontier_max", "__winner__"]

    # Count wins (lower is better for numerical metrics)
    num_metrics = ["cost", "path_len", "expanded", "frontier_max"]
    w1_total, w2_total = 0, 0
    for attr in num_metrics:
        a, b = _winner_char(_val(result1, attr), _val(result2, attr))
        if a: w1_total += 1
        if b: w2_total += 1

    table_data  = []
    cell_colors = []
    for label, attr in zip(row_labels, row_attrs):
        if attr == "found":
            c1 = "Yes" if result1.found else "No"
            c2 = "Yes" if result2.found else "No"
            cc1 = COL_WIN if result1.found else COL_FAIL
            cc2 = COL_WIN if result2.found else COL_FAIL
        elif attr == "__winner__":
            c1 = f"{w1_total} / {len(num_metrics)}"
            c2 = f"{w2_total} / {len(num_metrics)}"
            cc1 = COL_WIN if w1_total > w2_total else (DIM_COL if w1_total == w2_total else COL_FAIL)
            cc2 = COL_WIN if w2_total > w1_total else (DIM_COL if w1_total == w2_total else COL_FAIL)
        else:
            c1 = _fmt(_val(result1, attr), attr)
            c2 = _fmt(_val(result2, attr), attr)
            a, b = _winner_char(_val(result1, attr), _val(result2, attr))
            cc1 = COL_WIN if a else TEXT_COL
            cc2 = COL_WIN if b else TEXT_COL

        table_data.append([label, c1, c2])
        cell_colors.append(["#1a2030", cc1, cc2])

    col_headers = ["Metric", algo1_name.upper(), algo2_name.upper()]
    tbl = ax_tbl.table(
        cellText=table_data,
        colLabels=col_headers,
        cellLoc="center",
        loc="center",
        bbox=[0.0, -0.15, 1.0, 1.15],
    )
    tbl.auto_set_font_size(False)
    tbl.set_fontsize(9)

    # Style header row
    for col_idx, header in enumerate(col_headers):
        cell = tbl[0, col_idx]
        cell.set_facecolor("#1a2a45")
        cell.set_text_props(color=TEXT_COL, fontweight="bold")
        cell.set_edgecolor("#2a3555")

    # Style data rows
    for row_idx, (row_data, row_cc) in enumerate(zip(table_data, cell_colors)):
        for col_idx in range(3):
            cell = tbl[row_idx + 1, col_idx]
            cell.set_facecolor(row_cc[col_idx] if col_idx == 0 else "#141820")
            cell.set_text_props(
                color=row_cc[col_idx] if col_idx > 0 else DIM_COL,
                fontweight="bold" if col_idx > 0 else "normal",
            )
            cell.set_edgecolor("#1e2435")

    # ── Save ─────────────────────────────────────────────────────────────────
    fig.savefig(out_path, format="jpeg", dpi=150,
                bbox_inches="tight", facecolor=BG)
    plt.close(fig)
