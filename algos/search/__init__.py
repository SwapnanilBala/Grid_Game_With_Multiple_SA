"""
Search algorithms package.

Public API:
- bfs_search, dfs_search, dls_search
- ucs_search, astar_search
- bidirectional_search
- SearchResult, NeighborsFn, HeuristicFn
"""

from .base import SearchResult, NeighborsFn, HeuristicFn

from .bfs import bfs as bfs_search
from .dfs import dfs as dfs_search
from .dls import dls as dls_search
from .ucs import ucs as ucs_search
from .astar import astar as astar_search
from .bds import bidirectional_search

__all__ = [
    # Types
    "SearchResult",
    "NeighborsFn",
    "HeuristicFn",
    # Algorithms
    "bfs_search",
    "dfs_search",
    "dls_search",
    "ucs_search",
    "astar_search",
    "bidirectional_search",
]
