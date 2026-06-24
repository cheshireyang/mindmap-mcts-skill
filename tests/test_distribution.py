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
    for command in [
        "init",
        "add",
        "eval",
        "prune",
        "select",
        "backprop",
        "render-html",
        "render-markmap",
        "path",
        "doctor",
        "next",
    ]:
        assert command in result.stdout


def test_python_launcher_runs_cli_help():
    launcher = REPO_ROOT / "mindmap-mcts" / "scripts" / "mindmap.py"

    result = run(["python3", str(launcher), "--help"])

    assert result.returncode == 0, result.stderr
    assert "MindMap-MCTS tree engine" in result.stdout
    assert "render-html" in result.stdout
    assert "render-markmap" in result.stdout


def test_windows_launchers_document_python_module_and_utf8_setup():
    cmd_launcher = REPO_ROOT / "mindmap-mcts" / "scripts" / "mindmap.cmd"
    ps_launcher = REPO_ROOT / "mindmap-mcts" / "scripts" / "mindmap.ps1"

    cmd_text = cmd_launcher.read_text(encoding="utf-8").lower()
    ps_text = ps_launcher.read_text(encoding="utf-8").lower()

    assert "pythonioencoding" in cmd_text
    assert "pythonpath" in cmd_text
    assert "-m mindmap_mcts.cli" in cmd_text
    assert "outputencoding" in ps_text
    assert "pythonioencoding" in ps_text
    assert "pythonpath" in ps_text
    assert "-m mindmap_mcts.cli" in ps_text


def test_install_script_copies_skill_and_smoke_tests_cli(tmp_path):
    codex_home = tmp_path / "codex-home"
    install_script = REPO_ROOT / "install.sh"

    result = run([str(install_script)], env={"CODEX_HOME": str(codex_home)})

    installed_skill = codex_home / "skills" / "mindmap-mcts"
    installed_wrapper = installed_skill / "scripts" / "mindmap"
    installed_python_launcher = installed_skill / "scripts" / "mindmap.py"
    installed_cmd_launcher = installed_skill / "scripts" / "mindmap.cmd"
    installed_ps_launcher = installed_skill / "scripts" / "mindmap.ps1"
    assert result.returncode == 0, result.stderr
    assert installed_wrapper.exists()
    assert installed_python_launcher.exists()
    assert installed_cmd_launcher.exists()
    assert installed_ps_launcher.exists()
    assert "Installed mindmap-mcts" in result.stdout
    assert "MindMap-MCTS tree engine" in result.stdout


def test_readme_documents_install_script_and_wrapper():
    readme = (REPO_ROOT / "README.md").read_text(encoding="utf-8")

    assert "./install.sh" in readme
    assert "mindmap-mcts/scripts/mindmap --help" in readme
    assert "python -m mindmap_mcts.cli" in readme
    assert "PowerShell" in readme
    assert "--parent n1" in readme
    assert "UTF-8" in readme
    assert "render-markmap" in readme


def test_readme_uses_generated_png_assets_and_preserves_legacy_svgs():
    readme = (REPO_ROOT / "README.md").read_text(encoding="utf-8")

    assert "assets/alpha-style-architecture.png" in readme
    assert "assets/reasoning-tree-loop.png" in readme
    assert (REPO_ROOT / "assets" / "alpha-style-architecture.png").exists()
    assert (REPO_ROOT / "assets" / "reasoning-tree-loop.png").exists()
    assert (REPO_ROOT / "assets" / "legacy" / "mindmap-mcts-overview.svg").exists()
    assert (REPO_ROOT / "assets" / "legacy" / "mcts-loop.svg").exists()


def test_readme_and_repository_metadata_include_discovery_terms():
    readme = (REPO_ROOT / "README.md").read_text(encoding="utf-8").lower()
    metadata = (REPO_ROOT / ".github" / "repository-metadata.md").read_text(encoding="utf-8").lower()

    for term in [
        "codex skill",
        "claude code skill",
        "ai agents",
        "agent reasoning",
        "reasoning tree",
        "tree search",
        "monte carlo tree search",
        "mcts",
        "ucb",
    ]:
        assert term in readme

    assert "repository description" in metadata
    assert "repository topics" in metadata
    assert "codex-skill" in metadata
    assert "claude-code" in metadata
    assert "monte-carlo-tree-search" in metadata


def test_skill_uses_wrapper_script_instead_of_long_pythonpath_commands():
    skill = (REPO_ROOT / "mindmap-mcts" / "SKILL.md").read_text(encoding="utf-8")

    assert "scripts/mindmap" in skill
    assert "python -m mindmap_mcts.cli" in skill
    assert "PowerShell" in skill
    assert "n1" in skill
    assert "UTF-8" in skill
    assert "render-markmap" in skill


def test_github_actions_runs_tests():
    workflow = (REPO_ROOT / ".github" / "workflows" / "test.yml").read_text(encoding="utf-8")

    assert "PYTHONPATH=mindmap-mcts/scripts pytest tests -q" in workflow
    assert "python-version" in workflow
