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
