#!/usr/bin/env python3
"""PreToolUse gate on billed Roboflow operations.

`CLAUDE.md` asks the assistant to estimate a cost before spending it. The `ask`
rules in `settings.json` then surface a prompt, which you can approve without
reading. Neither actually stops anything: the first is prose a model can talk
past, the second is a button.

This hook is the third layer, and it is the only one that cannot be reasoned
around. A billed call does not fire unless `docs/credit-budget.md` already
carries a row for it with an estimate and no actual — the arithmetic has to exist
on disk before the money moves.

Exit 0  → allowed, proceed to the normal permission prompt.
Exit 2  → blocked. stderr goes back to the assistant as the reason.
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from ledger import LEDGER_RELATIVE_PATH, read_ledger

# Below this, refuse outright. A course that runs out of credits in Week 4 does
# not get a Week 5, so the floor exists to make the last lesson reachable.
RESERVE_FLOOR = 0.5


def block(message: str) -> None:
    print(message, file=sys.stderr)
    sys.exit(2)


def main() -> None:
    try:
        payload = json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError):
        # A malformed payload is a broken hook, not a spending decision.
        # Fail open and let the permission prompt do its job.
        sys.exit(0)

    tool_name = payload.get("tool_name", "the requested operation")
    project_dir = Path(os.environ.get("CLAUDE_PROJECT_DIR") or payload.get("cwd") or ".")

    ledger = read_ledger(project_dir)

    if ledger is None:
        block(
            f"BLOCKED: {tool_name} bills Roboflow credits, and "
            f"{LEDGER_RELATIVE_PATH} does not exist.\n"
            "Create the ledger and record an estimate before calling a billed tool."
        )

    if ledger.remaining is None:
        block(
            f"BLOCKED: could not read a Remaining balance from {ledger.path}.\n"
            "Fix the `| **Remaining** | <number> |` row, then retry."
        )

    if ledger.remaining <= RESERVE_FLOOR:
        block(
            f"BLOCKED: {ledger.remaining} credits remain, at or below the "
            f"{RESERVE_FLOOR} reserve floor.\n"
            "Report the balance to the user and stop. Do not run a smaller version "
            "of this operation to fit."
        )

    pending = ledger.pending
    if pending is None:
        block(
            f"BLOCKED: {tool_name} bills credits and {LEDGER_RELATIVE_PATH} has no "
            "pending estimate.\n"
            "Before retrying, append a Ledger row with the date, lesson, operation, "
            "the rate from `roboflow:plans-and-pricing`, and the estimated cost with "
            "the arithmetic shown. Leave Actual blank until the call returns.\n"
            f"Remaining balance: {ledger.remaining}"
        )

    try:
        estimate = float(pending.estimated.strip().rstrip("+~"))
    except ValueError:
        block(
            f"BLOCKED: the pending ledger row for '{pending.operation}' has a "
            f"non-numeric estimate ({pending.estimated!r}).\n"
            "An estimate you cannot subtract from a balance is not an estimate."
        )

    if estimate > ledger.remaining:
        block(
            f"BLOCKED: estimated {estimate} credits against {ledger.remaining} "
            "remaining.\n"
            "Stop and report. Per CLAUDE.md, do not shrink the operation to fit — "
            "say what it would cost and let the user decide what to cut."
        )

    print(
        f"Credit gate passed: '{pending.operation}' estimated at {estimate}, "
        f"{ledger.remaining} remaining. Append the actual to the ledger when the "
        "call returns.",
        file=sys.stderr,
    )
    sys.exit(0)


if __name__ == "__main__":
    main()
