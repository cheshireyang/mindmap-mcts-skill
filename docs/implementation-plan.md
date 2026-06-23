# MindMap-MCTS Codex Skill Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a local Codex-first MindMap-MCTS toolchain with a Python CLI, JSON tree state, markdown rendering, tests, examples, and a Codex skill guide.

**Architecture:** The implementation is a small standard-library Python package under `tool/mindmap_mcts`. `model.py` owns serialization, validation, and atomic file writes; `engine.py` owns tree operations and MCTS selection/backprop; `render.py` owns markdown and text summaries; `cli.py` exposes the command interface. The skill document describes how Codex agents use the CLI without duplicating algorithm logic.

**Tech Stack:** Python 3.10+ standard library, `argparse`, `dataclasses`, `json`, `pytest` for tests, markdown for rendered views and skill docs.

---

## Scope Notes

The spec covers one coherent first-version loop: tree model, CLI operations, markdown rendering, and a Codex skill. These pieces are not independent products, so they stay in one plan.

`/home/yangdekun/mindmap` is currently not a git repository. Each task includes a commit step for use if the directory is later initialized as a repo. In the current directory state, the expected result of the commit step is a documented skip after `git -C /home/yangdekun/mindmap rev-parse --is-inside-work-tree` fails.

## File Structure

- Create: `/home/yangdekun/mindmap/tool/mindmap_mcts/__init__.py`
  - Package export surface and version string.
- Create: `/home/yangdekun/mindmap/tool/mindmap_mcts/model.py`
  - Dataclasses, JSON conversion, validation, stable node id generation, atomic load/save.
- Create: `/home/yangdekun/mindmap/tool/mindmap_mcts/engine.py`
  - Tree initialization, add/evaluate/prune/select/backprop/best-path/frontier logic.
- Create: `/home/yangdekun/mindmap/tool/mindmap_mcts/render.py`
  - Markdown tree rendering and CLI summary rendering.
- Create: `/home/yangdekun/mindmap/tool/mindmap_mcts/cli.py`
  - `argparse` CLI commands.
- Create: `/home/yangdekun/mindmap/tool/tests/test_model.py`
  - Serialization, validation, id generation, atomic save/load tests.
- Create: `/home/yangdekun/mindmap/tool/tests/test_engine.py`
  - Core operation and MCTS rule tests.
- Create: `/home/yangdekun/mindmap/tool/tests/test_render.py`
  - Markdown and summary output tests.
- Create: `/home/yangdekun/mindmap/tool/tests/test_cli.py`
  - End-to-end CLI behavior tests.
- Create: `/home/yangdekun/mindmap/skills/mindmap-mcts/SKILL.md`
  - Codex skill protocol for using the CLI loop.
- Create: `/home/yangdekun/mindmap/examples/login-timeout.tree.json`
  - Example tree state.
- Create: `/home/yangdekun/mindmap/examples/login-timeout.tree.md`
  - Rendered example tree.

---

### Task 1: Package Skeleton And Data Model

**Files:**
- Create: `/home/yangdekun/mindmap/tool/mindmap_mcts/__init__.py`
- Create: `/home/yangdekun/mindmap/tool/mindmap_mcts/model.py`
- Create: `/home/yangdekun/mindmap/tool/tests/test_model.py`

- [ ] **Step 1: Create package and test directories**

Run:

```bash
mkdir -p /home/yangdekun/mindmap/tool/mindmap_mcts /home/yangdekun/mindmap/tool/tests
```

Expected: directories exist and command prints no output.

- [ ] **Step 2: Write failing model tests**

Create `/home/yangdekun/mindmap/tool/tests/test_model.py` with:

```python
import json

import pytest

from mindmap_mcts.model import (
    MindMapError,
    Node,
    Params,
    Tree,
    load_tree,
    next_node_id,
    save_tree,
    tree_from_dict,
    tree_to_dict,
    validate_tree,
)


def test_tree_round_trips_through_plain_dict():
    tree = Tree(
        title="Root goal",
        root_id="n1",
        params=Params(),
        nodes=[
            Node(
                id="n1",
                parent=None,
                content="Root goal",
                type="goal",
                state="exploring",
                V=0.5,
                N=0,
                evidence="Initial goal",
                created_at="2026-06-23T00:00:00+00:00",
                updated_at="2026-06-23T00:00:00+00:00",
            )
        ],
    )

    payload = tree_to_dict(tree)
    restored = tree_from_dict(payload)

    assert restored == tree
    assert payload["version"] == 1
    assert payload["nodes"][0]["id"] == "n1"


def test_next_node_id_uses_highest_existing_numeric_suffix():
    tree = Tree(
        title="Root goal",
        root_id="n1",
        params=Params(),
        nodes=[
            Node(id="n1", parent=None, content="root", type="goal"),
            Node(id="n9", parent="n1", content="child", type="hypothesis"),
            Node(id="custom", parent="n1", content="manual", type="option"),
        ],
    )

    assert next_node_id(tree) == "n10"


def test_validate_rejects_duplicate_node_ids():
    tree = Tree(
        title="Root goal",
        root_id="n1",
        params=Params(),
        nodes=[
            Node(id="n1", parent=None, content="root", type="goal"),
            Node(id="n1", parent="n1", content="duplicate", type="option"),
        ],
    )

    with pytest.raises(MindMapError, match="duplicate node id"):
        validate_tree(tree)


def test_validate_rejects_invalid_value_range():
    tree = Tree(
        title="Root goal",
        root_id="n1",
        params=Params(),
        nodes=[Node(id="n1", parent=None, content="root", type="goal", V=1.5)],
    )

    with pytest.raises(MindMapError, match="V must be between 0 and 1"):
        validate_tree(tree)


def test_save_and_load_tree_use_json_file(tmp_path):
    path = tmp_path / "task.tree.json"
    tree = Tree(
        title="Root goal",
        root_id="n1",
        params=Params(),
        nodes=[Node(id="n1", parent=None, content="root", type="goal")],
    )

    save_tree(path, tree)
    raw = json.loads(path.read_text(encoding="utf-8"))
    loaded = load_tree(path)

    assert raw["title"] == "Root goal"
    assert loaded == tree
```

- [ ] **Step 3: Run model tests to verify they fail**

Run:

```bash
cd /home/yangdekun/mindmap/tool
PYTHONPATH=/home/yangdekun/mindmap/tool pytest tests/test_model.py -q
```

Expected: FAIL with `ModuleNotFoundError: No module named 'mindmap_mcts.model'`.

- [ ] **Step 4: Add package exports**

Create `/home/yangdekun/mindmap/tool/mindmap_mcts/__init__.py` with:

```python
"""MindMap-MCTS local tree engine."""

__version__ = "0.1.0"
```

- [ ] **Step 5: Implement the data model**

Create `/home/yangdekun/mindmap/tool/mindmap_mcts/model.py` with:

```python
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
    if tree.version != 1:
        raise MindMapError(f"unsupported tree version: {tree.version}")
    if not tree.title.strip():
        raise MindMapError("tree title must not be empty")
    if tree.params.exploration_c < 0:
        raise MindMapError("exploration_c must be non-negative")
    if tree.params.max_depth < 1:
        raise MindMapError("max_depth must be at least 1")
    if tree.params.max_iterations < 1:
        raise MindMapError("max_iterations must be at least 1")
    if tree.params.branch_width < 1:
        raise MindMapError("branch_width must be at least 1")

    ids: set[str] = set()
    for node in tree.nodes:
        if node.id in ids:
            raise MindMapError(f"duplicate node id: {node.id}")
        ids.add(node.id)
        if not node.id.strip():
            raise MindMapError("node id must not be empty")
        if node.type not in NODE_TYPES:
            raise MindMapError(f"invalid node type for {node.id}: {node.type}")
        if node.state not in NODE_STATES:
            raise MindMapError(f"invalid node state for {node.id}: {node.state}")
        if not 0 <= node.V <= 1:
            raise MindMapError(f"V must be between 0 and 1 for {node.id}")
        if node.N < 0:
            raise MindMapError(f"N must be non-negative for {node.id}")
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
```

- [ ] **Step 6: Run model tests to verify they pass**

Run:

```bash
cd /home/yangdekun/mindmap/tool
PYTHONPATH=/home/yangdekun/mindmap/tool pytest tests/test_model.py -q
```

Expected: PASS, `5 passed`.

- [ ] **Step 7: Commit or record skip**

Run:

```bash
git -C /home/yangdekun/mindmap rev-parse --is-inside-work-tree
```

Expected in current directory: FAIL with `fatal: not a git repository`. Record that commit is skipped because the project is not a git repository.

If the directory has been initialized as a repo before execution, run:

```bash
git -C /home/yangdekun/mindmap add tool/mindmap_mcts/__init__.py tool/mindmap_mcts/model.py tool/tests/test_model.py
git -C /home/yangdekun/mindmap commit -m "feat: add mindmap tree model"
```

Expected in a git repo: commit succeeds.

---

### Task 2: Core Tree Engine

**Files:**
- Create: `/home/yangdekun/mindmap/tool/mindmap_mcts/engine.py`
- Create: `/home/yangdekun/mindmap/tool/tests/test_engine.py`

- [ ] **Step 1: Write failing engine tests**

Create `/home/yangdekun/mindmap/tool/tests/test_engine.py` with:

```python
import math

import pytest

from mindmap_mcts.engine import (
    add_node,
    backpropagate,
    best_path,
    evaluate_node,
    frontier_nodes,
    init_tree,
    prune_node,
    select_frontier,
    ucb_score,
)
from mindmap_mcts.model import MindMapError, Node, Params, Tree, children_of, node_by_id


def test_init_tree_creates_exploring_root():
    tree = init_tree("Fix login timeout")

    assert tree.title == "Fix login timeout"
    assert tree.root_id == "n1"
    assert tree.nodes == [
        Node(
            id="n1",
            parent=None,
            content="Fix login timeout",
            type="goal",
            state="exploring",
            V=0.5,
            N=0,
            evidence="Initial goal",
            created_at=tree.nodes[0].created_at,
            updated_at=tree.nodes[0].updated_at,
        )
    ]


def test_add_node_attaches_child_and_uses_next_id():
    tree = init_tree("Root")
    tree, child = add_node(tree, parent_id="n1", content="DB pool exhausted", node_type="hypothesis")

    assert child.id == "n2"
    assert child.parent == "n1"
    assert child.type == "hypothesis"
    assert child.state == "frontier"
    assert children_of(tree, "n1") == [child]


def test_add_node_rejects_pruned_parent_without_force():
    tree = init_tree("Root")
    tree = prune_node(tree, "n1", evidence="not useful")

    with pytest.raises(MindMapError, match="cannot add a child to pruned node"):
        add_node(tree, parent_id="n1", content="child", node_type="option")


def test_evaluate_node_sets_default_state_from_value():
    tree = init_tree("Root")
    tree, child = add_node(tree, "n1", "Probe logs", "probe")

    tree = evaluate_node(tree, child.id, value=0.9, evidence="Log contains pool timeout")
    updated = node_by_id(tree, child.id)

    assert updated.V == 0.9
    assert updated.state == "verified"
    assert updated.evidence == "Log contains pool timeout"


def test_prune_node_sets_value_to_zero_and_state_pruned():
    tree = init_tree("Root")
    tree, child = add_node(tree, "n1", "Frontend retry storm", "hypothesis")

    tree = prune_node(tree, child.id, evidence="grep found no retry logic")
    updated = node_by_id(tree, child.id)

    assert updated.V == 0
    assert updated.state == "pruned"
    assert updated.evidence == "grep found no retry logic"


def test_ucb_score_prioritizes_unvisited_child():
    assert math.isinf(ucb_score(parent_visits=5, child_value=0.1, child_visits=0, c=0.7))
    assert ucb_score(parent_visits=5, child_value=0.7, child_visits=2, c=0.7) > 0.7


def test_select_frontier_ignores_pruned_nodes_and_prefers_unvisited():
    tree = init_tree("Root")
    tree, a = add_node(tree, "n1", "Already explored", "hypothesis")
    tree, b = add_node(tree, "n1", "Never explored", "hypothesis")
    tree, c = add_node(tree, "n1", "Pruned", "hypothesis")
    tree = evaluate_node(tree, a.id, value=0.9, evidence="strong signal")
    tree = backpropagate(tree, a.id)
    tree = prune_node(tree, c.id, evidence="ruled out")

    selected = select_frontier(tree)

    assert selected.id == b.id


def test_select_frontier_descends_until_leaf_frontier():
    tree = init_tree("Root")
    tree, a = add_node(tree, "n1", "Promising", "hypothesis")
    tree = evaluate_node(tree, a.id, value=0.8, evidence="good signal")
    tree = backpropagate(tree, a.id)
    tree, leaf = add_node(tree, a.id, "Specific probe", "probe")

    selected = select_frontier(tree)

    assert selected.id == leaf.id


def test_backpropagate_increments_path_and_sets_parent_to_best_child_value():
    tree = init_tree("Root")
    tree, low = add_node(tree, "n1", "Weak", "hypothesis")
    tree, high = add_node(tree, "n1", "Strong", "hypothesis")
    tree = evaluate_node(tree, low.id, value=0.2, evidence="weak signal")
    tree = evaluate_node(tree, high.id, value=0.85, evidence="strong signal")

    tree = backpropagate(tree, high.id)

    root = node_by_id(tree, "n1")
    updated_high = node_by_id(tree, high.id)
    assert root.N == 1
    assert updated_high.N == 1
    assert root.V == 0.85


def test_frontier_nodes_return_unpruned_leaf_nodes():
    tree = init_tree("Root")
    tree, a = add_node(tree, "n1", "A", "hypothesis")
    tree, b = add_node(tree, "n1", "B", "hypothesis")
    tree, leaf = add_node(tree, a.id, "Leaf", "probe")
    tree = prune_node(tree, b.id, evidence="ruled out")

    assert [node.id for node in frontier_nodes(tree)] == [leaf.id]


def test_best_path_follows_highest_value_unpruned_child():
    tree = init_tree("Root")
    tree, low = add_node(tree, "n1", "Low", "hypothesis")
    tree, high = add_node(tree, "n1", "High", "hypothesis")
    tree = evaluate_node(tree, low.id, 0.3, "weak")
    tree = evaluate_node(tree, high.id, 0.8, "strong")
    tree, leaf = add_node(tree, high.id, "Leaf", "probe")
    tree = evaluate_node(tree, leaf.id, 0.95, "verified")

    assert [node.id for node in best_path(tree)] == ["n1", high.id, leaf.id]
```

- [ ] **Step 2: Run engine tests to verify they fail**

Run:

```bash
cd /home/yangdekun/mindmap/tool
PYTHONPATH=/home/yangdekun/mindmap/tool pytest tests/test_engine.py -q
```

Expected: FAIL with `ModuleNotFoundError: No module named 'mindmap_mcts.engine'`.

- [ ] **Step 3: Implement the tree engine**

Create `/home/yangdekun/mindmap/tool/mindmap_mcts/engine.py` with:

```python
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
```

- [ ] **Step 4: Run engine tests to verify they pass**

Run:

```bash
cd /home/yangdekun/mindmap/tool
PYTHONPATH=/home/yangdekun/mindmap/tool pytest tests/test_engine.py -q
```

Expected: PASS, `11 passed`.

- [ ] **Step 5: Run model and engine tests together**

Run:

```bash
cd /home/yangdekun/mindmap/tool
PYTHONPATH=/home/yangdekun/mindmap/tool pytest tests/test_model.py tests/test_engine.py -q
```

Expected: PASS, `16 passed`.

- [ ] **Step 6: Commit or record skip**

Run:

```bash
git -C /home/yangdekun/mindmap rev-parse --is-inside-work-tree
```

Expected in current directory: FAIL with `fatal: not a git repository`. Record that commit is skipped because the project is not a git repository.

If the directory has been initialized as a repo before execution, run:

```bash
git -C /home/yangdekun/mindmap add tool/mindmap_mcts/engine.py tool/tests/test_engine.py
git -C /home/yangdekun/mindmap commit -m "feat: add mindmap tree engine"
```

Expected in a git repo: commit succeeds.

---

### Task 3: Markdown Rendering And Summaries

**Files:**
- Create: `/home/yangdekun/mindmap/tool/mindmap_mcts/render.py`
- Create: `/home/yangdekun/mindmap/tool/tests/test_render.py`

- [ ] **Step 1: Write failing render tests**

Create `/home/yangdekun/mindmap/tool/tests/test_render.py` with:

```python
from mindmap_mcts.engine import add_node, backpropagate, best_path, evaluate_node, init_tree, prune_node
from mindmap_mcts.render import render_markdown, render_summary


def test_render_markdown_preserves_tree_shape_and_evidence():
    tree = init_tree("Fix login timeout")
    tree, db = add_node(tree, "n1", "Hypothesis: DB pool exhausted", "hypothesis")
    tree = evaluate_node(tree, db.id, 0.9, "Logs contain pool timeout")
    tree = backpropagate(tree, db.id)
    tree, frontend = add_node(tree, "n1", "Hypothesis: frontend retry storm", "hypothesis")
    tree = prune_node(tree, frontend.id, "grep found no retry logic")

    rendered = render_markdown(tree)

    assert rendered.startswith("# Fix login timeout\n")
    assert "- [n1] (V=0.90 N=1 exploring) Fix login timeout -- Initial goal" in rendered
    assert "  - [n2] (V=0.90 N=1 verified) Hypothesis: DB pool exhausted -- Logs contain pool timeout" in rendered
    assert "  - [n3] (V=0.00 N=0 pruned) Hypothesis: frontend retry storm -- grep found no retry logic" in rendered


def test_render_summary_shows_best_path_and_frontiers():
    tree = init_tree("Root")
    tree, child = add_node(tree, "n1", "Promising branch", "hypothesis")
    tree = evaluate_node(tree, child.id, 0.86, "verified signal")
    tree = backpropagate(tree, child.id)

    summary = render_summary(tree)

    assert "Title: Root" in summary
    assert "Best path: n1 -> n2" in summary
    assert "Frontier nodes: n2" in summary
    assert "Best value: 0.86" in summary
    assert [node.id for node in best_path(tree)] == ["n1", "n2"]
```

- [ ] **Step 2: Run render tests to verify they fail**

Run:

```bash
cd /home/yangdekun/mindmap/tool
PYTHONPATH=/home/yangdekun/mindmap/tool pytest tests/test_render.py -q
```

Expected: FAIL with `ModuleNotFoundError: No module named 'mindmap_mcts.render'`.

- [ ] **Step 3: Implement markdown and summary rendering**

Create `/home/yangdekun/mindmap/tool/mindmap_mcts/render.py` with:

```python
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
```

- [ ] **Step 4: Run render tests to verify they pass**

Run:

```bash
cd /home/yangdekun/mindmap/tool
PYTHONPATH=/home/yangdekun/mindmap/tool pytest tests/test_render.py -q
```

Expected: PASS, `2 passed`.

- [ ] **Step 5: Run all current tests**

Run:

```bash
cd /home/yangdekun/mindmap/tool
PYTHONPATH=/home/yangdekun/mindmap/tool pytest tests/test_model.py tests/test_engine.py tests/test_render.py -q
```

Expected: PASS, `18 passed`.

- [ ] **Step 6: Commit or record skip**

Run:

```bash
git -C /home/yangdekun/mindmap rev-parse --is-inside-work-tree
```

Expected in current directory: FAIL with `fatal: not a git repository`. Record that commit is skipped because the project is not a git repository.

If the directory has been initialized as a repo before execution, run:

```bash
git -C /home/yangdekun/mindmap add tool/mindmap_mcts/render.py tool/tests/test_render.py
git -C /home/yangdekun/mindmap commit -m "feat: render mindmap trees"
```

Expected in a git repo: commit succeeds.

---

### Task 4: CLI Commands

**Files:**
- Create: `/home/yangdekun/mindmap/tool/mindmap_mcts/cli.py`
- Create: `/home/yangdekun/mindmap/tool/tests/test_cli.py`

- [ ] **Step 1: Write failing CLI tests**

Create `/home/yangdekun/mindmap/tool/tests/test_cli.py` with:

```python
import json
import subprocess
import sys


def run_cli(*args, cwd=None):
    return subprocess.run(
        [sys.executable, "-m", "mindmap_mcts.cli", *args],
        cwd=cwd,
        text=True,
        capture_output=True,
        check=False,
    )


def test_cli_init_add_eval_backprop_render_show(tmp_path):
    tree_path = tmp_path / "task.tree.json"
    md_path = tmp_path / "task.tree.md"

    result = run_cli("init", "--title", "Fix login timeout", "--out", str(tree_path))
    assert result.returncode == 0, result.stderr
    assert tree_path.exists()

    result = run_cli(
        "add",
        str(tree_path),
        "--parent",
        "n1",
        "--type",
        "hypothesis",
        "--content",
        "DB pool exhausted",
    )
    assert result.returncode == 0, result.stderr
    assert "Added n2" in result.stdout

    result = run_cli(
        "eval",
        str(tree_path),
        "--id",
        "n2",
        "--value",
        "0.9",
        "--evidence",
        "Logs contain pool timeout",
    )
    assert result.returncode == 0, result.stderr

    result = run_cli("backprop", str(tree_path), "--from", "n2")
    assert result.returncode == 0, result.stderr

    result = run_cli("render", str(tree_path), "--out", str(md_path))
    assert result.returncode == 0, result.stderr
    assert "DB pool exhausted -- Logs contain pool timeout" in md_path.read_text(encoding="utf-8")

    result = run_cli("show", str(tree_path))
    assert result.returncode == 0, result.stderr
    assert "Best path: n1 -> n2" in result.stdout

    payload = json.loads(tree_path.read_text(encoding="utf-8"))
    assert payload["nodes"][0]["V"] == 0.9


def test_cli_select_prints_frontier_node(tmp_path):
    tree_path = tmp_path / "task.tree.json"
    assert run_cli("init", "--title", "Root", "--out", str(tree_path)).returncode == 0
    assert run_cli("add", str(tree_path), "--parent", "n1", "--type", "hypothesis", "--content", "A").returncode == 0

    result = run_cli("select", str(tree_path))

    assert result.returncode == 0, result.stderr
    assert "Selected n2" in result.stdout


def test_cli_invalid_value_returns_nonzero(tmp_path):
    tree_path = tmp_path / "task.tree.json"
    assert run_cli("init", "--title", "Root", "--out", str(tree_path)).returncode == 0

    result = run_cli("eval", str(tree_path), "--id", "n1", "--value", "2", "--evidence", "bad")

    assert result.returncode == 2
    assert "value must be between 0 and 1" in result.stderr
```

- [ ] **Step 2: Run CLI tests to verify they fail**

Run:

```bash
cd /home/yangdekun/mindmap/tool
PYTHONPATH=/home/yangdekun/mindmap/tool pytest tests/test_cli.py -q
```

Expected: FAIL with `No module named mindmap_mcts.cli`.

- [ ] **Step 3: Implement the CLI**

Create `/home/yangdekun/mindmap/tool/mindmap_mcts/cli.py` with:

```python
from __future__ import annotations

import argparse
from pathlib import Path
import sys

from .engine import add_node, backpropagate, evaluate_node, init_tree, prune_node, select_frontier
from .model import MindMapError, load_tree, save_tree
from .render import render_markdown, render_summary


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="mindmap", description="MindMap-MCTS tree engine")
    subcommands = parser.add_subparsers(dest="command", required=True)

    init_parser = subcommands.add_parser("init", help="create a new tree")
    init_parser.add_argument("--title", required=True)
    init_parser.add_argument("--out", required=True)
    init_parser.set_defaults(func=cmd_init)

    add_parser = subcommands.add_parser("add", help="add a child node")
    add_parser.add_argument("tree")
    add_parser.add_argument("--parent", required=True)
    add_parser.add_argument("--type", required=True)
    add_parser.add_argument("--content", required=True)
    add_parser.add_argument("--force", action="store_true")
    add_parser.set_defaults(func=cmd_add)

    eval_parser = subcommands.add_parser("eval", help="evaluate a node")
    eval_parser.add_argument("tree")
    eval_parser.add_argument("--id", required=True)
    eval_parser.add_argument("--value", required=True, type=float)
    eval_parser.add_argument("--evidence", required=True)
    eval_parser.add_argument("--state", choices=["frontier", "exploring", "verified", "pruned", "selected"])
    eval_parser.set_defaults(func=cmd_eval)

    prune_parser = subcommands.add_parser("prune", help="prune a node")
    prune_parser.add_argument("tree")
    prune_parser.add_argument("--id", required=True)
    prune_parser.add_argument("--evidence", required=True)
    prune_parser.set_defaults(func=cmd_prune)

    select_parser = subcommands.add_parser("select", help="select the next frontier")
    select_parser.add_argument("tree")
    select_parser.set_defaults(func=cmd_select)

    backprop_parser = subcommands.add_parser("backprop", help="backpropagate from a node")
    backprop_parser.add_argument("tree")
    backprop_parser.add_argument("--from", dest="from_id", required=True)
    backprop_parser.set_defaults(func=cmd_backprop)

    render_parser = subcommands.add_parser("render", help="render tree markdown")
    render_parser.add_argument("tree")
    render_parser.add_argument("--out", required=True)
    render_parser.set_defaults(func=cmd_render)

    show_parser = subcommands.add_parser("show", help="show tree summary")
    show_parser.add_argument("tree")
    show_parser.set_defaults(func=cmd_show)

    return parser


def cmd_init(args: argparse.Namespace) -> int:
    tree = init_tree(args.title)
    save_tree(args.out, tree)
    print(f"Created {args.out}")
    return 0


def cmd_add(args: argparse.Namespace) -> int:
    tree_path = Path(args.tree)
    tree = load_tree(tree_path)
    tree, node = add_node(tree, args.parent, args.content, args.type, force=args.force)
    save_tree(tree_path, tree)
    print(f"Added {node.id}")
    return 0


def cmd_eval(args: argparse.Namespace) -> int:
    tree_path = Path(args.tree)
    tree = load_tree(tree_path)
    tree = evaluate_node(tree, args.id, args.value, args.evidence, state=args.state)
    save_tree(tree_path, tree)
    print(f"Evaluated {args.id}")
    return 0


def cmd_prune(args: argparse.Namespace) -> int:
    tree_path = Path(args.tree)
    tree = load_tree(tree_path)
    tree = prune_node(tree, args.id, args.evidence)
    save_tree(tree_path, tree)
    print(f"Pruned {args.id}")
    return 0


def cmd_select(args: argparse.Namespace) -> int:
    tree = load_tree(args.tree)
    node = select_frontier(tree)
    print(f"Selected {node.id}: {node.content}")
    return 0


def cmd_backprop(args: argparse.Namespace) -> int:
    tree_path = Path(args.tree)
    tree = load_tree(tree_path)
    tree = backpropagate(tree, args.from_id)
    save_tree(tree_path, tree)
    print(f"Backpropagated from {args.from_id}")
    return 0


def cmd_render(args: argparse.Namespace) -> int:
    tree = load_tree(args.tree)
    output_path = Path(args.out)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(render_markdown(tree), encoding="utf-8")
    print(f"Rendered {args.out}")
    return 0


def cmd_show(args: argparse.Namespace) -> int:
    tree = load_tree(args.tree)
    print(render_summary(tree), end="")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return args.func(args)
    except MindMapError as exc:
        print(str(exc), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 4: Run CLI tests to verify they pass**

Run:

```bash
cd /home/yangdekun/mindmap/tool
PYTHONPATH=/home/yangdekun/mindmap/tool pytest tests/test_cli.py -q
```

Expected: PASS, `3 passed`.

- [ ] **Step 5: Run full Python test suite**

Run:

```bash
cd /home/yangdekun/mindmap/tool
PYTHONPATH=/home/yangdekun/mindmap/tool pytest tests -q
```

Expected: PASS, `21 passed`.

- [ ] **Step 6: Commit or record skip**

Run:

```bash
git -C /home/yangdekun/mindmap rev-parse --is-inside-work-tree
```

Expected in current directory: FAIL with `fatal: not a git repository`. Record that commit is skipped because the project is not a git repository.

If the directory has been initialized as a repo before execution, run:

```bash
git -C /home/yangdekun/mindmap add tool/mindmap_mcts/cli.py tool/tests/test_cli.py
git -C /home/yangdekun/mindmap commit -m "feat: add mindmap cli"
```

Expected in a git repo: commit succeeds.

---

### Task 5: Codex Skill Document

**Files:**
- Create: `/home/yangdekun/mindmap/skills/mindmap-mcts/SKILL.md`

- [ ] **Step 1: Create skill directory**

Run:

```bash
mkdir -p /home/yangdekun/mindmap/skills/mindmap-mcts
```

Expected: directory exists and command prints no output.

- [ ] **Step 2: Write the skill document**

Create `/home/yangdekun/mindmap/skills/mindmap-mcts/SKILL.md` with:

```markdown
---
name: mindmap-mcts
description: Use when a Codex task is complex, has multiple plausible paths, needs systematic debugging, or shows signs of repeated trial-and-error; runs a visible reasoning tree with lightweight MCTS selection and evidence-backed evaluation.
---

# MindMap-MCTS

Use this skill to keep complex Codex work on a visible, evidence-backed reasoning tree instead of a hidden linear thread.

## Trigger

Use MindMap-MCTS when any of these are true:

- The task has multiple plausible hypotheses, designs, or implementation paths.
- Debugging needs systematic elimination of likely causes.
- The model has already tried more than one path without converging.
- The user asks for a mindmap, reasoning tree, MCTS, or visible exploration.

Do not use it for simple one-step commands, obvious one-file edits, or direct factual lookups.

## Required Tool

Use the local CLI through Python module execution unless a `mindmap` console script has been installed:

```bash
PYTHONPATH=/home/yangdekun/mindmap/tool python3 -m mindmap_mcts.cli --help
```

Never hand-edit rendered markdown as the truth source. The JSON tree is the truth source.

## Tree Files

For each task, keep files near the work being analyzed or under a local scratch directory:

```text
<task-name>.tree.json
<task-name>.tree.md
```

The JSON file stores state. The markdown file is a rendered view for people and agents.

## Startup

1. Decide whether this skill applies.
2. If no tree exists, create one:

```bash
PYTHONPATH=/home/yangdekun/mindmap/tool python3 -m mindmap_mcts.cli init --title "<task title>" --out <task-name>.tree.json
```

3. If a tree exists, inspect it:

```bash
PYTHONPATH=/home/yangdekun/mindmap/tool python3 -m mindmap_mcts.cli show <task-name>.tree.json
```

4. Render the readable view:

```bash
PYTHONPATH=/home/yangdekun/mindmap/tool python3 -m mindmap_mcts.cli render <task-name>.tree.json --out <task-name>.tree.md
```

## Per-Round Loop

1. Select the next frontier:

```bash
PYTHONPATH=/home/yangdekun/mindmap/tool python3 -m mindmap_mcts.cli select <task-name>.tree.json
```

2. Expand the selected node with 2 or 3 child nodes. Children must be mutually exclusive, concrete, and verifiable.

```bash
PYTHONPATH=/home/yangdekun/mindmap/tool python3 -m mindmap_mcts.cli add <task-name>.tree.json --parent <node-id> --type hypothesis --content "<specific hypothesis>"
```

3. Evaluate each new child using the cheapest real probe available: read code, grep a symbol, run a focused test, inspect a log, or check a config.

4. Record the value and evidence:

```bash
PYTHONPATH=/home/yangdekun/mindmap/tool python3 -m mindmap_mcts.cli eval <task-name>.tree.json --id <node-id> --value <0-to-1> --evidence "<short evidence>"
```

5. Prune disproven branches instead of deleting them:

```bash
PYTHONPATH=/home/yangdekun/mindmap/tool python3 -m mindmap_mcts.cli prune <task-name>.tree.json --id <node-id> --evidence "<why this branch is ruled out>"
```

6. Backpropagate from evaluated nodes:

```bash
PYTHONPATH=/home/yangdekun/mindmap/tool python3 -m mindmap_mcts.cli backprop <task-name>.tree.json --from <node-id>
```

7. Render and show the updated state:

```bash
PYTHONPATH=/home/yangdekun/mindmap/tool python3 -m mindmap_mcts.cli render <task-name>.tree.json --out <task-name>.tree.md
PYTHONPATH=/home/yangdekun/mindmap/tool python3 -m mindmap_mcts.cli show <task-name>.tree.json
```

## Evaluation Scale

- `0.90` to `1.00`: real evidence verifies this path reaches the target.
- `0.60` to `0.80`: strong signal, still needs confirmation.
- `0.30` to `0.50`: uncertain or neutral signal.
- `0.10` to `0.20`: evidence mostly rules this out.
- `0.00`: confirmed dead branch; prune it.

## Stop Conditions

Stop exploring and write an execution plan when one of these is true:

- A root-to-leaf path has value at least `0.85` and key nodes have real evidence.
- The iteration budget is exhausted.
- Several paths remain close in value and no cheap probe can separate them.

When multiple paths remain close, stop and ask the user to choose. Show the best path, close alternatives, and evidence for each.

## Reporting

When reporting progress, include:

- Current selected frontier.
- New child nodes and why they are distinct.
- Probe evidence for each evaluated node.
- Pruned branches and why they should not be retried.
- Updated best path.
```

- [ ] **Step 3: Verify the skill document has required sections**

Run:

```bash
rg -n "Trigger|Required Tool|Per-Round Loop|Evaluation Scale|Stop Conditions|Never hand-edit" /home/yangdekun/mindmap/skills/mindmap-mcts/SKILL.md
```

Expected: output includes all six section names or required phrases.

- [ ] **Step 4: Commit or record skip**

Run:

```bash
git -C /home/yangdekun/mindmap rev-parse --is-inside-work-tree
```

Expected in current directory: FAIL with `fatal: not a git repository`. Record that commit is skipped because the project is not a git repository.

If the directory has been initialized as a repo before execution, run:

```bash
git -C /home/yangdekun/mindmap add skills/mindmap-mcts/SKILL.md
git -C /home/yangdekun/mindmap commit -m "docs: add mindmap mcts skill"
```

Expected in a git repo: commit succeeds.

---

### Task 6: Example Tree And End-To-End Verification

**Files:**
- Create: `/home/yangdekun/mindmap/examples/login-timeout.tree.json`
- Create: `/home/yangdekun/mindmap/examples/login-timeout.tree.md`

- [ ] **Step 1: Create examples directory**

Run:

```bash
mkdir -p /home/yangdekun/mindmap/examples
```

Expected: directory exists and command prints no output.

- [ ] **Step 2: Generate the example tree through the CLI**

Run:

```bash
cd /home/yangdekun/mindmap
PYTHONPATH=/home/yangdekun/mindmap/tool python3 -m mindmap_mcts.cli init --title "Fix intermittent login timeout" --out examples/login-timeout.tree.json
PYTHONPATH=/home/yangdekun/mindmap/tool python3 -m mindmap_mcts.cli add examples/login-timeout.tree.json --parent n1 --type hypothesis --content "DB connection pool is exhausted"
PYTHONPATH=/home/yangdekun/mindmap/tool python3 -m mindmap_mcts.cli eval examples/login-timeout.tree.json --id n2 --value 0.90 --evidence "Logs contain pool timeout during failed login"
PYTHONPATH=/home/yangdekun/mindmap/tool python3 -m mindmap_mcts.cli backprop examples/login-timeout.tree.json --from n2
PYTHONPATH=/home/yangdekun/mindmap/tool python3 -m mindmap_mcts.cli add examples/login-timeout.tree.json --parent n1 --type hypothesis --content "Frontend retry storm overloads login"
PYTHONPATH=/home/yangdekun/mindmap/tool python3 -m mindmap_mcts.cli prune examples/login-timeout.tree.json --id n3 --evidence "grep found no retry loop in login client"
PYTHONPATH=/home/yangdekun/mindmap/tool python3 -m mindmap_mcts.cli render examples/login-timeout.tree.json --out examples/login-timeout.tree.md
```

Expected:

- `examples/login-timeout.tree.json` exists.
- `examples/login-timeout.tree.md` exists.
- Command output includes `Created`, `Added n2`, `Evaluated n2`, `Backpropagated from n2`, `Added n3`, `Pruned n3`, and `Rendered`.

- [ ] **Step 3: Verify example summary**

Run:

```bash
cd /home/yangdekun/mindmap
PYTHONPATH=/home/yangdekun/mindmap/tool python3 -m mindmap_mcts.cli show examples/login-timeout.tree.json
```

Expected output contains:

```text
Title: Fix intermittent login timeout
Best path: n1 -> n2
Best value: 0.90
Frontier nodes: n2
```

- [ ] **Step 4: Verify rendered markdown contains the evidence trail**

Run:

```bash
rg -n "DB connection pool is exhausted|Frontend retry storm|pool timeout|grep found no retry loop" /home/yangdekun/mindmap/examples/login-timeout.tree.md
```

Expected: output shows matches for all four phrases.

- [ ] **Step 5: Run full verification**

Run:

```bash
cd /home/yangdekun/mindmap/tool
PYTHONPATH=/home/yangdekun/mindmap/tool pytest tests -q
```

Expected: PASS, `21 passed`.

- [ ] **Step 6: Commit or record skip**

Run:

```bash
git -C /home/yangdekun/mindmap rev-parse --is-inside-work-tree
```

Expected in current directory: FAIL with `fatal: not a git repository`. Record that commit is skipped because the project is not a git repository.

If the directory has been initialized as a repo before execution, run:

```bash
git -C /home/yangdekun/mindmap add examples/login-timeout.tree.json examples/login-timeout.tree.md
git -C /home/yangdekun/mindmap commit -m "docs: add mindmap example tree"
```

Expected in a git repo: commit succeeds.

---

## Final Verification

Run:

```bash
cd /home/yangdekun/mindmap/tool
PYTHONPATH=/home/yangdekun/mindmap/tool pytest tests -q
```

Expected: PASS, `21 passed`.

Run:

```bash
cd /home/yangdekun/mindmap
PYTHONPATH=/home/yangdekun/mindmap/tool python3 -m mindmap_mcts.cli show examples/login-timeout.tree.json
```

Expected: output includes `Best path: n1 -> n2` and `Best value: 0.90`.

Run:

```bash
rg -n "Never hand-edit|Stop Conditions|Per-Round Loop" /home/yangdekun/mindmap/skills/mindmap-mcts/SKILL.md
```

Expected: output shows all three phrases.

## Spec Coverage Review

- JSON truth source: Task 1 implements dataclasses, JSON serialization, validation, and atomic save/load.
- Tree engine atomic operations: Task 2 implements init, add, evaluate, prune, select, backprop, frontier, and best-path logic.
- UCB selection and backprop rules: Task 2 tests and implements unvisited priority, pruned-node exclusion, and max-child value propagation.
- Markdown rendering: Task 3 implements readable tree and summary rendering.
- CLI commands: Task 4 implements all first-version commands named in the design spec.
- Codex skill behavior: Task 5 writes the skill trigger, loop, evaluation scale, and stop conditions.
- Example complete loop: Task 6 generates a sample tree through the CLI and verifies rendered evidence.
- Error handling: Tasks 1, 2, and 4 cover invalid JSON, missing nodes, invalid values, pruned parent behavior, and nonzero CLI errors.

## Type And Name Consistency Review

- Node field names are `id`, `parent`, `content`, `type`, `state`, `V`, `N`, `evidence`, `created_at`, and `updated_at` in every task.
- Tree field names are `version`, `title`, `root_id`, `params`, and `nodes` in every task.
- CLI command names are `init`, `add`, `eval`, `prune`, `select`, `backprop`, `render`, and `show` in every task.
- Python function names are consistent across tests and implementation snippets.
