"""graph 模块单元测试：BFS/Dijkstra/A* 的正确性与最短性。"""

from graph import bfs, dfs, dijkstra, astar

# 加权图：A-B-C-D 总代价 1+2+1=4，为最短
WEIGHTED = {
    "A": [("B", 1), ("C", 4)],
    "B": [("A", 1), ("C", 2), ("D", 5)],
    "C": [("A", 4), ("B", 2), ("D", 1)],
    "D": [("B", 5), ("C", 1)],
}


def test_dijkstra_shortest_weighted():
    res = dijkstra(WEIGHTED, "A", "D")
    assert res.path == ["A", "B", "C", "D"]
    assert res.cost == 4.0


def test_bfs_ignores_weight():
    # BFS 按跳数：A→D 最短 2 跳（A-B-D 或 A-C-D）
    res = bfs(WEIGHTED, "A", "D")
    assert res.cost == 2.0
    assert res.path[0] == "A" and res.path[-1] == "D"


def test_astar_matches_dijkstra_optimal():
    # 启发式取 0 时 A* 退化为 Dijkstra，结果一致
    res = astar(WEIGHTED, "A", "D", heuristic=lambda a, b: 0)
    assert res.cost == 4.0
    assert res.path == ["A", "B", "C", "D"]


def test_astar_consistent_heuristic_still_optimal():
    # 单调一致启发式（如用已知最短下界），仍保证最优
    h = {"A": 3, "B": 2, "C": 1, "D": 0}
    res = astar(WEIGHTED, "A", "D", heuristic=lambda a, b: h[a])
    assert res.cost == 4.0


def test_dfs_finds_path_but_not_necessarily_shortest():
    res = dfs(WEIGHTED, "A", "D")
    assert res.path is not None
    assert res.path[0] == "A" and res.path[-1] == "D"


def test_no_path_returns_none():
    g = {"X": [("Y", 1)], "Y": []}
    for fn in (bfs, dfs, dijkstra):
        res = fn(g, "X", "Z")
        assert res.path is None
    res = astar(g, "X", "Z", heuristic=lambda a, b: 0)
    assert res.path is None


def test_start_equals_goal():
    for fn in (bfs, dfs, dijkstra):
        res = fn(WEIGHTED, "A", "A")
        assert res.path == ["A"] and res.cost == 0.0
