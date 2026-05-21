"""Lightweight TSP tour builders for the routing port (no staging required)."""
from __future__ import annotations

import math
from typing import Sequence


def tour_cost(cities: Sequence[tuple[float, float]], tour: Sequence[int]) -> float:
    if len(tour) < 2:
        return 0.0
    total = 0.0
    for i in range(len(tour) - 1):
        a, b = tour[i], tour[i + 1]
        total += math.dist(cities[a], cities[b])
    return total


def nearest_neighbor_tour(cities: Sequence[tuple[float, float]], start: int = 0) -> list[int]:
    n = len(cities)
    if n == 0:
        return []
    if n == 1:
        return [0]
    unvisited = set(range(n))
    unvisited.remove(start)
    tour = [start]
    current = start
    while unvisited:
        nxt = min(unvisited, key=lambda j: math.dist(cities[current], cities[j]))
        unvisited.remove(nxt)
        tour.append(nxt)
        current = nxt
    tour.append(start)
    return tour
