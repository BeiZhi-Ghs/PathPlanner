"""maze 模块单元测试：生成算法的连通性与完美迷宫性质。"""

from collections import deque

from maze import Maze, generate_backtracker, generate_prim


def _reachable_count(g, start):
    seen = {start}
    q = deque([start])
    while q:
        cur = q.popleft()
        for nb, _ in g.get(cur, []):
            if nb not in seen:
                seen.add(nb)
                q.append(nb)
    return len(seen)


def _edge_count(g):
    return sum(len(v) for v in g.values()) // 2


def _assert_perfect_maze(maze):
    g = maze.to_graph()
    v = maze.rows * maze.cols
    # 完美迷宫是树：连通 + 边数 = V - 1
    assert _edge_count(g) == v - 1
    assert _reachable_count(g, (0, 0)) == v


def test_backtracker_perfect_maze():
    m = Maze(9, 9)
    generate_backtracker(m)
    _assert_perfect_maze(m)


def test_prim_perfect_maze():
    m = Maze(9, 9)
    generate_prim(m)
    _assert_perfect_maze(m)


def test_maze_graph_bidirectional():
    m = Maze(5, 5)
    generate_backtracker(m)
    g = m.to_graph()
    for node, edges in g.items():
        for nb, w in edges:
            assert w == 1
            # 反向边存在
            assert (node, 1) in g[nb]
