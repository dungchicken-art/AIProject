import json
from dataclasses import dataclass
from typing import Dict, List, Tuple

import networkx as nx
import osmnx as ox
from shapely.geometry import LineString


@dataclass
class GraphState:
    graph: nx.MultiDiGraph
    base_costs: Dict[Tuple[int, int, int], float]


_state: GraphState | None = None


def load_graph(place_name: str = "Khương Đình, Thanh Xuân, Hà Nội, Việt Nam") -> None:
    """Load the OSM graph for the given place and cache base edge costs."""
    global _state
    if _state is not None:
        return

    graph = ox.graph_from_place(place_name, network_type="drive")
    base_costs: Dict[Tuple[int, int, int], float] = {}

    for u, v, key, data in graph.edges(keys=True, data=True):
        length = float(data.get("length", 1.0))
        data["cost"] = length
        base_costs[(u, v, key)] = length

    _state = GraphState(graph=graph, base_costs=base_costs)


def get_graph() -> nx.MultiDiGraph:
    if _state is None:
        load_graph()
    assert _state is not None
    return _state.graph


def reset_weights() -> None:
    """Reset edge costs to the original length-based cost."""
    if _state is None:
        return
    for (u, v, key), base_cost in _state.base_costs.items():
        if get_graph().has_edge(u, v, key=key):
            get_graph()[u][v][key]["cost"] = base_cost


def update_weight(u: int, v: int, factor: float) -> None:
    """Update the weight of all edges between two nodes by a multiplier."""
    graph = get_graph()
    if not graph.has_edge(u, v) and not graph.has_edge(v, u):
        raise ValueError(f"No edge between {u} and {v}")
    for key in graph[u][v]:
        base_cost = _state.base_costs.get((u, v, key))
        if base_cost is None:
            base_cost = float(graph[u][v][key].get("length", 1.0))
            _state.base_costs[(u, v, key)] = base_cost
        graph[u][v][key]["cost"] = base_cost * factor

    # Mirror direction if present
    if graph.has_edge(v, u):
        for key in graph[v][u]:
            base_cost = _state.base_costs.get((v, u, key))
            if base_cost is None:
                base_cost = float(graph[v][u][key].get("length", 1.0))
                _state.base_costs[(v, u, key)] = base_cost
            graph[v][u][key]["cost"] = base_cost * factor


def nearest_node(lat: float, lng: float) -> int:
    graph = get_graph()
    return int(ox.distance.nearest_nodes(graph, lng, lat))


def _edge_geometry(u: int, v: int, data: dict) -> List[Tuple[float, float]]:
    if "geometry" in data and isinstance(data["geometry"], LineString):
        coords = list(data["geometry"].coords)
        return [(lat, lng) for lng, lat in coords]
    return [(data["y"] if "y" in data else get_graph().nodes[u]["y"],
             data["x"] if "x" in data else get_graph().nodes[u]["x"]),
            (get_graph().nodes[v]["y"], get_graph().nodes[v]["x"])]


def graph_to_json() -> dict:
    graph = get_graph()
    nodes = [
        {"id": int(node), "lat": float(data["y"]), "lng": float(data["x"])}
        for node, data in graph.nodes(data=True)
    ]

    edges = []
    for u, v, key, data in graph.edges(keys=True, data=True):
        geometry = _edge_geometry(u, v, data)
        edges.append(
            {
                "u": int(u),
                "v": int(v),
                "key": int(key),
                "geometry": geometry,
                "cost": float(data.get("cost", data.get("length", 1.0))),
            }
        )

    return {"nodes": nodes, "edges": edges}


def export_graph_json(path: str) -> None:
    with open(path, "w", encoding="utf-8") as f:
        json.dump(graph_to_json(), f, ensure_ascii=False)
