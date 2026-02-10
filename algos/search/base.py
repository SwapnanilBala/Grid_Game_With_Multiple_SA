from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Generic, Iterable, Optional, TypeVar

State = TypeVar("State")

NeighborsFn = Callable[[State], Iterable[tuple[State, float]]]
GoalTestFn = Callable[[State], bool]
HeuristicFn = Callable[[State], float]


@dataclass(slots=True)
class SearchResult(Generic[State]):
    found: bool
    path: list[State]
    cost: float
    expanded: int
    frontier_max: int


def reconstruct_path(parent: dict[State, Optional[State]], end: State) -> list[State]:
    path: list[State] = []
    cur: Optional[State] = end
    while cur is not None:
        path.append(cur)
        cur = parent[cur]
    path.reverse()
    return path
