# Smart Scene Analyzer

> Scaffold copied from the course `template/` in Lesson 01. The Documentation Agent
> replaces this file in Lesson 01 step 8 — what you see now is a placeholder so the
> repo is coherent from the first commit.

A mobile perception system that runs entirely on the handset. An Expo app on iOS or
Android captures an image, runs object detection and monocular depth estimation **on the
device**, and draws the detected objects with class labels, bounding boxes, and per-object
relative depth. No image leaves the phone.

| Layer | Choice |
|---|---|
| Detection / classification | YOLO11 → int8 TFLite |
| Monocular depth | Depth Anything V2 → ExecuTorch (`.pte`) |
| On-device runtimes | `react-native-fast-tflite`, `react-native-executorch` |
| App | Expo / React Native (TypeScript), development build |
| Training, export, reference implementation | Python (`src/`) |
| Experiment tracking | MLflow |
| Dataset versioning | Roboflow |

## Setup

```bash
uv python install 3.11
uv sync
cp .env.example .env    # then fill in ROBOFLOW_API_KEY and ROBOFLOW_WORKSPACE
```

The app is set up in Lesson 05; `app/` is empty until then. It needs Xcode (for the iOS
Simulator) and/or Android Studio (for the Android Emulator) — see `app/README.md`.

## Commands

```bash
uv run pytest            # tests, including export parity
uv run ruff check .      # lint
uv run ruff format .     # format
uv run mypy src          # type check

cd app && npm install          # app dependencies              (Lesson 05)
cd app && npx expo run:ios     # build + run on the iOS Simulator     (Lesson 05)
cd app && npx expo run:android # build + run on the Android Emulator  (Lesson 05)
```

## Layout

```
src/smart_scene_analyzer/   Python — training, export, reference implementation
app/                        The Expo app — the product (Lesson 05)
app/assets/models/          Bundled .tflite and .pte artifacts — what actually runs
app/src/fusion/             TypeScript port of the Python fusion layer
tests/                      Unit, integration, regression, and export-parity tests
docs/                       Architecture, roadmap, model cards
docs/decisions/             ADRs — one per architectural decision
docs/credit-budget.md       Roboflow credit ledger — read before any billed call
docs/artifact-budget.md     Model and app size — the budget that fails at install time
data/                       Dataset exports (gitignored)
notebooks/                  Exploration only
.claude/agents/             Engineering role definitions
.claude/skills/             This project's own procedures
.claude/hooks/              Enforcement — these run whether or not you read them
.agents/plugins/            Local Codex role Skills marketplace
```

## Working with assistants

Project rules live in [`CLAUDE.md`](CLAUDE.md) and load into every Claude Code session
here. The harness has four layers, and they are not interchangeable:

| Layer | Where | What it does |
|---|---|---|
| Rules | `CLAUDE.md` | Loaded into every session. Constrains by being read |
| Roles | `.claude/agents/` | Separate context, scoped tools, one responsibility each |
| Procedures | `.claude/skills/` | Repeatable methods with their own acceptance criteria |
| Enforcement | `.claude/hooks/` | Runs on tool calls. Constrains by **blocking** |

Read all four before your first session. The last one is the only layer that does not
depend on anybody cooperating — two of its hooks return a hard block, and if one stops
you, the fix is to satisfy it rather than to edit it.

## Working with Codex

Project rules for Codex live in [`AGENTS.md`](AGENTS.md). Install the local role Skills
once after copying this scaffold:

```bash
codex plugin marketplace add .
codex plugin add smart-scene-analyzer@smart-scene-analyzer-course
```

Use the matching installed Skill for architecture, documentation, DevOps, dataset
engineering, mobile, or local data-pipeline work. The Dataset Engineer Skill requires the
Roboflow tools and reference Skills before it performs platform operations.

**Codex does not run the hooks in `.claude/hooks/`.** The two that block — the credit gate
and the depth-units guard — are rules you keep yourself here. `AGENTS.md` says so, and the
hook scripts state each rule more precisely than prose does.
