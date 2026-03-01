from __future__ import annotations

from typing import TypeVar, Optional

from .base import NeighborsFn, GoalTestFn, SearchResult, reconstruct_path

State = TypeVar("State")


def dls(
    start: State,
    is_goal: GoalTestFn[State],
    neighbors: NeighborsFn[State],
    depth_limit: int = 300,         # How deep we're allowed to go before we say "nope, not going further"
    h=None,                         # Not used here; kept so the caller can pass the same params to every algorithm
    trace: list[State] | None = None,  # If provided, we log which nodes we expanded (useful for pygame replay)
) -> SearchResult[State]:
    """
    Depth-Limited Search: DFS with a maximum depth.
    Returns failure if not found within limit.
    """
    # We do DFS using a stack, but we also store the depth next to each node.
    # Each stack entry is (state, depth_from_start).
    stack: list[tuple[State, int]] = [(start, 0)]

    # Parent pointers let us rebuild the path when we hit the goal.
    parent: dict[State, Optional[State]] = {start: None}

    # For each state, remember the shallowest depth we've seen it at.
    # This helps avoid revisiting the same node at a deeper (worse) depth.
    best_depth_seen: dict[State, int] = {start: 0}

    # Some stats we return (handy for debugging / comparing algorithms).
    expanded = 0
    frontier_max = 1

    while stack:
        # Track the biggest the stack ever gets.
        frontier_max = max(frontier_max, len(stack))
        # Pop last-in node (this is what makes it DFS).
        cur, depth = stack.pop()

        expanded += 1
        if trace is not None:
            # Record expansion order if requested.
            trace.append(cur)

        # Goal check: if this node is the target, rebuild and return the path.
        if is_goal(cur):
            path = reconstruct_path(parent, cur)
            return SearchResult(True, path, float(len(path) - 1), expanded, frontier_max)

        # If we're at the depth limit, we stop expanding deeper from here.
        if depth >= depth_limit:
            continue

        # Otherwise, push neighbors onto the stack with depth+1.
        for nxt, _ in neighbors(cur):
            nd = depth + 1
            prev = best_depth_seen.get(nxt)
            if prev is None or nd < prev:
                # Found `nxt` at a better (shallower) depth than before.
                best_depth_seen[nxt] = nd
                parent[nxt] = cur
                stack.append((nxt, nd))

    # Stack ran dry => no solution within the depth limit.
    return SearchResult(False, [], float("inf"), expanded, frontier_max)