from __future__ import annotations

from typing import Optional, TypeVar

from .base import GoalTestFn, NeighborsFn, SearchResult, reconstruct_path

State = TypeVar("State")


def dfs(
    start: State,
    is_goal: GoalTestFn[State],
    neighbors: NeighborsFn[State],
    h=None,  # Not used here; kept so the caller can pass the same params to every algorithm
    trace: list[State] | None = None,
) -> SearchResult[State]:
    # DFS uses a stack (LIFO): last thing we discovered is the next thing we explore.
    stack: list[State] = [start]

    # Parent pointers so we can rebuild a path when we find the goal.
    parent: dict[State, Optional[State]] = {start: None}

    # Keep a visited set so we don't loop forever on cycles.
    visited: set[State] = {start}

    # Some stats we return (handy for debugging / comparing algorithms).
    expanded = 0
    frontier_max = 1

    while stack:
        # Track the biggest the stack ever gets.
        frontier_max = max(frontier_max, len(stack))
        # Pop last-in node (this is the "depth-first" part).
        cur = stack.pop()

        expanded += 1
        if trace is not None:
            # Record expansion order if requested.
            trace.append(cur)

        # Goal check: if this is our target, rebuild the path and we're done.
        if is_goal(cur):
            path = reconstruct_path(parent, cur)
            # DFS doesn't use step costs; report path length - 1 as cost (edges)
            return SearchResult(True, path, float(len(path) - 1), expanded, frontier_max)

        # Push neighbors we haven't seen yet.
        for nxt, _ in neighbors(cur):
            if nxt not in visited:
                # Mark visited *when we push* so we don't push the same node multiple times.
                visited.add(nxt)
                parent[nxt] = cur
                stack.append(nxt)

    # Ran out of nodes without hitting a goal.
    return SearchResult(False, [], float("inf"), expanded, frontier_max)