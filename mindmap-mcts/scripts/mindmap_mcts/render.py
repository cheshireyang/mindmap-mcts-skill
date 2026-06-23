from __future__ import annotations

from .engine import best_path, frontier_nodes
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


def _render_node(tree: Tree, node: Node, depth: int) -> list[str]:
    indent = "  " * depth
    evidence = f" -- {node.evidence}" if node.evidence else ""
    line = f"{indent}- [{node.id}] (V={node.V:.2f} N={node.N} {node.state}) {node.content}{evidence}"
    lines = [line]
    for child in children_of(tree, node.id):
        lines.extend(_render_node(tree, child, depth + 1))
    return lines
