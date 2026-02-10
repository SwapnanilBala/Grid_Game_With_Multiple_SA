from __future__ import annotations

import pygame

State = tuple[int, int]


def run_trace_viewer(
    grid: list[list[str]],
    trace: list[State],
    path: list[State] | None,
    cell_size: int = 30,
    start_fps: int = 20,
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
        hud = font.render(
            f"step {i}/{len(trace)} | fps {fps} | {'PAUSED' if paused else 'RUNNING'}",
            True,
            (255, 255, 255),
        )
        screen.blit(hud, (8, 6))

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

    pygame.quit()
