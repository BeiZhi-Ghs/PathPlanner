"""通用图与搜索算法内核。

图用邻接表表示：dict[node] -> list[(neighbor, weight)]。
node 可为任意可哈希对象（迷宫用 (r,c) 元组、地铁用站点名字符串）。

统一接口 search(graph, start, goal, algorithm, heuristic) -> SearchResult。
"""

from __future__ import annotations

import heapq
import itertools
from collections import deque
from dataclasses import dataclass
from typing import Callable, Dict, List, Optional, Tuple

Graph = Dict[object, List[Tuple[object, float]]]
Heuristic = Callable[[object, object], float]
INF = float("inf")


@dataclass
class SearchResult:
    path: Optional[List[object]]  # 节点序列，未找到为 None
    cost: float                   # 路径总代价
    visited: List[object]         # 节点弹出顺序（供动画展示搜索过程）
    explored: int                 # 弹出的节点数
    frontier_peak: int            # frontier 峰值大小


def _reconstruct(parent: Dict[object, Optional[object]], goal: object) -> List[object]:
    path: List[object] = []
    cur: Optional[object] = goal
    while cur is not None:
        path.append(cur)
        cur = parent[cur]
    path.reverse()
    return path


def bfs(graph: Graph, start: object, goal: object) -> SearchResult:
    """广度优先搜索：无权图最短路径（忽略边权）。"""
    if start == goal:
        return SearchResult([start], 0.0, [start], 1, 1)
    frontier = deque([start])
    parent: Dict[object, Optional[object]] = {start: None}
    dist: Dict[object, float] = {start: 0.0}
    visited: List[object] = []
    explored = 0
    peak = 1

    while frontier:
        cur = frontier.popleft()
        visited.append(cur)
        explored += 1
        if cur == goal:
            return SearchResult(_reconstruct(parent, goal), dist[goal], visited, explored, peak)
        for nb, _ in graph.get(cur, []):
            if nb not in parent:
                parent[nb] = cur
                dist[nb] = dist[cur] + 1
                frontier.append(nb)
                peak = max(peak, len(frontier))

    return SearchResult(None, INF, visited, explored, peak)


def dfs(graph: Graph, start: object, goal: object) -> SearchResult:
    """深度优先搜索：展示搜索顺序差异，不保证最短路径。"""
    if start == goal:
        return SearchResult([start], 0.0, [start], 1, 1)
    stack = [start]
    parent: Dict[object, Optional[object]] = {start: None}
    dist: Dict[object, float] = {start: 0.0}
    visited: List[object] = []
    closed = set()
    explored = 0
    peak = 1

    while stack:
        cur = stack.pop()
        if cur in closed:
            continue
        closed.add(cur)
        visited.append(cur)
        explored += 1
        if cur == goal:
            return SearchResult(_reconstruct(parent, goal), dist[goal], visited, explored, peak)
        for nb, w in graph.get(cur, []):
            if nb not in closed:
                parent[nb] = cur
                dist[nb] = dist[cur] + w
                stack.append(nb)
                peak = max(peak, len(stack))

    return SearchResult(None, INF, visited, explored, peak)


def dijkstra(graph: Graph, start: object, goal: object) -> SearchResult:
    """Dijkstra：加权图最短路径（二叉堆优化）。"""
    if start == goal:
        return SearchResult([start], 0.0, [start], 1, 1)
    counter = itertools.count()
    dist: Dict[object, float] = {start: 0.0}
    parent: Dict[object, Optional[object]] = {start: None}
    heap = [(0.0, next(counter), start)]
    closed = set()
    visited: List[object] = []
    explored = 0
    peak = 1

    while heap:
        d, _, cur = heapq.heappop(heap)
        if cur in closed:
            continue
        closed.add(cur)
        visited.append(cur)
        explored += 1
        if cur == goal:
            return SearchResult(_reconstruct(parent, goal), dist[goal], visited, explored, peak)
        for nb, w in graph.get(cur, []):
            nd = d + w
            if nb not in dist or nd < dist[nb]:
                dist[nb] = nd
                parent[nb] = cur
                heapq.heappush(heap, (nd, next(counter), nb))
                peak = max(peak, len(heap))

    return SearchResult(None, INF, visited, explored, peak)


def astar(graph: Graph, start: object, goal: object, heuristic: Heuristic) -> SearchResult:
    """A*：f(n)=g(n)+h(n)，启发式可采纳且一致时保证最优。"""
    if start == goal:
        return SearchResult([start], 0.0, [start], 1, 1)
    counter = itertools.count()
    g: Dict[object, float] = {start: 0.0}
    parent: Dict[object, Optional[object]] = {start: None}
    heap = [(heuristic(start, goal), next(counter), start)]
    closed = set()
    visited: List[object] = []
    explored = 0
    peak = 1

    while heap:
        _, _, cur = heapq.heappop(heap)
        if cur in closed:
            continue
        closed.add(cur)
        visited.append(cur)
        explored += 1
        if cur == goal:
            return SearchResult(_reconstruct(parent, goal), g[goal], visited, explored, peak)
        for nb, w in graph.get(cur, []):
            ng = g[cur] + w
            if nb not in g or ng < g[nb]:
                g[nb] = ng
                parent[nb] = cur
                heapq.heappush(heap, (ng + heuristic(nb, goal), next(counter), nb))
                peak = max(peak, len(heap))

    return SearchResult(None, INF, visited, explored, peak)


def search(
    graph: Graph,
    start: object,
    goal: object,
    algorithm: str = "dijkstra",
    heuristic: Optional[Heuristic] = None,
) -> SearchResult:
    """统一分发入口。algorithm ∈ {"bfs", "dfs", "dijkstra", "astar"}。"""
    if algorithm == "bfs":
        return bfs(graph, start, goal)
    if algorithm == "dfs":
        return dfs(graph, start, goal)
    if algorithm == "astar":
        if heuristic is None:
            raise ValueError("A* 需要提供启发式函数")
        return astar(graph, start, goal, heuristic)
    return dijkstra(graph, start, goal)
