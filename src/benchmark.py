"""算法对比：迷宫寻路四种算法 + 地铁双目标。

运行：python benchmark.py
"""

from __future__ import annotations

import os
import random
import time

from graph import search
from maze import Maze, generate_backtracker, manhattan
from metro import fastest_path, fewest_transfers_path, load_metro

DATA = os.path.join(os.path.dirname(__file__), "data", "metro.json")


def bench_maze() -> None:
    print("=" * 62)
    print("迷宫寻路算法对比（21x21 迷宫，递归回溯生成）")
    print("=" * 62)
    random.seed(42)
    m = Maze(21, 21)
    generate_backtracker(m)
    g = m.to_graph()
    start, goal = (0, 0), (m.rows - 1, m.cols - 1)

    print(f"{'算法':<10}{'路径长度':>8}{'访问节点':>10}{'frontier峰值':>12}{'耗时(ms)':>10}")
    for algo in ("bfs", "dfs", "dijkstra", "astar"):
        t0 = time.perf_counter()
        if algo == "astar":
            res = search(g, start, goal, "astar", heuristic=manhattan)
        else:
            res = search(g, start, goal, algo)
        dt = (time.perf_counter() - t0) * 1000
        length = len(res.path) if res.path else "-"
        print(f"{algo:<10}{length:>8}{res.explored:>10}{res.frontier_peak:>12}{dt:>10.2f}")
    print()


def bench_metro() -> None:
    print("=" * 62)
    print("地铁规划双目标对比")
    print("=" * 62)
    data = load_metro(DATA)
    lines = data["lines"]
    cases = [("西山站", "东郊站"), ("西山站", "东北站"), ("北门站", "东北站")]
    for s, t in cases:
        fast = fastest_path(lines, s, t)
        few = fewest_transfers_path(lines, s, t)
        print(f"{s} → {t}")
        print(f"  最快路径:  {' → '.join(fast['stations'])}  ({len(fast['stations']) - 1} 站, {fast['transfers']} 次换乘)")
        print(f"  最少换乘:  {' → '.join(few['stations'])}  ({len(few['stations']) - 1} 站, {few['transfers']} 次换乘)")
    print()


def main() -> None:
    bench_maze()
    bench_metro()


if __name__ == "__main__":
    main()
