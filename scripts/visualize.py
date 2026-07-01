#!/usr/bin/env python3
"""
Render an OKF bundle (as produced by the codebase-knowledge skill) as a
self-contained, offline HTML graph: nodes are documents (colored by `type`),
edges are markdown cross-links. No external assets, no CDN, no build step.

Usage: python visualize.py <bundle_dir> [output_file]
"""

import json
import re
import sys
from pathlib import Path

try:
    import yaml
except ImportError:
    print("Missing dependency: PyYAML. Install with: pip install pyyaml")
    sys.exit(1)

FRONTMATTER_RE = re.compile(r"^---\n(.*?)\n---\n?", re.DOTALL)
LINK_RE = re.compile(r"\]\(([^)]+)\)")


def load_node(bundle_path, md_file):
    rel = str(md_file.relative_to(bundle_path))
    content = md_file.read_text()

    if md_file.name == "index.md":
        node_type = "Index"
        title = rel
    elif md_file.name == "log.md":
        node_type = "Log"
        title = rel
    else:
        node_type, title = "Untyped", rel
        match = FRONTMATTER_RE.match(content)
        if match:
            try:
                fm = yaml.safe_load(match.group(1)) or {}
            except yaml.YAMLError:
                fm = {}
            node_type = fm.get("type") or "Untyped"
            title = fm.get("title") or rel

    links = []
    for target in LINK_RE.findall(content):
        if target.startswith(("http://", "https://", "#", "mailto:")):
            continue
        target_path = target.split("#")[0]
        if not target_path:
            continue
        if target_path.startswith("/"):
            resolved = (bundle_path / target_path.lstrip("/")).resolve()
        else:
            resolved = (md_file.parent / target_path).resolve()
        try:
            resolved_rel = str(resolved.relative_to(bundle_path.resolve()))
        except ValueError:
            continue
        links.append(resolved_rel)

    return rel, {"id": rel, "type": node_type, "title": title, "links": links}


def build_graph(bundle_path):
    bundle_path = Path(bundle_path).resolve()
    nodes = {}
    for md_file in sorted(bundle_path.rglob("*.md")):
        if md_file.name == "visualization.html":
            continue
        rel, node = load_node(bundle_path, md_file)
        nodes[rel] = node

    edges = []
    seen = set()
    for rel, node in nodes.items():
        for target in node["links"]:
            if target in nodes and target != rel:
                key = tuple(sorted((rel, target)))
                if key not in seen:
                    seen.add(key)
                    edges.append({"source": rel, "target": target})

    return list(nodes.values()), edges


HTML_TEMPLATE = """<!doctype html>
<html>
<head>
<meta charset="utf-8">
<title>OKF Bundle Visualization</title>
<style>
  html, body { margin: 0; height: 100%; overflow: hidden; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; background: #0f1117; color: #e6e6e6; }
  #toolbar { position: absolute; top: 12px; left: 12px; z-index: 10; display: flex; gap: 8px; align-items: center; }
  #search { padding: 6px 10px; border-radius: 6px; border: 1px solid #333; background: #1a1d27; color: #e6e6e6; width: 220px; }
  #legend { position: absolute; top: 12px; right: 12px; z-index: 10; background: #1a1d27cc; border: 1px solid #333; border-radius: 8px; padding: 10px; max-height: 80vh; overflow-y: auto; font-size: 12px; }
  #legend div { display: flex; align-items: center; gap: 6px; margin: 3px 0; cursor: pointer; }
  #legend span.swatch { width: 10px; height: 10px; border-radius: 50%; display: inline-block; flex-shrink: 0; }
  #tooltip { position: absolute; pointer-events: none; background: #1a1d27; border: 1px solid #444; border-radius: 6px; padding: 8px 10px; font-size: 12px; max-width: 320px; display: none; z-index: 20; }
  svg { width: 100%; height: 100%; cursor: grab; }
  .edge { stroke: #444; stroke-width: 1; }
  .node circle { stroke: #0f1117; stroke-width: 1.5; cursor: pointer; }
  .node text { fill: #cfd2dc; font-size: 10px; pointer-events: none; }
  .dim { opacity: 0.12; }
</style>
</head>
<body>
<div id="toolbar"><input id="search" placeholder="Search title or path..."></div>
<div id="legend"></div>
<div id="tooltip"></div>
<svg id="canvas"></svg>
<script>
const DATA = __DATA_JSON__;

const svg = document.getElementById('canvas');
const W = () => window.innerWidth, H = () => window.innerHeight;
const NS = 'http://www.w3.org/2000/svg';

const types = [...new Set(DATA.nodes.map(n => n.type))].sort();
const palette = ['#5b8def','#e85d75','#57c785','#e8b73b','#a45de2','#3dc7c7','#e8785d','#8d99ae','#c15be8','#5de8a8'];
const colorOf = {};
types.forEach((t, i) => colorOf[t] = palette[i % palette.length]);

const legend = document.getElementById('legend');
types.forEach(t => {
  const row = document.createElement('div');
  row.innerHTML = '<span class="swatch" style="background:' + colorOf[t] + '"></span>' + t;
  row.onclick = () => toggleType(t);
  row.dataset.type = t;
  legend.appendChild(row);
});

const hiddenTypes = new Set();
function toggleType(t) {
  if (hiddenTypes.has(t)) hiddenTypes.delete(t); else hiddenTypes.add(t);
  render();
}

const idIndex = {};
DATA.nodes.forEach((n, i) => { idIndex[n.id] = i; n.x = Math.random() * 800; n.y = Math.random() * 600; n.vx = 0; n.vy = 0; });

function step() {
  const nodes = DATA.nodes, edges = DATA.edges;
  const k = 0.02, rep = 2200, damp = 0.85;
  for (const n of nodes) { n.fx = 0; n.fy = 0; }
  for (let i = 0; i < nodes.length; i++) {
    for (let j = i + 1; j < nodes.length; j++) {
      const a = nodes[i], b = nodes[j];
      let dx = a.x - b.x, dy = a.y - b.y;
      let d2 = dx * dx + dy * dy + 0.01;
      let f = rep / d2;
      let d = Math.sqrt(d2);
      dx /= d; dy /= d;
      a.fx += dx * f; a.fy += dy * f;
      b.fx -= dx * f; b.fy -= dy * f;
    }
  }
  for (const e of edges) {
    const a = nodes[idIndex[e.source]], b = nodes[idIndex[e.target]];
    let dx = b.x - a.x, dy = b.y - a.y;
    a.fx += dx * k; a.fy += dy * k;
    b.fx -= dx * k; b.fy -= dy * k;
  }
  const cx = W() / 2, cy = H() / 2;
  for (const n of nodes) {
    n.fx += (cx - n.x) * 0.002;
    n.fy += (cy - n.y) * 0.002;
    n.vx = (n.vx + n.fx) * damp;
    n.vy = (n.vy + n.fy) * damp;
    n.x += n.vx;
    n.y += n.vy;
  }
}

let transform = { x: 0, y: 0, k: 1 };
let dragging = null, panStart = null;

function render() {
  svg.innerHTML = '';
  const g = document.createElementNS(NS, 'g');
  g.setAttribute('transform', `translate(${transform.x},${transform.y}) scale(${transform.k})`);

  for (const e of DATA.edges) {
    const a = DATA.nodes[idIndex[e.source]], b = DATA.nodes[idIndex[e.target]];
    if (hiddenTypes.has(a.type) || hiddenTypes.has(b.type)) continue;
    const line = document.createElementNS(NS, 'line');
    line.setAttribute('class', 'edge');
    line.setAttribute('x1', a.x); line.setAttribute('y1', a.y);
    line.setAttribute('x2', b.x); line.setAttribute('y2', b.y);
    g.appendChild(line);
  }

  for (const n of DATA.nodes) {
    const grp = document.createElementNS(NS, 'g');
    grp.setAttribute('class', 'node' + (hiddenTypes.has(n.type) || n._dim ? ' dim' : ''));
    grp.setAttribute('transform', `translate(${n.x},${n.y})`);
    const c = document.createElementNS(NS, 'circle');
    c.setAttribute('r', 7);
    c.setAttribute('fill', colorOf[n.type]);
    grp.appendChild(c);
    const t = document.createElementNS(NS, 'text');
    t.setAttribute('x', 10); t.setAttribute('y', 4);
    t.textContent = n.title;
    grp.appendChild(t);
    grp.addEventListener('mouseenter', (ev) => showTooltip(ev, n));
    grp.addEventListener('mouseleave', hideTooltip);
    g.appendChild(grp);
  }
  svg.appendChild(g);
}

function showTooltip(ev, n) {
  const tip = document.getElementById('tooltip');
  tip.innerHTML = '<b>' + n.title + '</b><br>' + n.type + '<br><span style="color:#999">' + n.id + '</span>';
  tip.style.left = (ev.clientX + 14) + 'px';
  tip.style.top = (ev.clientY + 14) + 'px';
  tip.style.display = 'block';
}
function hideTooltip() { document.getElementById('tooltip').style.display = 'none'; }

svg.addEventListener('mousedown', (ev) => { panStart = { x: ev.clientX - transform.x, y: ev.clientY - transform.y }; });
window.addEventListener('mousemove', (ev) => { if (panStart) { transform.x = ev.clientX - panStart.x; transform.y = ev.clientY - panStart.y; render(); } });
window.addEventListener('mouseup', () => { panStart = null; });
svg.addEventListener('wheel', (ev) => {
  ev.preventDefault();
  const factor = ev.deltaY < 0 ? 1.1 : 0.9;
  transform.k = Math.min(4, Math.max(0.1, transform.k * factor));
  render();
}, { passive: false });

document.getElementById('search').addEventListener('input', (ev) => {
  const q = ev.target.value.trim().toLowerCase();
  for (const n of DATA.nodes) n._dim = q && !(n.title.toLowerCase().includes(q) || n.id.toLowerCase().includes(q));
  render();
});

for (let i = 0; i < 300; i++) step();
render();
</script>
</body>
</html>
"""


def render_html(nodes, edges):
    data = json.dumps({"nodes": nodes, "edges": edges})
    return HTML_TEMPLATE.replace("__DATA_JSON__", data)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python visualize.py <bundle_dir> [output_file]")
        sys.exit(1)

    bundle_dir = Path(sys.argv[1])
    if not bundle_dir.is_dir():
        print(f"Error: {bundle_dir} is not a directory")
        sys.exit(1)

    output = Path(sys.argv[2]) if len(sys.argv) > 2 else bundle_dir / "visualization.html"

    nodes, edges = build_graph(bundle_dir)
    if not nodes:
        print(f"No .md files found under {bundle_dir}")
        sys.exit(1)

    output.write_text(render_html(nodes, edges))
    print(f"Wrote {output} ({len(nodes)} nodes, {len(edges)} edges)")
