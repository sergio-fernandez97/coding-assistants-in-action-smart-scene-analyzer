"""The units guard is enforcement, so it gets tested like enforcement.

`units_guard.py` is the only thing standing between this project and a variable
called `depth_meters`. It runs as a `PreToolUse` hook, which means nothing else
in the suite exercises it and a typo in a regex would fail silently and forever.

The cases below are the contract, not a sample. In particular: the guard reaches
`app/` as well as `src/`, and `.ts`/`.tsx` as well as `.py`, because the depth
tensor is read and reduced on the handset now. A regression that narrowed the
guard back to `src/*.py` would leave the computation unguarded and every one of
the `src/` cases still passing.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

HOOK = Path(__file__).resolve().parents[1] / ".claude" / "hooks" / "units_guard.py"

BLOCKED = [
    # The reason `app/` is guarded at all: this is where depth is computed now.
    ("app/src/fusion/index.ts", "const depth_meters = reduce(tensor);"),
    ("app/src/fusion/depth.ts", "export function toMeters(d: number) {}"),
    # A distance reaching the screen is the failure this project cares most about.
    ("app/src/ui/DetectionCard.tsx", "<Text>{`${d} meters away`}</Text>"),
    # The original coverage, which must not regress.
    ("src/smart_scene_analyzer/fusion.py", "depth_m = median(region)"),
    ("src/smart_scene_analyzer/schemas.py", '"""Depth in metres, roughly."""'),
]

ALLOWED = [
    # The sanctioned vocabulary.
    ("app/src/fusion/index.ts", "const relativeDepth = reduce(tensor);"),
    ("src/smart_scene_analyzer/fusion.py", "relative_inverse_depth = median(region)"),
    # Word-boundary neighbours that must not trip it.
    ("app/src/geometry/letterbox.ts", "const parameters = { diameter: 2 };"),
    # Vendored code is not ours to name things in.
    ("app/node_modules/some-lib/index.ts", "export const meters = 1;"),
    # Outside the guarded prefixes.
    ("scripts/train.py", "depth_meters = 1.0"),
    # Guarded prefix, unguarded extension.
    ("app/src/labels.json", '{"unit": "meters"}'),
]


def run(file_path: str, content: str, key: str = "content") -> subprocess.CompletedProcess[str]:
    payload = json.dumps({"tool_input": {"file_path": file_path, key: content}})
    return subprocess.run(
        [sys.executable, str(HOOK)],
        input=payload,
        capture_output=True,
        text=True,
        timeout=10,
    )


@pytest.mark.parametrize(("path", "content"), BLOCKED)
def test_blocks_metric_depth(path: str, content: str) -> None:
    result = run(path, content)
    assert result.returncode == 2, f"{path} should have been blocked"
    assert "BLOCKED" in result.stderr


@pytest.mark.parametrize(("path", "content"), ALLOWED)
def test_allows_everything_else(path: str, content: str) -> None:
    assert run(path, content).returncode == 0, f"{path} should have been allowed"


def test_edit_payloads_are_guarded_too() -> None:
    """`Write` carries `content`; `Edit` carries `new_string`. Both are writes."""
    result = run("app/src/fusion/index.ts", "const depth_cm = 4;", key="new_string")
    assert result.returncode == 2


@pytest.mark.xfail(
    reason=(
        "Known gap, deliberately recorded rather than quietly patched. The banned "
        "patterns require the unit to sit adjacent to its noun (`depth_cm`, "
        "`distance_m`), so prose that separates them — 'distance in cm', "
        "'roughly 2 m away' — passes the hook while failing the manual grep in "
        "Lesson 05's Verification. Widening the regexes is a deliberate change to "
        "what the guard means, not a bug fix: it would start blocking legitimate "
        "writes like 'distance in pixels'. Tracked in TODO.md."
    ),
    strict=True,
)
@pytest.mark.parametrize(
    ("path", "content"),
    [
        ("src/smart_scene_analyzer/schemas.py", '"""Distance in cm."""'),
        ("app/src/ui/Card.tsx", "<Text>roughly 2 m away</Text>"),
    ],
)
def test_known_gap_prose_that_separates_unit_from_noun(path: str, content: str) -> None:
    assert run(path, content).returncode == 2


def test_malformed_payload_does_not_block() -> None:
    """A guard that fails closed on junk input blocks legitimate work forever."""
    result = subprocess.run(
        [sys.executable, str(HOOK)], input="not json", capture_output=True, text=True, timeout=10
    )
    assert result.returncode == 0
