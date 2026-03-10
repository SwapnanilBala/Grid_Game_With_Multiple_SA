from __future__ import annotations

import math
import os
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Callable

import pygame

State = tuple[int, int]

# ─── Tile constants ───────────────────────────────────────────────────────────
WALL  = "O"
START = "S"
GOAL  = "G"
FREE  = "F"

# ─── Shared colour palette ────────────────────────────────────────────────────
BG_DARK     = (10,  12,  18)
BG_PANEL    = (16,  20,  30)
BG_CARD     = (22,  28,  42)
BORDER_DIM  = (45,  55,  75)
BORDER_LIT  = (70,  90, 130)

TEXT_BRIGHT = (240, 245, 255)
TEXT_MID    = (170, 185, 210)
TEXT_DIM    = (100, 115, 140)

ACCENT_CYAN  = (  0, 210, 230)
ACCENT_PINK  = (255,  80, 160)
ACCENT_LIME  = ( 80, 255, 140)
ACCENT_AMBER = (255, 190,  40)
ACCENT_TEAL  = (  0, 170, 150)

WALL_COL   = ( 28,  32,  45)
FLOOR_COL  = (210, 220, 235)
START_COL  = ( 50, 240, 130)
GOAL_COL   = (255,  70, 100)
TERRAIN_R  = (230, 220, 180)
TERRAIN_M  = (160, 110,  70)
TERRAIN_W  = ( 60, 130, 220)

# Per-algo overlay colours (RGBA)
EXP1_NORMAL  = (100, 130, 255,  90)
EXP1_RECENT  = (150, 180, 255, 200)
EXP1_CURRENT = (200, 220, 255)
EXP2_NORMAL  = (255, 160,  60,  90)
EXP2_RECENT  = (255, 200, 100, 200)
EXP2_CURRENT = (255, 240, 160)
PATH_OVERLAY = (255, 255, 255, 160)
PATH_HEAD    = (255, 230,   0)

TRAIL_LEN = 8


# ─── Helpers ──────────────────────────────────────────────────────────────────

def _lerp(a: tuple, b: tuple, t: float) -> tuple:
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(len(a)))


def _tile_base(ch: str) -> tuple:
    if ch == WALL:  return WALL_COL
    if ch == START: return START_COL
    if ch == GOAL:  return GOAL_COL
    return {
        "R": TERRAIN_R,
        "M": TERRAIN_M,
        "W": TERRAIN_W,
    }.get(ch, FLOOR_COL)


def _draw_grid(
    screen: pygame.Surface,
    grid: list[list[str]],
    origin_x: int,
    origin_y: int,
    cell: int,
    expanded: set,
    expanded_order: list,
    trace_i: int,
    trace: list,
    shown_path: set,
    front_head,
    back_head,
    exp_normal: tuple,
    exp_recent: tuple,
    exp_current: tuple,
    show_path: bool,
) -> None:
    rows = len(grid)
    cols = len(grid[0]) if rows else 0
    radius = 0 if cell < 18 else max(3, cell // 6)
    trail_start = max(0, len(expanded_order) - TRAIL_LEN)
    recent_set  = set(expanded_order[trail_start:])
    overlay = pygame.Surface((cell, cell), pygame.SRCALPHA)

    for r in range(rows):
        for c in range(cols):
            ch = grid[r][c]
            x  = origin_x + c * cell
            y  = origin_y + r * cell
            rect = pygame.Rect(x, y, cell, cell)

            # Base tile
            pygame.draw.rect(screen, _tile_base(ch), rect, border_radius=radius)
            pygame.draw.rect(screen, (0, 0, 0, 20), rect, 1, border_radius=radius)

            state = (r, c)

            # Expanded overlay
            if state in expanded and ch != WALL:
                overlay.fill(exp_recent if state in recent_set else exp_normal)
                screen.blit(overlay, (x, y))

            # Current-node pulse
            if not show_path and trace_i > 0 and state == trace[trace_i - 1] and ch != WALL:
                pulse = 0.6 + 0.4 * math.sin(time.time() * 10)
                sz = max(4, int(cell * 0.42 * pulse))
                pygame.draw.circle(screen, exp_current, rect.center, sz)

            # Path overlay (after trace completes)
            if show_path and state in shown_path and ch not in (START, GOAL, WALL):
                overlay.fill(PATH_OVERLAY)
                screen.blit(overlay, (x, y))

            # Path heads (golden tips)
            if show_path and (state == front_head or state == back_head) and ch != WALL:
                pygame.draw.circle(screen, PATH_HEAD, rect.center, max(4, cell // 3))

            # Start / goal
            if ch == START:
                pygame.draw.rect(screen, START_COL, rect, border_radius=radius)
            elif ch == GOAL:
                pygame.draw.rect(screen, GOAL_COL, rect, border_radius=radius)

            # Terrain labels
            if ch in ("M", "W", "R") and cell >= 18:
                fnt = pygame.font.SysFont(None, max(14, int(cell * 0.46)))
                lbl = fnt.render(ch, True, (20, 20, 20))
                screen.blit(lbl, (rect.right - lbl.get_width() - 4, rect.y + 3))

            # Grid line
            pygame.draw.rect(screen, (0, 0, 0, 25), rect, 1, border_radius=radius)


# ─── run_trace_viewer (single-mode, backward compat) ─────────────────────────

def run_trace_viewer(
    grid: list[list[str]],
    trace: list[State],
    path: list[State] | None,
    cell_size: int = 30,
    start_fps: int = 15,
    title_line1: str = "",
    title_line2: str = "",
) -> None:
    rows = len(grid)
    cols = len(grid[0]) if rows else 0
    if rows == 0 or cols == 0:
        raise ValueError("Grid is empty.")

    pygame.init()
    PAD   = max(8, cell_size // 5)
    HUD_H = max(82, cell_size + 52)
    screen_w = cols * cell_size + PAD * 2
    screen_h = rows * cell_size + PAD * 2 + HUD_H
    info = pygame.display.Info()
    os.environ["SDL_VIDEO_WINDOW_POS"] = (
        f"{(info.current_w - screen_w) // 2},{(info.current_h - screen_h) // 2}"
    )
    screen = pygame.display.set_mode((screen_w, screen_h))
    pygame.display.set_caption("GridWorld Search Visualization")
    clock  = pygame.font.SysFont(None, max(22, int(cell_size * 0.72)))
    clock_ = pygame.time.Clock()
    font   = pygame.font.SysFont(None, max(22, int(cell_size * 0.72)))
    font_s = pygame.font.SysFont(None, max(18, int(cell_size * 0.56)))

    i = 0
    paused = False
    fps = start_fps
    expanded: set[State] = set()
    expanded_order: list[State] = []
    path_set  = set(path) if path else set()
    path_list = list(path) if path else []
    path_front = path_back = 0

    running = True
    while running:
        clock_.tick(fps)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                elif event.key == pygame.K_SPACE:
                    paused = not paused
                elif event.key == pygame.K_UP:
                    fps = min(240, fps + 10)
                elif event.key == pygame.K_DOWN:
                    fps = max(5, fps - 10)
                elif event.key == pygame.K_r:
                    i = 0; expanded.clear(); expanded_order.clear()
                    path_front = path_back = 0; paused = False

        if not paused and i < len(trace):
            expanded.add(trace[i]); expanded_order.append(trace[i]); i += 1
        elif not paused and i >= len(trace) and path_list:
            if path_front + path_back < len(path_list):
                if path_front <= path_back: path_front += 1
                else: path_back += 1

        show_path = i >= len(trace)
        shown_path: set[State] = set()
        front_head = back_head = None
        if show_path and path_list:
            shown_path = set(path_list[:path_front]) | set(path_list[len(path_list) - path_back:])
            if path_front > 0: front_head = path_list[path_front - 1]
            if path_back  > 0: back_head  = path_list[len(path_list) - path_back]

        screen.fill(BG_DARK)
        # HUD bar
        pygame.draw.rect(screen, BG_PANEL, (0, 0, screen_w, HUD_H))
        pygame.draw.line(screen, BORDER_DIM, (0, HUD_H - 1), (screen_w, HUD_H - 1), 2)
        y_txt = 10
        if title_line1:
            s = font.render(title_line1, True, TEXT_BRIGHT)
            screen.blit(s, (12, y_txt)); y_txt += s.get_height() + 2
        if title_line2:
            s = font_s.render(title_line2, True, TEXT_MID)
            screen.blit(s, (12, y_txt)); y_txt += s.get_height() + 2
        hud = font_s.render(
            f"step {i}/{len(trace)}  fps {fps}  {'PAUSED' if paused else 'RUNNING'}",
            True, TEXT_DIM,
        )
        screen.blit(hud, (12, y_txt))

        _draw_grid(
            screen, grid, PAD, HUD_H + PAD, cell_size,
            expanded, expanded_order, i, trace,
            shown_path, front_head, back_head,
            EXP1_NORMAL, EXP1_RECENT, EXP1_CURRENT, show_path,
        )
        pygame.display.flip()

    pygame.quit()


# ─── run_dual_viewer ──────────────────────────────────────────────────────────

def run_dual_viewer(
    grid: list[list[str]],
    trace1: list[State],
    result1: Any,
    trace2: list[State],
    result2: Any,
    algo1_name: str,
    algo2_name: str,
    map_name: str,
    fps: int = 15,
    cell_size: int = 38,
    analysis_dir: Path | None = None,
) -> None:
    rows = len(grid)
    cols = len(grid[0]) if rows else 0
    if rows == 0 or cols == 0:
        raise ValueError("Grid is empty.")

    PAD      = 16
    DIVIDER  = 12
    HUD_H    = 130
    FOOTER_H = 52

    GRID_W  = cols * cell_size + PAD * 2
    GRID_H  = rows * cell_size + PAD * 2
    screen_w = GRID_W * 2 + DIVIDER
    screen_h = HUD_H + GRID_H + FOOTER_H

    screen = pygame.display.set_mode((screen_w, screen_h))
    pygame.display.set_caption("GridWorld — Dual Search Viewer")
    clock = pygame.time.Clock()

    font_lg = pygame.font.SysFont("consolas", max(26, cell_size // 2 + 6), bold=True)
    font_md = pygame.font.SysFont("consolas", max(22, cell_size // 2), bold=True)
    font_sm = pygame.font.SysFont("consolas", max(18, cell_size // 3))

    # ── Playback state ────────────────────────────────────────────────────────
    i1 = i2 = 0
    exp1: set[State] = set(); ord1: list[State] = []
    exp2: set[State] = set(); ord2: list[State] = []
    path1 = result1.path if result1.found else []
    path2 = result2.path if result2.found else []
    pf1 = pb1 = pf2 = pb2 = 0
    phase = "trace"    # "trace" | "path" | "done"
    popup_triggered = False
    paused = False

    ox_left  = 0
    ox_right = GRID_W + DIVIDER

    def _path_shown(path_list, front, back):
        if not path_list:
            return set(), None, None
        s = set(path_list[:front]) | set(path_list[max(0, len(path_list) - back):])
        fh = path_list[front - 1]  if front > 0 else None
        bh = path_list[len(path_list) - back] if back > 0 else None
        return s, fh, bh

    def _draw_hud():
        pygame.draw.rect(screen, BG_PANEL, (0, 0, screen_w, HUD_H))
        pygame.draw.line(screen, BORDER_DIM, (0, HUD_H - 1), (screen_w, HUD_H - 1), 2)

        # Row 1: map name
        title = font_lg.render(f"MAP:  {map_name}", True, ACCENT_CYAN)
        screen.blit(title, ((screen_w - title.get_width()) // 2, 10))

        # Row 2: algo names + steps
        a1_lbl = font_md.render(f"ALGO 1:  {algo1_name.upper()}", True, (150, 180, 255))
        a2_lbl = font_md.render(f"ALGO 2:  {algo2_name.upper()}", True, (255, 200, 100))
        screen.blit(a1_lbl, (16, 48))
        screen.blit(a2_lbl, (screen_w - a2_lbl.get_width() - 16, 48))
        step_txt = font_sm.render(
            f"L: {i1}/{len(trace1)}   R: {i2}/{len(trace2)}", True, TEXT_MID,
        )
        screen.blit(step_txt, ((screen_w - step_txt.get_width()) // 2, 52))

        # Row 3: expanded counts + fps + phase
        e1 = font_sm.render(f"expanded: {len(exp1)}", True, (150, 180, 255))
        e2 = font_sm.render(f"expanded: {len(exp2)}", True, (255, 200, 100))
        fps_lbl = font_sm.render(
            f"fps {fps}  {'PAUSED' if paused else phase.upper()}", True, TEXT_DIM,
        )
        screen.blit(e1, (16, 84))
        screen.blit(e2, (screen_w - e2.get_width() - 16, 84))
        screen.blit(fps_lbl, ((screen_w - fps_lbl.get_width()) // 2, 84))

        # Row 4: separator + hint
        pygame.draw.line(screen, BORDER_DIM, (0, 116), (screen_w, 116), 1)
        hint = font_sm.render("SPACE pause   R restart   ESC/Q back to launcher", True, TEXT_DIM)
        screen.blit(hint, ((screen_w - hint.get_width()) // 2, 122))

    def _draw_footer():
        fy = HUD_H + GRID_H
        pygame.draw.rect(screen, BG_PANEL, (0, fy, screen_w, FOOTER_H))
        pygame.draw.line(screen, BORDER_DIM, (0, fy), (screen_w, fy), 1)
        if result1.found:
            r1 = font_md.render(
                f"{algo1_name.upper()}  cost={result1.cost:.1f}  path={len(result1.path)}  exp={result1.expanded}",
                True, (150, 180, 255),
            )
            screen.blit(r1, (16, fy + 18))
        if result2.found:
            r2 = font_md.render(
                f"{algo2_name.upper()}  cost={result2.cost:.1f}  path={len(result2.path)}  exp={result2.expanded}",
                True, (255, 200, 100),
            )
            screen.blit(r2, (screen_w - r2.get_width() - 16, fy + 18))

    def _draw_divider():
        pygame.draw.rect(screen, ACCENT_TEAL, (GRID_W, HUD_H, DIVIDER, GRID_H))

    running = True
    while running:
        clock.tick(fps)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_ESCAPE, pygame.K_q):
                    running = False
                elif event.key == pygame.K_SPACE:
                    paused = not paused
                elif event.key == pygame.K_r:
                    i1 = i2 = 0
                    exp1.clear(); ord1.clear()
                    exp2.clear(); ord2.clear()
                    pf1 = pb1 = pf2 = pb2 = 0
                    phase = "trace"
                    popup_triggered = False
                    paused = False

        if not paused:
            if phase == "trace":
                if i1 < len(trace1):
                    exp1.add(trace1[i1]); ord1.append(trace1[i1]); i1 += 1
                if i2 < len(trace2):
                    exp2.add(trace2[i2]); ord2.append(trace2[i2]); i2 += 1
                if i1 >= len(trace1) and i2 >= len(trace2):
                    phase = "path"

            elif phase == "path":
                done1 = not path1 or (pf1 + pb1 >= len(path1))
                done2 = not path2 or (pf2 + pb2 >= len(path2))
                if not done1:
                    if pf1 <= pb1: pf1 += 1
                    else:          pb1 += 1
                if not done2:
                    if pf2 <= pb2: pf2 += 1
                    else:          pb2 += 1
                if done1 and done2:
                    phase = "done"

        # Trigger analysis popup once
        if phase == "done" and not popup_triggered:
            popup_triggered = True
            _trigger_analysis(
                algo1_name, result1, algo2_name, result2,
                map_name, analysis_dir,
            )

        # ── Draw ─────────────────────────────────────────────────────────────
        screen.fill(BG_DARK)
        _draw_hud()
        _draw_divider()

        sp1, fh1, bh1 = _path_shown(path1, pf1, pb1)
        sp2, fh2, bh2 = _path_shown(path2, pf2, pb2)
        show_path = phase in ("path", "done")

        _draw_grid(
            screen, grid, ox_left + PAD, HUD_H + PAD, cell_size,
            exp1, ord1, i1, trace1, sp1, fh1, bh1,
            EXP1_NORMAL, EXP1_RECENT, EXP1_CURRENT, show_path,
        )
        _draw_grid(
            screen, grid, ox_right + PAD, HUD_H + PAD, cell_size,
            exp2, ord2, i2, trace2, sp2, fh2, bh2,
            EXP2_NORMAL, EXP2_RECENT, EXP2_CURRENT, show_path,
        )
        _draw_footer()
        pygame.display.flip()


def _trigger_analysis(
    algo1_name: str, result1: Any,
    algo2_name: str, result2: Any,
    map_name: str,
    analysis_dir: Path | None,
) -> None:
    """Save JPG then open interactive matplotlib popup."""
    if analysis_dir is not None:
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        stem = map_name.replace(".txt", "")
        fname = f"{algo1_name}_vs_{algo2_name}__{stem}__{ts}.jpg"
        out_path = Path(analysis_dir) / fname
        try:
            from visualization.gridworld_viz import save_comparison_jpg
            save_comparison_jpg(
                algo1_name, result1,
                algo2_name, result2,
                map_name, out_path,
            )
            print(f"Analysis saved → {out_path}")
        except Exception as exc:
            print(f"[analysis] save failed: {exc}")

    # Interactive popup (blocks until closed; pygame window stays visible behind it)
    try:
        import matplotlib.pyplot as plt
        import matplotlib.gridspec as gridspec

        BG = "#0f1117"; TC = "#e8eaf0"; DC = "#8890a4"
        C1 = "#6482ff"; C2 = "#ffa03c"; CW = "#50ff8c"; CF = "#ff4060"

        def _v(res, attr):
            if not res.found and attr in ("cost", "path_len"):
                return None
            return len(res.path) if attr == "path_len" else getattr(res, attr)

        metrics = [
            ("Nodes\nExpanded",  "expanded"),
            ("Max\nFrontier",    "frontier_max"),
            ("Path\nCost",       "cost"),
            ("Path\nLength",     "path_len"),
        ]
        v1 = [_v(result1, m[1]) for m in metrics]
        v2 = [_v(result2, m[1]) for m in metrics]

        fig = plt.figure(figsize=(14, 8), facecolor=BG)
        gs  = gridspec.GridSpec(2, 4, figure=fig, hspace=0.55, wspace=0.45,
                                top=0.88, bottom=0.12, left=0.06, right=0.97)
        fig.suptitle(f"Algorithm Comparison  —  {map_name}",
                     color=TC, fontsize=14, fontweight="bold", y=0.97)

        for ci, (label, attr) in enumerate(metrics):
            ax = fig.add_subplot(gs[0, ci])
            ax.set_facecolor(BG)
            ax.spines[:].set_color("#2a3040")
            ax.tick_params(colors=DC, labelsize=8)
            a1, a2 = v1[ci], v2[ci]
            bars = ax.bar([0.35, 1.15],
                          [a1 if a1 is not None else 0,
                           a2 if a2 is not None else 0],
                          width=0.55, color=[C1, C2], edgecolor="none", zorder=3)
            ax.set_xticks([0.35, 1.15])
            ax.set_xticklabels([algo1_name.upper(), algo2_name.upper()],
                               fontsize=7, color=TC)
            ax.set_title(label, color=TC, fontsize=8.5, pad=4)
            ax.set_xlim(-0.1, 1.65)
            ax.grid(axis="y", color="#1e2435", linewidth=0.6, zorder=0)
            for bar, val in zip(bars, [a1, a2]):
                if val is None:
                    ax.text(bar.get_x() + bar.get_width() / 2, 0.5, "N/A",
                            ha="center", va="bottom", fontsize=7,
                            color=CF, fontweight="bold")
                else:
                    lbl_txt = f"{val:.1f}" if isinstance(val, float) and val != int(val) else str(int(val))
                    ax.text(bar.get_x() + bar.get_width() / 2,
                            bar.get_height() * 1.02, lbl_txt,
                            ha="center", va="bottom", fontsize=7.5,
                            color=TC, fontweight="bold")

        # Table
        ax_t = fig.add_subplot(gs[1, :])
        ax_t.set_facecolor(BG); ax_t.axis("off")

        def _wc(x, y):
            if x is None and y is None: return False, False
            if x is None: return False, True
            if y is None: return True, False
            return x < y, y < x

        num_m = ["cost", "path_len", "expanded", "frontier_max"]
        w1t = w2t = 0
        for a in num_m:
            a_, b_ = _wc(_v(result1, a), _v(result2, a))
            if a_: w1t += 1
            if b_: w2t += 1

        rows_data, row_cc = [], []
        specs = [
            ("Found",          "found"),
            ("Path Cost",      "cost"),
            ("Path Length",    "path_len"),
            ("Nodes Expanded", "expanded"),
            ("Max Frontier",   "frontier_max"),
            ("Winner (↓ better)", "__winner__"),
        ]
        for lbl, attr in specs:
            if attr == "found":
                c1t = "Yes" if result1.found else "No"
                c2t = "Yes" if result2.found else "No"
                cc1 = CW if result1.found else CF
                cc2 = CW if result2.found else CF
            elif attr == "__winner__":
                c1t = f"{w1t}/{len(num_m)}"; c2t = f"{w2t}/{len(num_m)}"
                cc1 = CW if w1t > w2t else (DC if w1t == w2t else CF)
                cc2 = CW if w2t > w1t else (DC if w1t == w2t else CF)
            else:
                raw1 = _v(result1, attr); raw2 = _v(result2, attr)
                c1t = "—" if raw1 is None else (f"{raw1:.2f}" if attr == "cost" else str(int(raw1)))
                c2t = "—" if raw2 is None else (f"{raw2:.2f}" if attr == "cost" else str(int(raw2)))
                a_, b_ = _wc(raw1, raw2)
                cc1 = CW if a_ else TC
                cc2 = CW if b_ else TC
            rows_data.append([lbl, c1t, c2t])
            row_cc.append(["#1a2030", cc1, cc2])

        tbl = ax_t.table(
            cellText=rows_data,
            colLabels=["Metric", algo1_name.upper(), algo2_name.upper()],
            cellLoc="center", loc="center",
            bbox=[0.0, -0.15, 1.0, 1.15],
        )
        tbl.auto_set_font_size(False); tbl.set_fontsize(9)
        for ci2 in range(3):
            cell = tbl[0, ci2]
            cell.set_facecolor("#1a2a45")
            cell.set_text_props(color=TC, fontweight="bold")
            cell.set_edgecolor("#2a3555")
        for ri, (_, rcc) in enumerate(zip(rows_data, row_cc)):
            for ci2 in range(3):
                cell = tbl[ri + 1, ci2]
                cell.set_facecolor(rcc[ci2] if ci2 == 0 else "#141820")
                cell.set_text_props(
                    color=rcc[ci2] if ci2 > 0 else DC,
                    fontweight="bold" if ci2 > 0 else "normal",
                )
                cell.set_edgecolor("#1e2435")

        plt.show()
        plt.close(fig)

    except Exception as exc:
        print(f"[analysis] popup failed: {exc}")


# ─── run_launcher ─────────────────────────────────────────────────────────────

def run_launcher(
    maps: list[Path],
    algos: list[str],
    run_once: Callable[[Path, str], tuple[Any, Any, list[State]]],
    cell_size: int = 38,
    start_fps: int = 15,
    analysis_dir: Path | None = None,
) -> None:
    """
    Revamped launcher: dual algo selection, FPS control, animated UI.

    Controls
    --------
    LEFT / RIGHT   cycle map
    A / D          cycle Algo 1  (left card)
    J / L          cycle Algo 2  (right card)
    UP / DOWN      FPS ± 5  (range 5–120)
    ENTER          run dual viewer
    ESC / Q        ignored  (close the window to exit)
    """
    if not maps:
        raise ValueError("No maps found.")
    if not algos:
        raise ValueError("No algorithms provided.")

    W, H = 1440, 760
    pygame.init()
    screen = pygame.display.set_mode((W, H))
    pygame.display.set_caption("GridWorld — Dual Search Launcher")
    clock = pygame.time.Clock()

    ft = pygame.font.SysFont("consolas", 48, bold=True)
    fm = pygame.font.SysFont("consolas", 32, bold=True)
    fn = pygame.font.SysFont("consolas", 28)
    fh = pygame.font.SysFont("consolas", 21)

    map_i   = 0
    algo1_i = 0
    algo2_i = min(1, len(algos) - 1)
    fps     = max(5, min(120, start_fps))
    t0      = time.time()

    def _draw_launcher():
        t = time.time() - t0

        # ── Gradient background ───────────────────────────────────────────────
        for y in range(H):
            col = _lerp((12, 14, 20), (22, 28, 44), y / H)
            pygame.draw.line(screen, col, (0, y), (W, y))

        # ── Top animated accent stripe ────────────────────────────────────────
        sw2 = 200
        sx = int((math.sin(t * 0.8) * 0.5 + 0.5) * (W - sw2))
        ss = pygame.Surface((sw2, 4), pygame.SRCALPHA)
        ss.fill((*ACCENT_CYAN, 110))
        screen.blit(ss, (sx, 0))

        # ── Title ─────────────────────────────────────────────────────────────
        glow = int(180 + 75 * math.sin(t * 2.2))
        title_col = (glow, glow, 255)
        title = ft.render("GRIDWORLD   DUAL   SEARCH", True, title_col)
        screen.blit(title, ((W - title.get_width()) // 2, 24))

        # Separator
        lny = 92
        pygame.draw.line(screen, ACCENT_CYAN, (60, lny), (W - 60, lny), 2)

        # ── Helper: draw card ─────────────────────────────────────────────────
        def card(x, y, w, h, label, label_col, value, idx, total, arrow_col):
            pygame.draw.rect(screen, BG_CARD, (x, y, w, h), border_radius=10)
            pygame.draw.rect(screen, BORDER_DIM, (x, y, w, h), 2, border_radius=10)
            lbl_surf = fm.render(label, True, label_col)
            screen.blit(lbl_surf, (x + 12, y + 8))
            font_center_render(fn, value, TEXT_BRIGHT, x, y, w, h, dx=0, dy=10)
            arr = fn.render("<", True, arrow_col)
            arr2 = fn.render(">", True, arrow_col)
            screen.blit(arr,  (x + 18, y + h // 2 + 4))
            screen.blit(arr2, (x + w - 18 - arr2.get_width(), y + h // 2 + 4))
            ctr_lbl = fh.render(f"{idx + 1} / {total}", True, TEXT_DIM)
            screen.blit(ctr_lbl, (x + w - ctr_lbl.get_width() - 12, y + 10))

        def font_center_render(font_obj, text, color, cx, cy, cw, ch, dx=0, dy=0):
            s = font_obj.render(text, True, color)
            bx = cx + (cw - s.get_width()) // 2 + dx
            by = cy + (ch - s.get_height()) // 2 + dy
            screen.blit(s, (bx, by))
            return s

        arr_col = _lerp(TEXT_DIM, TEXT_BRIGHT, 0.5 + 0.5 * math.sin(t * 3))

        # ── MAP CARD ──────────────────────────────────────────────────────────
        card(50, 108, W - 100, 104, "MAP", ACCENT_CYAN,
             maps[map_i].name, map_i, len(maps), arr_col)

        # ── DUAL ALGO ROW ─────────────────────────────────────────────────────
        half = (W - 100 - 24) // 2
        arr2_col = _lerp(TEXT_DIM, TEXT_BRIGHT, 0.5 + 0.5 * math.sin(t * 3 + 1))

        card(50, 236, half, 124, "ALGO 1  (A / D)",
             (150, 180, 255), algos[algo1_i].upper(), algo1_i, len(algos), arr2_col)

        card(50 + half + 24, 236, half, 124, "ALGO 2  (J / L)",
             ACCENT_PINK, algos[algo2_i].upper(), algo2_i, len(algos), arr2_col)

        # ── FPS CARD ──────────────────────────────────────────────────────────
        fx, fy, fw, fh_ = 50, 384, W - 100, 90
        pygame.draw.rect(screen, BG_CARD, (fx, fy, fw, fh_), border_radius=12)
        pygame.draw.rect(screen, BORDER_DIM, (fx, fy, fw, fh_), 2, border_radius=12)
        fps_lbl = fm.render("ANIMATION FPS  (UP / DOWN)", True, ACCENT_AMBER)
        screen.blit(fps_lbl, (fx + 16, fy + 10))
        fps_val = ft.render(str(fps), True, ACCENT_AMBER)
        screen.blit(fps_val, (fx + (fw - fps_val.get_width()) // 2, fy + 30))
        rng = fh.render("5 — 120", True, TEXT_DIM)
        screen.blit(rng, (fx + fw - rng.get_width() - 16, fy + 12))

        # ── RUN BUTTON ────────────────────────────────────────────────────────
        pulse = 0.5 + 0.5 * math.sin(t * 4)
        btn_col = _lerp((30, 120, 70), (70, 240, 130), pulse)
        bx = (W - 440) // 2; by = 498
        pygame.draw.rect(screen, btn_col, (bx, by, 440, 66), border_radius=18)
        btn_txt = fm.render("PRESS  ENTER  TO  RUN", True, (8, 8, 8))
        screen.blit(btn_txt, (bx + (440 - btn_txt.get_width()) // 2, by + 16))

        # ── HINT BAR ─────────────────────────────────────────────────────────
        hints = [
            ("LEFT/RIGHT", "map", ACCENT_CYAN),
            ("A/D", "algo 1", (150, 180, 255)),
            ("J/L", "algo 2", ACCENT_PINK),
            ("UP/DOWN", "fps", ACCENT_AMBER),
            ("ENTER", "run", ACCENT_LIME),
        ]
        hx = 50
        for key, desc, col in hints:
            k = fh.render(key, True, col)
            d = fh.render(f" {desc}  ", True, TEXT_DIM)
            screen.blit(k, (hx, H - 64))
            screen.blit(d, (hx + k.get_width(), H - 64))
            hx += k.get_width() + d.get_width()

        close_hint = fh.render("close window to exit", True, TEXT_DIM)
        screen.blit(close_hint, (W - close_hint.get_width() - 50, H - 64))

        # ── Bottom accent stripe ──────────────────────────────────────────────
        sx2 = int((math.cos(t * 0.6) * 0.5 + 0.5) * (W - sw2))
        ss2 = pygame.Surface((sw2, 4), pygame.SRCALPHA)
        ss2.fill((*ACCENT_PINK, 90))
        screen.blit(ss2, (sx2, H - 4))

        pygame.display.flip()

    running = True
    while running:
        clock.tick(60)
        _draw_launcher()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                running = False
                return

            elif event.type == pygame.KEYDOWN:
                key = event.key

                if key in (pygame.K_ESCAPE, pygame.K_q):
                    pass  # intentionally ignored

                elif key == pygame.K_LEFT:
                    map_i = (map_i - 1) % len(maps)
                elif key == pygame.K_RIGHT:
                    map_i = (map_i + 1) % len(maps)

                elif key == pygame.K_a:
                    algo1_i = (algo1_i - 1) % len(algos)
                elif key == pygame.K_d:
                    algo1_i = (algo1_i + 1) % len(algos)

                elif key == pygame.K_j:
                    algo2_i = (algo2_i - 1) % len(algos)
                elif key == pygame.K_l:
                    algo2_i = (algo2_i + 1) % len(algos)

                elif key == pygame.K_UP:
                    fps = min(120, fps + 5)
                elif key == pygame.K_DOWN:
                    fps = max(5, fps - 5)

                elif key == pygame.K_RETURN:
                    env1, result1, trace1 = run_once(maps[map_i], algos[algo1_i])
                    env2, result2, trace2 = run_once(maps[map_i], algos[algo2_i])
                    run_dual_viewer(
                        grid=env1.grid,
                        trace1=trace1, result1=result1,
                        trace2=trace2, result2=result2,
                        algo1_name=algos[algo1_i],
                        algo2_name=algos[algo2_i],
                        map_name=maps[map_i].name,
                        fps=fps,
                        cell_size=cell_size,
                        analysis_dir=analysis_dir,
                    )
                    # Restore launcher window
                    screen = pygame.display.set_mode((1440, 760))
                    pygame.display.set_caption("GridWorld — Dual Search Launcher")
