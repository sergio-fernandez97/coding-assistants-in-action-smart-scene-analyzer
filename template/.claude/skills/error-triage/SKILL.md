---
name: error-triage
description: Use when diagnosing why a detection model performs badly on some classes — after any evaluation run, model comparison, export, or regression. Measures on the test split, then classifies each weak class as DATA, TAXONOMY, MODEL, or EXPORT with stated evidence, and produces one recommended action. Invoke whenever asked why a class has low precision or recall, why the app disagrees with the reference, whether to retrain, or what to do next about model quality.
---

# Error triage: DATA / TAXONOMY / MODEL / EXPORT

The question "why is this class bad?" has exactly three useful answers in this project,
and they call for completely different responses. Getting the category wrong is how a
week disappears into hyperparameter tuning on a class with 47 instances.

Run this with the `evaluation` role. **Not `ml-engineer`** — the agent that trained the
model does not grade it, and `evaluation` has no `Edit` tool precisely so that it cannot
improve the number instead of the model.

**Credits: zero.** Roboflow's evaluation UI is a paid-plan feature; `ultralytics`
computes all of this locally.

## Step 1 — measure, on the test split

Evaluate against **test**, never valid. Validation drove checkpoint selection during
training, so the model has already been selected against it and it is no longer a clean
estimate. Test is untouched.

State the measurement conditions **once, at the top, before any number**: model, weights
path, dataset version, split, image count, confidence threshold, IoU threshold. Every
figure below that heading is meaningless without them.

Then report, in this order:

1. **The per-class table** — instances in the split, precision, recall, mAP@50, mAP@50-95
2. Aggregate mAP@50 and mAP@50-95
3. The confusion matrix, with the top five confusion pairs named in prose

The per-class table leads. A headline mAP quoted before the reader knows which classes it
averages over is a summary of something nobody has seen yet.

**Flag any class with fewer than 30 instances in the split** and say its rates are noise.
A class with 6 instances at "0.00 recall" is not a finding.

## Step 2 — diagnose, through the playbook

Read the confusion matrix through the decision tree in
`roboflow:training-and-evaluation` → `improvement-playbook.md`.

For every class with recall below 0.5 or precision below 0.5, establish:

- What the confusion matrix says it is confused with, if anything
- Whether `docs/dataset-card-v<N>.md` explains it — instance count, capture bias,
  annotation convention
- Whether `docs/taxonomy.md`'s mapping merged things that should have stayed separate,
  or split things that should have merged
- Whether the Lesson 02 Auto Label audit also found this class hard

That last cross-reference is independent evidence and it is cheap to check. A class that
a foundation model also handled badly is probably intrinsically hard — ambiguous extent,
heavy occlusion, low visual distinctiveness. That points at TAXONOMY or DATA, not MODEL.

Then classify each weak class as exactly one of:

| Category | Means | Response |
|---|---|---|
| **DATA** | Too few instances, or biased ones | More training will not fix it. Collect or rebalance |
| **TAXONOMY** | The class boundary is wrong | Retraining the same labels will not fix it. Redefine and re-export |
| **MODEL** | Enough good data, underfitting or capacity-limited | Training might fix it. This is the only category where more epochs is a real answer |
| **EXPORT** | The trained model is fine; the shipped artifact is not | Retraining fixes nothing. Re-export, change quantization, or fix the consumer |

Say what evidence decided it. "chair could be improved with more training" is not a
diagnosis — it names no category and cites nothing.

### EXPORT — check this one first when the symptom came from the app

EXPORT exists because it is the category most easily mistaken for the other three, and
misdiagnosing it is expensive: it sends someone to relabel images that were never wrong.

**Check it first whenever the complaint arrived from the device rather than from an
evaluation run.** The distinguishing question is cheap: *does the PyTorch model, on the
same images, have this problem?* If it does not, no amount of data or training is the
answer, and the other three categories are all wrong by construction.

Within EXPORT, four sub-causes with different fixes:

| Sub-cause | Signature | Distinguishing test |
|---|---|---|
| **Quantization** | One or two classes degraded, the rest fine | Does an fp32 export agree where the int8 one does not? |
| **Preprocessing** | Everything slightly worse; boxes systematically offset or scaled | Does the offset scale with the letterbox padding? |
| **Decoding** | Boxes plausible, classes wrong or shifted | Is it a constant class-index shift? Check label order against its source of truth |
| **Layout** | Output is nonsense rather than degraded | NCHW vs NHWC, or output tensors read in the wrong order |

Quantization is the only one of the four that is a property of the *model*. The other three
are properties of the code around it, which is why "the export broke class X" is a
conclusion to reach after the other three are excluded, not before.

## Step 3 — the report

Write `docs/evaluation-v<N>.md` containing the measurement conditions, the per-class
table, the confusion matrix, the classification per weak class with evidence, and
**exactly one recommended next action** with what you expect it to change.

One action. If more than one thing is worth doing, say which is first and why. A list of
seven recommendations is a way of not deciding.

## What good output looks like

- Measurement conditions stated before any number
- Per-class table leads; aggregate follows
- Low-instance classes flagged as noise rather than quoted as results
- Each weak class traced to the specific dataset-card or taxonomy line that explains it
- Each weak class classified DATA / TAXONOMY / MODEL / EXPORT with stated evidence
- If the symptom came from the device, EXPORT was excluded **first**, against the PyTorch
  reference, before any data or training explanation was considered
- One recommendation, with a prediction attached

## Reject and re-run if

- The evaluation ran on **valid**, or the split is not stated
- A headline mAP appears before the per-class breakdown
- A class with 6 instances is reported as a finding
- The diagnosis is generic rather than tied to a specific dataset-card line
- The agent proposes editing training code — it has no `Edit` tool, and asking for one
  means the role boundary is working
- **Every weak class is classified MODEL.** That is the answer that requires no evidence,
  and it is almost never right in this project
- **A device-reported symptom was diagnosed as DATA or MODEL without first checking the
  PyTorch reference.** That check is one command and it excludes an entire category; 
  skipping it is how a team ends up relabelling images to fix an array ordering
