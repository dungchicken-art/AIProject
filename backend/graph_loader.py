import json
from ast import literal_eval
from math import cos, radians, sqrt
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

    if ox is not None and hasattr(ox, "load_graphml"):
        return ox.load_graphml(path)

    # Fallback to pure networkx loading so we do not require OSMnx utilities
    graph = nx.read_graphml(path)
    if not isinstance(graph, nx.MultiDiGraph):
        graph = nx.MultiDiGraph(graph)
    return graph


def _load_from_osmnx() -> nx.MultiDiGraph:
    if ox is None or not hasattr(ox, "graph_from_place"):
        raise ImportError("osmnx is not installed; cannot download graph")
    return ox.graph_from_place("Khương Đình, Thanh Xuân, Hà Nội, Việt Nam", network_type="drive")


def _build_sample_graph(rows: int = 14, cols: int = 14) -> nx.MultiDiGraph:
    """Build a geospatial grid centered on Khương Đình so nodes appear on the map."""

    # Bounding box roughly covering Khương Đình so markers render in the right place
    lat_min, lat_max = 20.9965, 21.0045
    lng_min, lng_max = 105.808, 105.823

    lat_step = (lat_max - lat_min) / max(rows - 1, 1)
    lng_step = (lng_max - lng_min) / max(cols - 1, 1)

    def edge_length(lat1, lng1, lat2, lng2):
        dlat = lat2 - lat1
        dlng = lng2 - lng1
        mean_lat = radians((lat1 + lat2) / 2)
        return sqrt((dlat * 111_000) ** 2 + (dlng * 111_320 * cos(mean_lat)) ** 2)

    graph = nx.MultiDiGraph()

    for r in range(rows):
        for c in range(cols):
            lat = lat_min + r * lat_step
            lng = lng_min + c * lng_step
            graph.add_node((r, c), x=lng, y=lat)

    for r in range(rows):
        for c in range(cols):
            if c + 1 < cols:
                u, v = (r, c), (r, c + 1)
                lat1, lng1 = graph.nodes[u]["y"], graph.nodes[u]["x"]
                lat2, lng2 = graph.nodes[v]["y"], graph.nodes[v]["x"]
                length = edge_length(lat1, lng1, lat2, lng2)
                graph.add_edge(u, v, length=length)
                graph.add_edge(v, u, length=length)
            if r + 1 < rows:
                u, v = (r, c), (r + 1, c)
                lat1, lng1 = graph.nodes[u]["y"], graph.nodes[u]["x"]
                lat2, lng2 = graph.nodes[v]["y"], graph.nodes[v]["x"]
                length = edge_length(lat1, lng1, lat2, lng2)
                graph.add_edge(u, v, length=length)
                graph.add_edge(v, u, length=length)

    return graph


def load_graph() -> nx.MultiDiGraph:
    try:
        if DATA_PATH.exists():
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
