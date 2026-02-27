from __future__ import annotations

from typing import Optional, TypeVar

from .base import GoalTestFn, NeighborsFn, SearchResult, reconstruct_path

State = TypeVar("State")


def dfs(
    start: State,
    is_goal: GoalTestFn[State],
    neighbors: NeighborsFn[State],
    h=None,  # ✅ added: ignored (lets main.py always pass h)
    trace: list[State] | None = None,
) -> SearchResult[State]:
    stack: list[State] = [start]
    parent: dict[State, Optional[State]] = {start: None}
    visited: set[State] = {start}

    expanded = 0
    frontier_max = 1

    while stack:
        frontier_max = max(frontier_max, len(stack))
        cur = stack.pop()

        expanded += 1
        if trace is not None:
            trace.append(cur)

        if is_goal(cur):
            path = reconstruct_path(parent, cur)
            # DFS doesn't use step costs; report path length - 1 as cost (edges)
            return SearchResult(True, path, float(len(path) - 1), expanded, frontier_max)

        for nxt, _ in neighbors(cur):
            if nxt not in visited:
                visited.add(nxt)
                parent[nxt] = cur
                stack.append(nxt)

    return SearchResult(False, [], float("inf"), expanded, frontier_max)