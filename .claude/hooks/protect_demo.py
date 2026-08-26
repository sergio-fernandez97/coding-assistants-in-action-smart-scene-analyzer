#!/usr/bin/env python3
"""Block Claude Code from operating on the protected demo checkout.

This is deliberately a PreToolUse hook rather than a permission deny rule:
the target is a directory, and Bash can change it through many commands
(`cd`, `cp`, `mv`, redirection, formatters, package managers, and so on).
The hook examines both file-edit paths and every Bash command before it runs.

Exit 0 allows the tool call.  A JSON deny response makes Claude Code cancel it.
"""

from __future__ import annotations

import json
import re
import sys


PROTECTED_DIRECTORY = "smart-scene-analyzer-demo"
PROTECTED_DIRECTORY_PATTERN = re.compile(
    rf"(?<![A-Za-z0-9_.-]){re.escape(PROTECTED_DIRECTORY)}(?![A-Za-z0-9_.-])"
)


def denies(reason: str) -> None:
    print(
        json.dumps(
            {
                "hookSpecificOutput": {
                    "hookEventName": "PreToolUse",
                    "permissionDecision": "deny",
                    "permissionDecisionReason": reason,
                }
            }
        )
    )


def contains_protected_directory(value: str) -> bool:
    """Match the directory as a path component or shell token."""
    return bool(PROTECTED_DIRECTORY_PATTERN.search(value))


def main() -> None:
    try:
        payload = json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError):
        return

    tool_name = payload.get("tool_name", "")
    tool_input = payload.get("tool_input") or {}

    if tool_name in {"Write", "Edit"}:
        path = str(tool_input.get("file_path", ""))
        if contains_protected_directory(path):
            denies(
                f"BLOCKED: {PROTECTED_DIRECTORY}/ is protected in this workspace. "
                "Claude Code must not create, edit, move, delete, or otherwise "
                "manipulate its files."
            )
        return

    if tool_name == "Bash":
        command = str(tool_input.get("command", ""))
        # Intentionally conservative: a shell command that names the protected
        # checkout can operate on it indirectly, even when it looks read-only.
        if contains_protected_directory(command):
            denies(
                f"BLOCKED: Bash commands may not reference {PROTECTED_DIRECTORY}/. "
                "Use Claude Code's Read tool only when you need to inspect it."
            )


if __name__ == "__main__":
    main()
