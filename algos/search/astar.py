from __future__ import annotations

import heapq
from dataclasses import dataclass, field
from typing import Optional, TypeVar

from .base import GoalTestFn, HeuristicFn, NeighborsFn, SearchResult, reconstruct_path

State = TypeVar("State")


@dataclass(order=True, slots=True)
class _PQItem:
    # This is what we store in the priority queue.
    # The heap will sort by: lowest f first, then lowest g, then a tiny tie-breaker.
    f: float
    g: float
    tie: int
    # We exclude `state` from comparisons so `State` itself doesn't need to be sortable.
    state: State = field(compare=False)


def astar(
    start: State,
    is_goal: GoalTestFn[State],
    neighbors: NeighborsFn[State],
    h: HeuristicFn[State],
    trace: list[State] | None = None,   # If provided, we’ll append nodes as we expand them (nice for visualization)
) -> SearchResult[State]:
    """
    A* Search.
    - Requires non-negative step costs.
    - Optimal if h is admissible (never overestimates).
    """
    # The “open set” as a min-heap (priority queue).
    # Each entry is prioritized by f = g + h.
    heap: list[_PQItem] = []
    tie = 0

    # Best known cost from start to each node (g-score in A* terms).
    g_cost: dict[State, float] = {start: 0.0}
    # Parent pointers so we can rebuild the final path when we hit the goal.
    parent: dict[State, Optional[State]] = {start: None}

    # Start with the initial node.
    heapq.heappush(heap, _PQItem(f=h(start), g=0.0, tie=tie, state=start))

    # Some stats we return (handy for debugging / comparing algorithms).
    expanded = 0
    frontier_max = 1

    while heap:
        # Track the largest the frontier ever gets.
        frontier_max = max(frontier_max, len(heap))
        item = heapq.heappop(heap)
        cur = item.state
        cur_g = item.g

        # Important A* trick:
        # The heap might contain “old” entries if we later found a cheaper way to reach `cur`.
        # If this entry doesn't match our best-known g-cost anymore, ignore it.
        if cur_g != g_cost.get(cur, float("inf")):
            continue

        expanded += 1
        if trace is not None:
            # Record expansion order if requested.
            trace.append(cur)

        # Goal check: if this is the goal, we can rebuild the path and return.
        if is_goal(cur):
            path = reconstruct_path(parent, cur)
            return SearchResult(True, path, g_cost[cur], expanded, frontier_max)

        # Try “relaxing” edges: see if going through `cur` gives a better path to a neighbor.
        for nxt, step in neighbors(cur):
            if step < 0:
                # A* assumes non-negative edges; negative costs break the guarantees.
                raise ValueError("A* requires non-negative step costs.")

            # Proposed new g-cost if we go from start -> ... -> cur -> nxt.
            new_g = cur_g + step
            if nxt not in g_cost or new_g < g_cost[nxt]:
                # Found a better way to reach `nxt`: update best cost + parent and push into the heap.
                g_cost[nxt] = new_g
                parent[nxt] = cur
                tie += 1
                heapq.heappush(
                    heap,
                    # f = g + h: cost so far + “guess” to the goal.
                    _PQItem(f=new_g + h(nxt), g=new_g, tie=tie, state=nxt),
                )

    # Nothing left to explore and we never hit a goal.
    return SearchResult(False, [], float("inf"), expanded, frontier_max)
