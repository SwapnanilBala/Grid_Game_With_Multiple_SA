from __future__ import annotations

from collections import deque
from typing import TypeVar, Optional

from .base import NeighborsFn, GoalTestFn, SearchResult, reconstruct_path

State = TypeVar("State")


def bfs(start: State, is_goal: GoalTestFn[State], neighbors: NeighborsFn[State],trace: list[State] | None = None,) -> SearchResult[State]:
    """
    Breadth-First Search: optimal in number of steps when all step costs are equal.
    Ignores weights (uses neighbors but discards step_cost).
    """
    q = deque([start])
    parent: dict[State, Optional[State]] = {start: None}
    expanded = 0
    frontier_max = 1

    while q:
        frontier_max = max(frontier_max, len(q))
        cur = q.popleft()
        expanded += 1
        if trace is not None:
            trace.append(cur)

        if is_goal(cur):
            path = reconstruct_path(parent, cur)
            return SearchResult(True, path, float(len(path) - 1), expanded, frontier_max)

        for nxt, _ in neighbors(cur):
            if nxt not in parent:
                parent[nxt] = cur
                q.append(nxt)

    return SearchResult(False, [], float("inf"), expanded, frontier_max)
