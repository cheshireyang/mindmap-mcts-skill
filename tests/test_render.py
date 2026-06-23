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
