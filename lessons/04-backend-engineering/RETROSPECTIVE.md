# Lesson 04 — retrospective

> Instructor-facing working notes on fitting Lesson 04 into a **90-minute live session**.
> Written 2026-08-25, while running step 2 for the first time.
>
> Linked from `README.md`'s header so students can see the shape of their own week. It
> stays instructor-facing in voice — a student reading it learns what is homework and
> why, which is not a secret worth keeping.

## The constraint

**The live session is 90 minutes. That is fixed.** The README's 5–6 hours is honest for
doing the lesson end to end, so the question is not what to trim — it is what has to
happen *in the room*, and what can be moved either side of it.

Pre-session homework is available and is used heavily here. That is what makes 90 minutes
possible at all.

## What has to be live

Lesson 04 teaches three things. Everything else is scaffolding around them:

1. **An artifact makes promises nothing verifies.** The payoff is the moment a student
   compares the contract they wrote against the file they actually got.
2. **Three coordinate spaces, and a box indexed into the wrong one returns a plausible
   number.** This is the fusion layer, and it is the only part of the lesson where a
   student reliably gets stuck in a way that teaches them something.
3. **"It exported" and "it still works" are different claims.** Export parity.

One, two, and three stay. Everything else moves.

## What makes the move possible

Two course assets have to exist before this shape works. Neither exists yet — **both are
prerequisites for running the 90-minute version**, not nice-to-haves.

### Asset A — a ready-made export script **and pre-exported artifacts**

`resources/templates/export.py`, complete and runnable, plus **both exported artifacts
published as a course download** (the int8 `.tflite` and the `.pte`).

The fallback artifacts are the important half. The lesson's own Open items record that the
export commands are unverified against this project's models on a clean machine, and that
`ultralytics` TFLite export and `optimum-executorch` pull large, platform-sensitive
dependency trees. A student who hits that alone at 11pm loses the evening and arrives with
nothing to work on — which costs the live session, not just their evening.

With the fallback in place, a failed export becomes a finding they report rather than a
blocker. **Tell them explicitly that using the fallback is an acceptable outcome and that
the failure should be written down.**

### Asset B — a fusion skeleton and its fixtures

`resources/templates/fusion.py` with the real signatures, docstrings naming both coordinate
spaces and the depth units, every degenerate case listed in the docstring, and bodies that
`raise NotImplementedError`. Plus `tests/fixtures/fusion_cases.json`, ready to load.

Students fill bodies with the `integration` agent. They do not design the interface in the
room — designing it is where the 60 minutes went.

### Asset C — the live viewer, provided; the one-frame check, written

`resources/scripts/watch_fusion_live.py` ships finished. It is an MJPEG server, a worker
thread, and a frame buffer — real code, and none of it is detection, depth, fusion, or
export. Building it in the room would spend the session on plumbing.

`check_fusion_live.py` is the opposite call: students **write** it, in step 3b, from
`resources/prompts/07-live-check.md`. It is fifty lines, and the fifty lines are the first
code in the project that puts all three models' outputs on the same pixels. The rule that
makes it worth the time is in the prompt: **import `fuse_detections_with_depth`, do not
reimplement the reduction.** A verification script that reimplements what it verifies
proves only that two things written in the same hour agree with each other.

Deliberately **not** in `resources/scripts/` — a finished copy there would make the step a
`cp`, and the course's own rule for that directory is verification helpers, never solution
code.

## Pre-session homework (~1h 45m)

Order matters: **P2 must be finished before P3 starts.** Writing the contract after seeing
the artifact is not the exercise, it is the failure mode the exercise exists to prevent.

| # | Task | Hand in | Est. |
|---|---|---|---|
| **P1** | Read `.claude/agents/ml-engineer.md`, `qa.md`, `integration.md`. Answer: who owns *"the int8 export lost the `lamp` class"*, who owns *"the depth value is sampled from the wrong region"*, and why the boundary is responsibility rather than capability | Two sentences | 15 min |
| **P2** | **Step 2 in full.** Using `resources/prompts/01-artifact-contract.md` with `ml-engineer`, fill the **Exported artifact** table in both model cards with what you INTEND to produce. Every value marked `INTENDED`. Name one — and only one — source of truth for label order. Decide the int8 calibration set here and write it down | Both cards, committed **before** P3 | 45 min |
| **P3** | Run `resources/templates/export.py`. If it fails, record what broke and download the fallback artifacts. Record both file sizes in `docs/artifact-budget.md` | Two files in `app/assets/models/`, sizes recorded | 45 min |

P2 committed before P3 runs is what makes the first ten minutes of the session work. If a
student does them in the wrong order they have nothing to be surprised by.

## The 90 minutes

| Time | What | Why it is here |
|---|---|---|
| **0–10** | **The reveal.** Open the contract from P2 next to the real artifact from P3. Every disagreement is a finding. Where they differ, **the artifact wins and the card is wrong** | This is steps 2 and 4's entire payoff, and it takes ten minutes because the work was done beforehand |
| **10–42** | **Fusion layer** (step 3), from the Asset B skeleton, with the `integration` agent. Coordinate spaces reconciled explicitly. Median not mean. Every degenerate case defined — `NaN` reaching a caller is not a defined result | The only part that genuinely needs the room |
| **42–57** | **Point it at your own room** (step 3b): write `check_fusion_live.py` with `integration`, run it on a webcam, and name a real failure out loud | The first time the thing they built looks at something the dataset never saw. It is also the only source of a real *Known failure modes* section |
| **57–72** | **Fusion tests**, with `qa` and the `offline-suite` skill. Including the signature test: *does this function actually use its depth argument?* | A fusion that ignores depth and returns a constant passes a surprising number of naive tests |
| **72–88** | **Export parity.** Same fixtures through the artifact and the PyTorch reference. **Per-class delta, not the aggregate.** Depth is an ordering check, not a value check | "It exported" vs "it still works" |
| **88–90** | Wrap. Assign the follow-ups below | |

**Step 3b is in the session on purpose, and it cost fifteen minutes taken from tests and
parity.** It could have been homework — it was, in the first draft of this file — and
moving it in is a deliberate trade. The argument for the room: it is the only block a
student will *want* to run, it is where a webcam permission dialog or a missing
`opencv-python-headless` will bite, and the failure they name out loud is the raw material
for round 3's model-card work. The argument against, which is real: it proves nothing, and
the fifteen minutes came out of the two blocks that do.

Cut lines, in order, if you are running behind: the depth half of parity first (state the
ordering result out loud and leave the test as follow-up), then the contract-assertion
tests, then **step 3b's round 3** — keep the run, move the model-card writing to F5.
**Never cut the fusion block** — it is the reason the session is synchronous.

## Post-session homework (~1h 30m)

| # | Task | From | Hand in | Est. |
|---|---|---|---|---|
| **F1** | Finish the suite: assert the artifact contract (label order matches `docs/taxonomy.md`; no identifier anywhere implies metres), then verify the offline claim — `mv runs runs.hidden && uv run pytest` | Step 5 | `pytest` green with `runs/` hidden | 30 min |
| **F2** | Write `docs/execution-target-comparison.md` from the template — XNNPACK, NNAPI, CoreML/ANE, GPU delegate, plus the cloud rows as contrast. State a default backend per platform and the device floor it implies | Step 7 | The file, with a recommendation and a device floor | 30 min |
| **F3** | **Amend** `docs/decisions/0003-on-device-inference-target.md` with your measured numbers — parity tolerance, per-class quantization delta, both artifact sizes, default backend per platform. Write the *Revisit when* clause knowing Lesson 05 measures on-device latency and memory | Step 8 | The amendment | 20 min |
| **F4** | Reconcile `docs/credit-budget.md` (Lesson 04 spend is **0**), then `ruff check` / `mypy src` / `pytest` green, and commit | Step 9 | A commit with no `*.pt`, `*.tflite`, `*.pte`, `data/`, or `.env` | 10 min |
| **F5** | Finish the **Known failure modes** section of `docs/model-card-v1.md` from the frames you ran in the session — class, symptom, and the frame it was seen on, classified DATA / TAXONOMY / MODEL / EXPORT. Optionally run the provided `watch_fusion_live.py` on more of your room first | Step 3b round 3 | The section, and a saved annotated frame | 20 min |

F5 is cheap because the looking already happened in the room. It is the only source of a
real *Known failure modes* section — the part of a model card that saves the most time
later, and the part nobody writes, because it is the one part that cannot be generated
from a metrics table.

F1 and F4 are not optional. F1 is the only thing that proves the suite runs in CI; F4 is
where the artifact budget gets its first real numbers. A cohort that skips them arrives at
Lesson 05 with an app-sized surprise.

## Course-level changes this depends on

### 1. One YOLO model, not two — **decided 2026-08-25**

This project trains and exports exactly one detection model: **V1, the fine-tuned baseline**
(`runs/detect/runs/v1-baseline/weights/best.pt`). There is no V2.

Removed: the second export run and its calibration pass, the V1-vs-V2 **Comparison**
section in the model card (now a one-line note), and the per-model split of the parity
report. Doing the export once teaches the same thing as doing it twice.

Affects the README at steps 2, 4, and 6, and the model card template.

### 2. Step 8 becomes an amendment, not a new ADR

The README asks students to close the Lesson 01 open decision by writing an ADR for the
inference target. **That ADR already exists in the scaffold**:
`docs/decisions/0003-on-device-inference-target.md`, dated 2026-08-12, superseding ADR 0001
outright, with `CLAUDE.md` already written against it.

Asking a student to decide what the repository has already decided rewards writing a
plausible rationale for a handed-down conclusion — precisely what the `/adr` command warns
against. Amending it with numbers they measured keeps the valuable half and drops the
theatre. This is F3.

### 3. The depth input square is a course fact, not a student decision

Running step 2 for the first time surfaced a contradiction the scaffold had been carrying:
`depth.py`'s preprocessing (aspect-preserved, non-square, short edge 518) and
`docs/architecture.md` §2 (one square shared with detection) were two different input
contracts for one artifact — and **neither was implementable**, because Depth Anything V2
Small is a ViT-S/14 and `640 / 14 = 45.71`.

Resolved **2026-08-25** by adding a fourth coordinate space, `DEPTH_INPUT` = 518×518
letterboxed. The rejected alternative was unifying both models on 672.

**Deliberately not left as an ADR for students to write.** A ninety-minute session cannot
absorb a coordinate-space discovery, and a student who hits the shape mismatch live loses
the block that matters most. It is stated as given in:

- `lessons/03-model-development/resources/prompts/05-depth-inference.md` — the raw raster
  must stay reachable, because Lesson 04 compares it
- `lessons/03-model-development/resources/templates/model-card.md` — both squares named in
  the **Input tensor** row, plus a new **Output raster space** row
- `lessons/04-backend-engineering/README.md` steps 2 and 3
- `lessons/04-backend-engineering/resources/prompts/01-artifact-contract.md` — a *Given*
  block with the arithmetic and the rejected alternative
- `.../02-fusion-layer.md` — four spaces, not three
- `.../03-export-pipeline.md` — the `.pte` is compiled for a fixed 518², and does not
  resize inside the graph
- `.../05-export-parity.md` — feed both sides the same letterboxed square, compare the raw
  raster

What students still do themselves is everything the contract *cannot* hand them: dtype,
tensor layout, output ordering, and the quantization decision. Those are read off the
export, which is the actual lesson.

**Left open on purpose:** `depth.py`'s constants now describe the reference's recipe rather
than the artifact's. Reconciling that module is step 4 work and is called out in the export
prompt.

### 4. Step 1 and step 7 leave the session entirely

Both are reading and writing with nothing to run. They become P1 and F2.

## What this does not fix

The lesson's **Open items** are unchanged, and the first one now sits inside a student's
homework rather than inside a supervised session — which raises the stakes on Asset A:

- ⚠️ The export commands remain unverified against this project's models on a clean
  machine. **Verify both on macOS and Linux, and publish the fallback artifacts, before a
  cohort.** Without the fallback, the 90-minute shape does not survive contact.
- ⚠️ The export toolchain is still not in `pyproject.toml`.
- ⚠️ The int8 calibration set is still unspecified. The val split is the obvious default
  and the one that makes the parity number optimistic. P2 now forces the decision before
  the export runs, which is an improvement — but the README should say which way to lean.

## Open questions for the next pass

- ~~Does dropping model V2 weaken Lesson 03's evaluation story?~~ **Answered
  2026-09-09:** the course went single-dataset, and Lesson 03's H2 comparison was deleted
  rather than kept as a step nobody could run. Lesson 03 no longer sets up a comparison, so
  there is nothing here left dangling. What the deletion cost is recorded in
  `lessons/03-model-development/RETROSPECTIVE.md` §11.
- Should F3 be graded? An amendment with fabricated numbers is worse than no amendment,
  and it is the one item where that failure is invisible from the outside.
- Pre-session homework of 1h 45m is more than the session itself. Check that against the
  other five lessons before committing to it as the course's shape.
