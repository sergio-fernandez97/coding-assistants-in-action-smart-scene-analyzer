# Lesson 01 — Deliverables checklist

Complete this in the README's order. The live session is complete after its live boxes;
the lesson is complete when every box is checked after post-session homework.

## Voice workflow

- [ ] `ffmpeg -version` succeeds before the session
- [ ] VoiceMode is visible in `/mcp`
- [ ] `/voicemode:converse` completes one short spoken exchange, or the typed fallback
      card was used and the failure was recorded for follow-up
- [ ] You can name VAD, Whisper STT, Claude, and Kokoro TTS in the conversation pipeline
- [ ] You can say why VoiceMode is user-scoped and why the course Roboflow MCP config is
      project-scoped

## Repository

- [ ] `smart-scene-analyzer` exists as its own git repository, separate from the course repo
- [ ] `uv sync` succeeds from a clean clone
- [ ] `uv run pytest` runs (passing with zero tests is fine at this stage)
- [ ] `uv run ruff check .` is clean
- [ ] Pushed to GitHub

## Harness

- [ ] `CLAUDE.md` exists and keeps the *Engineering roles*, *Conventions*, and *Constraints for assistants* sections
- [ ] `CLAUDE.md` contains nothing derivable by reading `src/` — no restated code
- [ ] `.claude/settings.json` reviewed; you can explain why each entry is in `allow` vs. `ask` vs. `deny`
- [ ] `/permissions` shows the policy loaded
- [ ] `/agents` lists all ten agents
- [ ] You can state the purpose of `architecture`, `documentation`, and `devops` in one
      sentence each, without re-reading them
- [ ] `/skills` lists the five project skills
- [ ] You can name the four harness layers and say how each one constrains

## Hooks

- [ ] The `hooks` block in `.claude/settings.json` read, and each script opened
- [ ] **`notify_done.py` observed running** — a desktop notification arrives at the end of
      a turn, or the terminal bell does on a platform without a notification daemon
- [ ] **A permission prompt also notified you** — the same script on the `Notification` event
- [ ] You can say why `Stop` takes no `matcher` when `PreToolUse` does
- [ ] **`format_python.py` observed running** — a badly formatted file came back formatted
- [ ] **`units_guard.py` observed blocking** — a write containing "meters" was refused
- [ ] You can say why `CLAUDE.md` saying "not metres" was not sufficient on its own
- [ ] You can say what to do when a hook blocks you, and what not to do

## Design artifacts

- [ ] `docs/requirements.md` — every `<...>` placeholder replaced
- [ ] N1 (p95 latency) is a real number derived from the user experience, not from the model
- [ ] **N1 states whether it is client- or server-observed**, and if client-observed, the
      link characteristics it assumes. Lesson 05 measures against this
- [ ] The requirements are written for a user holding a phone, not for a `curl` command
- [ ] "Out of scope" section is non-empty
- [ ] `docs/architecture.md` — component diagram present
- [ ] Every module boundary has a data contract stating **type, units, and coordinate convention**
- [ ] The fusion strategy (box + depth map → one depth value) names a specific method and its failure mode
- [ ] Latency budget allocates N1 across stages and the numbers sum correctly
- [ ] An "Assumptions" section exists and is non-empty
- [ ] `src/smart_scene_analyzer/` has module stubs with docstrings and **no function bodies**
- [ ] `docs/roadmap.md` — Weeks 2–6, each with artifact-shaped exit criteria
- [ ] `docs/roadmap.md` has a "Blocked on decisions" section

## Decisions

- [ ] `docs/decisions/0001-*.md` records the inference target with real consequences listed
- [ ] Each ADR's "Consequences" names the files and infrastructure now depending on it
- [ ] The `TODO(Lesson 01)` markers in `CLAUDE.md` are resolved or still flagged deliberately

## Documentation

- [ ] `README.md` replaced — no template placeholder text remains
- [ ] **Setup section verified by deleting `.venv/` and following it verbatim**
- [ ] "Current status" section honestly marks stubs as stubs
- [ ] No performance numbers appear anywhere (no model has been trained)
- [ ] `CONTRIBUTING.md` exists with the quality gates and their commands

## Environment

- [ ] `app/app.json` is valid JSON and names the native config plugins both ML runtimes need
- [ ] `app/metro.config.js` includes **both** `tflite` and `pte` in `resolver.assetExts`
- [ ] `git check-ignore -v app/ios app/android node_modules` prints a rule for **each**
      (a path it says nothing about is a path that gets committed)
- [ ] `.github/workflows/ci.yml` runs lint before tests, and has **no** build or deploy job
- [ ] No credential is bound for the app bundle: `grep -rn "EXPO_PUBLIC" app/` returns
      nothing, or only build flags

## Hygiene

- [ ] `git status` shows no `.env`, no `data/`, no `.venv/`, no `*.pt`
- [ ] `.env` exists locally, is filled in, and is **not** tracked: `git check-ignore .env` prints `.env`
- [ ] `.env.example` documents every variable with no real values

## The one that isn't mechanical

- [ ] **You found at least one thing in `docs/architecture.md` you disagree with, and
      either changed it or wrote down why you kept it.**

If you skipped this box, go back. Every generated architecture contains a debatable
choice. Being unable to find it means you accepted the output rather than reviewed it
— and reviewing generated design is the entire skill this session teaches.
