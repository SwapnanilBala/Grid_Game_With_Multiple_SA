from __future__ import annotations

import pygame

State = tuple[int, int]


def run_trace_viewer(
        grid: list[list[str]],
        trace: list[State],
        path: list[State] | None,
        cell_size: int = 30,
        start_fps: int = 20,
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

    pygame.init()
    screen = pygame.display.set_mode((cols * cell_size, rows * cell_size))
    pygame.display.set_caption("GridWorld Search Visualization (Pygame)")
    clock = pygame.time.Clock()
    font = pygame.font.SysFont(None, 18)

    # playback state
    i = 0
    paused = False
    fps = start_fps

    expanded: set[State] = set()
    path_set = set(path) if path else set()

    def draw() -> None:
        screen.fill((0, 0, 0))
        show_path = (i >= len(trace))


        for r in range(rows):
            for c in range(cols):
                ch = grid[r][c]
                rect = pygame.Rect(c * cell_size, r * cell_size, cell_size, cell_size)

                # base tile
                if ch == "#":
                    base = (35, 35, 35)  # wall
                else:
                    base = (230, 230, 230)  # free
                pygame.draw.rect(screen, base, rect)

                # expanded overlay (blue)
                if (r, c) in expanded and ch != "#":
                    pygame.draw.rect(screen, (120, 170, 255), rect)

                # final path overlay (RED now)
                if show_path and (r, c) in path_set and ch not in ("S", "G", "#"):
                    pygame.draw.rect(screen, (255, 60, 60), rect)

                # start/goal markers
                if ch == "S":
                    pygame.draw.rect(screen, (120, 255, 120), rect)
                elif ch == "G":
                    pygame.draw.rect(screen, (255, 120, 120), rect)

                # optional: show weights
                if ch.isdigit():
                    txt = font.render(ch, True, (0, 0, 0))
                    screen.blit(txt, (rect.x + 4, rect.y + 2))

                # grid lines
                pygame.draw.rect(screen, (0, 0, 0), rect, 1)

        # HUD
        # HUD
        y = 6
        if title_line1:
            hud0 = font.render(title_line1, True, (255, 255, 255))
            screen.blit(hud0, (8, y))
            y += 18
        if title_line2:
            hud00 = font.render(title_line2, True, (255, 255, 255))
            screen.blit(hud00, (8, y))
            y += 18

        hud = font.render(
            f"step {i}/{len(trace)} | fps {fps} | {'PAUSED' if paused else 'RUNNING'}",
            True,
            (255, 255, 255),
        )
        screen.blit(hud, (8, y))

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
                    i = 0
                    expanded.clear()
                    paused = False

        if not paused and i < len(trace):
            expanded.add(trace[i])
            i += 1

        draw()

from pathlib import Path
from typing import Callable, Any

def run_launcher(
    maps: list[Path],
    algos: list[str],
    run_once: Callable[[Path, str], tuple[Any, Any, list[State]]],
    cell_size: int = 30,
    start_fps: int = 20,
) -> None:
    """
    Simple launcher that lets you cycle maps/algorithms and run the viewer.

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

    pygame.init()
    screen = pygame.display.set_mode((900, 260))
    pygame.display.set_caption("GridWorld Launcher")
    clock = pygame.time.Clock()
    font = pygame.font.SysFont(None, 28)
    small = pygame.font.SysFont(None, 22)

    def draw_launcher() -> None:
        screen.fill((20, 20, 20))

        title = font.render("GridWorld Search Launcher", True, (255, 255, 255))
        screen.blit(title, (20, 20))

        map_name = maps[map_i].name
        algo_name = algos[algo_i]

        line1 = font.render(f"Map:  {map_name}   ({map_i+1}/{len(maps)})", True, (220, 220, 220))
        line2 = font.render(f"Algo: {algo_name}   ({algo_i+1}/{len(algos)})", True, (220, 220, 220))
        screen.blit(line1, (20, 80))
        screen.blit(line2, (20, 120))

        help1 = small.render("LEFT/RIGHT: change map   UP/DOWN: change algo", True, (180, 180, 180))
        help2 = small.render("ENTER: run   ESC/Q: quit", True, (180, 180, 180))
        screen.blit(help1, (20, 180))
        screen.blit(help2, (20, 205))

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
                    # Compute + run viewer
                    env, result, trace = run_once(maps[map_i], algos[algo_i])
                    title1 = f"Map: {maps[map_i].name} | Algo: {algos[algo_i]}"
                    title2 = f"found={result.found} cost={result.cost} expanded={result.expanded} frontier_max={result.frontier_max}"

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


