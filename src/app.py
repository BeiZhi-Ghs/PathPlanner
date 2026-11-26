"""PathPlanner 图形界面（Pygame）。

运行：python app.py
两个模式（顶部 tab 切换）：
- 迷宫寻路：生成迷宫（递归回溯 / Prim）+ BFS/DFS/Dijkstra/A* 求解动画 + 统计
- 地铁规划：点击选择起终点，展示「最快路径」与「最少换乘」两条路线
"""

from __future__ import annotations

import os
import random
from typing import Optional

import pygame

from graph import search
from maze import Maze, generate_backtracker, generate_prim, manhattan
from metro import fastest_path, fewest_transfers_path, load_metro

WIDTH, HEIGHT = 1000, 660

# 颜色
BG = (247, 247, 249)
PANEL = (233, 233, 238)
WALL = (58, 58, 64)
TEXT = (32, 32, 36)
MUTED = (120, 120, 126)
VISITED = (173, 216, 230)
PATH = (255, 200, 60)
START_C = (40, 170, 90)
GOAL_C = (220, 70, 70)
BUTTON = (205, 208, 214)
BUTTON_ACTIVE = (80, 130, 210)
LINE_COLORS = {
    "1号线": (220, 70, 70),
    "2号线": (70, 120, 220),
    "3号线": (60, 160, 95),
    "4号线": (160, 90, 200),
}

MAZE_ALGOS = ["bfs", "dfs", "dijkstra", "astar"]
MAZE_ALGO_LABELS = {"bfs": "BFS", "dfs": "DFS", "dijkstra": "Dijkstra", "astar": "A*"}
GENS = ["backtracker", "prim"]
GEN_LABELS = {"backtracker": "递归回溯", "prim": "随机 Prim"}

DATA_PATH = os.path.join(os.path.dirname(__file__), "data", "metro.json")

_font_cache = {}
_FONT_CANDIDATES = [
    "C:/Windows/Fonts/msyh.ttc",
    "C:/Windows/Fonts/simhei.ttf",
    "C:/Windows/Fonts/simsun.ttc",
]


def font(size: int) -> pygame.font.Font:
    if size not in _font_cache:
        f = None
        for path in _FONT_CANDIDATES:
            if os.path.exists(path):
                try:
                    f = pygame.font.Font(path, size)
                    break
                except Exception:
                    continue
        if f is None:
            f = pygame.font.Font(None, size)
        _font_cache[size] = f
    return _font_cache[size]


class App:
    def __init__(self) -> None:
        pygame.init()
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("PathPlanner — 图最短路径可视化与规划")
        self.clock = pygame.time.Clock()
        self.running = True
        self.mode = "maze"  # "maze" | "metro"

        # ---- 迷宫状态 ----
        self.maze: Optional[Maze] = None
        self.gen = "backtracker"
        self.algo = "astar"
        self.maze_visited: list = []
        self.maze_path: list = []
        self.maze_cost = 0.0
        self.maze_explored = 0
        self.anim_frame = 0
        self.new_maze()

        # ---- 地铁状态 ----
        data = load_metro(DATA_PATH)
        self.lines = data["lines"]
        self.coords = data["coords"]
        self.start_station: Optional[str] = None
        self.goal_station: Optional[str] = None
        self.metro_fast: Optional[dict] = None
        self.metro_few: Optional[dict] = None

    # ================= 迷宫 =================
    def new_maze(self) -> None:
        self.maze = Maze(21, 21)
        if self.gen == "backtracker":
            generate_backtracker(self.maze)
        else:
            generate_prim(self.maze)
        self.maze_visited = []
        self.maze_path = []
        self.anim_frame = 0

    def solve_maze(self) -> None:
        if self.maze is None:
            return
        g = self.maze.to_graph()
        start, goal = (0, 0), (self.maze.rows - 1, self.maze.cols - 1)
        if self.algo == "astar":
            res = search(g, start, goal, "astar", heuristic=manhattan)
        else:
            res = search(g, start, goal, self.algo)
        self.maze_visited = res.visited
        self.maze_path = res.path or []
        self.maze_cost = res.cost
        self.maze_explored = res.explored
        self.anim_frame = 0

    # ================= 地铁 =================
    def solve_metro(self) -> None:
        if self.start_station and self.goal_station:
            self.metro_fast = fastest_path(self.lines, self.start_station, self.goal_station)
            self.metro_few = fewest_transfers_path(self.lines, self.start_station, self.goal_station)

    # ================= 主循环 =================
    def run(self) -> None:
        while self.running:
            self.handle_events()
            self.update()
            self.render(self.screen)
            pygame.display.flip()
            self.clock.tick(60)
        pygame.quit()

    def handle_events(self) -> None:
        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                self.running = False
            elif e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
                self.on_click(e.pos)

    def update(self) -> None:
        if self.mode == "maze" and self.maze_visited:
            # 动画逐步展开搜索过程，随后展示路径
            if self.anim_frame < len(self.maze_visited) + len(self.maze_path):
                self.anim_frame += 2

    def on_click(self, pos) -> None:
        x, y = pos
        # 顶部 tab（按实际按钮矩形判定）
        if y < 40:
            if pygame.Rect(170, 5, 150, 30).collidepoint(x, y):
                self.mode = "metro"
            elif pygame.Rect(10, 5, 150, 30).collidepoint(x, y):
                self.mode = "maze"
            return
        if self.mode == "maze":
            self._maze_click(x, y)
        else:
            self._metro_click(x, y)

    def _maze_click(self, x, y) -> None:
        # 右侧面板按钮
        if x < WIDTH - 200:
            return
        r = pygame.Rect(WIDTH - 180, 80, 160, 34)
        if r.collidepoint(x, y):
            self.gen = GENS[(GENS.index(self.gen) + 1) % len(GENS)]
            self.new_maze()
            return
        r2 = pygame.Rect(WIDTH - 180, 124, 160, 34)
        if r2.collidepoint(x, y):
            self.algo = MAZE_ALGOS[(MAZE_ALGOS.index(self.algo) + 1) % len(MAZE_ALGOS)]
            return
        r3 = pygame.Rect(WIDTH - 180, 168, 160, 34)
        if r3.collidepoint(x, y):
            self.solve_maze()
            return
        r4 = pygame.Rect(WIDTH - 180, 212, 160, 34)
        if r4.collidepoint(x, y):
            self.new_maze()
            return

    def _metro_click(self, x, y) -> None:
        station = self._nearest_station(x, y)
        if station is None:
            return
        if self.start_station is None:
            self.start_station = station
        elif self.goal_station is None and station != self.start_station:
            self.goal_station = station
            self.solve_metro()
        else:
            self.start_station = station
            self.goal_station = None
            self.metro_fast = self.metro_few = None

    def _nearest_station(self, x, y) -> Optional[str]:
        best, best_d = None, 1e9
        for s, (cx, cy) in self._station_screen_pos().items():
            d = (x - cx) ** 2 + (y - cy) ** 2
            if d < best_d:
                best, best_d = s, d
        return best if best_d <= 20 ** 2 else None

    # ================= 渲染 =================
    def render(self, screen) -> None:
        screen.fill(BG)
        self._draw_tabs(screen)
        if self.mode == "maze":
            self._draw_maze_mode(screen)
        else:
            self._draw_metro_mode(screen)

    def _draw_tabs(self, screen) -> None:
        pygame.draw.rect(screen, PANEL, (0, 0, WIDTH, 40))
        self._draw_button(screen, pygame.Rect(10, 5, 150, 30), "迷宫寻路", self.mode == "maze")
        self._draw_button(screen, pygame.Rect(170, 5, 150, 30), "地铁规划", self.mode == "metro")

    def _draw_button(self, screen, rect, text, active=False) -> None:
        color = BUTTON_ACTIVE if active else BUTTON
        pygame.draw.rect(screen, color, rect, border_radius=6)
        t = font(16).render(text, True, (255, 255, 255) if active else TEXT)
        screen.blit(t, t.get_rect(center=rect.center))

    def _draw_maze_mode(self, screen) -> None:
        if self.maze is None:
            return
        rows, cols = self.maze.rows, self.maze.cols
        area = min(HEIGHT - 80, WIDTH - 240)
        cell = area // rows
        ox = (WIDTH - 240 - rows * cell) // 2
        oy = 60

        # visited 与 path 填充
        shown = self.anim_frame
        for i, node in enumerate(self.maze_visited):
            if i < shown:
                r, c = node
                pygame.draw.rect(
                    screen, VISITED, (ox + c * cell + 1, oy + r * cell + 1, cell - 2, cell - 2)
                )
        if shown >= len(self.maze_visited):
            for node in self.maze_path:
                r, c = node
                pygame.draw.rect(
                    screen, PATH, (ox + c * cell + 1, oy + r * cell + 1, cell - 2, cell - 2)
                )
        # 起点 / 终点
        pygame.draw.rect(screen, START_C, (ox + 1, oy + 1, cell - 2, cell - 2))
        pygame.draw.rect(
            screen, GOAL_C,
            (ox + (cols - 1) * cell + 1, oy + (rows - 1) * cell + 1, cell - 2, cell - 2),
        )
        # 墙
        for r in range(rows):
            for c in range(cols):
                x, y = ox + c * cell, oy + r * cell
                w = self.maze.walls[r][c]
                if w & 1:
                    pygame.draw.line(screen, WALL, (x, y), (x + cell, y), 2)
                if w & 2:
                    pygame.draw.line(screen, WALL, (x, y + cell), (x + cell, y + cell), 2)
                if w & 4:
                    pygame.draw.line(screen, WALL, (x + cell, y), (x + cell, y + cell), 2)
                if w & 8:
                    pygame.draw.line(screen, WALL, (x, y), (x, y + cell), 2)

        # 右侧面板
        self._draw_maze_panel(screen)

    def _draw_maze_panel(self, screen) -> None:
        px = WIDTH - 180
        self._draw_button(screen, pygame.Rect(px, 80, 160, 34), "生成: " + GEN_LABELS[self.gen])
        self._draw_button(screen, pygame.Rect(px, 124, 160, 34), "算法: " + MAZE_ALGO_LABELS[self.algo])
        self._draw_button(screen, pygame.Rect(px, 168, 160, 34), "求解")
        self._draw_button(screen, pygame.Rect(px, 212, 160, 34), "重新生成")

        lines = [
            "统计",
            f"访问节点: {self.maze_explored}",
            f"路径长度: {len(self.maze_path)}",
            f"路径代价: {self.maze_cost:.0f}",
            "",
            "绿=起点 红=终点",
            "黄=路径 蓝=探索",
        ]
        y = 280
        for i, txt in enumerate(lines):
            color = MUTED if i == 0 or txt == "" else TEXT
            t = font(15 if i else 18).render(txt, True, color)
            screen.blit(t, (px, y))
            y += 30

    def _station_screen_pos(self):
        xs = [c[0] for c in self.coords.values()]
        ys = [c[1] for c in self.coords.values()]
        minx, maxx = min(xs), max(xs)
        miny, maxy = min(ys), max(ys)
        pad = 60
        scale_x = (WIDTH - 2 * pad) / max(1, maxx - minx)
        scale_y = (HEIGHT - 140) / max(1, maxy - miny)
        scale = min(scale_x, scale_y)
        cx0 = (WIDTH - (maxx - minx) * scale) / 2
        cy0 = 60 + (HEIGHT - 140 - (maxy - miny) * scale) / 2
        return {
            s: (cx0 + (x - minx) * scale, cy0 + (y - miny) * scale)
            for s, (x, y) in self.coords.items()
        }

    def _draw_metro_mode(self, screen) -> None:
        pos = self._station_screen_pos()
        # 线路
        for line, stations in self.lines.items():
            pts = [pos[s] for s in stations]
            pygame.draw.lines(screen, LINE_COLORS.get(line, (150, 150, 150)), False, pts, 5)
        # 高亮路径
        if self.metro_fast:
            pts = [pos[s] for s in self.metro_fast["stations"]]
            pygame.draw.lines(screen, (30, 160, 70), False, pts, 10)
        if self.metro_few:
            pts = [pos[s] for s in self.metro_few["stations"]]
            pygame.draw.lines(screen, (240, 150, 30), False, pts, 10)
        # 站点
        transfer = set()
        station_lines = {}
        for line, stations in self.lines.items():
            for s in stations:
                station_lines.setdefault(s, []).append(line)
        for s, ls in station_lines.items():
            if len(ls) >= 2:
                transfer.add(s)
        for s, (x, y) in pos.items():
            r = 9 if s in transfer else 6
            color = (255, 255, 255) if s in transfer else LINE_COLORS[station_lines[s][0]]
            pygame.draw.circle(screen, color, (int(x), int(y)), r)
            pygame.draw.circle(screen, (60, 60, 60), (int(x), int(y)), r, 2)
            t = font(13).render(s, True, TEXT)
            screen.blit(t, (x + 10, y - 8))
        # 起终点
        if self.start_station:
            x, y = pos[self.start_station]
            pygame.draw.circle(screen, START_C, (int(x), int(y)), 12, 3)
        if self.goal_station:
            x, y = pos[self.goal_station]
            pygame.draw.circle(screen, GOAL_C, (int(x), int(y)), 12, 3)

        # 底部说明
        info = "点击站点选择起点 → 再点选终点"
        if self.start_station and not self.goal_station:
            info = f"起点: {self.start_station}，请点击终点"
        t = font(16).render(info, True, TEXT)
        screen.blit(t, (60, HEIGHT - 55))
        if self.metro_fast and self.metro_few:
            fast = self.metro_fast
            few = self.metro_few
            txt = (
                f"最快(绿): {len(fast['stations']) - 1} 站 / {fast['transfers']} 次换乘   |   "
                f"最少换乘(橙): {len(few['stations']) - 1} 站 / {few['transfers']} 次换乘"
            )
            t2 = font(15).render(txt, True, TEXT)
            screen.blit(t2, (60, HEIGHT - 30))
        # 图例
        leg = "图例: 绿=最快路径  橙=最少换乘  大圆点=换乘站"
        t3 = font(13).render(leg, True, MUTED)
        screen.blit(t3, (WIDTH - 360, HEIGHT - 40))


def main() -> None:
    App().run()


if __name__ == "__main__":
    main()
