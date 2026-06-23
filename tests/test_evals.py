import json
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]


def test_evals_file_contains_three_realistic_skill_evals():
    payload = json.loads((REPO_ROOT / "evals" / "evals.json").read_text(encoding="utf-8"))

    assert payload["skill_name"] == "mindmap-mcts"
    assert len(payload["evals"]) == 3
    assert {item["id"] for item in payload["evals"]} == {
        "debug-login-timeout",
        "choose-storage-architecture",
        "research-transformer-defects",
    }
    for item in payload["evals"]:
        assert item["prompt"].strip()
        assert item["expected_output"].strip()
        assert item["assertions"]
        assertion_text = " ".join(assertion["text"] for assertion in item["assertions"])
        assert "tree" in assertion_text.lower()
        assert "evidence" in assertion_text.lower()
