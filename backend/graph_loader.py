import json
from ast import literal_eval
from pathlib import Path
from typing import Dict, List, Tuple

try:
    import osmnx as ox
except ImportError:  # pragma: no cover - optional dependency
    ox = None

import networkx as nx

DATA_PATH = Path(__file__).resolve().parent.parent / "data" / "khuong_dinh.graphml"


def _load_from_graphml(path: Path) -> nx.MultiDiGraph:
    if not path.exists():
        raise FileNotFoundError("GraphML file not found")
    return ox.load_graphml(path)


def _load_from_osmnx() -> nx.MultiDiGraph:
    if ox is None:
        raise ImportError("osmnx is not installed; cannot download graph")
    return ox.graph_from_place("Khương Đình, Thanh Xuân, Hà Nội, Việt Nam", network_type="drive")


def _build_sample_graph() -> nx.MultiDiGraph:
    graph = ox.utils_graph.get_largest_component(nx.grid_graph((4, 4), create_using=nx.DiGraph())).copy() if ox else nx.grid_graph((4, 4), create_using=nx.DiGraph())
    multi_graph = nx.MultiDiGraph()
    for node, data in graph.nodes(data=True):
        y, x = node if isinstance(node, tuple) else (0.0, 0.0)
        multi_graph.add_node(node, x=float(x), y=float(y))
    for u, v in graph.edges():
        length = 1.0
        multi_graph.add_edge(u, v, length=length)
    return multi_graph


def load_graph() -> nx.MultiDiGraph:
    try:
        if DATA_PATH.exists() and ox is not None:
            graph = _load_from_graphml(DATA_PATH)
        else:
            graph = _load_from_osmnx()
    except Exception:
        graph = _build_sample_graph()

    for _, _, data in graph.edges(data=True):
        length = float(data.get("length", 1.0))
        data.setdefault("length", length)
        data["base_cost"] = length
        data["cost"] = length
    return graph
def _encode_node(node):
    return int(node) if isinstance(node, int) else str(node)


def _decode_node(node):
    if isinstance(node, (int, tuple)):
        return node
    if isinstance(node, list) and len(node) == 2:
        return tuple(node)
    try:
        parsed = literal_eval(str(node))
        return parsed
    except Exception:
        return node


def serialize_graph(graph: nx.MultiDiGraph) -> Dict[str, List[Dict]]:
    def _latlng(n):
        data = graph.nodes[n]
        return data.get("y"), data.get("x")

    nodes = [
        {"id": _encode_node(node), "lat": data.get("y"), "lng": data.get("x")}
        for node, data in graph.nodes(data=True)
    ]

    edges = []
    for u, v, data in graph.edges(data=True):
        geom = data.get("geometry")
        if geom is not None:
            coords = [(pt[1], pt[0]) for pt in geom.coords]
        else:
            coords = [_latlng(u), _latlng(v)]
        edges.append(
            {
                "u": _encode_node(u),
                "v": _encode_node(v),
                "coords": coords,
                "cost": data.get("cost", data.get("length", 1.0)),
            }
        )

    return {"nodes": nodes, "edges": edges}


def update_weight(graph: nx.MultiDiGraph, u, v, factor: float) -> float:
    u = _decode_node(u)
    v = _decode_node(v)
    edge_data = graph.get_edge_data(u, v)
    if not edge_data:
        raise ValueError("Edge does not exist")

    first_key = next(iter(edge_data))
    data = edge_data[first_key]
    base = float(data.get("base_cost", data.get("length", 1.0)))
    data["cost"] = base * factor
    return data["cost"]


def reset_weights(graph: nx.MultiDiGraph) -> None:
    for _, _, data in graph.edges(data=True):
        base = float(data.get("base_cost", data.get("length", 1.0)))
        data["cost"] = base


def nearest_node(graph: nx.MultiDiGraph, lat: float, lng: float):
    if ox is not None:
        return ox.distance.nearest_nodes(graph, lng, lat)
    best_node = None
    best_dist = float("inf")
    for node, data in graph.nodes(data=True):
        y, x = data.get("y"), data.get("x")
        if y is None or x is None:
            continue
        dist = (y - lat) ** 2 + (x - lng) ** 2
        if dist < best_dist:
            best_dist = dist
            best_node = node
    if best_node is None:
        raise ValueError("Graph has no spatial data")
    return best_node


__all__ = [
    "load_graph",
    "serialize_graph",
    "update_weight",
    "reset_weights",
    "nearest_node",
    "_encode_node",
    "_decode_node",
]
