from __future__ import annotations

import heapq
from dataclasses import dataclass, field
from typing import Optional, TypeVar

from .base import NeighborsFn, GoalTestFn, SearchResult, reconstruct_path

State = TypeVar("State")


@dataclass(order=True, slots=True)
class _PQItem:
    # This is what we store in the priority queue.
    # UCS always expands the node with the smallest total cost-so-far (g).
    g: float
    tie: int
    # Don't compare by `state` (so `State` doesn't need to be orderable).
    state: State = field(compare=False)


def ucs(
    start: State,
    is_goal: GoalTestFn[State],
    neighbors: NeighborsFn[State],
    h=None,  # Not used here; kept so the caller can pass the same params to every algorithm
    trace: list[State] | None = None,
) -> SearchResult[State]:
    """
    Uniform Cost Search (Dijkstra): optimal for non-negative step costs.
    """
    # The "frontier" (aka open set) as a min-heap.
    # We always pop the state with the lowest known cost from the start.
    heap: list[_PQItem] = []
    tie = 0
    # Start at the start node with cost 0.
    heapq.heappush(heap, _PQItem(0.0, tie, start))

    # Best known cost from start -> state (g-score).
    g_cost: dict[State, float] = {start: 0.0}
    # Parent pointers so we can rebuild the final path once we reach the goal.
    parent: dict[State, Optional[State]] = {start: None}

    # Some stats we return (handy for debugging / comparing algorithms).
    expanded = 0
    frontier_max = 1

    while heap:
        # Track the biggest the frontier ever gets.
        frontier_max = max(frontier_max, len(heap))
        item = heapq.heappop(heap)
        cur = item.state
        cur_g = item.g

        # The heap can contain "old" entries if we later found a cheaper way to reach `cur`.
        # If this isn't the best known cost anymore, ignore it.
        if cur_g != g_cost.get(cur, float("inf")):
            continue

        expanded += 1
        if trace is not None:
            # Record expansion order if requested (useful for visualization).
            trace.append(cur)

        # Goal check: if this is the target, rebuild and return.
        if is_goal(cur):
            path = reconstruct_path(parent, cur)
            return SearchResult(True, path, g_cost[cur], expanded, frontier_max)

        # Explore neighbors and see if going through `cur` gives them a cheaper cost.
        for nxt, step in neighbors(cur):
            if step < 0:
                # UCS/Dijkstra assumes non-negative edges. Negative costs break the guarantees.
                raise ValueError("UCS requires non-negative step costs.")

            # New possible cost to reach nxt via cur.
            new_g = cur_g + step
            if nxt not in g_cost or new_g < g_cost[nxt]:
                # Found a better (cheaper) route to nxt.
                g_cost[nxt] = new_g
                parent[nxt] = cur
                tie += 1
                # Push the updated cost into the heap.
                heapq.heappush(heap, _PQItem(new_g, tie, nxt))

    # Nothing left to explore and we never reached a goal.
    return SearchResult(False, [], float("inf"), expanded, frontier_max)