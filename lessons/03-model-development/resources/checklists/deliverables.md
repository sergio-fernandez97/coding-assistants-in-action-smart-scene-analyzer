# Lesson 03 — Deliverables checklist

Split the way the lesson is: **Part 1 is the 90-minute session**, Part 2 is homework.
If you are checking this during class, only Part 1 applies.

## Before you start

- [ ] `docs/credit-budget.md` reconciled at the end of Lesson 02
- [ ] At least 3 credits remaining (or you have decided to skip the hosted run in H6)
- [ ] A dataset version exported and passing `verify_export.py`
- [ ] `uv sync --extra ml --extra depth` runs cleanly
- [ ] A webcam, or a photo you can use instead, for steps 6 and 7

---

# Part 1 — Session

## Roles (step 1)

- [ ] `.claude/agents/ml-engineer.md` and `evaluation.md` both read
- [ ] You can state why `evaluation` has no `Edit` tool
- [ ] Training was done by `ml-engineer`, evaluation by `evaluation` — not one agent doing both
- [ ] The Evaluation Agent never proposed a change to training code

## Architecture decision (step 2)

- [ ] You asked what `roboflow:training-and-evaluation` recommends, and got RF-DETR NAS
- [ ] ADR recorded: `/adr detection architecture: YOLO11 over RF-DETR`
- [ ] The ADR states what the skill recommends, why the project departs, **and what the
      departure costs**
- [ ] No RF-DETR NAS run was started, proposed, or accidentally approved

## MLflow, and training started (step 3)

- [ ] Tracking server running, `MLFLOW_TRACKING_URI` exported and in `.env`
- [ ] `mlflow.db` and `mlruns/` are gitignored
- [ ] ADR recorded for MLflow hosting
- [ ] `scripts/train.py` takes the dataset path as an argument; nothing hardcoded
- [ ] `scripts/train.py` fails loudly if `MLFLOW_TRACKING_URI` is unset
- [ ] A V1 run is **started** and logging — you will read it in H1, not now

## Depth module (step 4)

- [ ] `src/smart_scene_analyzer/depth.py` exists
- [ ] Functions named `estimate_relative_inverse_depth` and `region_relative_depth`
- [ ] Docstrings state: larger = nearer, arbitrary scale, not a distance in any unit, no
      scale to calibrate against
- [ ] **No public identifier contains** `meter`, `metre`, `mm`, `cm`, or `distance`
- [ ] Region reduction uses the **median**, with the reason in the docstring
- [ ] All degenerate box cases have defined, documented results — and return `None`, never `NaN`
- [ ] The model is cached, not loaded per call
- [ ] The module makes no network, filesystem, or Roboflow calls

> **`units_guard.py` blocked a write and you satisfied it.**
>
> - [ ] The hook fired at least once
> - [ ] You did **not** edit, weaken, or bypass it
> - [ ] You can say why it greps the whole file rather than only identifiers

## Sign convention (step 5)

- [ ] `check_depth_ordering.py` passes on real scenes, nearest declared first
- [ ] You used `--box` (repeatable) or `--cases` — there is no `--boxes` flag
- [ ] **You rendered a depth map and looked at it** — nearer surfaces brighter
- [ ] You can say what a `none` row in the output means

## Live capture (step 6)

- [ ] `check_live_capture.py` run against your camera, or a photo
- [ ] **You opened both PNGs** — the annotated frame and the depth render
- [ ] You can name a taxonomy class COCO weights cannot possibly find, and why
- [ ] The near-to-far ordering was checked against your own eyes
- [ ] `docs/live-validation.md` written, stating its conditions
- [ ] The write-up reports **no accuracy figure** — one frame is not a rate

## Reference Depth Calibration (step 7)

- [ ] Two scenes, three or more objects each, positions measured
- [ ] **The camera actually moved between them** — different range and angle
- [ ] Ordering accuracy and rank correlation reported per scene
- [ ] `--transfer` run, and the error on the un-fitted scene is clearly worse
- [ ] You can state what that proves, in one sentence, without the word "metres"
- [ ] **No unit appears anywhere** — not in the JSON, the output, or the write-up
- [ ] Nobody proposed publishing the fitted conversion "with caveats"

## Session hygiene (step 8)

- [ ] Session spend is **0 credits**
- [ ] `git status` shows no `.pt`, no `runs/`, no `mlflow.db`, no `mlruns/`, no `data/`
- [ ] `git status --porcelain | grep -E '\.pt$|mlflow\.db|\.env$'` returns nothing

---

# Part 2 — Homework

## H1 — V1 finished, evaluated, diagnosed

- [ ] Run visible in MLflow with **all** parameters populated
- [ ] Dataset version number logged as a parameter
- [ ] Class list logged, and it matches `docs/taxonomy.md` in name and order
- [ ] Git commit SHA tagged; dirty tree flagged if applicable
- [ ] Weights exist under `runs/` and are **not** committed
- [ ] Measured on the **test** split, not valid — and the split is stated
- [ ] Measurement conditions stated before any number: model, version, split, image count,
      confidence, IoU
- [ ] Per-class table leads; aggregate follows
- [ ] Classes with fewer than 30 instances flagged as noise
- [ ] Confusion matrix produced, top pairs named in prose
- [ ] Every weak class classified **DATA / TAXONOMY / MODEL**, with evidence
- [ ] Weak classes cross-referenced against the dataset card and the Lesson 02 audit table
- [ ] Exactly one recommended next action, with a prediction attached
- [ ] `docs/evaluation-v1.md` written

> If every weak class came back as MODEL, reject the analysis. That is the answer that
> requires no evidence, and in this project it is almost never the right one.

## H2 — V2 and the honest comparison

- [ ] A second dataset version exported and passing `verify_export.py`
- [ ] Class lists confirmed identical in **name and order** — checked, not assumed
- [ ] V2 fine-tuned **from V1's weights**, not from COCO
- [ ] Lineage traceable in MLflow
- [ ] **All three** comparisons reported: on v1 test, on v2 test, side by side
- [ ] Per-class deltas, not only aggregates
- [ ] Test-split sizes stated so deltas can be judged
- [ ] Verdict addresses **both** the gain and the forgetting
- [ ] Taxonomy ruled out as an explanation for the largest per-class changes

## H3 — Camera check against your own weights

- [ ] `check_live_capture.py` re-run with `--weights runs/.../best.pt`
- [ ] The two annotated frames compared side by side
- [ ] Classes COCO could not find now appear
- [ ] **Any regression on classes COCO could find is recorded**, not skipped

## H4 — The depth test suite

- [ ] `tests/test_depth.py` exists
- [ ] Fixtures generated in code — **no binary fixtures committed**
- [ ] A known-gradient depth map makes the median assertions exact
- [ ] The "does this function actually use its expensive argument" test exists
- [ ] Every degenerate box case covered
- [ ] The units test walks public names **programmatically**, not a hardcoded list
- [ ] Anything needing real weights is marked `integration`
- [ ] **The offline claim was verified by breaking it**, not by reading the code:
      `HF_HOME=$(mktemp -d) HF_HUB_OFFLINE=1 uv run pytest`
- [ ] The default suite genuinely deselects `integration` — check `addopts`, do not assume

## H5 — N5 over the test split

- [ ] You checked **what your source dataset ships on disk** before concluding anything
- [ ] The margin was declared **before** the rate was computed, not tuned to it
- [ ] A sweep across margins is reported, so the rate's sensitivity is visible
- [ ] The reference is used for **ordering only** — no magnitude enters the project
- [ ] Both the pair-weighted and the image-averaged rate are reported if they differ
- [ ] Classes under 30 instances flagged, and not built into a story
- [ ] Any class that fails badly was **opened and looked at** before being blamed

## H6 — Platform paths

- [ ] Instant model trained
- [ ] Credit balance **verified unchanged** on the usage page afterwards
- [ ] One paragraph on what the platform path costs and buys

Hosted run — skip entirely if you had fewer than 3 credits. That is a legitimate outcome.

- [ ] Estimate produced **before** any tool call, with arithmetic shown
- [ ] `model_id` quoted exactly from the skill, not from memory
- [ ] Epochs capped so wall time stays under one hour
- [ ] Estimate written into the ledger **before** approving
- [ ] The permission prompt fired, and you read it before approving
- [ ] Actual cost recorded and reconciled against the estimate
- [ ] The weight-download limitation noted in the ADR
- [ ] You know the difference between Cancel Training and Early Stopping

## H7 — Model cards

- [ ] `docs/model-card-v1.md` and `docs/model-card-v2.md` complete
- [ ] Every metric names its split, dataset version, and confidence threshold
- [ ] Dataset referenced **by version number**, never "the latest"
- [ ] The Depth section carries the step 7 calibration result **and** the H5 rate
- [ ] The Depth section states what a consumer must **not** do with the values
- [ ] **Known failure modes written by you**, not generated
- [ ] The reproduction command is present and actually works
- [ ] No reference points at a file that does not exist — **check every link you write**

## Ledger

- [ ] One row per billed operation
- [ ] Lesson 03 spend is 0 (skipped the hosted run) or about 2
- [ ] Running total across Lessons 02–03 at or under 6
- [ ] Reconciled against `app.roboflow.com/<workspace>/settings/usage`
- [ ] Any estimate-vs-actual gap investigated and noted

---

## The ones that are not mechanical

- [ ] **You ran inference on real images and looked at the boxes.** A model at
      mAP@50 = 0.55 can be uniformly slightly loose, or excellent on four classes and blind
      on two. Those call for opposite responses, and the aggregate cannot tell them apart.

- [ ] **You can explain, without notes, why this project may rank depth and may never
      print it.** You measured that in step 7. If the explanation still sounds like a rule
      somebody handed you, run the transfer test again and watch the number.
