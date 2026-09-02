# Making the Desktop Notification Hook Actually Notify You

The scaffold ships `.claude/hooks/notify_done.py`, wired to the `Stop` and
`Notification` events in `.claude/settings.json`. It raises a macOS desktop
notification when Claude finishes a turn or is waiting on you.

On a fresh macOS machine it will do nothing at all — no banner, no sound — and
it will not tell you why. This page is how you get it working, and how you tell
"macOS is blocking it" apart from "the hook is broken".

## 1. Understand why it looks broken

`notify_done.py` shells out to `osascript`:

```applescript
display notification "..." with title "Smart Scene Analyzer" sound name "Glass"
```

The notification is **not** attributed to your terminal, to VS Code, or to
Claude Code. macOS attributes it to **Script Editor** (`com.apple.ScriptEditor2`),
because that is the app that owns AppleScript execution.

So the permission that matters is Script Editor's — and if Script Editor is not
allowed to post notifications, macOS drops the request **silently**. `osascript`
still exits `0`. The hook still exits `0`. Nothing anywhere reports a failure.

That silence is the whole problem: an exit code of zero tells you the script
ran, not that anyone saw it.

## 2. Confirm the hook itself is fine

Run the hook by hand with a fake payload. From the project root:

```bash
echo '{"hook_event_name":"Stop","last_assistant_message":"Hook smoke test"}' \
  | python3 .claude/hooks/notify_done.py; echo "exit=$?"
```

And run the underlying command directly, cutting the hook out entirely:

```bash
osascript -e 'display notification "direct test" with title "Smart Scene Analyzer" sound name "Glass"'
echo "exit=$?"
```

Read the result this way:

| What you see | What it means |
|---|---|
| `exit=0`, banner appears | Working. Nothing to do. |
| `exit=0`, no banner, no sound | macOS is blocking it. Go to step 3. |
| Non-zero exit or a Python traceback | The hook is genuinely broken. Fix the script. |

The second row is the common one, and it is the one that wastes an afternoon if
you assume the script is at fault.

## 3. Grant Script Editor permission to notify

1. Open **System Settings → Notifications**.
2. Scroll the application list to **Script Editor**.
3. Turn on **Allow notifications**.
4. Set the alert style to **Banners** (or **Alerts** if you want them to stay on
   screen until dismissed).
5. Turn on **Play sound for notifications**.

Then re-run the `osascript` command from step 2. You should get a banner and the
Glass chime.

If **Script Editor does not appear in the list**, macOS has not registered it
yet. Run the `osascript` command once, then look again — the first attempt is
what puts the app in the list.

## 4. Check that a Focus mode is not eating it

Notifications suppressed by **Do Not Disturb** or any other Focus mode behave
exactly like permission-denied ones: silent, exit `0`.

Open **Control Centre → Focus** and confirm nothing is active. If you keep a
Focus on while you work, add Script Editor to that Focus's **Allowed
Notifications** so long-running turns can still reach you.

## 5. Sound, and why it does not use `sound name`

The obvious way to make a notification audible is the AppleScript argument:

```applescript
display notification "..." with title "..." sound name "Glass"
```

Do not rely on it. **The chime rides on the notification.** When macOS
suppresses the banner — for the permission reason in step 1, or the Focus
reason in step 4 — it suppresses the sound along with it. You get silence and
exit `0`, which is the failure mode this whole page is about.

So `notify_done.py` plays the sound on a separate path:

```python
SOUND_FILE = "/System/Library/Sounds/Glass.aiff"

subprocess.Popen(
    ["afplay", SOUND_FILE],
    stdout=subprocess.DEVNULL,
    stderr=subprocess.DEVNULL,
)
```

`afplay` writes to the audio device directly and is not routed through
Notification Center, so it survives a machine where Script Editor was never
granted permission. On a machine where banners *do* work, you get the banner
from `osascript` and the chime from `afplay` — which is why the AppleScript no
longer asks for a sound of its own, and does not double-chime.

`Popen` rather than `run`: the hook fires at the end of every turn, and a
notifier has no business making you wait for a sound file to finish playing.

This also gives you a clean way to split the problem when something is silent:

```bash
afplay /System/Library/Sounds/Glass.aiff        # audio output itself
osascript -e 'display notification "x" with title "y"'   # Notification Center
```

If the first is audible and the second shows nothing, the fault is squarely in
notification permissions, not in your sound settings.

To change the chime, point `SOUND_FILE` at another file from:

```bash
ls /System/Library/Sounds
```

`Ping.aiff`, `Submarine.aiff`, and `Hero.aiff` are the usual alternatives.

## 6. The change, before and after

The scaffold shipped with the obvious version of this hook, and the obvious
version is the broken one. If you are comparing against an older copy — or
wondering why the code does not look like every `display notification` example
online — this is what moved and why.

### Before

One command did everything. Banner and chime were the same request:

```python
command = [
    "osascript",
    "-e",
    f'display notification "{safe}" with title "{TITLE}" sound name "Glass"',
]

try:
    subprocess.run(command, capture_output=True, timeout=5, check=False)
except (OSError, subprocess.TimeoutExpired):
    pass
```

Readable, portable, and completely silent on a machine that has not granted
Script Editor permission to notify — which is every machine, until someone
does. `subprocess.run` returns cleanly. The hook exits `0`. Nothing is shown
and nothing is heard.

### After

The chime is lifted out onto its own path, and the AppleScript keeps only the
banner:

```python
SOUND_FILE = "/System/Library/Sounds/Glass.aiff"


def play_sound() -> None:
    if not os.path.exists(SOUND_FILE):
        return

    # Detached, not waited on: a notifier must not add latency to a turn.
    with contextlib.suppress(OSError):
        subprocess.Popen(
            ["afplay", SOUND_FILE],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
```

```python
if system == "Darwin":
    # The chime goes first and on its own path, because it is the half of
    # this that still works when the banner is being dropped.
    play_sound()

    safe = body.replace("\\", "").replace('"', "'")
    command = [
        "osascript",
        "-e",
        f'display notification "{safe}" with title "{TITLE}"',   # no sound name
    ]
```

### What it buys you

| Machine state | Before | After |
|---|---|---|
| Script Editor allowed to notify | Banner + chime | Banner + chime |
| Script Editor not allowed (the default) | **Nothing** | Chime |
| A Focus mode is active | **Nothing** | Chime |
| System notification sound switched off | Silent banner | Chime |

Three changes, and only the first is the fix:

1. **`afplay` instead of `sound name`.** The sound no longer travels inside the
   notification, so it no longer dies with it.
2. **`Popen` instead of `run`.** The old call was already waited on; adding a
   second waited-on call would have put audio playback on the end of every
   turn. Nothing needs the exit status of a chime.
3. **`sound name` removed from the AppleScript.** Without this, a correctly
   configured machine would chime twice.

### The part that did not change

The hook still never blocks, still exits `0` on every path, and still falls
back to `notify-send` and then the terminal bell off macOS. `play_sound` checks
that the sound file exists before calling `afplay`, and suppresses `OSError` if
it is missing anyway. A notifier that can fail a turn is a notifier that will.

## 7. Non-macOS, and the portable floor

`notify_done.py` already branches on platform:

- **Linux** — uses `notify-send`, if it is on `PATH`. Install it with
  `sudo apt install libnotify-bin` on Debian/Ubuntu. A machine with no
  notification daemon running (a bare container, some WMs) will accept the
  command and show nothing.
- **Windows, headless containers, anything else** — falls back to writing the
  terminal bell (`\a`) and the message to stderr. Whether the bell is audible
  depends on your terminal; VS Code's integrated terminal mutes it by default.

## 8. Optional: `terminal-notifier`

If Script Editor permissions are not an option — a locked-down managed Mac, for
instance — `terminal-notifier` posts under its own bundle identifier and can be
granted permission independently:

```bash
brew install terminal-notifier
terminal-notifier -title "Smart Scene Analyzer" -message "test" -sound Glass
```

Using it means editing `notify_done.py` to prefer `terminal-notifier` when
`shutil.which("terminal-notifier")` finds it, and falling back to `osascript`
otherwise. This is an extra dependency on every student's machine, so it is a
deliberate choice rather than the default.

## 9. What this teaches

`notify_done.py` is the harmless hook in the scaffold — it fires constantly,
does something immediately visible, and cannot fail a turn. That is exactly why
it is the right place to learn this lesson:

**A hook that exits `0` has not necessarily done anything.**

`credit_gate.py` and `units_guard.py` block by returning exit code `2`, and you
find out immediately when they fire. A notifier that fails does so in silence,
and the only evidence is a banner you never saw. When you write your own hooks,
decide which of those two failure modes you are building — and if it is the
silent one, give yourself a way to test it by hand, as step 2 does here.
