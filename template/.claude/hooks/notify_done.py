#!/usr/bin/env python3
"""Stop: raise a desktop notification when the assistant finishes its turn.

The second boring hook, and it is here for the same reason as the first: it
fires constantly, does something immediately visible, and cannot hurt you. A
student who has seen this one fire understands what "the harness runs a script
of yours on a Claude Code event" means before `credit_gate.py` runs one where
being wrong costs money.

It is also the only hook in the scaffold that exists for the *operator* rather
than for the code. Nothing in `src/` is safer because of it. Long training and
export runs finish while you are in another window, and a hook is a better
answer to "is it done yet" than checking.

The same script serves the `Notification` event, which fires when the assistant
is waiting on you rather than done — wire it up in `settings.json` if a course
that never skips permission prompts leaves you waiting more often than you like.

It never blocks. A notifier that can fail a turn is a notifier that will.
"""

from __future__ import annotations

import contextlib
import json
import os
import platform
import shutil
import subprocess
import sys

TITLE = "Smart Scene Analyzer"
MAX_BODY = 120
SOUND_FILE = "/System/Library/Sounds/Glass.aiff"


def summarize(payload: dict) -> str:
    """One line of the assistant's last message, short enough for a toast."""
    if payload.get("hook_event_name") == "Notification":
        return str(payload.get("message") or "Waiting on you.")

    message = str(payload.get("last_assistant_message") or "").strip()
    if not message:
        return "Turn finished."

    first_line = next((ln.strip() for ln in message.splitlines() if ln.strip()), "")
    if len(first_line) > MAX_BODY:
        first_line = first_line[: MAX_BODY - 1].rstrip() + "…"
    return first_line or "Turn finished."


def play_sound() -> None:
    """Ring the alert sound directly, outside Notification Center.

    `display notification ... sound name "Glass"` sounds like it covers this,
    but the chime rides on the notification: when macOS suppresses the banner
    it suppresses the sound too — silently, and still exit 0. That suppression
    is the default on a fresh machine, because AppleScript notifications are
    attributed to Script Editor, which has no notification permission until
    somebody grants it.

    `afplay` writes to the audio device and is not routed through Notification
    Center, so it survives that. On a machine where the banner works you now
    get the banner from osascript and the chime from here, which is why the
    AppleScript below no longer asks for a sound of its own.

    See docs/desktop_notifications.md in the course repo.
    """
    if not os.path.exists(SOUND_FILE):
        return

    # Detached, not waited on: a notifier must not add latency to a turn.
    with contextlib.suppress(OSError):
        subprocess.Popen(  # noqa: S603
            ["afplay", SOUND_FILE],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )


def notify(body: str) -> None:
    """Best-effort desktop notification. Every branch is allowed to do nothing."""
    system = platform.system()

    if system == "Darwin":
        # The chime goes first and on its own path, because it is the half of
        # this that still works when the banner is being dropped.
        play_sound()

        # osascript is the only notifier guaranteed present on a stock macOS.
        # Quotes inside the body would end the AppleScript string early.
        safe = body.replace("\\", "").replace('"', "'")
        command = [
            "osascript",
            "-e",
            f'display notification "{safe}" with title "{TITLE}"',
        ]
    elif system == "Linux" and shutil.which("notify-send"):
        command = ["notify-send", TITLE, body]
    else:
        # Windows, a headless container, a Linux box with no notification daemon.
        # The terminal bell is the portable floor.
        sys.stderr.write(f"\a{TITLE}: {body}\n")
        return

    with contextlib.suppress(OSError, subprocess.TimeoutExpired):
        subprocess.run(command, capture_output=True, timeout=5, check=False)


def main() -> None:
    try:
        payload = json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError):
        sys.exit(0)

    notify(summarize(payload))
    sys.exit(0)


if __name__ == "__main__":
    main()
