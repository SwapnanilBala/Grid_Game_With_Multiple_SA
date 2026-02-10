from __future__ import annotations

import heapq
from dataclasses import dataclass
from typing import TypeVar, Optional

from .base import NeighborsFn, GoalTestFn, SearchResult, reconstruct_path

State = TypeVar("State")


@dataclass(order=True, slots=True)
class _PQItem:
    g: float
    tie: int
    state: object


def ucs(start: State, is_goal: GoalTestFn[State], neighbors: NeighborsFn[State]) -> SearchResult[State]:
    """
    Uniform Cost Search: optimal for non-negative step costs.
    Equivalent to Dijkstra when goal_test is used.
    """
    heap: list[_PQItem] = []
    tie = 0
    heapq.heappush(heap, _PQItem(0.0, tie, start))

    g_cost: dict[State, float] = {start: 0.0}
    parent: dict[State, Optional[State]] = {start: None}

    expanded = 0
    frontier_max = 1

    while heap:
        frontier_max = max(frontier_max, len(heap))
        item = heapq.heappop(heap)
        cur = item.state  # type: ignore[assignment]
        cur_g = item.g

        # Skip stale entries
        if cur_g != g_cost.get(cur, float("inf")):  # type: ignore[arg-type]
            continue

        expanded += 1
        if is_goal(cur):  # type: ignore[arg-type]
            path = reconstruct_path(parent, cur)  # type: ignore[arg-type]
            return SearchResult(True, path, g_cost[cur], expanded, frontier_max)  # type: ignore[index]

        for nxt, step in neighbors(cur):  # type: ignore[arg-type]
            if step < 0:
                raise ValueError("UCS requires non-negative step costs.")
            new_g = cur_g + step
            if nxt not in g_cost or new_g < g_cost[nxt]:
                g_cost[nxt] = new_g
                parent[nxt] = cur  # type: ignore[assignment]
                tie += 1
                heapq.heappush(heap, _PQItem(new_g, tie, nxt))

    return SearchResult(False, [], float("inf"), expanded, frontier_max)
