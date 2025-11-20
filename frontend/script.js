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
  markers: {},
  animation: null,
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
  const bounds = [];
  state.edges.forEach((edge) => {
    const polyline = L.polyline(edge.coords.map(([lat, lng]) => [lat, lng]), {
      color: "#d0d0d0",
      weight: 2,
    }).addTo(map);
    const key = `${edge.u}-${edge.v}`;
    state.polylines.set(key, polyline);
    bounds.push(...edge.coords.map(([lat, lng]) => [lat, lng]));
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
    .then(({ node }) => {
      if (!state.start) {
        state.start = node;
        state.markers.start = L.marker(e.latlng, { title: "Start" }).addTo(map);
        state.markers.start.bindTooltip("Start", { permanent: true }).openTooltip();
        setStatus(`Start = ${node}. Chọn Goal.`);
        return;
      }
      if (!state.goal) {
        state.goal = node;
        state.markers.goal = L.marker(e.latlng, { title: "Goal", icon: L.icon({
          iconUrl: "https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png",
          iconAnchor: [12, 41],
        }) }).addTo(map);
        state.markers.goal.bindTooltip("Goal", { permanent: true }).openTooltip();
        setStatus("Đã chọn Start/Goal. Click 2 node liên tiếp để đánh dấu đường.");
        return;
      }

      if (!state.pendingEdgeNode) {
        state.pendingEdgeNode = node;
        setStatus(`Đã chọn node ${node}. Chọn node kế tiếp để đánh dấu cạnh.`);
        return;
      }

      const u = state.pendingEdgeNode;
      const v = node;
      const type = getSelectedType();
      state.pendingEdgeNode = null;
      markEdge(u, v, type);
    })
    .catch((err) => setStatus(`Lỗi chọn node: ${err}`));
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

function highlightNodes(nodes, color) {
  nodes.forEach((n) => {
    const match = state.edges.find((e) => `${e.u}` === `${n}` || `${e.v}` === `${n}`);
    if (match) {
      const poly = state.polylines.get(`${match.u}-${match.v}`);
      if (poly && poly.options.color === "#d0d0d0") {
        poly.setStyle({ color, weight: 3 });
      }
    }
  });
}

function animateSteps(steps, finalPath) {
  resetColors();
  let idx = 0;
  state.animation = setInterval(() => {
    if (idx >= steps.length) {
      clearInterval(state.animation);
      drawFinalPath(finalPath);
      setStatus("Hoàn thành.");
      return;
    }
    const step = steps[idx];
    resetColors();
    highlightNodes(step.explored, "#888");
    highlightNodes(step.frontier, "#2274a5");
    highlightNodes([step.current], "#ffd166");
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
    const poly = state.polylines.get(key);
    if (poly) {
      poly.setStyle({ color: "#d90429", weight: 6 });
    }
  }
}

fetchGraph();
bindButtons();

