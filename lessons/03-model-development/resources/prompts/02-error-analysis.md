# Prompt — evaluation and error analysis

**When:** Lesson 03, **H1**. Homework — it runs after training finishes.

**Which agent:** `evaluation`. **Not** `ml-engineer` — the agent that trained the model
does not get to grade it.

**Which skill:** `error-triage`. It carries the DATA / TAXONOMY / MODEL classification and
its acceptance criteria. You run this once per model and once per version — twice in this
lesson alone, and again in Lesson 06 every time a retrain lands — which is precisely why
the method lives in a skill and only the model-specific details live here.

**Credits: zero.** Roboflow's evaluation UI is a paid-plan feature; `ultralytics`
computes all of this locally.

---

## Round 1 — measure

```
Use the evaluation agent.

Evaluate the model at runs/v1-baseline/weights/best.pt against the v1 TEST split
(data/v1/data.yaml). Not valid — test.

Report:
  - Per class: instances in the split, precision, recall, mAP@50, mAP@50-95
  - Aggregate mAP@50 and mAP@50-95
  - The confidence threshold and IoU threshold you used
  - The confusion matrix, with the top five confusion pairs named in prose

State the measurement conditions once at the top: model, weights path, dataset version,
split, image count, confidence threshold, IoU threshold. Every number below that heading
is meaningless without them.

Lead with the per-class table. I do not want a headline mAP quoted before I have seen
which classes it is averaging over.

Flag any class with fewer than 30 instances in the split — its rates are noise and I do
not want them presented as findings.
```

**Why test and not valid.** Validation drove checkpoint selection during training, so the
model has been selected against it. It is no longer a clean estimate. Test is untouched,
and it is the split the Lesson 02 taxonomy work was protecting.

---

## Round 2 — diagnose

```
Now read the confusion matrix through the decision tree in
roboflow:training-and-evaluation -> improvement-playbook.md.

For every class with recall below 0.5 or precision below 0.5, tell me:
  - What the confusion matrix says it is being confused with, if anything
  - Whether docs/dataset-card-v1.md explains it — instance count, capture bias,
    annotation convention
  - Whether docs/taxonomy.md's mapping for this class merged things that should have
    stayed separate, or split things that should have merged
  - Whether the Lesson 02 Auto Label audit also found this class hard

Then classify each weak class as ONE of:
  - DATA: not enough instances, or biased instances. More training will not fix it.
  - TAXONOMY: the class boundary is wrong. Retraining the same labels will not fix it.
  - MODEL: enough good data, model underfitting or lacking capacity. Training might fix it.

Be specific about which, and say what evidence decided it. "chair could be improved with
more training" is not a diagnosis.
```

**The classification is the deliverable.** Each category calls for a different response,
and the expensive mistake is treating a DATA problem as a MODEL problem — that is how a
week disappears into hyperparameter tuning on a class with 47 instances.

**Cross-reference the audit.** A class that Grounding DINO also handled badly in Lesson 02
is probably intrinsically hard — ambiguous extent, heavy occlusion, poor visual
distinctiveness. That is a TAXONOMY or DATA finding, not a model one, and you have
independent evidence for it.

---

## Round 3 — the report

```
Write docs/evaluation-v1.md with:
  - Measurement conditions
  - The per-class table
  - The confusion matrix
  - The DATA / TAXONOMY / MODEL classification per weak class, with evidence
  - Exactly one recommended next action, and what you expect it to change

One action. Not a list of seven. If more than one thing is worth doing, say which is
first and why.
```

---

## What good output looks like

- Measurement conditions stated before any number
- Per-class table leads; aggregate follows
- Low-instance classes flagged as noise rather than quoted as results
- Weak classes traced to the dataset card and taxonomy, with the specific line that
  explains them
- Each weak class classified DATA / TAXONOMY / MODEL with stated evidence
- One recommendation, with a prediction attached

## Reject and re-run if

- The evaluation ran on the **valid** split, or the split is not stated
- A headline mAP appears before the per-class breakdown
- A class with 6 instances is reported at "0.00 recall" as though it were a finding
- The diagnosis is generic ("more data would help") rather than tied to a specific
  dataset-card line
- The agent proposes editing training code — it has no `Edit` tool, and if it is asking
  for one, the role boundary is doing its job
- Every weak class is classified MODEL. That is the answer that requires no evidence, and
  it is almost never right in this project
