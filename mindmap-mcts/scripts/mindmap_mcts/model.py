from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
import json
from pathlib import Path
import re
import tempfile
from typing import Any


NODE_TYPES = {"goal", "hypothesis", "option", "probe", "decision"}
NODE_STATES = {"frontier", "exploring", "verified", "pruned", "selected"}


class MindMapError(Exception):
    """Raised when a tree operation cannot be completed."""


def now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


@dataclass(frozen=True)
class Params:
    exploration_c: float = 0.7
    max_depth: int = 6
    max_iterations: int = 8
    branch_width: int = 3


@dataclass(frozen=True)
class Node:
    id: str
    parent: str | None
    content: str
    type: str
    state: str = "frontier"
    V: float = 0.5
    N: int = 0
    evidence: str = ""
    probe_type: str = ""
    source: str = ""
    confidence: str = ""
    created_at: str = field(default_factory=now_iso)
    updated_at: str = field(default_factory=now_iso)


@dataclass(frozen=True)
class Tree:
    title: str
    root_id: str
    params: Params
    nodes: list[Node]
    version: int = 1


def tree_to_dict(tree: Tree) -> dict[str, Any]:
    return {
        "version": tree.version,
        "title": tree.title,
        "root_id": tree.root_id,
        "params": asdict(tree.params),
        "nodes": [asdict(node) for node in tree.nodes],
    }


def tree_from_dict(payload: dict[str, Any]) -> Tree:
    try:
        params = Params(**payload.get("params", {}))
        nodes = [Node(**node_payload) for node_payload in payload["nodes"]]
        tree = Tree(
            version=payload.get("version", 1),
            title=payload["title"],
            root_id=payload["root_id"],
            params=params,
            nodes=nodes,
        )
    except KeyError as exc:
        raise MindMapError(f"missing required field: {exc.args[0]}") from exc
    except TypeError as exc:
        raise MindMapError(f"invalid tree payload: {exc}") from exc

    validate_tree(tree)
    return tree


def node_by_id(tree: Tree, node_id: str) -> Node:
    for node in tree.nodes:
        if node.id == node_id:
            return node
    raise MindMapError(f"node id not found: {node_id}")


def children_of(tree: Tree, parent_id: str) -> list[Node]:
    return [node for node in tree.nodes if node.parent == parent_id]


def replace_node(tree: Tree, replacement: Node) -> Tree:
    found = False
    nodes: list[Node] = []
    for node in tree.nodes:
        if node.id == replacement.id:
            nodes.append(replacement)
            found = True
        else:
            nodes.append(node)
    if not found:
        raise MindMapError(f"node id not found: {replacement.id}")
    return Tree(
        version=tree.version,
        title=tree.title,
        root_id=tree.root_id,
        params=tree.params,
        nodes=nodes,
    )


def validate_tree(tree: Tree) -> None:
    if not _is_int(tree.version):
        raise MindMapError("tree version must be an integer")
    if tree.version != 1:
        raise MindMapError(f"unsupported tree version: {tree.version}")
    if not isinstance(tree.title, str):
        raise MindMapError("tree title must be a string")
    if not tree.title.strip():
        raise MindMapError("tree title must not be empty")
    if not isinstance(tree.root_id, str):
        raise MindMapError("root_id must be a string")
    if not _is_number(tree.params.exploration_c):
        raise MindMapError("exploration_c must be numeric")
    if tree.params.exploration_c < 0:
        raise MindMapError("exploration_c must be non-negative")
    if not _is_int(tree.params.max_depth):
        raise MindMapError("max_depth must be an integer")
    if tree.params.max_depth < 1:
        raise MindMapError("max_depth must be at least 1")
    if not _is_int(tree.params.max_iterations):
        raise MindMapError("max_iterations must be an integer")
    if tree.params.max_iterations < 1:
        raise MindMapError("max_iterations must be at least 1")
    if not _is_int(tree.params.branch_width):
        raise MindMapError("branch_width must be an integer")
    if tree.params.branch_width < 1:
        raise MindMapError("branch_width must be at least 1")

    ids: set[str] = set()
    for node in tree.nodes:
        if not isinstance(node.id, str):
            raise MindMapError("node id must be a string")
        if node.id in ids:
            raise MindMapError(f"duplicate node id: {node.id}")
        ids.add(node.id)
        if not node.id.strip():
            raise MindMapError("node id must not be empty")
        if node.parent is not None and not isinstance(node.parent, str):
            raise MindMapError(f"parent must be a string for {node.id}")
        if not isinstance(node.type, str):
            raise MindMapError(f"type must be a string for {node.id}")
        if node.type not in NODE_TYPES:
            raise MindMapError(f"invalid node type for {node.id}: {node.type}")
        if not isinstance(node.state, str):
            raise MindMapError(f"state must be a string for {node.id}")
        if node.state not in NODE_STATES:
            raise MindMapError(f"invalid node state for {node.id}: {node.state}")
        if not _is_number(node.V):
            raise MindMapError(f"V must be numeric for {node.id}")
        if not 0 <= node.V <= 1:
            raise MindMapError(f"V must be between 0 and 1 for {node.id}")
        if not _is_int(node.N):
            raise MindMapError(f"N must be an integer for {node.id}")
        if node.N < 0:
            raise MindMapError(f"N must be non-negative for {node.id}")
        if not isinstance(node.content, str):
            raise MindMapError(f"content must be a string for {node.id}")
        if not node.content.strip():
            raise MindMapError(f"content must not be empty for {node.id}")

    if tree.root_id not in ids:
        raise MindMapError(f"root_id not found: {tree.root_id}")

    roots = [node for node in tree.nodes if node.parent is None]
    if len(roots) != 1:
        raise MindMapError("tree must contain exactly one root node")
    if roots[0].id != tree.root_id:
        raise MindMapError("root node id must match root_id")

    for node in tree.nodes:
        if node.parent is not None and node.parent not in ids:
            raise MindMapError(f"orphan node {node.id} references {node.parent}")

    _validate_acyclic(tree)


def _validate_acyclic(tree: Tree) -> None:
    parent_by_id = {node.id: node.parent for node in tree.nodes}
    for node in tree.nodes:
        seen: set[str] = set()
        current: str | None = node.id
        while current is not None:
            if current in seen:
                raise MindMapError(f"cycle detected at node {current}")
            seen.add(current)
            current = parent_by_id[current]


def _is_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def _is_int(value: Any) -> bool:
    return isinstance(value, int) and not isinstance(value, bool)


def next_node_id(tree: Tree) -> str:
    highest = 0
    for node in tree.nodes:
        match = re.fullmatch(r"n(\d+)", node.id)
        if match:
            highest = max(highest, int(match.group(1)))
    return f"n{highest + 1}"


def load_tree(path: str | Path) -> Tree:
    tree_path = Path(path)
    try:
        payload = json.loads(tree_path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise MindMapError(f"tree file not found: {tree_path}") from exc
    except json.JSONDecodeError as exc:
        raise MindMapError(f"invalid JSON in {tree_path}: {exc}") from exc
    return tree_from_dict(payload)


def save_tree(path: str | Path, tree: Tree) -> None:
    validate_tree(tree)
    tree_path = Path(path)
    tree_path.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(tree_to_dict(tree), ensure_ascii=False, indent=2)
    payload += "\n"

    with tempfile.NamedTemporaryFile(
        "w",
        encoding="utf-8",
        dir=str(tree_path.parent),
        delete=False,
    ) as tmp:
        tmp.write(payload)
        tmp_path = Path(tmp.name)

    tmp_path.replace(tree_path)
