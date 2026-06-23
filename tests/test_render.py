from mindmap_mcts.engine import add_node, backpropagate, best_path, evaluate_node, init_tree, prune_node
from mindmap_mcts.render import render_html, render_markdown, render_path, render_summary


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


def test_render_path_includes_evidence_metadata():
    tree = init_tree("Root")
    tree, child = add_node(tree, "n1", "Promising branch", "hypothesis")
    tree = evaluate_node(
        tree,
        child.id,
        0.9,
        "focused test passed",
        probe_type="test",
        source="tests/test_login.py::test_timeout",
        confidence="high",
    )
    tree = backpropagate(tree, child.id)

    rendered = render_path(tree)

    assert "n1 Root" in rendered
    assert "n2 Promising branch" in rendered
    assert "focused test passed" in rendered
    assert "probe_type=test" in rendered
    assert "source=tests/test_login.py::test_timeout" in rendered
    assert "confidence=high" in rendered


def test_render_html_outputs_static_document_with_node_data():
    tree = init_tree("Root")
    tree, child = add_node(tree, "n1", "Promising branch", "hypothesis")
    tree = evaluate_node(tree, child.id, 0.9, "verified")

    html = render_html(tree)

    assert html.startswith("<!doctype html>")
    assert "MindMap-MCTS: Root" in html
    assert 'data-node-id="n2"' in html
    assert "Promising branch" in html
    assert "verified" in html
