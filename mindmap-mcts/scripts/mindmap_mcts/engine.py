from __future__ import annotations

from dataclasses import replace
import math

from .model import (
    MindMapError,
    Node,
    Params,
    Tree,
    children_of,
    next_node_id,
    node_by_id,
    now_iso,
    replace_node,
    validate_tree,
)


def init_tree(title: str, params: Params | None = None) -> Tree:
    cleaned_title = title.strip()
    if not cleaned_title:
        raise MindMapError("title must not be empty")
    timestamp = now_iso()
    root = Node(
        id="n1",
        parent=None,
        content=cleaned_title,
        type="goal",
        state="exploring",
        V=0.5,
        N=0,
        evidence="Initial goal",
        created_at=timestamp,
        updated_at=timestamp,
    )
    tree = Tree(title=cleaned_title, root_id="n1", params=params or Params(), nodes=[root])
    validate_tree(tree)
    return tree


def add_node(
    tree: Tree,
    parent_id: str,
    content: str,
    node_type: str,
    *,
    force: bool = False,
) -> tuple[Tree, Node]:
    parent = node_by_id(tree, parent_id)
    if parent.state == "pruned" and not force:
        raise MindMapError(f"cannot add a child to pruned node: {parent_id}")
    cleaned_content = content.strip()
    if not cleaned_content:
        raise MindMapError("content must not be empty")
    timestamp = now_iso()
    child = Node(
        id=next_node_id(tree),
        parent=parent_id,
        content=cleaned_content,
        type=node_type,
        state="frontier",
        V=0.5,
        N=0,
        evidence="",
        created_at=timestamp,
        updated_at=timestamp,
    )
    updated_tree = Tree(
        version=tree.version,
        title=tree.title,
        root_id=tree.root_id,
        params=tree.params,
        nodes=[*tree.nodes, child],
    )
    validate_tree(updated_tree)
    return updated_tree, child


def evaluate_node(
    tree: Tree,
    node_id: str,
    value: float,
    evidence: str,
    *,
    state: str | None = None,
) -> Tree:
    if not 0 <= value <= 1:
        raise MindMapError("value must be between 0 and 1")
    node = node_by_id(tree, node_id)
    chosen_state = state or ("verified" if value >= 0.85 else "exploring")
    updated = replace(
        node,
        V=float(value),
        evidence=evidence.strip(),
        state=chosen_state,
        updated_at=now_iso(),
    )
    updated_tree = replace_node(tree, updated)
    validate_tree(updated_tree)
    return updated_tree


def prune_node(tree: Tree, node_id: str, evidence: str) -> Tree:
    node = node_by_id(tree, node_id)
    updated = replace(
        node,
        V=0.0,
        evidence=evidence.strip(),
        state="pruned",
        updated_at=now_iso(),
    )
    updated_tree = replace_node(tree, updated)
    validate_tree(updated_tree)
    return updated_tree


def ucb_score(parent_visits: int, child_value: float, child_visits: int, c: float) -> float:
    if child_visits == 0:
        return math.inf
    return child_value + c * math.sqrt(math.log(parent_visits + 1) / child_visits)


def select_frontier(tree: Tree) -> Node:
    current = node_by_id(tree, tree.root_id)
    while True:
        candidates = [child for child in children_of(tree, current.id) if child.state != "pruned"]
        if not candidates:
            return current
        current = max(
            candidates,
            key=lambda child: (
                ucb_score(current.N, child.V, child.N, tree.params.exploration_c),
                child.V,
                _numeric_id_tiebreak(child.id),
            ),
        )


def backpropagate(tree: Tree, from_id: str) -> Tree:
    path = _path_to_root(tree, from_id)
    updated_tree = tree
    for node in path:
        current = node_by_id(updated_tree, node.id)
        children = [child for child in children_of(updated_tree, current.id) if child.state != "pruned"]
        value = max((child.V for child in children), default=current.V)
        updated = replace(current, N=current.N + 1, V=value, updated_at=now_iso())
        updated_tree = replace_node(updated_tree, updated)
    validate_tree(updated_tree)
    return updated_tree


def frontier_nodes(tree: Tree) -> list[Node]:
    leaves: list[Node] = []
    for node in tree.nodes:
        if node.state == "pruned":
            continue
        children = [child for child in children_of(tree, node.id) if child.state != "pruned"]
        if not children:
            leaves.append(node)
    return leaves


def best_path(tree: Tree) -> list[Node]:
    path = [node_by_id(tree, tree.root_id)]
    while True:
        children = [child for child in children_of(tree, path[-1].id) if child.state != "pruned"]
        if not children:
            return path
        path.append(
            max(
                children,
                key=lambda child: (child.V, child.N, _numeric_id_tiebreak(child.id)),
            )
        )


def _path_to_root(tree: Tree, node_id: str) -> list[Node]:
    by_id = {node.id: node for node in tree.nodes}
    if node_id not in by_id:
        raise MindMapError(f"node id not found: {node_id}")
    path: list[Node] = []
    current: Node | None = by_id[node_id]
    while current is not None:
        path.append(current)
        current = by_id[current.parent] if current.parent is not None else None
    return path


def _numeric_id_tiebreak(node_id: str) -> int:
    if node_id.startswith("n") and node_id[1:].isdigit():
        return -int(node_id[1:])
    return 0
