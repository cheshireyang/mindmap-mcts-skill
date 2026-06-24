#!/usr/bin/env python3
from __future__ import annotations

import sys
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

from mindmap_mcts.cli import main  # noqa: E402


if __name__ == "__main__":
    raise SystemExit(main())
