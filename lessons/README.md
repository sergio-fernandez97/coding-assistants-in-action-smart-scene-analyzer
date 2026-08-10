# Lessons

One directory per session. Everything needed to run a session lives inside it — no
hunting through the repo mid-lesson.

| Lesson | Notion week | Focus | Status |
|---|---|---|---|
| [01 — Project Definition & System Design](01-project-definition-and-system-design/) | Week 1 | Repository, Claude Code harness, architecture, roadmap | Ready |
| [02 — Dataset Engineering](02-dataset-engineering/) | Week 2 | Roboflow MCP, annotation conversion, dataset versions, the credit harness | Ready |
| [03 — Model Development](03-model-development/) | Week 3 | YOLO11 fine-tuning, MLflow, domain adaptation, depth inference | Ready |
| [04 — Backend Engineering & Production APIs](04-backend-engineering/) | Week 4 | FastAPI, detection–depth fusion, Docker, tests, deployment economics | Ready |
| 05 — CI / CD / CT | Week 5 | GitHub Actions, continuous training, promotion logic | Not written |

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
| `devops` | 01 | Docker, dev environment, GitHub Actions, releases |
| `dataset-engineer` | 02 | Roboflow platform: projects, annotations, versions, exports |
| `data-pipeline` | 02 | Local data code: conversion, preprocessing, validation |
| `ml-engineer` | 03 | Training, fine-tuning, hyperparameters, error diagnosis |
| `evaluation` | 03 | Metric reports, confusion matrices, performance summaries |
| `backend` | 04 | FastAPI, dependency injection, logging |
| `qa` | 04 | Unit, integration, and regression tests |
| `integration` | 04 | Fusing detection, classification, and depth |
| `mlops` | 05 | Training and evaluation pipelines, promotion logic, rollback |

**All ten ship in [`template/.claude/agents/`](../template/.claude/agents/)**, with Codex
twins under `template/plugins/smart-scene-analyzer/skills/`. "Introduced in" means the
lesson where the student first reads the definition and uses it — not where the file
appears. Lesson 02 already established that pattern with `dataset-engineer`.

Two boundaries in that table are load-bearing rather than tidy:

- **`ml-engineer` / `evaluation`** — `evaluation` has no `Edit` tool. An agent that both
  trains a model and reports whether it is good can improve the number without improving
  the model, and will not need to be dishonest to do it. Removing the tool removes the
  shortcut.
- **`backend` / `integration` / `qa`** — identical tool lists, different responsibilities,
  drawn where the failure modes differ. `qa` did not write the code it tests.

---

## Reusable material for Lesson 05

`computer-vision-skills/` (local clone of
[roboflow/computer-vision-skills](https://github.com/roboflow/computer-vision-skills),
gitignored) contains 9 skills across ~3,500 lines. **Reuse it rather than restating it**
— and verify facts against it rather than from memory, since model IDs, credit rates, and
tool names change upstream.

Lessons 02–04 draw on it as follows, recorded here so a maintainer can trace a claim back
to its source:

| Lesson | Sources used |
|---|---|
| 02 | `data-management/SKILL.md` (upload, tags, RoboQL, versions), `data-management/labeling.md` (Auto Label and its free 4-image preview), `plans-and-pricing/SKILL.md` (the rate table behind the whole credit harness), `universe/SKILL.md`, `inference/workflows.md` (the YOLO-World block) |
| 03 | `training-and-evaluation/SKILL.md` (exact `model_id` values, training controls, **and the RF-DETR NAS default the course overrides**), `improvement-playbook.md` (the confusion-matrix decision tree behind the error analysis), `custom-weights-upload/SKILL.md`, `plans-and-pricing/SKILL.md` (training rates, Core-plan feature list) |
| 04 | `inference/SKILL.md` (deployment option comparison), `inference/local-tooling.md` (the metered `localhost:9001` server), `api-reference/inference.md` (v2 bills by execution seconds), `plans-and-pricing/SKILL.md` |

### Lesson 05 — CI / CD / CT

| Source | What it gives the lesson |
|---|---|
| `training-and-evaluation/active-learning.md` | The production feedback loop via the Project Model Workflow block — essentially the CT pipeline pre-written |
| `inference/batch-jobs.md`, `batch-staging.md` | Batch evaluation runs, the shape CI needs for model comparison |
| `inference/bin/poll_batch_job.py` | A working polling script — usable in a GitHub Actions step with minimal change |
| `api-reference/api-key-management.md` | Secret handling; maps onto GitHub Actions secrets |
| `plans-and-pricing/SKILL.md` | Credit rates — an automated retraining pipeline can burn a budget quietly |

⚠️ **Lesson 05 has roughly 4 credits to work with**, and it is the lesson most able to
spend them without anyone noticing. Two constraints to design around from the start:

- **Batch processing on GPU is 4 credits/hour** — the worst rate on the platform — and
  **dedicated deployments bill uptime**, so a pipeline that provisions one and fails
  before tearing it down costs 24 credits a day. Both are already denied or forbidden in
  the scaffold; the CI design has to stay inside that.
- **The active-learning review loop has a head start.** Lesson 02's Auto Label audit
  produced a per-class table of where a foundation model agrees with human annotators.
  That table is exactly the input the "which predictions can we accept without review"
  question needs, and it was measured on this project's own data.

### Cross-cutting

| Source | Where it applies |
|---|---|
| `product-navigation/SKILL.md`, `features-by-page.md` | Appendix material for students navigating `app.roboflow.com` |
| `universe/SKILL.md` | Dataset and model discovery; used in Lesson 02, useful again for checkpoint selection |
| `data-management/labeling.md` | Annotation tooling and Auto Label. The reference for Lesson 02's audit; returns in Lesson 05 for the active-learning review loop |
| `plans-and-pricing/SKILL.md` | The rate table behind the credit harness. Referenced by every lesson from 02 onward |

### Not currently used

`cloud-storage/SKILL.md` — it was the candidate answer to depth-artifact storage, which
the inference-only depth scope removed the need for. Still the right starting point if a
later cohort wants quantitative depth evaluation.

The VLM/multimodal sections of `training-and-evaluation`, available if the course later
adds an optional module.
