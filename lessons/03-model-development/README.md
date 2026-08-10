# Lesson 03 — Model Development

> Notion Week 3. Estimated time: 4–5 hours, most of it waiting for training runs.
> Start the first one early.

## Session goal

Turn two dataset versions into two trained models and one defensible comparison.

The engineering content is **where computation happens and who decides**. Lesson 02
connected the harness to a live platform; this session connects it to a live platform
that charges by the minute. Training is the first operation in this course that can
consume your entire remaining budget in a single call, and the agent proposing it will
do so with complete confidence.

So this lesson runs local-first. You fine-tune YOLO11 on your machine for free,
iterate as much as you like, and spend credits exactly twice: never, if you use the free
platform path, and once — deliberately, behind a permission prompt you wrote yourself in
Lesson 02 — on a hosted run whose purpose is comparison rather than production.

By the end you have model V1, model V2, an honest account of whether V2 is actually
better, and a depth channel that says what it means.

## Prerequisites

- [ ] Lesson 02 complete: `data/v1/` exported and passing `verify_export.py`
- [ ] Dataset version 2 exists in Roboflow with the same class list
- [ ] `docs/credit-budget.md` reconciled, with **at least 3 credits remaining**
- [ ] `.claude/settings.json` has `ask` on `mcp__roboflow__trainings_create`
- [ ] `uv sync --extra ml --extra depth` runs cleanly
- [ ] A GPU is *helpful* but not required — `yolo11n` on 1,500 images trains on a
      modern laptop CPU in roughly an hour, and on Apple Silicon MPS considerably faster

Check the budget before you start:

```bash
grep -A2 'Remaining' docs/credit-budget.md
```

> **If you have fewer than 3 credits left, do not start step 8.** Steps 1–7 and 9–11 cost
> nothing and produce every deliverable that matters. The hosted run is the one piece of
> this lesson that is optional by design, and the lesson says so at the point of spending.

## Deliverables

- [ ] `.claude/agents/ml-engineer.md` and `evaluation.md` in use
- [ ] `docs/decisions/` — an ADR for the detection architecture (YOLO11, and why not RF-DETR)
- [ ] A local MLflow tracking server with at least two runs
- [ ] `scripts/train.py` — parameterized by dataset version, logging to MLflow
- [ ] **Model V1** fine-tuned on dataset v1, with per-class metrics on the v1 test split
- [ ] **Model V2** fine-tuned from V1 on dataset v2
- [ ] An evaluation report comparing them, with the measurement conditions stated
- [ ] `src/smart_scene_analyzer/depth.py` — Depth Anything V2 inference, units stated
- [ ] `docs/model-card-v1.md` and `docs/model-card-v2.md`
- [ ] The ledger updated and reconciled

Verify with [`resources/checklists/deliverables.md`](resources/checklists/deliverables.md).

---

## Step-by-step

### 1. Meet the two new roles

**Do:** Read both definitions. They shipped with the Lesson 01 scaffold and have been
unused until now.

```bash
$EDITOR .claude/agents/ml-engineer.md .claude/agents/evaluation.md
```

Compare their `tools` lines:

```yaml
# ml-engineer
tools: Read, Grep, Glob, Write, Edit, Bash, Skill, mcp__roboflow__*

# evaluation
tools: Read, Grep, Glob, Write, Bash, Skill
```

**The Evaluation Agent has no `Edit`.** It can write reports; it cannot modify training
code. That is the whole design.

An agent that both trains the model and reports whether the model is good has an
incentive problem, and it does not need to be malicious to act on it — asked to "improve
the results", the shortest path is to adjust the threshold, or evaluate on the train
split, or quietly drop the class that was dragging the average down. None of those are
lies. All of them produce a better number and a worse model.

Splitting the roles removes the shortcut. The Evaluation Agent cannot change what it
measures, so its only way to produce a better number is for the number to be better.

> This generalizes past this project. When you give an agent a goal and the tools to
> reach it, check whether any of those tools reach the goal *without* doing the work.
> That is where harness design earns its keep.

**Expected result:** you can state why `evaluation` lacks `Edit` without rereading this.

---

### 2. Choose the architecture — and override the skill

**Do:** Ask the ML Engineer what Roboflow recommends, and notice that it disagrees with
this course.

```
Read roboflow:training-and-evaluation. What architecture does it recommend for a
non-COCO indoor object detection dataset of ~1,500 images, and what does its decision
tree say at step 14? Give me the exact model_id values. Do not start any training.
```

**Expected result:** the agent reports the decision tree's recommendation — **RF-DETR
NAS** (`rfdetr-nas-parent`), falling back to `rfdetr-medium`. Not YOLO11.

That is a real conflict and it is worth understanding rather than papering over. The
skill is not out of date and it is not wrong. It optimizes for accuracy on Roboflow's
platform, where NAS genuinely does produce the best model.

**This course chooses YOLO11 anyway**, for reasons the skill has no way to know:

| Reason | Detail |
|---|---|
| **Local training** | YOLO11 trains with `ultralytics`, on your machine, for zero credits. RF-DETR training in this ecosystem is a hosted operation |
| **Weight access** | You need a `.pt` file to load into FastAPI in Lesson 04. On the free Public plan **weight downloads are a Core-plan feature** — a hosted-trained model is reachable only through the hosted API |
| **Budget** | NAS costs 2 credits/hour, runs longer than a single fine-tune, and one upstream example produced **76 child models from 289 images**. It would consume this entire course several times over |
| **Plan** | NAS requires Core or Growth. On the free plan `trainings_create` rejects it with `nas_not_available_for_plan` |

**Do:** Record the decision.

```
/adr detection architecture: YOLO11 over RF-DETR
```

The ADR should say what the skill recommends, why the project departs from it, and what
the departure costs — likely a few points of mAP. A decision recorded only as "we use
YOLO11" is not a decision; it is a fact with its reasoning deleted.

> **This is the lesson, not a detour.** Vendor knowledge encodes vendor defaults, which
> are correct on average and wrong for specific projects. Your `CLAUDE.md` is where the
> specifics live. When the two conflict, the constraint layer wins — and an agent that
> silently followed the skill here would have spent your entire budget being right in
> general.

---

### 3. Stand up MLflow

**Do:** Start a local tracking server. This costs nothing and runs entirely on your
machine.

```bash
uv run mlflow server --host 127.0.0.1 --port 5000 --backend-store-uri sqlite:///mlflow.db
```

In another shell:

```bash
export MLFLOW_TRACKING_URI=http://127.0.0.1:5000
```

Add it to `.env` as well. Then confirm:

```bash
uv run python -c "import mlflow, os; mlflow.set_tracking_uri(os.environ['MLFLOW_TRACKING_URI']); print(mlflow.search_experiments())"
```

**Expected result:** the command prints a list (the Default experiment) without erroring,
and `http://127.0.0.1:5000` loads in a browser.

**Do:** Confirm `mlflow.db` and `mlruns/` are gitignored. Tracking data is not source.

> Lesson 01 left MLflow hosting as an ⚠️ OPEN decision. Local SQLite is the answer for a
> course-scale project: zero cost, zero setup, and every run reproducible on one machine.
> Record it — `/adr mlflow hosting: local sqlite` — and note the consequence, which is
> that runs are not shared across machines. Lesson 05 revisits this when CI needs to see
> them.

---

### 4. Train model V1 locally

**Do:** Use [`resources/prompts/01-local-training.md`](resources/prompts/01-local-training.md)
to have the ML Engineer write `scripts/train.py`.

The script must take the dataset version as an argument, not hardcode it, and must log
to MLflow: the dataset version number, the base checkpoint, every hyperparameter, and
the resulting metrics. A run you cannot reproduce from its MLflow record did not happen.

Then train:

```bash
uv run python scripts/train.py --data data/v1/data.yaml --model yolo11n.pt --epochs 50 --name v1-baseline
```

**Expected result:** a completed run visible in the MLflow UI, with `mAP@50`,
`mAP@50-95`, precision, and recall logged, and weights saved under `runs/`.

**Credits: zero.** Iterate freely — this is the phase where free compute matters most.
If the run looks wrong at epoch 5, kill it and fix it. That instinct is exactly what a
metered environment suppresses, which is why the expensive path comes later and only
once.

**Sizing guidance**, so you do not spend the session waiting:

| Situation | Suggestion |
|---|---|
| CPU only | `yolo11n`, 25–50 epochs, batch 8. Expect ~1 hour on 1,500 images |
| Apple Silicon | `yolo11n` or `yolo11s`, `device=mps`, 50 epochs |
| NVIDIA GPU | `yolo11s`, 100 epochs, batch 16 |

Start smaller than you think you need. A finished 25-epoch run tells you more than a
75-epoch run you abandoned.

---

### 5. Evaluate, and diagnose

**Do:** Hand off to the Evaluation Agent with
[`resources/prompts/02-error-analysis.md`](resources/prompts/02-error-analysis.md).

It computes per-class precision, recall, mAP@50 and mAP@50-95 on the **v1 test split**,
builds a confusion matrix, and reads it through the decision tree in
`roboflow:training-and-evaluation` → `improvement-playbook.md`.

**Expected result:** a per-class table, a confusion matrix, the top confusion pairs named
in prose, and a diagnosis that ties each weak class back to the data.

> **Roboflow's own evaluation UI — Production Metrics Explorer, the confusion matrix
> viewer, Model Improvement Recommendations — is a paid-plan feature.** On the free
> Public plan you compute these locally, which `ultralytics` does natively. No loss for
> this course; worth knowing before you go looking for a tab that is not there.

**Now go back to your dataset card.** Every weak class has two candidate explanations,
and they call for opposite responses:

| Symptom | Data explanation | Model explanation |
|---|---|---|
| One class near zero recall | Too few instances — check the card | Underfitting; train longer |
| Two classes confused symmetrically | The taxonomy merged things it should not have, or split things it should not have | Insufficient capacity |
| High precision, low recall everywhere | Confidence threshold too high | Genuine underfitting |
| Good train metrics, poor test | — | Overfitting; more augmentation |

**Most "model problems" in this project are dataset problems**, and the dataset card is
what lets you tell in seconds instead of an afternoon. If it records "only 47 instances
of `lamp`, mostly ceiling-mounted", then `lamp` at 0.11 recall is not a training failure.
It is a data collection finding, and no amount of retraining fixes it.

This is also where the audit table from Lesson 02 earns its credit: if a class scored
badly for the auto-labeler *and* trains badly now, the class itself is hard — not your
pipeline.

---

### 6. Train model V2, and compare honestly

**Do:** Export dataset version 2, then fine-tune **from model V1's weights** rather than
from COCO. Use [`resources/prompts/03-domain-adaptation.md`](resources/prompts/03-domain-adaptation.md).

```bash
uv run python scripts/train.py \
  --data data/v2/data.yaml \
  --model runs/v1-baseline/weights/best.pt \
  --epochs 50 --name v2-adapted
```

This is the course's central experiment. V2 stands in for newly acquired production
data; the question is whether adapting to it helps.

**Do:** Have the Evaluation Agent produce the comparison — and hold it to the standard in
its own definition: two runs are comparable only if measured on the same split of the
same dataset version at the same threshold.

That constraint bites here, and the bite is the lesson. There are three defensible
comparisons and they answer different questions:

| Compare | On | Answers |
|---|---|---|
| V1 vs V2 | **v1 test** | Did adapting to the new domain break the old one? (catastrophic forgetting) |
| V1 vs V2 | **v2 test** | Did adaptation work? |
| V1 vs V2 | both, reported side by side | The actual trade-off |

**Report all three.** A single number here is almost always the flattering one. If V2
gains 8 points on v2 test and loses 12 on v1 test, "V2 is better" is false, and it is the
kind of false that ships.

**Expected result:** a comparison table with the measurement conditions stated once
above it, covering both test splits, and a plain-language verdict — including "no
significant difference" if that is what happened.

> **These metrics mean something because Lesson 02 kept human labels.** Had the test
> split been auto-labeled, every number in this step would measure agreement with
> Grounding DINO rather than accuracy, and this comparison would be unreadable. That
> decision, made three weeks ago to save credits, is what makes this step valid.

---

### 7. The free platform path — Roboflow Instant

**Do:** Train a model on Roboflow without spending anything.

**Roboflow Instant is free.** It is few-shot, object-detection only, uses images as-is
with no preprocessing or augmentation, and trains in minutes. It is not competitive with
your fine-tune and it is not supposed to be.

Trigger it at **Project → Models → Train Model → Roboflow Instant Model**, or ask:

```
Start a Roboflow Instant training run on dataset version 1. Confirm first that Instant
is free and that this will not consume credits, citing roboflow:training-and-evaluation.
```

**Expected result:** an Instant model appears on the Models page, and your credit balance
is unchanged. Verify the second part on the usage page — checking that a "free" operation
was free is a habit worth forming.

**Do:** Compare its metrics against your local V1 and write one paragraph on what the
platform path costs and buys: minutes instead of an hour, no configuration, no
preprocessing control, no local weights, and a model you cannot inspect.

---

### 8. ⚠️ One hosted training run — 2 credits

**This is the only deliberately expensive step in the course, and it is optional.**

**Do not run it if you have fewer than 3 credits left.** Skip to step 9; you lose one
comparison row and no deliverable.

**Do:** Use [`resources/prompts/04-hosted-training.md`](resources/prompts/04-hosted-training.md).
The agent must state, before calling anything:

1. The `model_id` — `yolov11s`, matching your local architecture so the comparison is meaningful
2. The epoch count, capped so wall time stays **under one hour**
3. The arithmetic: 1 credit per 30 minutes → **≤ 2 credits**
4. Your remaining balance from `docs/credit-budget.md`

Then it calls `trainings_create` — and your Lesson 02 permission rule fires.

**Stop and read the prompt when it appears.** This is the moment the whole harness was
built for. You are being asked to approve a specific, irreversible, billed operation, with
the cost in front of you. Approving it should feel different from approving a file edit,
and the fact that it does is the design working.

**Do:** Record the estimate in the ledger *before* approving. Then approve, and record
the actual afterwards.

**Expected result:** a hosted model with metrics, and a ledger entry with both numbers.

#### What this run cannot give you

> **On the free Public plan you cannot download the weights.** `plans-and-pricing` lists
> weight downloads as a Core-plan differentiator. The hosted model exists, has metrics,
> and is servable through Roboflow's API — but the `.pt` file is not yours.

That is not a footnote; it decides Lesson 04's architecture. Your FastAPI service loads
**local** weights, because those are the only weights you have. The hosted model becomes
the thing you compare against over HTTP in Lesson 04 step 7, and the comparison is real
precisely because you cannot collapse it into "just use the local file".

**Do:** Note this in your ADR. A student six months from now on a Core plan should be able
to see that this constraint was known and priced, not overlooked.

<details>
<summary><b>Training controls worth knowing before you approve</b></summary>

| Control | Effect | Billing |
|---|---|---|
| **Cancel Training** | Stops the job, no weights saved | Refund if cancelled early |
| **Early Stopping** | Stops the job, **saves weights** | **Charges for credits used** |

If the curves converge at epoch 30 of 100, Early Stopping saves you the remaining credits
and keeps the model. Cancelling discards it. Know which button you want *before* you are
watching a run you regret.
</details>

---

### 9. Depth Anything V2 — inference only

**Do:** Use [`resources/prompts/05-depth-inference.md`](resources/prompts/05-depth-inference.md)
to have the ML Engineer write `src/smart_scene_analyzer/depth.py`.

Runs locally through `transformers`. **Zero credits, and no training** — this is a
pretrained model you run, not one you fine-tune.

**The deliverable here is the units, not the code.** Lesson 02 recorded the decision:
depth is inference-only, there is no ground truth, and there will be no depth error
metric. That has a specific consequence which every signature in this module must carry:

> Depth Anything V2 outputs **relative inverse depth**. Larger values are nearer. The
> scale is arbitrary and it is **not metres**. With no ground truth there is nothing to
> calibrate against, so the relative units travel all the way to the API response.

A function called `estimate_depth` returning an array called `depth` is ambiguous and
therefore wrong. `estimate_relative_inverse_depth`, returning an array documented as
"larger = nearer, arbitrary scale, not metres", is right. `CLAUDE.md` has demanded this
since Lesson 01 — "Ambiguity about whether a depth value is metres or normalized
disparity is a real source of bugs in this project" — and this is where the demand
becomes concrete.

**Do:** Validate what you actually can:

```bash
uv run python scripts/check_depth_ordering.py <image> --boxes <detections.json>
```

Since absolute error is unavailable, check **relative ordering**, which is falsifiable:
on a scene where a chair sits in front of a wall, the chair's region must read as nearer.
[`resources/scripts/check_depth_ordering.py`](resources/scripts/check_depth_ordering.py)
does this and fails loudly if the sign convention is inverted — the single most likely
bug in this module, and one that produces perfectly plausible numbers.

**Expected result:** a depth module whose signatures state units, and an ordering check
that passes on at least five real scenes.

> **Say what you cannot do, in the model card.** "Depth is relative; no absolute error is
> reported because no ground truth exists" is a complete, honest statement. Silence on
> the subject invites a downstream reader to assume metres, and the first person to
> divide by that number will be building on sand.

---

### 10. Write the model cards

**Do:**

```bash
cp <path-to-course-repo>/lessons/03-model-development/resources/templates/model-card.md docs/model-card-v1.md
```

Fill in for V1, repeat for V2. The Documentation Agent can draft from MLflow run data;
**you** write the known-failure-modes section.

Each card records: architecture and size, base checkpoint, dataset version *by number*,
hyperparameters, per-class metrics with the split and threshold they were measured at,
the comparison against the other version, and what the model is not for.

**Expected result:** two model cards where every metric names its split, its dataset
version, and its confidence threshold.

---

### 11. Reconcile and commit

**Do:**

1. Open `app.roboflow.com/<workspace>/settings/usage`
2. Compare against `docs/credit-budget.md`
3. Update **Remaining** and **Last reconciled**

**Expected result:** spend for this lesson is **0 credits** (if you skipped step 8) or
**about 2** (if you did not). Running total across Lessons 02–03 should be at or under 6,
leaving 14 or more for Lessons 04–05.

```bash
git add -A
git status          # confirm: no runs/, no *.pt, no mlflow.db, no data/
git commit -m "Lesson 03: YOLO11 V1 and V2, evaluation, depth inference"
git push
```

> **Do not commit weights.** `runs/`, `*.pt`, `mlflow.db`, and `mlruns/` all stay out.
> Weights live in MLflow, datasets in Roboflow. If `git status` shows a `.pt` file, fix
> `.gitignore` before committing.

---

## Verification

Work through
[`resources/checklists/deliverables.md`](resources/checklists/deliverables.md).

```bash
# Two runs exist and are reproducible from their records
uv run python -c "
import mlflow, os
mlflow.set_tracking_uri(os.environ['MLFLOW_TRACKING_URI'])
df = mlflow.search_runs()
print(df[['tags.mlflow.runName', 'params.dataset_version', 'metrics.map50']])
"

# Depth sign convention is right
uv run python scripts/check_depth_ordering.py data/v1/test/images/<sample>.jpg

# Nothing large or secret staged
git status --porcelain | grep -E '\.pt$|^\?\? runs/|mlflow\.db|\.env$' && echo "LEAK" || echo "clean"
```

Then confirm by reading:

- Every metric in both model cards names its **split, dataset version, and threshold**
- The V1-vs-V2 comparison reports **both** test splits, not the flattering one
- `depth.py` signatures say "relative inverse depth", and no identifier contains `meter`
- The architecture ADR states what Roboflow's skill recommends and why you departed
- The ledger reconciles, and the hosted run (if any) has an estimate *and* an actual

The qualitative check: **run inference on ten test images and look at the boxes.** A
model at mAP@50 = 0.55 can be uniformly slightly loose, or excellent on four classes and
blind on two. Those need different responses, and the metric does not distinguish them.

---

## Open items

- ⚠️ **MLflow hosting beyond one machine** (step 3) — local SQLite is decided for now,
  but Lesson 05's CI needs to read runs it did not create. Revisit there.
- ⚠️ **Weight downloads require the Core plan** (step 8) — sourced from
  `roboflow:plans-and-pricing`, not confirmed on the platform. If it turns out free-tier
  weight download is possible, Lesson 04's comparison becomes optional rather than
  structural.
- ⚠️ **Whether `yolo11n` is sufficient for the taxonomy** — depends on the final class
  list and instance counts, which Lesson 02 left open. If small classes underperform,
  the first lever is data, not model size.
- ⚠️ **Free-plan credit allowance unconfirmed** — carried from Lesson 02.

All tracked in the course [`TODO.md`](../../TODO.md).

---

## Further reading

Local skill sources, in `computer-vision-skills/skills/`:

- `training-and-evaluation/SKILL.md` — architectures, **exact `model_id` values**,
  checkpoint strategy, training controls, post-training metrics
- `training-and-evaluation/improvement-playbook.md` — the confusion-matrix diagnostic
  decision tree behind step 5
- `custom-weights-upload/SKILL.md` — uploading locally trained weights back to Roboflow.
  Note `models_upload_custom_weights` is a **guide, not an uploader** — the MCP server
  cannot read local files, so the actual upload goes through the Python SDK
- `plans-and-pricing/SKILL.md` — training credit rates, and the Core-plan feature list

External:

- [Ultralytics YOLO11](https://docs.ultralytics.com/models/yolo11/)
- [Depth Anything V2](https://depth-anything-v2.github.io/)
- [MLflow tracking](https://mlflow.org/docs/latest/tracking.html)

**Previous:** [Lesson 02](../02-dataset-engineering/) ·
**Next:** [Lesson 04 — Backend Engineering & Production APIs](../04-backend-engineering/)
