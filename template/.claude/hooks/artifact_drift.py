#!/usr/bin/env python3
"""PostToolUse: notice when the app is about to run a model nobody exported.

When the models ran on a server, the seam between the two halves was the OpenAPI
document, and the silent failure was a renamed schema field leaving a client that
still compiled. The models run on the handset now, and the seam moved with them:
the app and the export pipeline share the model files themselves — their input
and output tensor shapes, their label order, their normalization constants.

That seam breaks the same way, and just as quietly. Retrain, adjust the export
config, change the taxonomy — and `app/assets/models/` still holds last week's
artifact. The app builds, launches, runs inference, and draws boxes. They are
labelled with the old class list, and nothing anywhere reports an error.

So this hook does what `contract_drift.py` used to do, for the seam that exists
now: it compares mtimes and warns when the source of an artifact is newer than
the artifact the app will bundle.

It warns rather than blocks, for the same reason as before. Retraining and
editing the export config are legitimate work, and re-exporting mid-edit — a
several-minute quantization run — would be far worse than being told to.
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

# Editing any of these puts the bundled artifacts in question.
SOURCE_SUFFIXES = ("export.py", "export.yaml", "export.yml", "taxonomy.md", "data.yaml")

BUNDLED_MODELS = Path("app/assets/models")
MODEL_SUFFIXES = (".tflite", ".pte")


def is_source(path: str) -> bool:
    normalized = path.replace("\\", "/")
    return normalized.endswith(SOURCE_SUFFIXES)


def main() -> None:
    try:
        payload = json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError):
        sys.exit(0)

    path = (payload.get("tool_input") or {}).get("file_path") or ""
    if not is_source(path):
        sys.exit(0)

    source = Path(path)
    if not source.is_file():
        sys.exit(0)

    project_dir = Path(os.environ.get("CLAUDE_PROJECT_DIR") or payload.get("cwd") or ".")
    models_dir = project_dir / BUNDLED_MODELS
    if not models_dir.is_dir():
        sys.exit(0)

    artifacts = [p for p in models_dir.iterdir() if p.suffix in MODEL_SUFFIXES and p.is_file()]
    if not artifacts:
        sys.exit(0)

    source_mtime = source.stat().st_mtime
    stale = sorted(p.name for p in artifacts if p.stat().st_mtime < source_mtime)
    if not stale:
        sys.exit(0)

    print(
        f"ARTIFACT DRIFT: {path} is now newer than {len(stale)} bundled model "
        f"artifact(s): {', '.join(stale)}.\n"
        "The app bundles what is in app/assets/models/, not what your export config "
        "now says. Inference will run, boxes will be drawn, and the labels may be "
        "from the previous taxonomy — no error is raised anywhere.\n"
        "Re-export before building or measuring:\n"
        "  uv run python scripts/export.py --all\n"
        "Then re-run the parity check, because an export that has not been compared "
        "against the reference is not yet known to be correct:\n"
        "  uv run pytest tests/test_export_parity.py",
        file=sys.stderr,
    )

    sys.exit(0)


if __name__ == "__main__":
    main()
