from __future__ import annotations

from collections import deque
from typing import Optional, TypeVar

from .base import NeighborsFn, GoalTestFn, SearchResult, reconstruct_path

State = TypeVar("State")


def bds(
    start: State,
    is_goal: GoalTestFn[State],          # Here for consistency with other search funcs (we don't actually use it here)
    neighbors: NeighborsFn[State],
    goal: State | None = None,           # We need the exact goal so we can search from both ends
    h=None,                              # Not a heuristic-based search, but we keep this param so the call style matches
    trace: list[State] | None = None,
) -> SearchResult[State]:
    """
    Bidirectional BFS (unweighted). Requires goal state.

    NOTE: cost returned = steps (len(path)-1), not weighted cost.
    """
    if goal is None:
        # Regular BFS can stop when it *finds* a goal.
        # Bidirectional BFS needs the *actual goal node* up front so it can also search backwards from it.
        raise ValueError("bds requires goal=... (explicit goal state).")

    if start == goal:
        # Easy win: you're already at the goal.
        return SearchResult(True, [start], 0.0, expanded=1, frontier_max=1)

    # Two queues (frontiers): one grows from the start, the other grows from the goal.
    q_f = deque([start])
    q_b = deque([goal])

    # These dicts let us rebuild the final path once the searches bump into each other.
    # - parent_f[x] tells us how we reached x from the start side
    # - parent_b[x] tells us how we reached x from the goal side
    # The first node on each side points to None.
    parent_f: dict[State, Optional[State]] = {start: None}
    parent_b: dict[State, Optional[State]] = {goal: None}

    # Some stats we return (handy for debugging / comparing algorithms).
    expanded = 0
    frontier_max = 2


    def expand(
        q: deque[State],
        parent_this: dict[State, Optional[State]],
        parent_other: dict[State, Optional[State]],
    ) -> Optional[State]:
        nonlocal expanded
        # Grab the next node from this side's queue (classic BFS order).
        cur = q.popleft()
        expanded += 1
        if trace is not None:
            # If someone passed in a trace list, we log what we expanded (nice for viz).
            trace.append(cur)

        # Check out all neighbors of `cur`.
        # neighbors(cur) gives (neighbor_state, step_cost) but we ignore the cost (unweighted BFS).
        for nxt, _ in neighbors(cur):
            # Already seen from this side? skip it.
            if nxt in parent_this:
                continue

            # First time seeing `nxt` from this side: remember where we came from.
            parent_this[nxt] = cur

            # The cool part: if the OTHER side already discovered `nxt`, the searches have met.
            if nxt in parent_other:
                return nxt

            # Otherwise, toss it in the queue so we can expand it later.
            q.append(nxt)
        return None


    while q_f and q_b:
        # Track the biggest the combined queues ever get (rough memory-ish metric).
        frontier_max = max(frontier_max, len(q_f) + len(q_b))

        # Expand one node from the start side.
        meet = expand(q_f, parent_f, parent_b)
        if meet is not None:
            # Nice — both sides can reach `meet`. Now we just rebuild the full route.
            # Build start -> meet using the forward parents.
            path_f = reconstruct_path(parent_f, meet)    # start -> meet
            # Build goal -> meet using the backward parents, then flip it to get meet -> goal.
            path_b = reconstruct_path(parent_b, meet)    # goal  -> meet
            path_b.reverse()                              # meet -> goal

            # Glue the two halves together.
            # (Skip the first item of path_b because it's the meeting node we already have in path_f.)
            full = path_f + path_b[1:]
            return SearchResult(True, full, float(len(full) - 1), expanded, frontier_max)

        # Expand one node from the goal side.
        meet = expand(q_b, parent_b, parent_f)
        if meet is not None:
            path_f = reconstruct_path(parent_f, meet)
            path_b = reconstruct_path(parent_b, meet)
            path_b.reverse()
            full = path_f + path_b[1:]
            return SearchResult(True, full, float(len(full) - 1), expanded, frontier_max)

    # If one side runs out of nodes to explore, there just isn't a path between start and goal.
    return SearchResult(False, [], float("inf"), expanded, frontier_max)