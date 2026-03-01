from __future__ import annotations

import math
import os
import time
from pathlib import Path
from typing import Any, Callable

import pygame

State = tuple[int, int]

# These are the tile characters used by the text maps.
# (The viewer mostly only cares about walls vs non-walls, plus start/goal colors.)
WALL = "O"
START = "S"
GOAL = "G"
FREE = "F"


def run_trace_viewer(
    grid: list[list[str]],
    trace: list[State],
    path: list[State] | None,
    cell_size: int = 30,
    start_fps: int = 15,
    title_line1: str = "",
    title_line2: str = "",
) -> None:
    """
    Replays the expansion trace in a Pygame window.

    Controls:
    - SPACE: pause/resume
    - UP/DOWN: speed up/down
    - R: restart replay
    - ESC / Close: quit
    """
    rows = len(grid)
    cols = len(grid[0]) if rows else 0
    if rows == 0 or cols == 0:
        raise ValueError("Grid is empty.")

    # Basic Pygame setup.
    # We add a little padding + a HUD bar so the viewer feels less "barebones".
    pygame.init()

    PAD = max(8, cell_size // 5)
    # Give the HUD plenty of breathing room so info is easy to read.
    HUD_H = max(82, cell_size + 52)
    screen_w = cols * cell_size + PAD * 2
    screen_h = rows * cell_size + PAD * 2 + HUD_H

    # Center the window on the screen.
    info = pygame.display.Info()
    os.environ["SDL_VIDEO_WINDOW_POS"] = f"{(info.current_w - screen_w) // 2},{(info.current_h - screen_h) // 2}"

    screen = pygame.display.set_mode((screen_w, screen_h))
    pygame.display.set_caption("GridWorld Search Visualization (Pygame)")
    clock = pygame.time.Clock()
    font = pygame.font.SysFont(None, max(22, int(cell_size * 0.72)))
    font_small = pygame.font.SysFont(None, max(20, int(cell_size * 0.58)))

    # A simple "premium" palette.
    BG = (16, 18, 22)
    WALL_COL = (34, 38, 46)
    FLOOR_COL = (238, 241, 246)
    GRIDLINE_COL = (0, 0, 0, 30)
    START_COL = (80, 220, 140)
    GOAL_COL = (255, 120, 120)
    HUD_BG = (22, 26, 33)
    HUD_BORDER = (60, 70, 85)

    # Terrain colors (only apply if those tiles exist in the map).
    TERRAIN = {
        "R": (245, 244, 236),  # road
        "M": (190, 160, 120),  # mud
        "W": (120, 170, 255),  # water
    }

    # Overlays (we'll alpha-blend these on top of tiles).
    EXPANDED_OVERLAY = (80, 150, 255, 100)
    EXPANDED_RECENT = (120, 200, 255, 180)   # brighter blue for recently expanded
    CURRENT_NODE_COL = (255, 255, 100)       # bright yellow for the current node
    PATH_OVERLAY = (255, 70, 70, 160)
    PATH_HEAD_COL = (255, 220, 60)           # golden head when path is being drawn

    # How many recent steps get the "bright" overlay so we can see the search frontier.
    TRAIL_LEN = 12

    # Playback state:
    # - i points at which step of the trace we're on
    # - expanded stores all states we've already "played" so far
    i = 0
    paused = False
    fps = start_fps

    expanded: set[State] = set()
    # We also keep an ordered list so we know which nodes are "recent".
    expanded_order: list[State] = []
    path_set = set(path) if path else set()
    path_list = list(path) if path else []
    # For the path-drawing animation: we grow from both ends toward the middle.
    path_front = 0   # how many cells revealed from the start side
    path_back = 0    # how many cells revealed from the goal side


    def draw() -> None:
        # Draw the entire grid every frame.
        # This is simple (and plenty fast for small grids) and keeps the code easy to follow.
        screen.fill(BG)
        show_path = i >= len(trace)

        # Figure out which nodes are "recent" for the brighter trail effect.
        trail_start = max(0, len(expanded_order) - TRAIL_LEN)
        recent_set = set(expanded_order[trail_start:])

        # Which path cells to show so far (animated reveal from both ends).
        shown_path_set: set[State] = set()
        front_head: State | None = None
        back_head: State | None = None
        if show_path and path_list:
            shown_path_set = set(path_list[:path_front]) | set(path_list[len(path_list) - path_back:])
            if path_front > 0 and path_front <= len(path_list):
                front_head = path_list[path_front - 1]
            if path_back > 0 and path_back <= len(path_list):
                back_head = path_list[len(path_list) - path_back]

        # Pre-make a tiny alpha surface for overlays (expanded/path).
        overlay = pygame.Surface((cell_size, cell_size), pygame.SRCALPHA)

        # HUD bar
        hud_rect = pygame.Rect(0, 0, screen_w, HUD_H)
        pygame.draw.rect(screen, HUD_BG, hud_rect)
        pygame.draw.line(screen, HUD_BORDER, (0, HUD_H - 1), (screen_w, HUD_H - 1), 2)

        for r in range(rows):
            for c in range(cols):
                ch = grid[r][c]
                x = PAD + c * cell_size
                y = HUD_H + PAD + r * cell_size
                rect = pygame.Rect(x, y, cell_size, cell_size)

                # Make corners a bit round on bigger cell sizes.
                radius = 0 if cell_size < 18 else max(3, cell_size // 6)

                # base tile
                if ch == WALL:
                    base = WALL_COL
                else:
                    base = TERRAIN.get(ch, FLOOR_COL)
                pygame.draw.rect(screen, base, rect, border_radius=radius)

                # subtle inner border so cells feel separated even without harsh lines
                pygame.draw.rect(screen, (0, 0, 0, 18), rect, 1, border_radius=radius)

                # expanded overlay (blue) with brighter trail for recent nodes
                if (r, c) in expanded and ch != WALL:
                    if (r, c) in recent_set:
                        overlay.fill(EXPANDED_RECENT)
                    else:
                        overlay.fill(EXPANDED_OVERLAY)
                    screen.blit(overlay, (rect.x, rect.y))

                # Current node marker (bright yellow pulsing dot)
                if not show_path and i > 0 and (r, c) == trace[i - 1] and ch != WALL:
                    pulse = 0.6 + 0.4 * math.sin(time.time() * 10)
                    sz = max(4, int(cell_size * 0.45 * pulse))
                    cx, cy = rect.centerx, rect.centery
                    pygame.draw.circle(screen, CURRENT_NODE_COL, (cx, cy), sz)

                # final path overlay (red) — drawn incrementally for animation
                if show_path and (r, c) in shown_path_set and ch not in (START, GOAL, WALL):
                    overlay.fill(PATH_OVERLAY)
                    screen.blit(overlay, (rect.x, rect.y))

                # path head markers (golden circles at the tips of both growing sides)
                if show_path and ((r, c) == front_head or (r, c) == back_head) and ch not in (WALL,):
                    pygame.draw.circle(screen, PATH_HEAD_COL, rect.center, max(4, cell_size // 3))

                # start/goal markers
                if ch == START:
                    pygame.draw.rect(screen, START_COL, rect, border_radius=radius)
                elif ch == GOAL:
                    pygame.draw.rect(screen, GOAL_COL, rect, border_radius=radius)

                # Optional: show weights (only if we still use digits)
                if ch.isdigit():
                    txt = font.render(ch, True, (10, 10, 10))
                    screen.blit(txt, (rect.x + 6, rect.y + 4))

                # Optional: label weighted terrain letters (small and subtle)
                if ch in ("M", "W", "R"):
                    txt = font_small.render(ch, True, (20, 20, 20))
                    screen.blit(txt, (rect.right - txt.get_width() - 6, rect.y + 4))

                # grid lines (very light)
                pygame.draw.rect(screen, GRIDLINE_COL, rect, 1, border_radius=radius)

        # HUD
        y = 10
        if title_line1:
            hud1 = font.render(title_line1, True, (235, 240, 247))
            screen.blit(hud1, (12, y))
            y += hud1.get_height() + 2
        if title_line2:
            hud2 = font_small.render(title_line2, True, (200, 210, 225))
            screen.blit(hud2, (12, y))
            y += hud2.get_height() + 2

        hud = font_small.render(
            f"step {i}/{len(trace)} | fps {fps} | {'PAUSED' if paused else 'RUNNING'}",
            True,
            (200, 210, 225),
        )
        screen.blit(hud, (12, y))

        pygame.display.flip()


    running = True
    while running:
        clock.tick(fps)

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
                    fps = max(10, fps - 10)
                elif event.key == pygame.K_r:
                    # Restart the replay.
                    i = 0
                    expanded.clear()
                    expanded_order.clear()
                    path_front = 0
                    path_back = 0
                    paused = False

        if not paused and i < len(trace):
            # "Play" one more expansion from the trace.
            expanded.add(trace[i])
            expanded_order.append(trace[i])
            i += 1
        elif not paused and i >= len(trace) and path_list and (path_front + path_back) < len(path_list):
            # After the trace is done, animate the path growing from both ends.
            if path_front <= path_back:
                path_front += 1
            else:
                path_back += 1

        draw()


def run_launcher(
    maps: list[Path],
    algos: list[str],
    run_once: Callable[[Path, str], tuple[Any, Any, list[State]]],
    cell_size: int = 30,
    start_fps: int = 15,
) -> None:
    """
    Flashy launcher that lets us cycle maps/algorithms and run the viewer.

    Controls (launcher screen):
      LEFT/RIGHT  -> change map
      UP/DOWN     -> change algorithm
      ENTER       -> run visualization
      ESC / Q     -> quit launcher
    """
    if not maps:
        raise ValueError("No maps found.")
    if not algos:
        raise ValueError("No algorithms provided.")

    map_i = 0
    algo_i = 0

    W, H = 960, 420
    pygame.init()
    screen = pygame.display.set_mode((W, H))
    pygame.display.set_caption("GridWorld Launcher")
    clock = pygame.time.Clock()

    # Fonts
    font_title = pygame.font.SysFont("consolas", 38, bold=True)
    font_sub = pygame.font.SysFont("consolas", 26)
    font_item = pygame.font.SysFont("consolas", 24)
    font_hint = pygame.font.SysFont("consolas", 18)

    # Palette
    BG_TOP = (12, 14, 18)
    BG_BOT = (26, 30, 42)
    ACCENT = (80, 180, 255)
    ACCENT2 = (255, 100, 130)
    ACCENT3 = (80, 220, 140)
    TEXT = (230, 235, 245)
    DIM = (140, 150, 170)
    CARD_BG = (30, 34, 46)
    CARD_BORDER = (55, 65, 85)

    t0 = time.time()

    def lerp_color(a, b, t):
        return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))

    def draw_launcher() -> None:
        t = time.time() - t0

        # Gradient background
        for y in range(H):
            frac = y / H
            col = lerp_color(BG_TOP, BG_BOT, frac)
            pygame.draw.line(screen, col, (0, y), (W, y))

        # Subtle animated accent stripe at top
        stripe_w = 220
        stripe_x = int((math.sin(t * 0.8) * 0.5 + 0.5) * (W - stripe_w))
        stripe_surf = pygame.Surface((stripe_w, 4), pygame.SRCALPHA)
        stripe_surf.fill((*ACCENT, 120))
        screen.blit(stripe_surf, (stripe_x, 0))

        # Title with glow-pulse
        glow = int(200 + 55 * math.sin(t * 2.5))
        title_col = (glow, glow, 255)
        title = font_title.render("GRIDWORLD  SEARCH  LAUNCHER", True, title_col)
        tx = (W - title.get_width()) // 2
        screen.blit(title, (tx, 28))

        # Decorative line under title
        line_y = 75
        pygame.draw.line(screen, ACCENT, (60, line_y), (W - 60, line_y), 2)

        # Map card
        card_y = 100
        card_h = 70
        card_rect = pygame.Rect(40, card_y, W - 80, card_h)
        pygame.draw.rect(screen, CARD_BG, card_rect, border_radius=10)
        pygame.draw.rect(screen, CARD_BORDER, card_rect, 2, border_radius=10)

        map_name = maps[map_i].name
        lbl = font_sub.render("MAP", True, ACCENT)
        screen.blit(lbl, (60, card_y + 8))
        arr_col = lerp_color(DIM, TEXT, 0.5 + 0.5 * math.sin(t * 3))
        arrows = font_item.render("<  ", True, arr_col)
        name_surf = font_item.render(f"{map_name}", True, TEXT)
        arrows2 = font_item.render("  >", True, arr_col)
        nx = (W - arrows.get_width() - name_surf.get_width() - arrows2.get_width()) // 2
        ny = card_y + 38
        screen.blit(arrows, (nx, ny))
        screen.blit(name_surf, (nx + arrows.get_width(), ny))
        screen.blit(arrows2, (nx + arrows.get_width() + name_surf.get_width(), ny))
        counter = font_hint.render(f"{map_i + 1} / {len(maps)}", True, DIM)
        screen.blit(counter, (W - 80 - counter.get_width(), card_y + 12))

        # Algo card
        card_y2 = 185
        card_rect2 = pygame.Rect(40, card_y2, W - 80, card_h)
        pygame.draw.rect(screen, CARD_BG, card_rect2, border_radius=10)
        pygame.draw.rect(screen, CARD_BORDER, card_rect2, 2, border_radius=10)

        algo_name = algos[algo_i].upper()
        lbl2 = font_sub.render("ALGO", True, ACCENT2)
        screen.blit(lbl2, (60, card_y2 + 8))
        arr2_col = lerp_color(DIM, TEXT, 0.5 + 0.5 * math.sin(t * 3 + 1))
        a1 = font_item.render("<  ", True, arr2_col)
        a_name = font_item.render(f"{algo_name}", True, TEXT)
        a2 = font_item.render("  >", True, arr2_col)
        ax = (W - a1.get_width() - a_name.get_width() - a2.get_width()) // 2
        ay = card_y2 + 38
        screen.blit(a1, (ax, ay))
        screen.blit(a_name, (ax + a1.get_width(), ay))
        screen.blit(a2, (ax + a1.get_width() + a_name.get_width(), ay))
        counter2 = font_hint.render(f"{algo_i + 1} / {len(algos)}", True, DIM)
        screen.blit(counter2, (W - 80 - counter2.get_width(), card_y2 + 12))

        # Pulsing "ENTER to run" button
        btn_y = 290
        pulse = 0.5 + 0.5 * math.sin(t * 4)
        btn_col = lerp_color((40, 160, 100), (80, 255, 160), pulse)
        btn_rect = pygame.Rect((W - 320) // 2, btn_y, 320, 50)
        pygame.draw.rect(screen, btn_col, btn_rect, border_radius=12)
        btn_txt = font_sub.render("ENTER  TO  RUN", True, (10, 10, 10))
        screen.blit(btn_txt, (btn_rect.x + (320 - btn_txt.get_width()) // 2, btn_y + 12))

        # Controls hint at bottom
        hints = [
            ("LEFT / RIGHT", "change map"),
            ("UP / DOWN", "change algo"),
            ("ESC / Q", "quit"),
        ]
        hx = 60
        for key, desc in hints:
            k = font_hint.render(key, True, ACCENT)
            d = font_hint.render(f"  {desc}", True, DIM)
            screen.blit(k, (hx, H - 50))
            screen.blit(d, (hx + k.get_width(), H - 50))
            hx += k.get_width() + d.get_width() + 30

        # Animated bottom accent stripe
        stripe_x2 = int((math.cos(t * 0.6) * 0.5 + 0.5) * (W - stripe_w))
        stripe_surf2 = pygame.Surface((stripe_w, 3), pygame.SRCALPHA)
        stripe_surf2.fill((*ACCENT2, 100))
        screen.blit(stripe_surf2, (stripe_x2, H - 3))

        pygame.display.flip()

    running = True
    while running:
        clock.tick(60)
        draw_launcher()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            elif event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_ESCAPE, pygame.K_q):
                    running = False
                elif event.key == pygame.K_LEFT:
                    map_i = (map_i - 1) % len(maps)
                elif event.key == pygame.K_RIGHT:
                    map_i = (map_i + 1) % len(maps)
                elif event.key == pygame.K_UP:
                    algo_i = (algo_i - 1) % len(algos)
                elif event.key == pygame.K_DOWN:
                    algo_i = (algo_i + 1) % len(algos)
                elif event.key == pygame.K_RETURN:
                    env, result, trace = run_once(maps[map_i], algos[algo_i])
                    title1 = f"Map: {maps[map_i].name} | Algo: {algos[algo_i]}"
                    title2 = (
                        f"found={result.found} cost={result.cost} "
                        f"expanded={result.expanded} frontier_max={result.frontier_max}"
                    )

                    run_trace_viewer(
                        grid=env.grid,
                        trace=trace,
                        path=result.path if result.found else None,
                        cell_size=cell_size,
                        start_fps=start_fps,
                        title_line1=title1,
                        title_line2=title2,
                    )

    pygame.quit()