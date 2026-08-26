#!/usr/bin/env python3
"""PreToolUse guard on depth units, in `src/` and in `app/`.

Depth Anything V2 returns *relative inverse depth*. It is not metres, it is not
centimetres, and it has no scale you can convert from. `CLAUDE.md`, three prompt
files, and one test all say so — and prose has a poor record against a plausible
identifier at eleven at night.

This blocks the write instead. Naming a variable `depth_meters` is not a style
violation to be corrected in review; it is a claim about the physical world that
this system cannot support, and the cheapest moment to stop it is before the
bytes land.

`app/` is guarded for the same reason `src/` is, and the reason is new. When the
models ran on a server, the phone only ever *displayed* a number somebody else
had computed, and the guard could stop at the Python that produced it. The models
run on the handset now: the depth tensor is read, reduced, and named in
TypeScript under `app/`. A guard that still only watched `.py` under `src/` would
be watching the one place the number no longer comes from.

Exit 0 → allowed. Exit 2 → blocked, stderr returned to the assistant.
"""

from __future__ import annotations

import json
import re
import sys

# Word-ish boundaries, so `parameters` and `diameter` do not trip it.
BANNED = [
    (
        re.compile(r"\bdepth[_ ]?(?:in[_ ])?(?:m|meters?|metres?|mm|cm)\b", re.I),
        "depth in metric units",
    ),
    (re.compile(r"\b(?:meters?|metres?)\b", re.I), "metres"),
    (re.compile(r"\bdistance[_ ]?(?:m|mm|cm|meters?|metres?)\b", re.I), "metric distance"),
    (re.compile(r"\bto[_ ]?(?:meters?|metres?)\b", re.I), "a conversion to metres"),
]

GUARDED_PREFIXES = ("src/", "app/")
GUARDED_SUFFIXES = (".py", ".ts", ".tsx")

# Vendored code is not ours to name things in, and `app/node_modules` contains
# plenty of honest metres belonging to other people.
EXCLUDED = ("/node_modules/", "/.venv/", "/build/", "/dist/")


def relevant(path: str) -> bool:
    if not path.endswith(GUARDED_SUFFIXES):
        return False
    normalized = "/" + path.replace("\\", "/")
    if any(fragment in normalized for fragment in EXCLUDED):
        return False
    return any(f"/{prefix}" in normalized for prefix in GUARDED_PREFIXES)


def main() -> None:
    try:
        payload = json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError):
        sys.exit(0)

    tool_input = payload.get("tool_input") or {}
    path = tool_input.get("file_path") or ""
    if not relevant(path):
        sys.exit(0)

    # Write carries `content`; Edit carries `new_string`.
    content = tool_input.get("content") or tool_input.get("new_string") or ""
    if not content:
        sys.exit(0)

    for pattern, description in BANNED:
        match = pattern.search(content)
        if match:
            print(
                f"BLOCKED: this write to {path} contains {match.group(0)!r} — "
                f"{description}.\n"
                "Depth in this project is relative inverse depth from Depth Anything "
                "V2. It has no metric scale, and no identifier, docstring, comment, or "
                "piece of UI text may imply that it does — in `src/` or in `app/`.\n"
                "Use `relative_depth`, `relative_inverse_depth`, or `depth_score`, and "
                "say in the docstring that larger means nearer. If you genuinely need "
                "metric depth, that is an ADR, not a rename.",
                file=sys.stderr,
            )
            sys.exit(2)

    sys.exit(0)


if __name__ == "__main__":
    main()
