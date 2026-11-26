"""metro 模块单元测试：最快路径与最少换乘。"""

import os

import pytest

from metro import (
    build_graph,
    fastest_path,
    fewest_transfers_path,
    load_metro,
    plan_route,
)

DATA = os.path.join(os.path.dirname(__file__), "..", "src", "data", "metro.json")
METRO = load_metro(DATA)
LINES = METRO["lines"]


def test_metro_data_fastest_vs_fewest():
    # 西山站 → 东郊站：4 号线捷径更短(2 站 1 换乘)，直达更少换乘(3 站 0 换乘)
    fast = fastest_path(LINES, "西山站", "东郊站")
    few = fewest_transfers_path(LINES, "西山站", "东郊站")
    assert fast["cost"] == 2.0 and fast["transfers"] == 1
    assert few["transfers"] == 0 and few["cost"] == 3.0


def test_fastest_one_transfer():
    # 西山站(1号线) → 南门站(2号线)，须在中心站换乘
    r = fastest_path(LINES, "西山站", "南门站")
    assert r["transfers"] == 1
    assert r["cost"] == 3.0
    assert r["stations"][0] == "西山站" and r["stations"][-1] == "南门站"


def test_fastest_two_transfers():
    # 西山站(1号线) → 东北站(3号线)，须经中心站、南关站两次换乘
    r = fastest_path(LINES, "西山站", "东北站")
    assert r["transfers"] == 2
    assert r["cost"] == 4.0


def test_same_station():
    r = plan_route(LINES, "中心站", "中心站")
    assert r["stations"] == ["中心站"]
    assert r["transfers"] == 0


def test_fewest_transfers_prefers_direct():
    # 构造：L2 提供 B→D 捷径（跳过 C），形成「换乘更短 vs 直达少换乘」的取舍
    lines = {"L1": ["A", "B", "C", "D", "E"], "L2": ["B", "D"]}
    fast = fastest_path(lines, "A", "E")
    few = fewest_transfers_path(lines, "A", "E")
    # 最快：A-B-D-E，3 站 2 换乘
    assert fast["cost"] == 3.0
    assert fast["transfers"] == 2
    # 最少换乘：A-B-C-D-E，0 换乘（站数更多）
    assert few["transfers"] == 0
    assert few["cost"] == 4.0


def test_unreachable_returns_none():
    lines = {"L1": ["A", "B"], "L2": ["C", "D"]}
    assert fastest_path(lines, "A", "C") is None


def test_build_graph_has_transfer_edges():
    # 中心站是 1、2 号线换乘站，跨线换乘边存在
    g = build_graph(LINES, transfer_penalty=3.0)
    assert (("中心站", "1号线"), 3.0) in g[("中心站", "2号线")]
