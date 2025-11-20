from __future__ import annotations

import json
from typing import Callable, Dict

from flask import Flask, jsonify, request
from flask_cors import CORS

from .algorithms import (
    astar_with_log,
    bfs_with_log,
    dfs_with_log,
    greedy_with_log,
    ucs_with_log,
)
from .graph_loader import _decode_node, _encode_node, load_graph, nearest_node, reset_weights, serialize_graph, update_weight

app = Flask(__name__)
CORS(app)

graph = load_graph()


ALGORITHMS: Dict[str, Callable] = {
    "bfs": bfs_with_log,
    "dfs": dfs_with_log,
    "ucs": ucs_with_log,
    "astar": astar_with_log,
    "greedy": greedy_with_log,
}


@app.route("/init_graph", methods=["GET"])
def init_graph():
    return jsonify(serialize_graph(graph))


@app.route("/nearest", methods=["GET"])
def nearest():
    lat = float(request.args.get("lat"))
    lng = float(request.args.get("lng"))
    node = nearest_node(graph, lat, lng)
    return jsonify({"node": _encode_node(node)})


@app.route("/mark_edge", methods=["POST"])
def mark_edge():
    payload = request.get_json(force=True)
    u = payload.get("u")
    v = payload.get("v")
    mark_type = payload.get("type", "jam")
    factor = 10 if mark_type == "flood" else 5
    cost = update_weight(graph, u, v, factor)
    return jsonify({"u": u, "v": v, "factor": factor, "new_cost": cost})


@app.route("/reset_weights", methods=["GET"])
def reset():
    reset_weights(graph)
    return jsonify({"status": "ok"})


@app.route("/run/<algo>", methods=["GET"])
def run(algo: str):
    start = request.args.get("start")
    goal = request.args.get("goal")
    if algo not in ALGORITHMS:
        return jsonify({"error": "Unknown algorithm"}), 400
    if start is None or goal is None:
        return jsonify({"error": "Missing start or goal"}), 400

    steps, final_path = ALGORITHMS[algo](graph, _cast_node(start), _cast_node(goal))
    return jsonify({"steps": steps, "final_path": final_path})


def _cast_node(value: str):
    try:
        return _decode_node(value)
    except Exception:
        return value


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
