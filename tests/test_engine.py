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
