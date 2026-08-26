# VoiceMode command card

Use this card when you are completing Lesson 01's pre-session voice setup, or when the
audio path fails during the live session. The primary course path is macOS.

## Install before the session

```bash
brew install ffmpeg
ffmpeg -version

claude plugin marketplace add mbailey/voicemode
claude plugin install voicemode@voicemode
```

Open or restart Claude Code, then run:

```text
/voicemode:install
/mcp
/voicemode:converse
```

Expected: `/mcp` shows VoiceMode, and `/voicemode:converse` transcribes your sentence and
speaks Claude's reply. Grant microphone access to your terminal application in macOS
Privacy & Security if prompted.

## Speak these kinds of requests

- “Read `CLAUDE.md` and explain the project constraints in three bullets.”
- “Use the architecture role. First repeat the inference-target decision back to me.”
- “Review `docs/architecture.md` against the acceptance criteria. Do not edit it yet.”
- “Show the exact command before you run it.”

Type instead of speaking commands, paths, code, model IDs, API keys, passwords, tokens,
and other sensitive or exact values.

## If voice is unavailable

You can complete the live session by typing the same intent. Use these equivalents:

| Voice action | Typed fallback |
|---|---|
| Start a conversation | Type the request directly at the Claude Code prompt. |
| Check the server | `/mcp` |
| Check Claude configuration sources | `/status` |
| Open the role list | `/agents` |
| Open project skills | `/skills` |

Tell the instructor which check failed and continue with the typed workflow. Do not spend
the live session reinstalling audio software.

## Quick recovery

1. Confirm FFmpeg: `ffmpeg -version`.
2. Confirm the plugin/server in `/mcp`; reconnect or restart Claude Code if it is absent.
3. Check macOS microphone permission for your terminal application.
4. If recording does not stop at silence, consult the course's
   [manual VoiceMode guide](https://gist.github.com/jlmalone/02d09aeb4e09890a8a9e7c2333a18377)
   for its `webrtcvad` and `setuptools<71` workaround and service diagnostics.

The audio pipeline is VAD → local Whisper speech-to-text → Claude Code → local Kokoro
text-to-speech. Audio is local; the transcript is still a Claude Code prompt. Sources
checked 2026-08-26.
