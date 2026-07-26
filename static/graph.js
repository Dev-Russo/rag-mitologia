const SVG_NS = "http://www.w3.org/2000/svg";

const elements = {
  apiStatus: document.querySelector("#api-status"),
  form: document.querySelector("#query-form"),
  input: document.querySelector("#question"),
  queryButton: document.querySelector("#query-button"),
  requestStatus: document.querySelector("#request-status"),
  graphEmpty: document.querySelector("#graph-empty"),
  svg: document.querySelector("#graph-svg"),
  sourceEmpty: document.querySelector("#source-empty"),
  nodeDetails: document.querySelector("#node-details"),
  nodeType: document.querySelector("#node-type"),
  nodeLabel: document.querySelector("#node-label"),
  sourceQuote: document.querySelector("#source-quote"),
  sourceMeta: document.querySelector("#source-meta"),
  expandButton: document.querySelector("#expand-button"),
  answerPanel: document.querySelector("#answer-panel"),
  answerText: document.querySelector("#answer-text"),
  answerMeta: document.querySelector("#answer-meta"),
};

const state = {
  nodes: new Map(),
  edges: [],
  sources: [],
  selectedNodeId: null,
  loading: false,
};

const typeLabels = {
  pergunta: "Pergunta",
  deus: "Deus",
  heroi: "Herói",
  lugar: "Lugar",
  evento: "Evento",
};

function setLoading(loading, message = "") {
  state.loading = loading;
  elements.input.disabled = loading;
  elements.queryButton.disabled = loading;
  elements.expandButton.disabled = loading;
  elements.queryButton.textContent = loading ? "Consultando…" : "Gerar mapa";
  elements.requestStatus.textContent = message;
}

async function apiRequest(endpoint, payload) {
  const response = await fetch(endpoint, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  const data = await response.json();
  if (!response.ok || data.status === "error") {
    throw new Error(data.error || "Não foi possível consultar o corpus.");
  }
  return data;
}

function mergeResponse(data, reset = false) {
  if (reset) {
    state.nodes.clear();
    state.edges = [];
    state.sources = [];
    state.selectedNodeId = null;
  }

  data.nodes.forEach((node) => state.nodes.set(node.id, node));
  const knownEdges = new Set(
    state.edges.map((edge) => `${edge.source}|${edge.target}|${edge.relation}`),
  );
  data.edges.forEach((edge) => {
    const key = `${edge.source}|${edge.target}|${edge.relation}`;
    if (!knownEdges.has(key)) {
      state.edges.push(edge);
      knownEdges.add(key);
    }
  });

  const knownSources = new Set(
    state.sources.map((source) => `${source.chunk_id}|${source.quote}`),
  );
  data.sources.forEach((source) => {
    const key = `${source.chunk_id}|${source.quote}`;
    if (!knownSources.has(key)) {
      state.sources.push(source);
      knownSources.add(key);
    }
  });

  elements.answerPanel.hidden = false;
  elements.answerText.textContent = data.answer;
  elements.answerMeta.textContent = data.evaluation.sufficient
    ? `${data.evaluation.attempts} tentativa(s) · relevância ${data.evaluation.max_score.toFixed(3)}`
    : `${data.evaluation.attempts} tentativa(s) sem evidência suficiente`;

  renderGraph();
}

function calculatePositions() {
  const levels = new Map();
  const roots = [...state.nodes.values()].filter((node) => node.type === "pergunta");
  roots.forEach((node) => levels.set(node.id, 0));

  for (let pass = 0; pass < state.nodes.size; pass += 1) {
    let changed = false;
    state.edges.forEach((edge) => {
      if (levels.has(edge.source) && !levels.has(edge.target)) {
        levels.set(edge.target, levels.get(edge.source) + 1);
        changed = true;
      }
    });
    if (!changed) break;
  }

  const fallbackLevel = Math.max(0, ...levels.values()) + 1;
  state.nodes.forEach((node) => {
    if (!levels.has(node.id)) levels.set(node.id, fallbackLevel);
  });

  const grouped = new Map();
  levels.forEach((level, id) => {
    if (!grouped.has(level)) grouped.set(level, []);
    grouped.get(level).push(id);
  });

  const columnGap = 260;
  const rowGap = 112;
  const paddingX = 90;
  const paddingY = 85;
  const largestColumn = Math.max(1, ...[...grouped.values()].map((ids) => ids.length));
  const height = Math.max(560, paddingY * 2 + (largestColumn - 1) * rowGap);
  const maxLevel = Math.max(0, ...grouped.keys());
  const width = Math.max(900, paddingX * 2 + maxLevel * columnGap);
  const positions = new Map();

  [...grouped.entries()]
    .sort(([first], [second]) => first - second)
    .forEach(([level, ids]) => {
      const columnHeight = (ids.length - 1) * rowGap;
      const startY = (height - columnHeight) / 2;
      ids.forEach((id, index) => {
        positions.set(id, {
          x: paddingX + level * columnGap,
          y: startY + index * rowGap,
        });
      });
    });

  return { positions, width, height };
}

function svgElement(name, attributes = {}) {
  const element = document.createElementNS(SVG_NS, name);
  Object.entries(attributes).forEach(([key, value]) => {
    element.setAttribute(key, value);
  });
  return element;
}

function addSelectedLabel(group, label) {
  const text = svgElement("text", {
    class: "graph-node-label is-visible",
    "text-anchor": "middle",
    y: "-52",
  });
  text.textContent = label;
  group.appendChild(text);
}

function renderGraph() {
  const { positions, width, height } = calculatePositions();
  elements.svg.replaceChildren();
  elements.graphEmpty.toggleAttribute("hidden", state.nodes.size > 0);
  elements.svg.toggleAttribute("hidden", state.nodes.size === 0);
  if (!state.nodes.size) return;
  elements.svg.setAttribute("viewBox", `0 0 ${width} ${height}`);

  const edgeLayer = svgElement("g", { class: "edge-layer" });
  state.edges.forEach((edge) => {
    const start = positions.get(edge.source);
    const end = positions.get(edge.target);
    if (!start || !end) return;
    const curve = Math.max(70, (end.x - start.x) * 0.45);
    edgeLayer.appendChild(svgElement("path", {
      class: "graph-edge",
      d: [
        `M ${start.x + 34} ${start.y}`,
        `C ${start.x + curve} ${start.y}`,
        `${end.x - curve} ${end.y}`,
        `${end.x - 34} ${end.y}`,
      ].join(" "),
      "aria-hidden": "true",
    }));
  });
  elements.svg.appendChild(edgeLayer);

  const nodeLayer = svgElement("g", { class: "node-layer" });
  state.nodes.forEach((node) => {
    const position = positions.get(node.id);
    const selected = node.id === state.selectedNodeId;
    const group = svgElement("g", {
      class: `graph-node graph-node-${node.type}${selected ? " is-selected" : ""}`,
      transform: `translate(${position.x} ${position.y})`,
      tabindex: "0",
      role: "button",
      "aria-label": `${typeLabels[node.type]}: ${node.label}`,
    });
    group.appendChild(
      svgElement("circle", {
        class: "graph-node-circle",
        r: node.type === "pergunta" ? "34" : "27",
      }),
    );
    if (selected) addSelectedLabel(group, node.label);
    group.addEventListener("click", () => selectNode(node.id));
    group.addEventListener("dblclick", () => expandSelectedNode(node.id));
    group.addEventListener("keydown", (event) => {
      if (event.key === "Enter" || event.key === " ") {
        event.preventDefault();
        selectNode(node.id);
      }
    });
    nodeLayer.appendChild(group);
  });
  elements.svg.appendChild(nodeLayer);
}

function findSource(node) {
  return (
    state.sources.find(
      (source) =>
        source.chunk_id === node.chunk_id && source.quote === node.source_quote,
    ) || state.sources.find((source) => source.chunk_id === node.chunk_id)
  );
}

function selectNode(nodeId) {
  const node = state.nodes.get(nodeId);
  if (!node) return;
  state.selectedNodeId = nodeId;
  elements.sourceEmpty.hidden = true;
  elements.nodeDetails.hidden = false;
  elements.nodeType.textContent = typeLabels[node.type];
  elements.nodeType.className = `node-type type-${node.type}`;
  elements.nodeLabel.textContent = node.label;

  const source = findSource(node);
  elements.sourceQuote.textContent =
    node.source_quote || source?.quote || "Este nó representa a pergunta inicial.";
  elements.sourceMeta.textContent = source
    ? `${source.source} · página ${source.page} · score ${source.score.toFixed(3)}`
    : "Nó sem trecho-fonte próprio.";
  elements.expandButton.hidden = node.type === "pergunta";
  renderGraph();
}

async function expandSelectedNode(nodeId = state.selectedNodeId) {
  const node = state.nodes.get(nodeId);
  if (!node || node.type === "pergunta" || state.loading) return;
  selectNode(nodeId);
  setLoading(true, `Expandindo ${node.label}…`);
  try {
    const data = await apiRequest("/expand", {
      node_id: node.id,
      concept: node.label,
    });
    mergeResponse(data);
    elements.requestStatus.textContent =
      data.status === "insufficient"
        ? data.answer
        : `${node.label} ganhou novos conceitos.`;
  } catch (error) {
    elements.requestStatus.textContent = error.message;
  } finally {
    setLoading(false, elements.requestStatus.textContent);
  }
}

elements.form.addEventListener("submit", async (event) => {
  event.preventDefault();
  const question = elements.input.value.trim();
  if (question.length < 3 || state.loading) return;

  setLoading(true, "Recuperando evidências e construindo o mapa…");
  try {
    const data = await apiRequest("/query", { question });
    mergeResponse(data, true);
    elements.requestStatus.textContent =
      data.status === "insufficient"
        ? data.answer
        : "Mapa gerado. Clique em um conceito para ver sua fonte.";
  } catch (error) {
    elements.requestStatus.textContent = error.message;
  } finally {
    setLoading(false, elements.requestStatus.textContent);
  }
});

elements.expandButton.addEventListener("click", () => expandSelectedNode());

async function checkApiHealth() {
  try {
    const response = await fetch("/health");
    if (!response.ok) throw new Error(`API respondeu com status ${response.status}`);
    const data = await response.json();
    elements.apiStatus.textContent =
      data.status === "ok" ? "API online" : "API indisponível";
    elements.apiStatus.classList.toggle("status-online", data.status === "ok");
  } catch (error) {
    elements.apiStatus.textContent = "API indisponível";
    elements.apiStatus.title = error.message;
  }
}

checkApiHealth();
