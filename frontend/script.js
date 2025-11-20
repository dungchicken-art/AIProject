const map = L.map('map').setView([21.0015, 105.816], 16);
L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
  attribution: '&copy; OpenStreetMap contributors'
}).addTo(map);

let nodes = {};
let edges = [];
let startNode = null;
let goalNode = null;
let tempEdgeStart = null;
let polylines = [];
let frontierLayer = L.layerGroup().addTo(map);
let exploredLayer = L.layerGroup().addTo(map);
let currentLayer = L.layerGroup().addTo(map);
let pathLayer = L.layerGroup().addTo(map);

const statusEl = document.getElementById('status');

function setStatus(text) {
  statusEl.textContent = text;
}

function colorForEdge(edge, defaultColor = '#d1d5db') {
  return edge.markerType === 'jam' ? '#f97316'
       : edge.markerType === 'flood' ? '#111827'
       : defaultColor;
}

async function fetchGraph() {
  const res = await fetch('/init_graph');
  const data = await res.json();
  nodes = Object.fromEntries(data.nodes.map(n => [n.id, n]));
  edges = data.edges;
  drawEdges();
  setStatus('Chọn Start bằng lần click đầu tiên.');
}

function drawEdges() {
  polylines.forEach(l => map.removeLayer(l));
  polylines = edges.map(edge => {
    const latlngs = edge.geometry.map(pair => [pair[0], pair[1]]);
    const line = L.polyline(latlngs, { color: colorForEdge(edge), weight: 3, opacity: 0.7 }).addTo(map);
    return line;
  });
}

async function getNearestNode(latlng) {
  const res = await fetch(`/nearest?lat=${latlng.lat}&lng=${latlng.lng}`);
  const data = await res.json();
  return data.node;
}

function placeMarker(latlng, color) {
  return L.circleMarker(latlng, { radius: 8, color, fillColor: color, fillOpacity: 0.9 }).addTo(map);
}

const startMarkerLayer = L.layerGroup().addTo(map);
const goalMarkerLayer = L.layerGroup().addTo(map);

function clearMarkers() {
  startMarkerLayer.clearLayers();
  goalMarkerLayer.clearLayers();
}

async function handleMapClick(e) {
  const clickedNode = await getNearestNode(e.latlng);
  const nodeData = nodes[clickedNode];
  if (!startNode) {
    startNode = clickedNode;
    placeMarker([nodeData.lat, nodeData.lng], '#22c55e').addTo(startMarkerLayer);
    setStatus(`Start: ${startNode}. Chọn Goal.`);
    return;
  }
  if (!goalNode) {
    goalNode = clickedNode;
    placeMarker([nodeData.lat, nodeData.lng], '#ef4444').addTo(goalMarkerLayer);
    setStatus(`Goal: ${goalNode}. Bạn có thể đánh dấu các cạnh tắc/ngập.`);
    return;
  }

  if (!tempEdgeStart) {
    tempEdgeStart = clickedNode;
    setStatus(`Đã chọn node A=${tempEdgeStart}. Click node B để đánh dấu cạnh.`);
  } else {
    await markEdge(tempEdgeStart, clickedNode);
    tempEdgeStart = null;
    setStatus('Cạnh đã được cập nhật trọng số.');
  }
}

async function markEdge(u, v) {
  const edgeType = document.getElementById('edgeType').value;
  await fetch('/mark_edge', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ u, v, type: edgeType })
  });
  const factor = edgeType === 'jam' ? 5 : 10;
  edges = edges.map(edge => {
    if ((edge.u === u && edge.v === v) || (edge.u === v && edge.v === u)) {
      return { ...edge, cost: edge.cost * factor, markerType: edgeType };
    }
    return edge;
  });
  drawEdges();
}

function clearAnimationLayers() {
  frontierLayer.clearLayers();
  exploredLayer.clearLayers();
  currentLayer.clearLayers();
  pathLayer.clearLayers();
}

function drawStep(step) {
  clearAnimationLayers();
  step.frontier.forEach(id => {
    const n = nodes[id];
    L.circleMarker([n.lat, n.lng], { radius: 6, color: '#2563eb', fillColor: '#2563eb', fillOpacity: 0.8 }).addTo(frontierLayer);
  });
  step.explored.forEach(id => {
    const n = nodes[id];
    L.circleMarker([n.lat, n.lng], { radius: 4, color: '#9ca3af', fillColor: '#9ca3af', fillOpacity: 0.8 }).addTo(exploredLayer);
  });
  const current = nodes[step.current];
  L.circleMarker([current.lat, current.lng], { radius: 9, color: '#fbbf24', fillColor: '#fbbf24', fillOpacity: 0.9 }).addTo(currentLayer);
  if (step.path && step.path.length) {
    const latlngs = step.path.map(id => [nodes[id].lat, nodes[id].lng]);
    L.polyline(latlngs, { color: '#b91c1c', weight: 5, opacity: 0.8 }).addTo(pathLayer);
  }
}

async function runAlgorithm(algo) {
  if (!startNode || !goalNode) {
    setStatus('Cần chọn Start và Goal trước.');
    return;
  }
  const res = await fetch(`/run/${algo}?start=${startNode}&goal=${goalNode}`);
  const data = await res.json();
  setStatus(`Thuật toán ${algo.toUpperCase()} | ${data.summary.steps} bước | explored: ${data.summary.explored}`);
  animateSteps(data.steps, data.final_path);
}

function animateSteps(steps, finalPath) {
  let idx = 0;
  const timer = setInterval(() => {
    if (idx >= steps.length) {
      clearAnimationLayers();
      if (finalPath && finalPath.length) {
        const latlngs = finalPath.map(id => [nodes[id].lat, nodes[id].lng]);
        L.polyline(latlngs, { color: '#b91c1c', weight: 6 }).addTo(pathLayer);
      }
      clearInterval(timer);
      return;
    }
    drawStep(steps[idx]);
    idx += 1;
  }, 500);
}

map.on('click', handleMapClick);

document.querySelectorAll('button[data-algo]').forEach(btn => {
  btn.addEventListener('click', () => runAlgorithm(btn.dataset.algo));
});

const resetBtn = document.getElementById('reset');
resetBtn.addEventListener('click', async () => {
  await fetch('/reset_weights');
  await fetchGraph();
  tempEdgeStart = null;
  setStatus('Trọng số đã reset.');
});

fetchGraph();
