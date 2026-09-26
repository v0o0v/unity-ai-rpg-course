"""Small, dependency-free illustrations of the course's shared data contracts.

These functions are teaching references, NOT a Unity movement implementation.
The grid function does not validate physical body clearance; Unity adapters must
perform their own Collider2D/3D casts and device tests.
"""
from __future__ import annotations

import heapq
import math
from decimal import Decimal, ROUND_HALF_UP
from typing import Iterable

Cell = tuple[int, int]


def world2d(u: float, v: float) -> tuple[float, float, float]:
    return (u, v, 0.0)


def world3d(u: float, v: float) -> tuple[float, float, float]:
    return (u, 0.0, v)


def cell_of(u: float, v: float, size: float = 1.0,
            origin: Cell = (0, 0)) -> Cell:
    if not math.isfinite(size) or size <= 0:
        raise ValueError('cell size must be finite and positive')
    if not all(math.isfinite(x) for x in (u, v, *origin)):
        raise ValueError('coordinates must be finite')
    return (math.floor((u-origin[0])/size), math.floor((v-origin[1])/size))


def damage(raw: float, armor: float) -> int:
    if not math.isfinite(raw) or not math.isfinite(armor):
        raise ValueError('damage inputs must be finite')
    if raw <= 0:
        return 0
    value = Decimal(str(raw)) * Decimal(100) / (Decimal(100) + Decimal(str(max(0, armor))))
    return max(1, int(value.quantize(Decimal('1'), rounding=ROUND_HALF_UP)))


def progression(total_xp: int) -> tuple[int, int]:
    if isinstance(total_xp, bool) or not isinstance(total_xp, int) or total_xp < 0:
        raise ValueError('XP must be a non-negative integer')
    level, xp = 1, total_xp
    while level < 10 and xp >= 40 + 25 * (level - 1):
        xp -= 40 + 25 * (level - 1)
        level += 1
    return level, 0 if level == 10 else xp


def grid_path(width: int, height: int, blocked: Iterable[Cell],
              start: Cell, goal: Cell, max_expansions: int = 4096) -> list[Cell] | None:
    """Deterministic eight-neighbor A*: 10/14 costs, no corner cutting.

    None means no route, TimeoutError means a budget failure. For an actual game,
    inflate obstacles for actor clearance AND validate traversed edges with body
    casts. This educational point-grid function deliberately does neither.
    """
    if width <= 0 or height <= 0 or max_expansions <= 0:
        raise ValueError('dimensions and expansion budget must be positive')
    walls = set(blocked)

    def free(p: Cell) -> bool:
        return 0 <= p[0] < width and 0 <= p[1] < height and p not in walls

    if not free(start) or not free(goal):
        return None

    def heuristic(p: Cell) -> int:
        dx, dy = abs(p[0]-goal[0]), abs(p[1]-goal[1])
        return 10 * max(dx, dy) + 4 * min(dx, dy)

    h = heuristic(start)
    queue = [(h, h, start[1]*width+start[0], 0, start)]
    costs, previous, closed = {start: 0}, {}, set()
    directions = ((0, 1),(1, 0),(0, -1),(-1, 0),(1, 1),(1, -1),(-1, -1),(-1, 1))
    expanded = 0
    while queue:
        _, _, _, score, cell = heapq.heappop(queue)
        if cell in closed or score != costs[cell]:
            continue
        if cell == goal:
            route = [cell]
            while cell in previous:
                cell = previous[cell]
                route.append(cell)
            return list(reversed(route))
        if expanded >= max_expansions:
            raise TimeoutError('path request expansion budget exceeded')
        expanded += 1
        closed.add(cell)
        x, y = cell
        for dx, dy in directions:
            nxt = x+dx, y+dy
            if not free(nxt) or nxt in closed:
                continue
            if dx and dy and (not free((x+dx, y)) or not free((x, y+dy))):
                continue
            candidate = score + (14 if dx and dy else 10)
            if candidate >= costs.get(nxt, math.inf):
                continue
            costs[nxt], previous[nxt] = candidate, cell
            h = heuristic(nxt)
            heapq.heappush(queue, (candidate+h, h, nxt[1]*width+nxt[0], candidate, nxt))
    return None
