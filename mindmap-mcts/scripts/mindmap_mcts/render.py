from __future__ import annotations

from html import escape

from .engine import best_path, frontier_nodes, select_frontier
from .model import Node, Tree, children_of


def render_markdown(tree: Tree) -> str:
    lines = [f"# {tree.title}", ""]
    root = next(node for node in tree.nodes if node.id == tree.root_id)
    lines.extend(_render_node(tree, root, depth=0))
    return "\n".join(lines) + "\n"


def render_summary(tree: Tree) -> str:
    path = best_path(tree)
    frontiers = frontier_nodes(tree)
    best_value = path[-1].V if path else 0
    lines = [
        f"Title: {tree.title}",
        f"Root: {tree.root_id}",
        f"Nodes: {len(tree.nodes)}",
        f"Best path: {' -> '.join(node.id for node in path)}",
        f"Best value: {best_value:.2f}",
        f"Frontier nodes: {', '.join(node.id for node in frontiers) if frontiers else '(none)'}",
        f"Budget: max_depth={tree.params.max_depth}, max_iterations={tree.params.max_iterations}, branch_width={tree.params.branch_width}",
    ]
    return "\n".join(lines) + "\n"


def render_path(tree: Tree) -> str:
    lines = [f"Best path for: {tree.title}"]
    for index, node in enumerate(best_path(tree), start=1):
        detail = f"{index}. {node.id} {node.content} (V={node.V:.2f} N={node.N} {node.state})"
        lines.append(detail)
        if node.evidence:
            lines.append(f"   evidence: {node.evidence}")
        metadata = _evidence_metadata(node)
        if metadata:
            lines.append(f"   {metadata}")
    return "\n".join(lines) + "\n"


def render_next(tree: Tree) -> str:
    selected = select_frontier(tree)
    path = best_path(tree)
    lines = [
        f"Selected frontier: {selected.id}",
        f"Frontier content: {selected.content}",
        f"Recommended action: expand {selected.id} with 2-3 concrete, verifiable child nodes",
        f"Current best path: {' -> '.join(node.id for node in path)}",
        "Best path evidence:",
    ]
    for node in path:
        if node.evidence:
            lines.append(f"- {node.id}: {node.evidence}")
        metadata = _evidence_metadata(node)
        if metadata:
            lines.append(f"  {metadata}")
    return "\n".join(lines) + "\n"


def render_html(tree: Tree) -> str:
    node_cards = "\n".join(_render_html_node(tree, node) for node in _root_order(tree))
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>MindMap-MCTS: {escape(tree.title)}</title>
  <style>
    :root {{
      color-scheme: light;
      --bg: #f8fafc;
      --panel: #ffffff;
      --text: #0f172a;
      --muted: #475569;
      --line: #cbd5e1;
      --frontier: #64748b;
      --exploring: #2563eb;
      --verified: #059669;
      --pruned: #e11d48;
      --selected: #7c3aed;
    }}
    body {{
      margin: 0;
      background: var(--bg);
      color: var(--text);
      font-family: ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
    }}
    main {{
      max-width: 1100px;
      margin: 0 auto;
      padding: 36px 22px 64px;
    }}
    h1 {{
      margin: 0 0 8px;
      font-size: 30px;
      line-height: 1.15;
    }}
    .subtitle {{
      color: var(--muted);
      margin: 0 0 26px;
    }}
    .tree {{
      display: grid;
      gap: 12px;
    }}
    .node {{
      margin-left: calc(var(--depth) * 28px);
      border: 1px solid var(--line);
      border-left: 7px solid var(--state-color);
      background: var(--panel);
      border-radius: 10px;
      padding: 14px 16px;
      box-shadow: 0 8px 24px rgba(15, 23, 42, 0.07);
    }}
    .node header {{
      display: flex;
      align-items: baseline;
      gap: 10px;
      flex-wrap: wrap;
      margin-bottom: 7px;
    }}
    .id {{
      font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
      font-weight: 700;
    }}
    .state {{
      color: var(--state-color);
      font-weight: 700;
    }}
    .content {{
      font-weight: 650;
      font-size: 17px;
    }}
    .metrics, .evidence, .metadata {{
      color: var(--muted);
      font-size: 14px;
      line-height: 1.45;
    }}
  </style>
</head>
<body>
  <main>
    <h1>MindMap-MCTS: {escape(tree.title)}</h1>
    <p class="subtitle">JSON is the truth source. This page is a static rendered view.</p>
    <section class="tree">
{node_cards}
    </section>
  </main>
</body>
</html>
"""


def _render_node(tree: Tree, node: Node, depth: int) -> list[str]:
    indent = "  " * depth
    evidence = f" -- {node.evidence}" if node.evidence else ""
    line = f"{indent}- [{node.id}] (V={node.V:.2f} N={node.N} {node.state}) {node.content}{evidence}"
    lines = [line]
    for child in children_of(tree, node.id):
        lines.extend(_render_node(tree, child, depth + 1))
    return lines


def _evidence_metadata(node: Node) -> str:
    parts = []
    if node.probe_type:
        parts.append(f"probe_type={node.probe_type}")
    if node.source:
        parts.append(f"source={node.source}")
    if node.confidence:
        parts.append(f"confidence={node.confidence}")
    return ", ".join(parts)


def _root_order(tree: Tree) -> list[Node]:
    root = next(node for node in tree.nodes if node.id == tree.root_id)
    ordered: list[Node] = []

    def visit(node: Node) -> None:
        ordered.append(node)
        for child in children_of(tree, node.id):
            visit(child)

    visit(root)
    return ordered


def _node_depth(tree: Tree, node: Node) -> int:
    depth = 0
    current = node
    while current.parent is not None:
        depth += 1
        current = next(parent for parent in tree.nodes if parent.id == current.parent)
    return depth


def _state_color(state: str) -> str:
    return {
        "frontier": "var(--frontier)",
        "exploring": "var(--exploring)",
        "verified": "var(--verified)",
        "pruned": "var(--pruned)",
        "selected": "var(--selected)",
    }.get(state, "var(--frontier)")


def _render_html_node(tree: Tree, node: Node) -> str:
    actual_depth = _node_depth(tree, node)
    metadata = _evidence_metadata(node)
    evidence_html = f'<div class="evidence">Evidence: {escape(node.evidence)}</div>' if node.evidence else ""
    metadata_html = f'<div class="metadata">{escape(metadata)}</div>' if metadata else ""
    return f"""      <article class="node" data-node-id="{escape(node.id)}" style="--depth: {actual_depth}; --state-color: {_state_color(node.state)}">
        <header>
          <span class="id">{escape(node.id)}</span>
          <span class="state">{escape(node.state)}</span>
          <span class="metrics">V={node.V:.2f} N={node.N}</span>
        </header>
        <div class="content">{escape(node.content)}</div>
        {evidence_html}
        {metadata_html}
      </article>"""
