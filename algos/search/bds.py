from __future__ import annotations

from collections import deque
from typing import TypeVar, Optional, Iterable, Callable

from .base import NeighborsFn, GoalTestFn, SearchResult, reconstruct_path

State = TypeVar("State")


def bidirectional_search(
    start: State,
    goal: State,
    neighbors: NeighborsFn[State],
trace: list[State] | None = None,
) -> SearchResult[State]:
    """
    Bidirectional BFS (unweighted).
    Requires explicit goal state (not just a goal_test), because we search from both ends.
    """
    if start == goal:
        return SearchResult(True, [start], 0.0, expanded=1, frontier_max=1)

    q_f = deque([start])
    q_b = deque([goal])

    parent_f: dict[State, Optional[State]] = {start: None}
    parent_b: dict[State, Optional[State]] = {goal: None}

    expanded = 0
    frontier_max = 2

    def expand_frontier(
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
            if nxt not in parent_this:
                parent_this[nxt] = cur
                if nxt in parent_other:
                    return nxt
                q.append(nxt)
        return None

    while q_f and q_b:
        frontier_max = max(frontier_max, len(q_f) + len(q_b))

        meet = expand_frontier(q_f, parent_f, parent_b)
        if meet is not None:
            path_f = reconstruct_path(parent_f, meet)
            # reconstruct backward side: meet -> goal
            # parent_b goes from goal outward; build meet->goal by walking parents from meet in parent_b
            tail: list[State] = []
            cur: Optional[State] = meet
            while cur is not None:
                tail.append(cur)
                cur = parent_b[cur]
            # tail is meet..goal, but includes meet; we already have meet in path_f
            tail = tail[1:]  # drop meet
            full = path_f + tail
            return SearchResult(True, full, float(len(full) - 1), expanded, frontier_max)

        meet = expand_frontier(q_b, parent_b, parent_f)
        if meet is not None:
            path_f = reconstruct_path(parent_f, meet)
            tail: list[State] = []
            cur: Optional[State] = meet
            while cur is not None:
                tail.append(cur)
                cur = parent_b[cur]
            tail = tail[1:]
            full = path_f + tail
            return SearchResult(True, full, float(len(full) - 1), expanded, frontier_max)

    return SearchResult(False, [], float("inf"), expanded, frontier_max)
