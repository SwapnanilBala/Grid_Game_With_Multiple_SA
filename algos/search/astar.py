from __future__ import annotations

import heapq
from dataclasses import dataclass, field
from typing import Optional, TypeVar

from .base import GoalTestFn, HeuristicFn, NeighborsFn, SearchResult, reconstruct_path

State = TypeVar("State")


@dataclass(order=True, slots=True)
class _PQItem:
    # Heap ordering: f then g then tie (stable-ish ordering)
    f: float
    g: float
    tie: int
    # Let's not use state for comparisons (avoids needing State to be orderable)
    state: State = field(compare=False)


def astar(
    start: State,
    is_goal: GoalTestFn[State],
    neighbors: NeighborsFn[State],
    h: HeuristicFn[State],
    trace: list[State] | None = None,   # <--- add this
) -> SearchResult[State]:
    """
    A* Search.
    - Requires non-negative step costs.
    - Optimal if h is admissible (never overestimates).
    """
    heap: list[_PQItem] = []
    tie = 0

    g_cost: dict[State, float] = {start: 0.0}
    parent: dict[State, Optional[State]] = {start: None}

    heapq.heappush(heap, _PQItem(f=h(start), g=0.0, tie=tie, state=start))

    expanded = 0
    frontier_max = 1

    while heap:
        frontier_max = max(frontier_max, len(heap))
        item = heapq.heappop(heap)
        cur = item.state
        cur_g = item.g

        # Skip stale heap entries (we found a better path to cur after this was pushed)
        if cur_g != g_cost.get(cur, float("inf")):
            continue

        expanded += 1
        if trace is not None:
            trace.append(cur)

        if is_goal(cur):
            path = reconstruct_path(parent, cur)
            return SearchResult(True, path, g_cost[cur], expanded, frontier_max)

        for nxt, step in neighbors(cur):
            if step < 0:
                raise ValueError("A* requires non-negative step costs.")

            new_g = cur_g + step
            if nxt not in g_cost or new_g < g_cost[nxt]:
                g_cost[nxt] = new_g
                parent[nxt] = cur
                tie += 1
                heapq.heappush(
                    heap,
                    _PQItem(f=new_g + h(nxt), g=new_g, tie=tie, state=nxt),
                )

    return SearchResult(False, [], float("inf"), expanded, frontier_max)
