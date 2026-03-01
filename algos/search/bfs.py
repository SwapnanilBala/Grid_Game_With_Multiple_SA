from __future__ import annotations

from collections import deque
from typing import TypeVar, Optional

from .base import NeighborsFn, GoalTestFn, SearchResult, reconstruct_path

State = TypeVar("State")


def bfs(
    start: State,
    is_goal: GoalTestFn[State],
    neighbors: NeighborsFn[State],
    h=None,  # Not used here; kept so the caller can pass the same params to every algorithm
    trace: list[State] | None = None,
) -> SearchResult[State]:
    """
    Breadth-First Search: optimal in number of steps when all step costs are equal.
    Ignores weights (uses neighbors but discards step_cost).
    """
    # BFS uses a queue (FIFO): we explore in "layers" outward from the start.
    q = deque([start])

    # Parent pointers let us rebuild the path once we find the goal.
    parent: dict[State, Optional[State]] = {start: None}

    # Some stats we return (handy for debugging / comparing algorithms).
    expanded = 0
    frontier_max = 1

    while q:
        # Track the biggest the queue ever gets.
        frontier_max = max(frontier_max, len(q))
        # Pop from the left to keep FIFO behavior.
        cur = q.popleft()

        expanded += 1
        if trace is not None:
            # Record expansion order if requested.
            trace.append(cur)

        # Goal check: if this is the target, rebuild and return the path.
        if is_goal(cur):
            path = reconstruct_path(parent, cur)
            return SearchResult(True, path, float(len(path) - 1), expanded, frontier_max)

        # Visit neighbors. For BFS, the first time we discover a node is the shortest (fewest-steps) way to it.
        for nxt, _ in neighbors(cur):
            if nxt not in parent:
                # Using `parent` as our "discovered" set: if it's not in here, it's new.
                parent[nxt] = cur
                q.append(nxt)

    # Queue ran dry => no path to a goal.
    return SearchResult(False, [], float("inf"), expanded, frontier_max)