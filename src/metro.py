"""地铁线路加载、加权图构建与双目标规划。

线路分层建模：
- 节点 = (station, line)：同一站不同线路视为不同节点。
- 运行边：同一线路内相邻站，权 1（一站）。
- 换乘边：同站跨线，权 = transfer_penalty。

双目标：
- 最快路径：transfer_penalty = 0（纯站数最短）。
- 最少换乘：transfer_penalty = 大值（优先减少换乘次数）。
"""

from __future__ import annotations

import json
from typing import Dict, List, Optional, Tuple

from graph import dijkstra

Node = Tuple[str, str]  # (station, line)


def load_metro(path: str) -> dict:
    """读取 metro.json：{"lines": {线路: [站...]}, "coords": {站: [x,y]}}。"""
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def build_graph(lines: Dict[str, List[str]], transfer_penalty: float = 0.0) -> dict:
    """按线路分层构建邻接表。"""
    g: dict = {}
    # 运行边：同一线路内相邻站
    for line, stations in lines.items():
        for i in range(len(stations) - 1):
            a = (stations[i], line)
            b = (stations[i + 1], line)
            g.setdefault(a, []).append((b, 1.0))
            g.setdefault(b, []).append((a, 1.0))
    # 换乘边：同站跨线
    station_lines: Dict[str, List[str]] = {}
    for line, stations in lines.items():
        for s in stations:
            station_lines.setdefault(s, []).append(line)
    for station, ls in station_lines.items():
        for i in range(len(ls)):
            for j in range(i + 1, len(ls)):
                a = (station, ls[i])
                b = (station, ls[j])
                g.setdefault(a, []).append((b, transfer_penalty))
                g.setdefault(b, []).append((a, transfer_penalty))
    return g


def _count_transfers(path: List[Node]) -> int:
    lines = [line for _, line in path]
    return sum(1 for i in range(1, len(lines)) if lines[i] != lines[i - 1])


def plan_route(
    lines: Dict[str, List[str]],
    start: str,
    goal: str,
    transfer_penalty: float = 0.0,
) -> Optional[dict]:
    """规划 start → goal。

    返回 {"stations": [站序列], "transfers": 换乘次数, "cost": 总代价}
    ；起点终点不连通返回 None。
    """
    if start == goal:
        return {"stations": [start], "transfers": 0, "cost": 0.0}

    g = build_graph(lines, transfer_penalty)
    S, T = "__START__", "__GOAL__"
    g[S] = []
    g[T] = []
    for line, stations in lines.items():
        if start in stations:
            g[S].append(((start, line), 0.0))
        if goal in stations:
            g.setdefault((goal, line), []).append((T, 0.0))

    res = dijkstra(g, S, T)
    if res.path is None:
        return None

    path: List[Node] = [n for n in res.path if n not in (S, T)]
    stations: List[str] = []
    for st, _line in path:
        if not stations or stations[-1] != st:
            stations.append(st)
    transfers = _count_transfers(path)
    return {"stations": stations, "transfers": transfers, "cost": res.cost}


def fastest_path(lines: Dict[str, List[str]], start: str, goal: str) -> Optional[dict]:
    """最快（站数最少）路径。"""
    return plan_route(lines, start, goal, transfer_penalty=0.0)


def fewest_transfers_path(lines: Dict[str, List[str]], start: str, goal: str) -> Optional[dict]:
    """最少换乘路径（换乘惩罚取较大值，站数次之）。"""
    # 惩罚取一个足够大、保证优先减少换乘的值
    return plan_route(lines, start, goal, transfer_penalty=10.0)
