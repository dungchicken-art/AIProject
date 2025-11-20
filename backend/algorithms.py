from __future__ import annotations

import heapq
from typing import Dict, List, Tuple

import networkx as nx

Step = Dict[str, object]


def _reconstruct_path(came_from: Dict, start, goal) -> List:
    if goal not in came_from and goal != start:
        return []
    path = [goal]
    while path[-1] != start:
        path.append(came_from[path[-1]])
    path.reverse()
    return path


def _log_step(step_idx: int, current, frontier, explored, path) -> Step:
    return {
        "step": step_idx,
        "current": current,
        "frontier": list(frontier),
        "explored": list(explored),
        "path": list(path),
    }


def bfs_with_log(graph: nx.MultiDiGraph, start, goal):
    from collections import deque

    queue = deque([start])
    explored = set()
    came_from = {start: start}
    steps: List[Step] = []
    step_idx = 0

    while queue:
        current = queue.popleft()
        explored.add(current)
        steps.append(_log_step(step_idx, current, queue, explored, _reconstruct_path(came_from, start, current)))
        step_idx += 1
        if current == goal:
            break
        for neighbor in graph.neighbors(current):
            if neighbor not in explored and neighbor not in queue:
                came_from[neighbor] = current
                queue.append(neighbor)

    final_path = _reconstruct_path(came_from, start, goal)
    return steps, final_path


def dfs_with_log(graph: nx.MultiDiGraph, start, goal):
    stack = [start]
    explored = set()
    came_from = {start: start}
    steps: List[Step] = []
    step_idx = 0

    while stack:
        current = stack.pop()
        if current in explored:
            continue
        explored.add(current)
        steps.append(_log_step(step_idx, current, stack, explored, _reconstruct_path(came_from, start, current)))
        step_idx += 1
        if current == goal:
            break
        for neighbor in reversed(list(graph.neighbors(current))):
            if neighbor not in explored:
                came_from.setdefault(neighbor, current)
                stack.append(neighbor)

    final_path = _reconstruct_path(came_from, start, goal)
    return steps, final_path


def ucs_with_log(graph: nx.MultiDiGraph, start, goal):
    frontier: List[Tuple[float, object]] = [(0, start)]
    explored = set()
    came_from = {start: start}
    cost_so_far = {start: 0}
    steps: List[Step] = []
    step_idx = 0

    while frontier:
        cost, current = heapq.heappop(frontier)
        if current in explored:
            continue
        explored.add(current)
        steps.append(_log_step(step_idx, current, [n for _, n in frontier], explored, _reconstruct_path(came_from, start, current)))
        step_idx += 1
        if current == goal:
            break
        for neighbor in graph.neighbors(current):
            weight = min(data.get("cost", data.get("length", 1.0)) for data in graph.get_edge_data(current, neighbor).values())
            new_cost = cost_so_far[current] + weight
            if neighbor not in cost_so_far or new_cost < cost_so_far[neighbor]:
                cost_so_far[neighbor] = new_cost
                came_from[neighbor] = current
                heapq.heappush(frontier, (new_cost, neighbor))

    final_path = _reconstruct_path(came_from, start, goal)
    return steps, final_path


def _heuristic(graph: nx.MultiDiGraph, node, goal):
    y1, x1 = graph.nodes[node].get("y", 0.0), graph.nodes[node].get("x", 0.0)
    y2, x2 = graph.nodes[goal].get("y", 0.0), graph.nodes[goal].get("x", 0.0)
    return abs(y1 - y2) + abs(x1 - x2)


def astar_with_log(graph: nx.MultiDiGraph, start, goal):
    frontier: List[Tuple[float, object]] = [(0, start)]
    came_from = {start: start}
    cost_so_far = {start: 0}
    explored = set()
    steps: List[Step] = []
    step_idx = 0

    while frontier:
        _, current = heapq.heappop(frontier)
        if current in explored:
            continue
        explored.add(current)
        steps.append(_log_step(step_idx, current, [n for _, n in frontier], explored, _reconstruct_path(came_from, start, current)))
        step_idx += 1
        if current == goal:
            break
        for neighbor in graph.neighbors(current):
            weight = min(data.get("cost", data.get("length", 1.0)) for data in graph.get_edge_data(current, neighbor).values())
            new_cost = cost_so_far[current] + weight
            if neighbor not in cost_so_far or new_cost < cost_so_far[neighbor]:
                cost_so_far[neighbor] = new_cost
                came_from[neighbor] = current
                priority = new_cost + _heuristic(graph, neighbor, goal)
                heapq.heappush(frontier, (priority, neighbor))

    final_path = _reconstruct_path(came_from, start, goal)
    return steps, final_path


def greedy_with_log(graph: nx.MultiDiGraph, start, goal):
    frontier: List[Tuple[float, object]] = [(0, start)]
    came_from = {start: start}
    explored = set()
    steps: List[Step] = []
    step_idx = 0

    while frontier:
        _, current = heapq.heappop(frontier)
        if current in explored:
            continue
        explored.add(current)
        steps.append(_log_step(step_idx, current, [n for _, n in frontier], explored, _reconstruct_path(came_from, start, current)))
        step_idx += 1
        if current == goal:
            break
        for neighbor in graph.neighbors(current):
            if neighbor in explored:
                continue
            came_from.setdefault(neighbor, current)
            priority = _heuristic(graph, neighbor, goal)
            heapq.heappush(frontier, (priority, neighbor))

    final_path = _reconstruct_path(came_from, start, goal)
    return steps, final_path


__all__ = [
    "bfs_with_log",
    "dfs_with_log",
    "ucs_with_log",
    "astar_with_log",
    "greedy_with_log",
]
