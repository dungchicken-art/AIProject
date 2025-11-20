from __future__ import annotations

from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS

from . import algorithms
from .graph_loader import get_graph, graph_to_json, load_graph, nearest_node, reset_weights, update_weight
from .utils import ensure_start_goal, serialize_path, summarize_steps

app = Flask(__name__, static_folder="../frontend", static_url_path="")
CORS(app)


@app.before_first_request
def init_graph() -> None:
    load_graph()


@app.route("/")
def serve_index():
    return send_from_directory(app.static_folder, "index.html")


@app.route("/init_graph", methods=["GET"])
def init_graph_route():
    graph_json = graph_to_json()
    return jsonify(graph_json)


@app.route("/nearest", methods=["GET"])
def nearest_route():
    lat = float(request.args.get("lat", 0))
    lng = float(request.args.get("lng", 0))
    node_id = nearest_node(lat, lng)
    return jsonify({"node": node_id})


@app.route("/mark_edge", methods=["POST"])
def mark_edge_route():
    payload = request.get_json(force=True)
    u = int(payload.get("u"))
    v = int(payload.get("v"))
    marker_type = payload.get("type", "jam")

    factor = 5 if marker_type == "jam" else 10
    try:
        update_weight(u, v, factor)
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400

    return jsonify({"status": "updated", "u": u, "v": v, "factor": factor})


@app.route("/run/<algo>", methods=["GET"])
def run_algo(algo: str):
    start = int(request.args.get("start"))
    goal = int(request.args.get("goal"))
    graph = get_graph()
    ensure_start_goal(graph, start, goal)

    algo_map = {
        "bfs": algorithms.bfs_with_log,
        "dfs": algorithms.dfs_with_log,
        "ucs": algorithms.ucs_with_log,
        "astar": algorithms.astar_with_log,
        "greedy": algorithms.greedy_with_log,
    }

    if algo not in algo_map:
        return jsonify({"error": "Unknown algorithm"}), 400

    steps, final_path = algo_map[algo](graph, start, goal)
    return jsonify(
        {
            "steps": steps,
            "final_path": serialize_path(final_path),
            "summary": summarize_steps(steps),
        }
    )


@app.route("/reset_weights", methods=["GET"])
def reset_weights_route():
    reset_weights()
    return jsonify({"status": "reset"})


if __name__ == "__main__":
    app.run(debug=True)
