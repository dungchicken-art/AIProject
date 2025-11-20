from __future__ import annotations

import heapq
import math
from typing import Dict, Iterable, List, Optional, Tuple

import networkx as nx


def haversine_distance(a: Tuple[float, float], b: Tuple[float, float]) -> float:
    lat1, lon1 = a
    lat2, lon2 = b
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)

    r = 6371e3
    h = (
        math.sin(dphi / 2) ** 2
        + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    )
    return 2 * r * math.atan2(math.sqrt(h), math.sqrt(1 - h))


def _reconstruct_path(parents: Dict[int, Optional[int]], current: int) -> List[int]:
    path: List[int] = [current]
    while parents[current] is not None:
        current = parents[current]
        path.append(current)
    return list(reversed(path))


def _log_step(steps: List[dict], step_idx: int, current: int, frontier: Iterable[int], explored: Iterable[int], parents: Dict[int, Optional[int]]):
    steps.append(
        {
            "step": step_idx,
            "current": current,
            "frontier": list(frontier),
            "explored": list(explored),
            "path": _reconstruct_path(parents, current),
        }
    )


def bfs_with_log(graph: nx.MultiDiGraph, start: int, goal: int) -> Tuple[List[dict], List[int]]:
    frontier: List[int] = [start]
    explored: List[int] = []
    parents: Dict[int, Optional[int]] = {start: None}
    steps: List[dict] = []
    step_idx = 0

    while frontier:
        current = frontier.pop(0)
        explored.append(current)
        _log_step(steps, step_idx, current, frontier, explored, parents)
        step_idx += 1

        if current == goal:
            return steps, _reconstruct_path(parents, current)

        for neighbor in graph.successors(current):
            if neighbor not in parents:
                parents[neighbor] = current
                frontier.append(neighbor)

    return steps, []


def dfs_with_log(graph: nx.MultiDiGraph, start: int, goal: int) -> Tuple[List[dict], List[int]]:
    frontier: List[int] = [start]
    explored: List[int] = []
    parents: Dict[int, Optional[int]] = {start: None}
    steps: List[dict] = []
    step_idx = 0

    while frontier:
        current = frontier.pop()
        if current in explored:
            continue
        explored.append(current)
        _log_step(steps, step_idx, current, frontier, explored, parents)
        step_idx += 1

        if current == goal:
            return steps, _reconstruct_path(parents, current)

        for neighbor in graph.successors(current):
            if neighbor not in parents:
                parents[neighbor] = current
                frontier.append(neighbor)

    return steps, []


def ucs_with_log(graph: nx.MultiDiGraph, start: int, goal: int) -> Tuple[List[dict], List[int]]:
    frontier: List[Tuple[float, int]] = [(0.0, start)]
    explored: List[int] = []
    parents: Dict[int, Optional[int]] = {start: None}
    costs: Dict[int, float] = {start: 0.0}
    steps: List[dict] = []
    step_idx = 0

    while frontier:
        cost, current = heapq.heappop(frontier)
        if current in explored:
            continue
        explored.append(current)
        _log_step(steps, step_idx, current, [node for _, node in frontier], explored, parents)
        step_idx += 1

        if current == goal:
            return steps, _reconstruct_path(parents, current)

        for _, neighbor, edge_data in graph.out_edges(current, data=True):
            edge_cost = float(edge_data.get("cost", 1.0))
            new_cost = cost + edge_cost
            if neighbor not in costs or new_cost < costs[neighbor]:
                costs[neighbor] = new_cost
                parents[neighbor] = current
                heapq.heappush(frontier, (new_cost, neighbor))

    return steps, []


def astar_with_log(graph: nx.MultiDiGraph, start: int, goal: int) -> Tuple[List[dict], List[int]]:
    return _best_first_search(graph, start, goal, use_heuristic=True, greedy_only=False)


def greedy_with_log(graph: nx.MultiDiGraph, start: int, goal: int) -> Tuple[List[dict], List[int]]:
    return _best_first_search(graph, start, goal, use_heuristic=True, greedy_only=True)


def _best_first_search(
    graph: nx.MultiDiGraph,
    start: int,
    goal: int,
    use_heuristic: bool,
    greedy_only: bool,
) -> Tuple[List[dict], List[int]]:
    nodes = graph.nodes
    frontier: List[Tuple[float, int]] = [(0.0, start)]
    explored: List[int] = []
    parents: Dict[int, Optional[int]] = {start: None}
    g_costs: Dict[int, float] = {start: 0.0}
    steps: List[dict] = []
    step_idx = 0

    goal_coords = (nodes[goal]["y"], nodes[goal]["x"])

    while frontier:
        _, current = heapq.heappop(frontier)
        if current in explored:
            continue
        explored.append(current)
        _log_step(steps, step_idx, current, [node for _, node in frontier], explored, parents)
        step_idx += 1

        if current == goal:
            return steps, _reconstruct_path(parents, current)

        current_cost = g_costs[current]
        for _, neighbor, edge_data in graph.out_edges(current, data=True):
            edge_cost = float(edge_data.get("cost", 1.0))
            g_score = current_cost + edge_cost
            if greedy_only:
                g_score = 0.0
            if neighbor not in g_costs or g_score < g_costs[neighbor]:
                g_costs[neighbor] = g_score if not greedy_only else current_cost
                parents[neighbor] = current
                priority = g_costs[neighbor]
                if use_heuristic:
                    neighbor_coords = (nodes[neighbor]["y"], nodes[neighbor]["x"])
                    heuristic = haversine_distance(neighbor_coords, goal_coords)
                    priority += heuristic
                heapq.heappush(frontier, (priority, neighbor))

    return steps, []
