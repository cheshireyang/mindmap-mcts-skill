#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CODEX_HOME_DIR="${CODEX_HOME:-$HOME/.codex}"
SKILLS_DIR="$CODEX_HOME_DIR/skills"
TARGET_DIR="$SKILLS_DIR/mindmap-mcts"

if ! command -v python3 >/dev/null 2>&1; then
  echo "python3 is required but was not found on PATH." >&2
  exit 1
fi

mkdir -p "$SKILLS_DIR"
rm -rf "$TARGET_DIR"
cp -R "$REPO_ROOT/mindmap-mcts" "$TARGET_DIR"

chmod +x "$TARGET_DIR/scripts/mindmap"
chmod +x "$TARGET_DIR/scripts/mindmap.py"

echo "Installed mindmap-mcts to $TARGET_DIR"
"$TARGET_DIR/scripts/mindmap" --help
