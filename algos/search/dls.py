from __future__ import annotations

from typing import TypeVar, Optional

from .base import NeighborsFn, GoalTestFn, SearchResult, reconstruct_path

State = TypeVar("State")


def dls(
    start: State,
    is_goal: GoalTestFn[State],
    neighbors: NeighborsFn[State],
    depth_limit: int = 50,          # ✅ default so launcher/CLI can run it
    h=None,                         # ✅ ignored; keeps run_once simple
    trace: list[State] | None = None,  # ✅ for pygame replay
) -> SearchResult[State]:
    """
    Depth-Limited Search: DFS with a maximum depth.
    Returns failure if not found within limit.
    """
    stack: list[tuple[State, int]] = [(start, 0)]
    parent: dict[State, Optional[State]] = {start: None}
    best_depth_seen: dict[State, int] = {start: 0}

    expanded = 0
    frontier_max = 1

    while stack:
        frontier_max = max(frontier_max, len(stack))
        cur, depth = stack.pop()

        expanded += 1
        if trace is not None:
            trace.append(cur)       # ✅ add

        if is_goal(cur):
            path = reconstruct_path(parent, cur)
            return SearchResult(True, path, float(len(path) - 1), expanded, frontier_max)

        if depth >= depth_limit:
            continue

        for nxt, _ in neighbors(cur):
            nd = depth + 1
            prev = best_depth_seen.get(nxt)
            if prev is None or nd < prev:
                best_depth_seen[nxt] = nd
                parent[nxt] = cur
                stack.append((nxt, nd))

    return SearchResult(False, [], float("inf"), expanded, frontier_max)