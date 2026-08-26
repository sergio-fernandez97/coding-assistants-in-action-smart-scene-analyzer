#!/usr/bin/env python3
"""PostToolUse: format and autofix the Python file that was just written.

The most boring hook in the project, and it is here deliberately. It runs on
every write, does something visible and harmless, and costs nothing to
understand — which makes it the right place to meet the mechanism before
meeting `credit_gate.py`, where being wrong costs money.

It never blocks. A formatter that can fail a write is a formatter that will,
at the worst possible moment.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


def main() -> None:
    try:
        payload = json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError):
        sys.exit(0)

    path = (payload.get("tool_input") or {}).get("file_path") or ""
    if not path.endswith(".py") or not Path(path).is_file():
        sys.exit(0)

    for args in (["ruff", "format", path], ["ruff", "check", "--fix", "--quiet", path]):
        try:
            subprocess.run(
                ["uv", "run", *args],
                capture_output=True,
                timeout=30,
                check=False,
            )
        except (OSError, subprocess.TimeoutExpired):
            # No uv, no ruff, or a slow cold start. Not worth interrupting for.
            break

    sys.exit(0)


if __name__ == "__main__":
    main()
