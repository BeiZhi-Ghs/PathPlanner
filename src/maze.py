"""迷宫生成与网格转图。

- 迷宫用「每个格子四向墙位掩码」表示：N=1, S=2, E=4, W=8。
- 生成算法：递归回溯（栈）、随机化 Prim（优先队列）。
- to_graph() 把网格转成邻接表（相邻且无墙 → 权 1 边），供统一图搜索内核使用。
"""

from __future__ import annotations

import heapq
import itertools
import random
from typing import Dict, List, Tuple

N, S, E, W = 1, 2, 4, 8
OPP = {N: S, S: N, E: W, W: E}
# (dr, dc, 方向位)
DIRS = [(-1, 0, N), (1, 0, S), (0, 1, E), (0, -1, W)]

Node = Tuple[int, int]


class Maze:
    def __init__(self, rows: int, cols: int):
        self.rows = rows
        self.cols = cols
        self.walls = [[N | S | E | W for _ in range(cols)] for _ in range(rows)]

    def in_bounds(self, r: int, c: int) -> bool:
        return 0 <= r < self.rows and 0 <= c < self.cols

    def carve(self, r: int, c: int, dr: int, dc: int, bit: int) -> None:
        """拆除 (r,c) 与 (r+dr,c+dc) 之间的墙。"""
        nr, nc = r + dr, c + dc
        self.walls[r][c] &= ~bit
        self.walls[nr][nc] &= ~OPP[bit]

    def to_graph(self) -> Dict[Node, List[Tuple[Node, int]]]:
        """网格 → 邻接表。每个无墙的相邻关系对应一条权 1 边（双向）。"""
        g: Dict[Node, List[Tuple[Node, int]]] = {
            (r, c): [] for r in range(self.rows) for c in range(self.cols)
        }
        for r in range(self.rows):
            for c in range(self.cols):
                if c + 1 < self.cols and not (self.walls[r][c] & E):
                    g[(r, c)].append(((r, c + 1), 1))
                    g[(r, c + 1)].append(((r, c), 1))
                if r + 1 < self.rows and not (self.walls[r][c] & S):
                    g[(r, c)].append(((r + 1, c), 1))
                    g[(r + 1, c)].append(((r, c), 1))
        return g


def generate_backtracker(maze: Maze, rng: random.Random = None) -> None:
    """递归回溯生成（用显式栈实现，避免递归深度）。长通道风格。"""
    rng = rng or random
    stack = [(0, 0)]
    visited = {(0, 0)}
    while stack:
        r, c = stack[-1]
        options = []
        for dr, dc, bit in DIRS:
            nr, nc = r + dr, c + dc
            if maze.in_bounds(nr, nc) and (nr, nc) not in visited:
                options.append((dr, dc, bit, nr, nc))
        if not options:
            stack.pop()
        else:
            dr, dc, bit, nr, nc = rng.choice(options)
            maze.carve(r, c, dr, dc, bit)
            visited.add((nr, nc))
            stack.append((nr, nc))


def generate_prim(maze: Maze, rng: random.Random = None) -> None:
    """随机化 Prim 生成（按随机权重的最小堆）。多分支风格。"""
    rng = rng or random
    in_maze = {(0, 0)}
    counter = itertools.count()
    heap: List[Tuple[float, int, Tuple[int, int, int, int, int]]] = []

    def push(r: int, c: int) -> None:
        for dr, dc, bit in DIRS:
            nr, nc = r + dr, c + dc
            if maze.in_bounds(nr, nc) and (nr, nc) not in in_maze:
                heapq.heappush(heap, (rng.random(), next(counter), (r, c, nr, nc, bit)))

    push(0, 0)
    while heap:
        _, _, (r, c, nr, nc, bit) = heapq.heappop(heap)
        if (nr, nc) in in_maze:
            continue
        maze.carve(r, c, nr - r, nc - c, bit)
        in_maze.add((nr, nc))
        push(nr, nc)


def manhattan(a: Node, b: Node) -> float:
    """网格曼哈顿距离，作为 A* 启发式。"""
    return abs(a[0] - b[0]) + abs(a[1] - b[1])
