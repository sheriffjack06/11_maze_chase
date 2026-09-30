import random
from collections import deque

import pygame

CELL = 44
WALL_THICKNESS = 4     # collision thickness of a wall (drawn line is 3px)
LOOP_CHANCE = 0.25     # chance to knock out each remaining interior wall

# Wall indices per cell: 0 = top, 1 = bottom, 2 = right, 3 = left


def generate_maze(cols, rows, loop_chance=LOOP_CHANCE):
    visited = [[False] * cols for _ in range(rows)]
    walls = [[[True, True, True, True] for _ in range(cols)] for _ in range(rows)]

    def neighbors(r, c):
        dirs = [(-1, 0, 0, 1), (1, 0, 1, 0), (0, 1, 2, 3), (0, -1, 3, 2)]
        res = []
        for dr, dc, wd, od in dirs:
            nr, nc = r + dr, c + dc
            if 0 <= nr < rows and 0 <= nc < cols and not visited[nr][nc]:
                res.append((nr, nc, wd, od))
        return res

    # 1) Depth-first carve: gives a "perfect" maze (exactly one path between cells)
    stack = [(0, 0)]
    visited[0][0] = True
    while stack:
        r, c = stack[-1]
        nbrs = neighbors(r, c)
        if nbrs:
            nr, nc, wd, od = random.choice(nbrs)
            walls[r][c][wd] = False
            walls[nr][nc][od] = False
            visited[nr][nc] = True
            stack.append((nr, nc))
        else:
            stack.pop()

    # 2) Braid: remove extra interior walls so the maze has loops / multiple routes.
    #    Outer border walls are never touched.
    for r in range(rows):
        for c in range(cols):
            if c < cols - 1 and walls[r][c][2] and random.random() < loop_chance:
                walls[r][c][2] = False
                walls[r][c + 1][3] = False
            if r < rows - 1 and walls[r][c][1] and random.random() < loop_chance:
                walls[r][c][1] = False
                walls[r + 1][c][0] = False
    return walls


def build_wall_rects(walls, rows, cols):
    """Solid rectangles for every wall segment (used for collision)."""
    t = WALL_THICKNESS
    h = t // 2
    segs = set()  # set removes the duplicates from walls shared by two cells
    for r in range(rows):
        for c in range(cols):
            x, y = c * CELL, r * CELL
            w = walls[r][c]
            if w[0]: segs.add((x - h, y - h, CELL + t, t))
            if w[1]: segs.add((x - h, y + CELL - h, CELL + t, t))
            if w[2]: segs.add((x + CELL - h, y - h, t, CELL + t))
            if w[3]: segs.add((x - h, y - h, t, CELL + t))
    return [pygame.Rect(*s) for s in segs]


def bfs(walls, start, goal, rows, cols):
    """Return next step direction (dr, dc) from start toward goal using BFS."""
    sr, sc = start
    gr, gc = goal
    queue = deque([(sr, sc, [])])
    visited = {(sr, sc)}
    dir_map = {0: (-1, 0), 1: (1, 0), 2: (0, 1), 3: (0, -1)}
    while queue:
        r, c, path = queue.popleft()
        if r == gr and c == gc:
            return path[0] if path else None
        for d, (dr, dc) in dir_map.items():
            if not walls[r][c][d]:
                nr, nc = r + dr, c + dc
                if (nr, nc) not in visited and 0 <= nr < rows and 0 <= nc < cols:
                    visited.add((nr, nc))
                    queue.append((nr, nc, path + [(dr, dc)]))
    return None
