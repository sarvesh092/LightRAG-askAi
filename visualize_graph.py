import sys
import os
import json
import networkx as nx
from pathlib import Path

if len(sys.argv) > 1:
    GRAPHML_PATH = sys.argv[1]
else:
    candidates = list(Path(".").rglob("*.graphml"))
    if not candidates:
        print("ERROR: No .graphml file found. Run app.py first, then re-run this script.")
        sys.exit(1)
    GRAPHML_PATH = str(candidates[0])

print(f"Loading graph from: {GRAPHML_PATH}")
G = nx.read_graphml(GRAPHML_PATH)
print(f"  Nodes : {G.number_of_nodes()}")
print(f"  Edges : {G.number_of_edges()}")

nodes = []
edges = []

degree = dict(G.degree())
max_deg = max(degree.values()) if degree else 1

for node_id, data in G.nodes(data=True):
    label = data.get("entity_type", data.get("label", str(node_id)))
    title = data.get("description", str(node_id))
    deg   = degree.get(node_id, 1)
    size  = 12 + (deg / max_deg) * 40

    etype = str(data.get("entity_type", "")).upper()
    color_map = {
        "PERSON":       "#60a5fa",
        "ORGANIZATION": "#f472b6",
        "LOCATION":     "#34d399",
        "EVENT":        "#fbbf24",
        "CONCEPT":      "#a78bfa",
        "OBJECT":       "#fb923c",
    }
    color = color_map.get(etype, "#94a3b8")

    nodes.append({
        "id":    node_id,
        "label": str(node_id),
        "title": title[:200],
        "size":  round(size, 1),
        "color": color,
        "type":  etype or "UNKNOWN",
    })

for u, v, data in G.edges(data=True):
    label = data.get("keywords", data.get("label", ""))
    title = data.get("description", "")
    edges.append({
        "from":  u,
        "to":    v,
        "label": str(label)[:40],
        "title": str(title)[:200],
    })

nodes_json = json.dumps(nodes)
edges_json = json.dumps(edges)

html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>LightRAG Knowledge Graph</title>
<script src="https://cdnjs.cloudflare.com/ajax/libs/vis/4.21.0/vis.min.js"></script>
<link  href="https://cdnjs.cloudflare.com/ajax/libs/vis/4.21.0/vis.min.css" rel="stylesheet">
<style>
  @import url('https://fonts.googleapis.com/css2?family=Space+Mono:wght@400;700&family=Inter:wght@300;400;600&display=swap');

  *, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}

  :root {{
    --bg:      #0a0e1a;
    --panel:   #111827;
    --border:  #1f2937;
    --accent:  #60a5fa;
    --text:    #e2e8f0;
    --muted:   #64748b;
    --success: #34d399;
  }}

  body {{
    background: var(--bg);
    color: var(--text);
    font-family: 'Inter', sans-serif;
    height: 100vh;
    display: grid;
    grid-template-rows: 56px 1fr;
    grid-template-columns: 1fr 280px;
    overflow: hidden;
  }}

  header {{
    grid-column: 1 / -1;
    background: var(--panel);
    border-bottom: 1px solid var(--border);
    display: flex;
    align-items: center;
    gap: 16px;
    padding: 0 24px;
  }}
  header h1 {{
    font-family: 'Space Mono', monospace;
    font-size: 15px;
    letter-spacing: 0.08em;
    color: var(--accent);
  }}
  .stats {{
    margin-left: auto;
    display: flex;
    gap: 24px;
  }}
  .stat {{
    font-family: 'Space Mono', monospace;
    font-size: 12px;
    color: var(--muted);
  }}
  .stat span {{ color: var(--text); }}

  #graph {{
    background: radial-gradient(ellipse at 30% 40%, #0d1b2e 0%, var(--bg) 70%);
    border-right: 1px solid var(--border);
  }}

  aside {{
    background: var(--panel);
    padding: 20px;
    overflow-y: auto;
    display: flex;
    flex-direction: column;
    gap: 20px;
  }}
  aside h2 {{
    font-family: 'Space Mono', monospace;
    font-size: 11px;
    letter-spacing: 0.12em;
    color: var(--muted);
    text-transform: uppercase;
    border-bottom: 1px solid var(--border);
    padding-bottom: 8px;
  }}

  #search {{
    width: 100%;
    background: var(--bg);
    border: 1px solid var(--border);
    border-radius: 6px;
    padding: 8px 12px;
    color: var(--text);
    font-family: 'Inter', sans-serif;
    font-size: 13px;
    outline: none;
    transition: border-color .2s;
  }}
  #search:focus {{ border-color: var(--accent); }}

  .legend-item {{
    display: flex;
    align-items: center;
    gap: 10px;
    font-size: 12px;
    color: var(--muted);
    padding: 3px 0;
  }}
  .dot {{
    width: 12px; height: 12px;
    border-radius: 50%;
    flex-shrink: 0;
  }}

  #info {{
    background: var(--bg);
    border: 1px solid var(--border);
    border-radius: 8px;
    padding: 14px;
    font-size: 12px;
    line-height: 1.7;
    color: var(--muted);
    min-height: 80px;
  }}
  #info strong {{ color: var(--text); display: block; margin-bottom: 6px; font-size: 13px; }}
  #info em {{ color: var(--accent); font-style: normal; }}

  /* controls */
  .btn {{
    width: 100%;
    padding: 9px;
    border-radius: 6px;
    border: 1px solid var(--border);
    background: var(--bg);
    color: var(--text);
    font-family: 'Space Mono', monospace;
    font-size: 11px;
    cursor: pointer;
    transition: border-color .2s, color .2s;
  }}
  .btn:hover {{ border-color: var(--accent); color: var(--accent); }}

  .btn-group {{ display: flex; flex-direction: column; gap: 8px; }}
</style>
</head>
<body>

<header>
  <h1>⬡ LIGHTRAG KNOWLEDGE GRAPH</h1>
  <div class="stats">
    <div class="stat">NODES <span>{G.number_of_nodes()}</span></div>
    <div class="stat">EDGES <span>{G.number_of_edges()}</span></div>
    <div class="stat">SOURCE <span>sample.md</span></div>
  </div>
</header>

<div id="graph"></div>

<aside>
  <div>
    <h2>Search</h2>
    <input id="search" type="text" placeholder="Find a node...">
  </div>

  <div>
    <h2>Legend</h2>
    <div class="legend-item"><div class="dot" style="background:#60a5fa"></div>Person</div>
    <div class="legend-item"><div class="dot" style="background:#f472b6"></div>Organization</div>
    <div class="legend-item"><div class="dot" style="background:#34d399"></div>Location</div>
    <div class="legend-item"><div class="dot" style="background:#fbbf24"></div>Event</div>
    <div class="legend-item"><div class="dot" style="background:#a78bfa"></div>Concept</div>
    <div class="legend-item"><div class="dot" style="background:#fb923c"></div>Object</div>
    <div class="legend-item"><div class="dot" style="background:#94a3b8"></div>Other</div>
  </div>

  <div>
    <h2>Selected Node</h2>
    <div id="info">Click any node to see its details.</div>
  </div>

  <div>
    <h2>Controls</h2>
    <div class="btn-group">
      <button class="btn" onclick="network.fit()">⊡ Fit to Screen</button>
      <button class="btn" onclick="togglePhysics()">⚙ Toggle Physics</button>
      <button class="btn" onclick="network.setOptions({{physics:{{stabilization:true}}}});network.stabilize()">↺ Re-layout</button>
    </div>
  </div>
</aside>

<script>
const rawNodes = {nodes_json};
const rawEdges = {edges_json};

const nodes = new vis.DataSet(rawNodes);
const edges = new vis.DataSet(rawEdges.map((e,i) => ({{...e, id:i}})));

const container = document.getElementById('graph');
const data = {{ nodes, edges }};

const options = {{
  nodes: {{
    shape: 'dot',
    font: {{ color: '#e2e8f0', size: 13, face: 'Inter' }},
    borderWidth: 1.5,
    borderWidthSelected: 3,
    color: {{ border: '#1f2937', highlight: {{ border: '#60a5fa', background: '#1e3a5f' }} }},
  }},
  edges: {{
    color: {{ color: '#2d3748', highlight: '#60a5fa', hover: '#4a5568' }},
    font: {{ color: '#64748b', size: 10, face: 'Space Mono', strokeWidth: 0 }},
    smooth: {{ type: 'continuous', roundness: 0.2 }},
    arrows: {{ to: {{ enabled: true, scaleFactor: 0.5 }} }},
    width: 1,
    selectionWidth: 2.5,
  }},
  physics: {{
    enabled: true,
    stabilization: {{
      enabled: true,
      iterations: 200,
      fit: true,
    }},
    barnesHut: {{
      gravitationalConstant: -8000,
      centralGravity: 0.3,
      springLength: 140,
      springConstant: 0.04,
      damping: 0.09,
    }},
  }},
  interaction: {{
    hover: true,
    tooltipDelay: 150,
    zoomView: true,
    dragView: true,
  }},
}};

const network = new vis.Network(container, data, options);

network.once('stabilized', () => {{
  network.setOptions({{ physics: {{ enabled: false }} }});
  physicsOn = false;
}});

network.on('click', params => {{
  if (!params.nodes.length) return;
  const node = nodes.get(params.nodes[0]);
  document.getElementById('info').innerHTML =
    `<strong>${{node.label}}</strong>` +
    `<em>${{node.type}}</em>` +
    (node.title ? `<br>${{node.title}}` : '');
}});

//search
document.getElementById('search').addEventListener('input', e => {{
  const q = e.target.value.toLowerCase();
  if (!q) {{ network.unselectAll(); return; }}
  const match = rawNodes.filter(n => n.label.toLowerCase().includes(q)).map(n => n.id);
  network.selectNodes(match);
  if (match.length) network.focus(match[0], {{ scale: 1.2, animation: true }});
}});

// toggle physics
let physicsOn = false;
function togglePhysics() {{
  physicsOn = !physicsOn;
  network.setOptions({{ physics: {{ enabled: physicsOn }} }});
}}
</script>
</body>
</html>"""

out_path = "graph.html"
with open(out_path, "w", encoding="utf-8") as f:
    f.write(html)
print(f"\n✓ Interactive graph saved → {out_path}")
print("  Open this file in your browser to explore the knowledge graph.\n")
