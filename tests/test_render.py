from mindmap_mcts.engine import add_node, backpropagate, best_path, evaluate_node, init_tree, prune_node
from mindmap_mcts.render import render_html, render_markdown, render_markmap, render_path, render_summary


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


def test_render_markmap_outputs_interactive_mindmap_html():
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

    html = render_markmap(tree)

    assert html.startswith("<!doctype html>")
    assert "markmap-autoloader" in html
    assert '<div class="markmap">' in html
    assert ".markmap strong" in html
    assert "font-weight: 800" in html
    assert "#030712" in html
    assert ".marker-complete" in html
    assert "#16a34a" in html
    assert ".marker-partial" in html
    assert "#ca8a04" in html
    assert "✗" not in html
    assert "# Root" in html
    assert "- Exploration status" in html
    assert "- Reasoning tree" in html
    assert '  - <span class="marker marker-partial">◐</span> **n1 Root** (V=0.90 N=1 exploring)' in html
    assert '    - <span class="marker marker-complete">✓</span> **n2 Promising branch** (V=0.90 N=1 verified)' in html
    assert "evidence: focused test passed" in html
    assert "probe_type=test, source=tests/test_login.py::test_timeout, confidence=high" in html


def test_render_markmap_summarizes_branch_exploration_status():
    tree = init_tree("Root")
    tree, verified = add_node(tree, "n1", "Verified branch", "hypothesis")
    tree = evaluate_node(tree, verified.id, 0.9, "strong signal")
    tree = backpropagate(tree, verified.id)
    tree, pruned = add_node(tree, "n1", "Pruned branch", "hypothesis")
    tree = prune_node(tree, pruned.id, "ruled out")
    tree, frontier = add_node(tree, "n1", "Unexplored branch", "hypothesis")

    html = render_markmap(tree)

    assert "  - best path: n1 -> n2" in html
    assert "  - selected frontier: n4" in html
    assert "  - state counts: exploring=1, frontier=1, verified=1, pruned=1" in html
    assert "  - open frontier: n4" in html
    assert "  - verified: n2" in html
    assert "  - pruned: n3" in html
    assert '    - <span class="marker marker-complete">✓</span> **n2 Verified branch** (V=0.90 N=1 verified)' in html
    assert '    - <span class="marker marker-complete">✓</span> **n3 Pruned branch** (V=0.00 N=0 pruned)' in html
    assert f'    - <span class="marker marker-open">○</span> **{frontier.id} Unexplored branch** (V=0.50 N=0 frontier) selected' in html
