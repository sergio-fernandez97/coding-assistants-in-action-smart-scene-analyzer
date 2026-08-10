# Lesson 03 — Deliverables checklist

## Before you start

- [ ] `docs/credit-budget.md` reconciled at the end of Lesson 02
- [ ] At least 3 credits remaining (or you have decided to skip step 8)
- [ ] `data/v1/` passes `verify_export.py`
- [ ] `uv sync --extra ml --extra depth` runs cleanly

## Roles

- [ ] `.claude/agents/ml-engineer.md` and `evaluation.md` both read
- [ ] You can state why `evaluation` has no `Edit` tool
- [ ] Training was done by `ml-engineer`, evaluation by `evaluation` — not one agent doing both
- [ ] The Evaluation Agent never proposed a change to training code

## Architecture decision

- [ ] You asked what `roboflow:training-and-evaluation` recommends, and got RF-DETR NAS
- [ ] ADR recorded: `/adr detection architecture: YOLO11 over RF-DETR`
- [ ] The ADR states what the skill recommends, why the project departs, **and what the
      departure costs**
- [ ] No RF-DETR NAS run was started, proposed, or accidentally approved

## MLflow

- [ ] Tracking server running, `MLFLOW_TRACKING_URI` exported and in `.env`
- [ ] `mlflow.db` and `mlruns/` are gitignored
- [ ] ADR recorded for MLflow hosting
- [ ] `scripts/train.py` fails loudly if `MLFLOW_TRACKING_URI` is unset

## Model V1 — local

- [ ] `scripts/train.py` takes the dataset path as an argument; nothing hardcoded
- [ ] A 3-epoch smoke test ran before the real run
- [ ] Run visible in MLflow with **all** parameters populated
- [ ] Dataset version number logged as a parameter
- [ ] Class list logged, and it matches `docs/taxonomy.md` in name and order
- [ ] Git commit SHA tagged; dirty tree flagged if applicable
- [ ] Weights exist under `runs/` and are **not** committed

## Evaluation

- [ ] Measured on the **test** split, not valid — and the split is stated
- [ ] Measurement conditions stated before any number: model, version, split, image count, confidence, IoU
- [ ] Per-class table leads; aggregate follows
- [ ] Classes with fewer than 30 instances flagged as noise
- [ ] Confusion matrix produced, top pairs named in prose
- [ ] Every weak class classified **DATA / TAXONOMY / MODEL**, with evidence
- [ ] Weak classes cross-referenced against `docs/dataset-card-v1.md`
- [ ] Weak classes cross-referenced against the Lesson 02 Auto Label audit table
- [ ] Exactly one recommended next action, with a prediction attached
- [ ] `docs/evaluation-v1.md` written

> If every weak class came back as MODEL, reject the analysis. That is the answer that
> requires no evidence, and in this project it is almost never the right one.

## Model V2 — domain adaptation

- [ ] `data/v2/` exported and passing `verify_export.py`
- [ ] Class lists of v1 and v2 confirmed identical in **name and order** — checked, not assumed
- [ ] V2 fine-tuned **from V1's weights**, not from COCO
- [ ] Lineage traceable in MLflow
- [ ] **All three** comparisons reported: on v1 test, on v2 test, side by side
- [ ] Per-class deltas, not only aggregates
- [ ] Test-split sizes stated so deltas can be judged
- [ ] Verdict addresses **both** the gain and the forgetting
- [ ] Taxonomy ruled out as an explanation for the largest per-class changes

## Roboflow Instant — free

- [ ] Instant model trained
- [ ] Credit balance **verified unchanged** on the usage page afterwards
- [ ] One paragraph written on what the platform path costs and buys

## Hosted training — optional, 2 credits

Skip entirely if you had fewer than 3 credits. That is a legitimate outcome.

- [ ] Estimate produced **before** any tool call, with arithmetic shown
- [ ] `model_id` quoted exactly from the skill, not from memory
- [ ] Epochs capped so wall time stays under one hour
- [ ] Estimate written into the ledger **before** approving
- [ ] The permission prompt fired, and you read it before approving
- [ ] Actual cost recorded and reconciled against the estimate
- [ ] The weight-download limitation was discovered by consulting the skill, and noted in the ADR
- [ ] You know the difference between Cancel Training and Early Stopping

## Depth — inference only

- [ ] `src/smart_scene_analyzer/depth.py` exists
- [ ] Functions named `estimate_relative_inverse_depth` and `region_relative_depth`
- [ ] Docstrings state: larger = nearer, arbitrary scale, **not metres**, no ground truth
- [ ] **No public identifier contains** `meter`, `metre`, `mm`, `cm`, or `distance`
- [ ] Region reduction uses the **median**, with the reason in the docstring
- [ ] All four degenerate box cases have defined, documented results
- [ ] The model is cached, not loaded per call
- [ ] `check_depth_ordering.py` passes on at least five real scenes
- [ ] **You rendered a depth map and looked at it** — nearer surfaces brighter
- [ ] The module makes no network, filesystem, or Roboflow calls

## Model cards

- [ ] `docs/model-card-v1.md` and `docs/model-card-v2.md` complete
- [ ] Every metric names its split, dataset version, and confidence threshold
- [ ] Dataset referenced **by version number**, never "the latest"
- [ ] Depth section states that no quantitative evaluation was performed, and why
- [ ] **Known failure modes written by you**, not generated
- [ ] The reproduction command is present and actually works

## Ledger

- [ ] One row per billed operation
- [ ] Lesson 03 spend is 0 (skipped step 8) or about 2
- [ ] Running total across Lessons 02–03 at or under 6
- [ ] Reconciled against `app.roboflow.com/<workspace>/settings/usage`
- [ ] Any estimate-vs-actual gap investigated and noted

## Hygiene

- [ ] `git status` shows no `.pt`, no `runs/`, no `mlflow.db`, no `mlruns/`, no `data/`
- [ ] `git status --porcelain | grep -E '\.pt$|mlflow\.db|\.env$'` returns nothing
- [ ] Scripts and docs committed; weights and datasets not

## The one that isn't mechanical

- [ ] **You ran inference on ten test images and looked at the boxes.**

A model at mAP@50 = 0.55 can be uniformly slightly loose, or excellent on four classes
and blind on two. Those call for opposite responses, and the aggregate metric cannot tell
them apart. Ten minutes here decides whether Lesson 04 is serving something worth serving.
