# Lessons

One directory per session. Everything needed to run a session lives inside it — no
hunting through the repo mid-lesson.

| Lesson | Notion week | Focus | Status |
|---|---|---|---|
| [01 — Project Definition & System Design](01-project-definition-and-system-design/) | Week 1 | Repository, the four-layer harness, architecture, roadmap | Ready |
| [02 — Dataset Engineering](02-dataset-engineering/) | Week 2 | Roboflow MCP, annotation conversion, dataset versions, the credit harness | Ready |
| [03 — Model Development](03-model-development/) | Week 3 | YOLO11 fine-tuning, MLflow, domain adaptation, depth inference | Ready |
| [04 — Export, Quantization & Numerical Parity](04-backend-engineering/) | Week 4 | Detection–depth fusion, model export, int8 quantization, parity against the reference | Rewriting |
| [05 — On-Device Inference & Mobile Delivery](05-mobile-client-and-delivery/) | Week 5 | Expo dev build on both simulators, two on-device runtimes, the artifact contract, device-vs-reference parity | Rewriting |
| 06 — CI / CD / CT | Week 6 | GitHub Actions, continuous training, promotion logic | Not written |

## Lesson directory layout

```
NN-slug/
├── README.md                 The step-by-step. The primary artifact.
└── resources/
    ├── prompts/              Copy-paste prompts, one file per agent handoff
    ├── templates/            Files students copy into their own project
    ├── checklists/           Deliverables and verification
    └── scripts/              Verification helpers only — never solution code
```

Prompts live in their own files rather than inline in the README because students copy
files reliably and mis-copy fenced blocks buried in prose. Each prompt file also
carries a *"what good output looks like"* and a *"reject and re-run if"* section —
judging generated output is the skill the course teaches, so every prompt states the
acceptance criteria alongside the request.

### Prompts versus skills

Both live in the harness and they are not the same thing. The rule this course applies:

| | Prompt file | Project skill |
|---|---|---|
| Lives in | `lessons/NN/resources/prompts/` | `template/.claude/skills/` |
| Invoked | Once, to produce a specific artifact | Many times, whenever the situation recurs |
| Contains | This dataset, this endpoint, this model | The method and its acceptance criteria |
| Example | "Convert SUN RGB-D, whose metadata is a MATLAB struct" | "Inspect before you convert; verify against pixels" |

Five procedures were repeating across lessons and are now skills:
`credit-ledger`, `error-triage`, `annotation-conversion`, `dataset-qa-sweep`,
`offline-suite`. Where a prompt uses one, its header names it — the prompt supplies the
instance, the skill supplies the method. The prompts were not deleted, because the
instance-specific detail is the part that was never generic.

The tell for which one you are writing: **if the second copy would differ only in nouns,
it is a skill.** The SUN RGB-D and NYU converter prompts were 150 lines each and shared
everything except the file format, which is what made the split obvious.

## README contract

Every lesson README uses this section order:

1. **Session goal** — one paragraph on what changes about the student's system
2. **Prerequisites** — what must already be true, with a check command each
3. **Deliverables** — the artifacts that exist when the session ends
4. **Step-by-step** — numbered, each step: *Do* → *Command/Prompt* → *Expected result*
5. **Verification** — how to prove the session succeeded
6. **Open items** — anything unresolved, marked `⚠️ OPEN`
7. **Further reading**

A step whose success a student cannot verify is an incomplete step.

### The ⚠️ OPEN convention

Where a step depends on a decision nobody has made, the lesson says so and presents the
real branches with their trade-offs. It never invents an answer. A confidently wrong
instruction costs a student an hour of debugging a problem that does not exist; a
flagged one costs nothing.

Every `⚠️ OPEN` marker has a matching entry in the course [`TODO.md`](../TODO.md).

## Engineering roles across the course

Roles accumulate. Each is a subagent in the student's `.claude/agents/`, introduced in
the lesson that needs it and reused afterwards.

| Role | Introduced | Owns |
|---|---|---|
| `architecture` | 01 | System design, module boundaries, data contracts, engineering plan |
| `documentation` | 01 | README, architecture prose, contribution guide, model cards |
| `devops` | 01 | Dev environment, mobile builds, GitHub Actions, releases |
| `dataset-engineer` | 02 | Roboflow platform: projects, annotations, versions, exports |
| `data-pipeline` | 02 | Local data code: conversion, preprocessing, validation |
| `ml-engineer` | 03 | Training, fine-tuning, error diagnosis, **export and quantization** |
| `evaluation` | 03 | Metric reports, confusion matrices, performance summaries |
| `qa` | 04 | Unit, integration, and regression tests |
| `integration` | 04 | Fusing detection, classification, and depth |
| `mobile` | 05 | The Expo app: on-device inference, the fusion port, overlays, latency |
| `mlops` | 06 | Training and evaluation pipelines, promotion logic, rollback |

**All ten ship in [`template/.claude/agents/`](../template/.claude/agents/)**, with
Codex twins under `template/plugins/smart-scene-analyzer/skills/`. "Introduced in" means
the lesson where the student first reads the definition and uses it — not where the file
appears. Lesson 02 already established that pattern with `dataset-engineer`.

Three boundaries in that table are load-bearing rather than tidy:

- **`ml-engineer` / `evaluation`** — `evaluation` has no `Edit` tool. An agent that both
  trains a model and reports whether it is good can improve the number without improving
  the model, and will not need to be dishonest to do it. Removing the tool removes the
  shortcut.
- **`integration` / `qa`** — identical tool lists, different responsibilities, drawn where
  the failure modes differ. `qa` did not write the code it tests.
- **`mobile` / `ml-engineer`** — `mobile` does not change the exported artifacts, and
  `ml-engineer` does not change the app. When the device disagrees with the Python
  reference, that disagreement is the finding. One role owning both sides would settle it
  by adjusting whichever side was easier to reach, and *which of the two was wrong* — the
  only thing worth knowing — would stop being recoverable.

## The hooks

`template/.claude/hooks/` is the layer that does not depend on anyone reading anything.
Introduced cheapest-first, so students meet the mechanism before it guards anything
expensive.

| Hook | Event | Effect | Introduced |
|---|---|---|---|
| `notify_done.py` | `Stop`, `Notification` | Desktop notification when the turn ends or a prompt is waiting. Never blocks | 01 — the free one |
| `format_python.py` | `PostToolUse` | `ruff format` + `--fix`. Never blocks | 01 — deliberately trivial |
| `session_balance.py` | `SessionStart` | Puts the credit balance into context | 01 |
| `credit_gate.py` | `PreToolUse` | **Blocks** billed Roboflow calls with no ledger estimate | **02 — the load-bearing one** |
| `units_guard.py` | `PreToolUse` | **Blocks** metric-depth identifiers in `src/` **and `app/`** | 01 (demonstrated), 03 (earns it), 05 (needs it) |
| `artifact_drift.py` | `PostToolUse` | Warns when the bundled model artifacts are older than what produced them | 05 |

Two design points worth preserving if these are edited:

- **`notify_done` is the introduction, and it is deliberately weightless.** It observes
  the turn ending and cannot affect it, which makes it the cheapest possible place to
  learn that the harness runs *your* script on a Claude Code event. It is also the only
  hook here serving the operator rather than the codebase. Keep that framing if it is
  edited — the distance between it and `credit_gate` is what Lesson 01 step 5 is built on.
- **Only two of them block.** `artifact_drift` warns because retraining and editing an
  export config are legitimate work with a consequence — and because re-exporting mid-edit
  would cost minutes of quantization. `units_guard` blocks because writing `depth_meters`
  is not legitimate at all. Choosing correctly between *wrong* and *has a consequence* is
  most of hook design, and Lesson 05 step 4 makes students compare the two directly.
- **`credit_gate` blocks unaccounted spending, not expensive spending.** A student can
  still spend the entire budget. They cannot spend it without having written down what
  they expected it to cost, which is the only part that was ever at risk.

Note also that **Codex does not run hooks.** `template/AGENTS.md` says so explicitly and
tells a Codex session that those two rules are its own to keep. Do not quietly let that
note rot if the hooks change.

---

## Reusable material for Lesson 06

`computer-vision-skills/` (local clone of
[roboflow/computer-vision-skills](https://github.com/roboflow/computer-vision-skills),
gitignored) contains 9 skills across ~3,500 lines. **Reuse it rather than restating it**
— and verify facts against it rather than from memory, since model IDs, credit rates, and
tool names change upstream.

Lessons 02–05 draw on it as follows, recorded here so a maintainer can trace a claim back
to its source:

| Lesson | Sources used |
|---|---|
| 02 | `data-management/SKILL.md` (upload, tags, RoboQL, versions), `data-management/labeling.md` (Auto Label and its free 4-image preview), `plans-and-pricing/SKILL.md` (the rate table behind the whole credit harness), `universe/SKILL.md`, `inference/workflows.md` (the YOLO-World block) |
| 03 | `training-and-evaluation/SKILL.md` (exact `model_id` values, training controls, **and the RF-DETR NAS default the course overrides**), `improvement-playbook.md` (the confusion-matrix decision tree behind the error analysis), `custom-weights-upload/SKILL.md`, `plans-and-pricing/SKILL.md` (training rates, Core-plan feature list) |
| 04 | `inference/SKILL.md` (deployment option comparison, retained as the cloud contrast rows), `plans-and-pricing/SKILL.md`. Its on-device half is sourced from the RF-DETR/Ultralytics export docs and PyTorch's ExecuTorch docs, cited inline |
| 05 | **None.** Lesson 05 spends zero Roboflow credits and touches no Roboflow surface — its sources are the Expo docs, the `react-native-fast-tflite` README, and the `react-native-executorch` docs, all cited inline in the lesson |

Row 05 is worth noticing rather than skipping. Every lesson from 02 onward has drawn on
`computer-vision-skills/` and priced its work against the credit ledger; Lesson 05 does
neither, and instead introduces a second budget that behaves differently. If a future
edit finds itself adding a Roboflow call to the inference path in Lesson 05, that row is
the thing it is breaking — and on-device makes the row stronger, not weaker: the phone
has no credentials to make such a call with.

### Lesson 06 — CI / CD / CT

| Source | What it gives the lesson |
|---|---|
| `training-and-evaluation/active-learning.md` | The production feedback loop via the Project Model Workflow block — essentially the CT pipeline pre-written |
| `inference/batch-jobs.md`, `batch-staging.md` | Batch evaluation runs, the shape CI needs for model comparison |
| `inference/bin/poll_batch_job.py` | A working polling script — usable in a GitHub Actions step with minimal change |
| `api-reference/api-key-management.md` | Secret handling; maps onto GitHub Actions secrets |
| `plans-and-pricing/SKILL.md` | Credit rates — an automated retraining pipeline can burn a budget quietly |

⚠️ **Lesson 06 has roughly 4 credits to work with**, and it is the lesson most able to
spend them without anyone noticing. Two constraints to design around from the start:

- **Batch processing on GPU is 4 credits/hour** — the worst rate on the platform — and
  **dedicated deployments bill uptime**, so a pipeline that provisions one and fails
  before tearing it down costs 24 credits a day. Both are already denied or forbidden in
  the scaffold; the CI design has to stay inside that.
- ⚠️ **Lesson 06 no longer has a deploy target, and this is unresolved.** The pipeline
  used to build an image and push it to a registry. There is no image and no registry now:
  "deploy" means producing an app binary plus the exported model artifacts, and shipping a
  model update means an app-store release on somebody else's timetable. What CI can
  usefully automate — export, quantization, the parity check, artifact-size regression —
  is a different pipeline from the one Lesson 06 was scoped around. **Redesign this before
  Lesson 06 is written**; do not assume the CD half survives the move.
- **The active-learning review loop has a head start.** Lesson 02's Auto Label audit
  produced a per-class table of where a foundation model agrees with human annotators.
  That table is exactly the input the "which predictions can we accept without review"
  question needs, and it was measured on this project's own data.

### Cross-cutting

| Source | Where it applies |
|---|---|
| `product-navigation/SKILL.md`, `features-by-page.md` | Appendix material for students navigating `app.roboflow.com` |
| `universe/SKILL.md` | Dataset and model discovery; used in Lesson 02, useful again for checkpoint selection |
| `data-management/labeling.md` | Annotation tooling and Auto Label. The reference for Lesson 02's audit; returns in Lesson 06 for the active-learning review loop |
| `plans-and-pricing/SKILL.md` | The rate table behind the credit harness. Referenced by every lesson from 02 onward |

### Not currently used

`cloud-storage/SKILL.md` — it was the candidate answer to depth-artifact storage, which
the inference-only depth scope removed the need for. Still the right starting point if a
later cohort wants quantitative depth evaluation.

The VLM/multimodal sections of `training-and-evaluation`, available if the course later
adds an optional module.
