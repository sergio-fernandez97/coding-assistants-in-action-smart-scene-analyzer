#!/usr/bin/env python3
"""SessionStart: put the credit balance in front of the assistant.

`CLAUDE.md` tells the assistant where the ledger lives. That only helps if it
goes and reads it, which it will not do before a call it does not think is
expensive. Printing the balance at session start makes the budget a fact the
session already knows rather than one it has to look up.

stdout from a SessionStart hook is added to the session context.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from ledger import read_ledger


def main() -> None:
    project_dir = Path(os.environ.get("CLAUDE_PROJECT_DIR") or ".")
    ledger = read_ledger(project_dir)

    if ledger is None or ledger.remaining is None:
        sys.exit(0)

    parts = [f"Roboflow credits remaining: {ledger.remaining} of 20.0."]

    pending = ledger.pending
    if pending is not None:
        parts.append(
            f"There is an unreconciled ledger row: '{pending.operation}' estimated at "
            f"{pending.estimated}. Record the actual cost before spending anything else."
        )

    if ledger.remaining <= 2.0:
        parts.append(
            "This is below the Lesson 05 allocation. Treat every billed operation as "
            "one that has to be argued for."
        )

    print(" ".join(parts))
    sys.exit(0)


if __name__ == "__main__":
    main()
