const map = L.map("map").setView([21.0, 105.8], 15);
L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
  attribution: "© OpenStreetMap",
}).addTo(map);

const state = {
  start: null,
  goal: null,
  pendingEdgeNode: null,
  edgeType: "jam",
  nodes: {},
  edges: [],
  polylines: new Map(),
  nodeMarkers: new Map(),
  markers: {},
  animation: null,
  layers: {
    edges: L.layerGroup().addTo(map),
    nodes: L.layerGroup().addTo(map),
  },
  defaultNodeStyle: {
    radius: 4,
    color: "#2563eb",
    weight: 1,
    fillColor: "#3b82f6",
    fillOpacity: 0.9,
  },
};

const statusBox = document.getElementById("status");

function setStatus(message) {
  statusBox.textContent = message;
}

function fetchGraph() {
  return fetch("/init_graph")
    .then((res) => res.json())
    .then((data) => {
      state.nodes = Object.fromEntries(data.nodes.map((n) => [n.id, n]));
      state.edges = data.edges;
      drawGraph();
      setStatus("Graph loaded. Chọn Start rồi Goal.");
    })
    .catch((err) => setStatus(`Không tải được graph: ${err}`));
}

function drawGraph() {
  state.layers.edges.clearLayers();
  state.layers.nodes.clearLayers();
  state.polylines.clear();
  state.nodeMarkers.clear();

  const bounds = [];

  state.edges.forEach((edge) => {
    const polyline = L.polyline(edge.coords.map(([lat, lng]) => [lat, lng]), {
      color: "#d0d0d0",
      weight: 2,
    }).addTo(state.layers.edges);
    const key = `${edge.u}-${edge.v}`;
    state.polylines.set(key, polyline);
    bounds.push(...edge.coords.map(([lat, lng]) => [lat, lng]));
  });

  Object.values(state.nodes).forEach((node) => {
    const marker = L.circleMarker([node.lat, node.lng], {
      ...state.defaultNodeStyle,
      interactive: true,
    })
      .on("click", () => selectNode(node.id))
      .addTo(state.layers.nodes);
    state.nodeMarkers.set(node.id, marker);
  });

  if (bounds.length) {
    map.fitBounds(bounds);
  }
}

function getSelectedType() {
  const checked = document.querySelector('input[name="edgeType"]:checked');
  state.edgeType = checked ? checked.value : "jam";
  return state.edgeType;
}

function handleMapClick(e) {
  fetch(`/nearest?lat=${e.latlng.lat}&lng=${e.latlng.lng}`)
    .then((res) => res.json())
    .then(({ node }) => selectNode(node))
    .catch((err) => setStatus(`Lỗi chọn node: ${err}`));
}

function selectNode(nodeId) {
  if (!state.nodes[nodeId]) {
    setStatus("Node không tồn tại trong graph");
    return;
  }

  if (!state.start) {
    state.start = nodeId;
    resetNodeStyles();
    setStatus(`Start = ${nodeId}. Chọn Goal.`);
    return;
  }

  if (!state.goal) {
    state.goal = nodeId;
    resetNodeStyles();
    previewPath();
    setStatus("Đã chọn Start/Goal. Click 2 node liên tiếp để đánh dấu đường.");
    return;
  }

  if (!state.pendingEdgeNode) {
    state.pendingEdgeNode = nodeId;
    setStatus(`Đã chọn node ${nodeId}. Chọn node kế tiếp để đánh dấu cạnh.`);
    return;
  }

  const u = state.pendingEdgeNode;
  const v = nodeId;
  const type = getSelectedType();
  state.pendingEdgeNode = null;
  markEdge(u, v, type);
}

function markEdge(u, v, type) {
  fetch("/mark_edge", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ u, v, type }),
  })
    .then((res) => res.json())
    .then((data) => {
      const key = `${u}-${v}`;
      const polyline = state.polylines.get(key);
      if (polyline) {
        polyline.setStyle({ color: type === "flood" ? "black" : "orange", weight: 5 });
      }
      setStatus(`Đánh dấu cạnh ${u} → ${v} (${type}), cost=${data.new_cost}`);
      previewPath();
    })
    .catch((err) => setStatus(`Không đánh dấu được cạnh: ${err}`));
}

function bindButtons() {
  document.querySelectorAll("button[data-algo]").forEach((btn) => {
    btn.addEventListener("click", () => runAlgorithm(btn.dataset.algo));
  });

  document.getElementById("reset").addEventListener("click", () => {
    fetch("/reset_weights")
      .then((res) => res.json())
      .then(() => {
        state.polylines.forEach((poly) => poly.setStyle({ color: "#d0d0d0", weight: 2 }));
        setStatus("Đã reset trọng số.");
      });
  });

  document.getElementById("toggle-nodes").addEventListener("click", () => {
    if (map.hasLayer(state.layers.nodes)) {
      map.removeLayer(state.layers.nodes);
      setStatus("Đã ẩn toàn bộ node.");
    } else {
      map.addLayer(state.layers.nodes);
      setStatus("Đã hiển thị node.");
    }
  });

  document.getElementById("toggle-edges").addEventListener("click", () => {
    if (map.hasLayer(state.layers.edges)) {
      map.removeLayer(state.layers.edges);
      setStatus("Đã ẩn các đường.");
    } else {
      map.addLayer(state.layers.edges);
      setStatus("Đã hiển thị các đường.");
    }
  });

  map.on("click", handleMapClick);
}

function runAlgorithm(algo) {
  if (!state.start || !state.goal) {
    setStatus("Chưa chọn Start/Goal");
    return;
  }
  if (state.animation) {
    clearInterval(state.animation);
  }
  setStatus(`Đang chạy ${algo.toUpperCase()}...`);
  fetch(`/run/${algo}?start=${state.start}&goal=${state.goal}`)
    .then((res) => res.json())
    .then((data) => animateSteps(data.steps, data.final_path))
    .catch((err) => setStatus(`Lỗi chạy thuật toán: ${err}`));
}

function setNodeStyle(nodeId, style) {
  const marker = state.nodeMarkers.get(nodeId);
  if (marker) {
    marker.setStyle({ ...state.defaultNodeStyle, ...style });
  }
}

function resetNodeStyles() {
  state.nodeMarkers.forEach((marker) => marker.setStyle(state.defaultNodeStyle));
  if (state.start) {
    setNodeStyle(state.start, {
      color: "#16a34a",
      fillColor: "#22c55e",
      radius: 6,
    });
  }
  if (state.goal) {
    setNodeStyle(state.goal, {
      color: "#ef4444",
      fillColor: "#f87171",
      radius: 6,
    });
  }
}

function highlightNodes(nodes, color) {
  nodes.forEach((n) => setNodeStyle(n, { color, fillColor: color, radius: 7 }));
}

function animateSteps(steps, finalPath) {
  resetColors();
  resetNodeStyles();
  let idx = 0;
  state.animation = setInterval(() => {
    if (idx >= steps.length) {
      clearInterval(state.animation);
      drawFinalPath(finalPath);
      setStatus("Hoàn thành. Đã hiển thị đường đi của thuật toán.");
      return;
    }
    const step = steps[idx];
    resetColors();
    resetNodeStyles();
    highlightNodes(step.explored, "#888");
    highlightNodes(step.frontier, "#2274a5");
    highlightNodes([step.current], "#ffd166");
    drawFinalPath(finalPath);
    idx += 1;
  }, 700);
}

function resetColors() {
  state.polylines.forEach((poly) => {
    const color = poly.options.color;
    if (color === "black" || color === "orange") return;
    poly.setStyle({ color: "#d0d0d0", weight: 2 });
  });
}

function drawFinalPath(path) {
  for (let i = 0; i < path.length - 1; i++) {
    const key = `${path[i]}-${path[i + 1]}`;
    const poly = state.polylines.get(key) || state.polylines.get(`${path[i + 1]}-${path[i]}`);
    if (poly) {
      poly.setStyle({ color: "#d90429", weight: 6 });
    }
  }
}

function previewPath() {
  if (!state.start || !state.goal) return;
  if (state.animation) {
    clearInterval(state.animation);
  }
  setStatus("Tìm đường nhanh giữa Start và Goal...");
  fetch(`/run/ucs?start=${state.start}&goal=${state.goal}`)
    .then((res) => res.json())
    .then((data) => {
      resetColors();
      resetNodeStyles();
      drawFinalPath(data.final_path);
      highlightNodes([state.start], "#22c55e");
      highlightNodes([state.goal], "#f87171");
      setStatus("Đã hiển thị đường đi giữa Start và Goal. Chọn thuật toán để xem từng bước.");
    })
    .catch((err) => setStatus(`Không tìm được đường đi: ${err}`));
}

fetchGraph();
bindButtons();

