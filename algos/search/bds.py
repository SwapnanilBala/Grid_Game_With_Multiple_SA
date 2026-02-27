from __future__ import annotations

from collections import deque
from typing import Optional, TypeVar

from .base import NeighborsFn, GoalTestFn, SearchResult, reconstruct_path

State = TypeVar("State")


def bds(
    start: State,
    is_goal: GoalTestFn[State],          # ✅ accept (not used directly)
    neighbors: NeighborsFn[State],
    goal: State | None = None,           # ✅ we need explicit goal
    h=None,                              # ✅ ignored
    trace: list[State] | None = None,
) -> SearchResult[State]:
    """
    Bidirectional BFS (unweighted). Requires goal state.

    NOTE: cost returned = steps (len(path)-1), not weighted cost.
    """
    if goal is None:
        raise ValueError("bds requires goal=... (explicit goal state).")

    if start == goal:
        return SearchResult(True, [start], 0.0, expanded=1, frontier_max=1)

    q_f = deque([start])
    q_b = deque([goal])

    parent_f: dict[State, Optional[State]] = {start: None}
    parent_b: dict[State, Optional[State]] = {goal: None}

    expanded = 0
    frontier_max = 2

    def expand(
        q: deque[State],
        parent_this: dict[State, Optional[State]],
        parent_other: dict[State, Optional[State]],
    ) -> Optional[State]:
        nonlocal expanded
        cur = q.popleft()
        expanded += 1
        if trace is not None:
            trace.append(cur)

        for nxt, _ in neighbors(cur):
            if nxt in parent_this:
                continue
            parent_this[nxt] = cur
            if nxt in parent_other:
                return nxt
            q.append(nxt)
        return None

    while q_f and q_b:
        frontier_max = max(frontier_max, len(q_f) + len(q_b))

        meet = expand(q_f, parent_f, parent_b)
        if meet is not None:
            path_f = reconstruct_path(parent_f, meet)    # start -> meet
            path_b = reconstruct_path(parent_b, meet)    # goal  -> meet
            path_b.reverse()                              # meet -> goal
            full = path_f + path_b[1:]
            return SearchResult(True, full, float(len(full) - 1), expanded, frontier_max)

        meet = expand(q_b, parent_b, parent_f)
        if meet is not None:
            path_f = reconstruct_path(parent_f, meet)
            path_b = reconstruct_path(parent_b, meet)
            path_b.reverse()
            full = path_f + path_b[1:]
            return SearchResult(True, full, float(len(full) - 1), expanded, frontier_max)

    return SearchResult(False, [], float("inf"), expanded, frontier_max)