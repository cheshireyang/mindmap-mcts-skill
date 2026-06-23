import os
from pathlib import Path
import subprocess


REPO_ROOT = Path(__file__).resolve().parents[1]


def run(command, *, env=None):
    merged_env = os.environ.copy()
    if env:
        merged_env.update(env)
    return subprocess.run(
        command,
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        check=False,
        env=merged_env,
    )


def test_wrapper_script_runs_cli_help():
    wrapper = REPO_ROOT / "mindmap-mcts" / "scripts" / "mindmap"

    result = run([str(wrapper), "--help"])

    assert result.returncode == 0, result.stderr
    assert "MindMap-MCTS tree engine" in result.stdout
    for command in ["init", "add", "eval", "prune", "select", "backprop", "render-html", "path", "doctor", "next"]:
        assert command in result.stdout


def test_install_script_copies_skill_and_smoke_tests_cli(tmp_path):
    codex_home = tmp_path / "codex-home"
    install_script = REPO_ROOT / "install.sh"

    result = run([str(install_script)], env={"CODEX_HOME": str(codex_home)})

    installed_skill = codex_home / "skills" / "mindmap-mcts"
    installed_wrapper = installed_skill / "scripts" / "mindmap"
    assert result.returncode == 0, result.stderr
    assert installed_wrapper.exists()
    assert "Installed mindmap-mcts" in result.stdout
    assert "MindMap-MCTS tree engine" in result.stdout


def test_readme_documents_install_script_and_wrapper():
    readme = (REPO_ROOT / "README.md").read_text(encoding="utf-8")

    assert "./install.sh" in readme
    assert "mindmap-mcts/scripts/mindmap --help" in readme


def test_readme_uses_generated_png_assets_and_preserves_legacy_svgs():
    readme = (REPO_ROOT / "README.md").read_text(encoding="utf-8")

    assert "assets/alpha-style-architecture.png" in readme
    assert "assets/reasoning-tree-loop.png" in readme
    assert (REPO_ROOT / "assets" / "alpha-style-architecture.png").exists()
    assert (REPO_ROOT / "assets" / "reasoning-tree-loop.png").exists()
    assert (REPO_ROOT / "assets" / "legacy" / "mindmap-mcts-overview.svg").exists()
    assert (REPO_ROOT / "assets" / "legacy" / "mcts-loop.svg").exists()


def test_skill_uses_wrapper_script_instead_of_long_pythonpath_commands():
    skill = (REPO_ROOT / "mindmap-mcts" / "SKILL.md").read_text(encoding="utf-8")

    assert "scripts/mindmap" in skill
    assert "python3 -m mindmap_mcts.cli" not in skill


def test_github_actions_runs_tests():
    workflow = (REPO_ROOT / ".github" / "workflows" / "test.yml").read_text(encoding="utf-8")

    assert "PYTHONPATH=mindmap-mcts/scripts pytest tests -q" in workflow
    assert "python-version" in workflow
