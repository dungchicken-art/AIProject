from typing import Dict, List

import networkx as nx


def serialize_path(path: List[int]) -> List[int]:
    return [int(node) for node in path]


def ensure_start_goal(graph: nx.MultiDiGraph, start: int, goal: int) -> None:
    if start not in graph:
        raise ValueError("Start node not in graph")
    if goal not in graph:
        raise ValueError("Goal node not in graph")


def summarize_steps(steps: List[dict]) -> Dict[str, int]:
    return {
        "steps": len(steps),
        "explored": len({item for step in steps for item in step.get("explored", [])}),
    }
