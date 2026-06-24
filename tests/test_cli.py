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


def test_cli_rejects_eval_pruned_state(tmp_path):
    tree_path = tmp_path / "task.tree.json"
    assert run_cli("init", "--title", "Root", "--out", str(tree_path)).returncode == 0
    assert run_cli("add", str(tree_path), "--parent", "n1", "--type", "hypothesis", "--content", "A").returncode == 0

    result = run_cli(
        "eval",
        str(tree_path),
        "--id",
        "n2",
        "--value",
        "0.9",
        "--state",
        "pruned",
        "--evidence",
        "conflicting",
    )

    assert result.returncode == 2
    assert "use prune_node" in result.stderr


def test_cli_next_rejects_pruned_root(tmp_path):
    tree_path = tmp_path / "task.tree.json"
    assert run_cli("init", "--title", "Root", "--out", str(tree_path)).returncode == 0
    assert run_cli("prune", str(tree_path), "--id", "n1", "--evidence", "ruled out").returncode == 0

    result = run_cli("next", str(tree_path))

    assert result.returncode == 2
    assert "no selectable frontier" in result.stderr


def test_cli_path_prints_best_path_with_evidence(tmp_path):
    tree_path = tmp_path / "task.tree.json"
    assert run_cli("init", "--title", "Root", "--out", str(tree_path)).returncode == 0
    assert run_cli("add", str(tree_path), "--parent", "n1", "--type", "hypothesis", "--content", "A").returncode == 0
    assert run_cli(
        "eval",
        str(tree_path),
        "--id",
        "n2",
        "--value",
        "0.9",
        "--evidence",
        "focused test passed",
        "--probe-type",
        "test",
        "--source",
        "tests/test_login.py::test_timeout",
        "--confidence",
        "high",
    ).returncode == 0
    assert run_cli("backprop", str(tree_path), "--from", "n2").returncode == 0

    result = run_cli("path", str(tree_path))

    assert result.returncode == 0, result.stderr
    assert "n1 Root" in result.stdout
    assert "n2 A" in result.stdout
    assert "focused test passed" in result.stdout
    assert "probe_type=test" in result.stdout
    assert "source=tests/test_login.py::test_timeout" in result.stdout


def test_cli_doctor_reports_valid_tree(tmp_path):
    tree_path = tmp_path / "task.tree.json"
    assert run_cli("init", "--title", "Root", "--out", str(tree_path)).returncode == 0

    result = run_cli("doctor", str(tree_path))

    assert result.returncode == 0, result.stderr
    assert "Tree OK" in result.stdout
    assert "nodes=1" in result.stdout
    assert "frontiers=n1" in result.stdout


def test_cli_render_html_writes_static_visualization(tmp_path):
    tree_path = tmp_path / "task.tree.json"
    html_path = tmp_path / "task.tree.html"
    assert run_cli("init", "--title", "Root", "--out", str(tree_path)).returncode == 0
    assert run_cli("add", str(tree_path), "--parent", "n1", "--type", "hypothesis", "--content", "A").returncode == 0
    assert run_cli("eval", str(tree_path), "--id", "n2", "--value", "0.9", "--evidence", "verified").returncode == 0

    result = run_cli("render-html", str(tree_path), "--out", str(html_path))

    assert result.returncode == 0, result.stderr
    html = html_path.read_text(encoding="utf-8")
    assert "<!doctype html>" in html
    assert "MindMap-MCTS: Root" in html
    assert "data-node-id=\"n2\"" in html
    assert "verified" in html


def test_cli_render_markmap_writes_interactive_mindmap(tmp_path):
    tree_path = tmp_path / "task.tree.json"
    html_path = tmp_path / "task.markmap.html"
    assert run_cli("init", "--title", "Root", "--out", str(tree_path)).returncode == 0
    assert run_cli("add", str(tree_path), "--parent", "n1", "--type", "hypothesis", "--content", "A").returncode == 0
    assert run_cli("eval", str(tree_path), "--id", "n2", "--value", "0.9", "--evidence", "verified").returncode == 0

    result = run_cli("render-markmap", str(tree_path), "--out", str(html_path))

    assert result.returncode == 0, result.stderr
    html = html_path.read_text(encoding="utf-8")
    assert "markmap-autoloader" in html
    assert '<div class="markmap">' in html
    assert "# Root" in html
    assert "- n2 A (V=0.90 N=0 verified)" in html


def test_cli_next_recommends_frontier_action_and_best_path(tmp_path):
    tree_path = tmp_path / "task.tree.json"
    assert run_cli("init", "--title", "Root", "--out", str(tree_path)).returncode == 0
    assert run_cli("add", str(tree_path), "--parent", "n1", "--type", "hypothesis", "--content", "A").returncode == 0
    assert run_cli(
        "eval",
        str(tree_path),
        "--id",
        "n2",
        "--value",
        "0.9",
        "--evidence",
        "focused test passed",
        "--probe-type",
        "test",
        "--source",
        "tests/test_login.py::test_timeout",
        "--confidence",
        "high",
    ).returncode == 0
    assert run_cli("backprop", str(tree_path), "--from", "n2").returncode == 0
    assert run_cli("add", str(tree_path), "--parent", "n1", "--type", "hypothesis", "--content", "B").returncode == 0

    result = run_cli("next", str(tree_path))

    assert result.returncode == 0, result.stderr
    assert "Selected frontier: n3" in result.stdout
    assert "Recommended action: expand n3 with 2-3 concrete, verifiable child nodes" in result.stdout
    assert "Current best path: n1 -> n2" in result.stdout
    assert "Best path evidence:" in result.stdout
    assert "focused test passed" in result.stdout
