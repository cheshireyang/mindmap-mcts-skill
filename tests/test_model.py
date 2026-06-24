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


def test_node_supports_structured_evidence_metadata():
    node = Node(
        id="n1",
        parent=None,
        content="root",
        type="goal",
        evidence="focused test passed",
        probe_type="test",
        source="tests/test_login.py::test_timeout",
        confidence="high",
    )
    tree = Tree(title="Root", root_id="n1", params=Params(), nodes=[node])

    payload = tree_to_dict(tree)
    restored = tree_from_dict(payload)

    assert payload["nodes"][0]["probe_type"] == "test"
    assert payload["nodes"][0]["source"] == "tests/test_login.py::test_timeout"
    assert payload["nodes"][0]["confidence"] == "high"
    assert restored.nodes[0].probe_type == "test"


def test_tree_from_dict_rejects_non_numeric_params_with_mindmap_error():
    payload = {
        "version": 1,
        "title": "Bad tree",
        "root_id": "n1",
        "params": {"exploration_c": "bad"},
        "nodes": [
            {
                "id": "n1",
                "parent": None,
                "content": "Bad tree",
                "type": "goal",
                "state": "exploring",
                "V": 0.5,
                "N": 0,
            }
        ],
    }

    with pytest.raises(MindMapError, match="exploration_c must be numeric"):
        tree_from_dict(payload)
