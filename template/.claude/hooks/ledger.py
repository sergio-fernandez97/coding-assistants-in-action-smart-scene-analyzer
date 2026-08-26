"""Shared parsing for docs/credit-budget.md.

Imported by the hooks in this directory. Standard library only, on purpose: hooks
run before `uv sync` has necessarily happened, and a hook that needs the project's
virtualenv to work is a hook that fails silently on a fresh clone.

The ledger format this parses is the one that ships in `docs/credit-budget.md`.
If you change the shape of that file, change this together with it — a parser that
silently finds nothing is worse than no parser, because it reports a balance of
zero and blocks every call.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

LEDGER_RELATIVE_PATH = "docs/credit-budget.md"

# | **Remaining** | **20.0** |
_REMAINING = re.compile(r"\|\s*\*{0,2}Remaining\*{0,2}\s*\|\s*\*{0,2}([\d.]+)\*{0,2}\s*\|")


@dataclass
class LedgerRow:
    """One row of the Ledger table."""

    date: str
    lesson: str
    operation: str
    rate: str
    estimated: str
    actual: str

    @property
    def is_pending_estimate(self) -> bool:
        """An estimate that has been recorded but not yet reconciled.

        This is the state the credit gate requires: the cost was worked out and
        written down *before* the call, and the actual has not come back yet.
        """
        return bool(self.estimated.strip()) and not self.actual.strip()


@dataclass
class Ledger:
    path: Path
    remaining: float | None
    rows: list[LedgerRow]

    @property
    def pending(self) -> LedgerRow | None:
        for row in reversed(self.rows):
            if row.is_pending_estimate:
                return row
        return None


def _cells(line: str) -> list[str]:
    return [cell.strip() for cell in line.strip().strip("|").split("|")]


def read_ledger(project_dir: Path) -> Ledger | None:
    """Parse the ledger, or return None if it does not exist."""
    path = project_dir / LEDGER_RELATIVE_PATH
    if not path.is_file():
        return None

    text = path.read_text(encoding="utf-8")

    remaining: float | None = None
    match = _REMAINING.search(text)
    if match:
        try:
            remaining = float(match.group(1))
        except ValueError:
            remaining = None

    rows: list[LedgerRow] = []
    in_ledger = False
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("## "):
            in_ledger = stripped.lower().startswith("## ledger")
            continue
        if not in_ledger or not stripped.startswith("|"):
            continue
        cells = _cells(stripped)
        if len(cells) < 6:
            continue
        # Skip the header row and the |---|---| separator.
        if cells[0].lower() == "date" or set("".join(cells)) <= {"-", ":"}:
            continue
        # Skip the seeded *starting balance* row.
        if "starting balance" in cells[2].lower():
            continue
        rows.append(
            LedgerRow(
                date=cells[0],
                lesson=cells[1],
                operation=cells[2],
                rate=cells[3],
                estimated=cells[4],
                actual=cells[5],
            )
        )

    return Ledger(path=path, remaining=remaining, rows=rows)
