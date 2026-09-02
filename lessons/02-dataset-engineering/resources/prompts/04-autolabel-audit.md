# Prompt — the Auto Label audit

**When:** Lesson 02, step 10.

**Which agent:** `dataset-engineer` for the prompt drafting and the platform work,
`data-pipeline` for the comparison script.

**Budget: 1 credit.** One hundred images at Roboflow's AI-labeling rate of 1 credit per
100 images. Everything before the final run is free.

---

## What this is for

You did not auto-label your dataset — you wrote a converter and kept the human
annotations. This step spends one credit to find out **what that decision was worth**.

The output is a per-class table: where does Grounding DINO agree with the SUN RGB-D
annotators, and where does it not? That number is only obtainable because you have human
labels to compare against. Had you taken the auto-labeling path, you would have had an
opinion about label quality and no way to check it.

You will need this table again in Lesson 06, when the active-learning loop asks which
classes are safe to accept from a model and which need review.

---

## Setup

From step 9 you have:

- 100 images uploaded to Roboflow **unlabeled**, tagged `audit`
- their converter-produced YOLO labels on disk at `data/audit-gt/`
- no overlap between these and the images that will form version 1

If the audit images are in your dataset version, stop and fix that first. A control group
that trained the model is not a control group.

---

## Round 1 — predict before you spend

```
Use the dataset-engineer agent.

Read docs/taxonomy.md. For each of the nine classes, draft the Auto Label configuration
I should use:
  - the class name to give the model (which need not be my internal class name)
  - a text description disambiguating it
  - a starting confidence threshold

Then, before I spend anything: rank the classes from most to least reliable and say why.
I want to know in advance which classes you expect Grounding DINO to get wrong, so I can
check your prediction against the measurement rather than rationalizing afterwards.

Consult roboflow:data-management -> labeling.md for how Auto Label uses class names and
descriptions. Do not call any tool that consumes credits.
```

**Expected result:** a nine-row configuration table and a ranked prediction with reasons.

Write the prediction down. Checking it against the real numbers in round 4 is most of the
value of this exercise — a calibrated sense of where open-vocabulary detection breaks is
worth more than any single dataset.

---

## Round 2 — the free loop

**This runs in the browser, not through the agent.** Auto Label is a web-app action.

Navigate to `app.roboflow.com/<workspace>/smart-scene-analyzer/annotate`, open the
`audit` batch, and choose **Auto Label**. Then:

1. Enter the class names and descriptions from round 1.
2. Click **Generate Test Results**. This runs on a **4-image subset and costs nothing**.
3. Look at the four results.
4. Adjust names, descriptions, and per-class confidence. Repeat.

**Iterate here as long as you like.** The 4-image preview is the only free
prompt-engineering loop Roboflow gives you, and using it well is the difference between
a 1-credit audit and a 1-credit audit that measured a badly configured model.

Things worth trying while it is free:

| Symptom | Try |
|---|---|
| A box around the entire image | A more specific class name. `sofa` beats `couch or sofa or settee`. Confidence thresholds do not fix whole-scene boxes |
| The same object returned twice under two classes | Tighten the description of the class that should not match, rather than raising confidence on both |
| A class never appears | Its name may not be in the model's vocabulary in the way you are phrasing it. Try the plain, common noun |
| `door` and `window` boxes disagree with each other about the frame | Decide the convention, write it into the description, and record it — this is a real ambiguity, not a bug |

---

## Round 3 — spend the credit

Record the estimate in `docs/credit-budget.md` **before** you click:

| Operation | Rate | Images | Estimate |
|---|---|---|---|
| Auto Label, `audit` batch | 1 credit / 100 images | 100 | 1.0 |

Then run **Auto Label with This Model** on the full 100-image batch.

When it completes, export the audit batch's annotations to `data/audit-export/` in YOLO
format, and append the *actual* cost to the ledger.

---

## Round 4 — measure

```
Use the data-pipeline agent.

Compare the auto-labeled annotations in data/audit-export/ against the human ground
truth in data/audit-gt/ using scripts/compare_autolabel.py.

Report, per class:
  - instances in ground truth, instances predicted
  - precision, recall, F1 at IoU >= 0.5
  - the median IoU of matched pairs
  - false positives and false negatives, with example image IDs for each

Then tell me:
  - which classes a machine-labeled dataset would have degraded, and by how much
  - which disagreements are model error and which are annotation-convention differences
    where neither label is wrong

Be concrete. "door: recall 0.34, and 18 of the 22 misses are doors occluded by more than
half" is useful. "door performs poorly" is not.
```

**Expected result:** a per-class table and a short prose reading of it.

**Do:** Compare it against round 1's prediction. Where the agent was wrong about which
classes would fail, ask why — that gap is the interesting part.

**Do:** Paste the table into `docs/dataset-card-v1.md`, under the audit section, together
with the final class names, descriptions, and confidence thresholds. Without the
configuration, the numbers are not reproducible.

---

## The distinction that matters when you read the results

Not every disagreement is model error.

A **model error** is a missed lamp, a box around a whole room, or a bookshelf called a
cabinet. It reflects a limit of the detector.

A **convention difference** is the model including a door frame that the human annotator
excluded, or splitting a sectional sofa into three boxes where the human drew one.
Neither label is wrong; they answer different questions.

The two have different implications. Model error at low recall means a machine-labeled
dataset would have *missing* objects, which teaches the model those objects are
background — genuinely damaging. Convention differences mean a machine-labeled dataset
would have been internally consistent but different from the human one, which is mostly
survivable and would have shown up as a systematic offset in your metrics.

Say which is which in your dataset card. This is the kind of judgment the course exists
to teach, and no script produces it.

---

## Optional — the agent-driven loop, ~0.05 credits

Where round 2 taught you prompt engineering against a vision model, this teaches the full
read → infer → write agent loop against a live platform.

```
Use the dataset-engineer agent.

Build a Roboflow Workflow that runs zero-shot object detection with the YOLO-World block
(roboflow_core/yolo_world_model@v1) over an image, using my nine taxonomy classes as the
class_list input.

Ground yourself first:
  - workflow_blocks_list and workflow_blocks_get_schema for the exact block inputs
  - workflow_specs_validate on the spec before running anything

Then run it on exactly 10 images from the audit batch with workflows_run, and SHOW ME the
raw predictions before writing anything back.

Before you write:
  - Report the coordinate format YOLO-World returns and the format annotations_save
    expects. A silent coordinate mismatch here writes plausible-looking garbage into my
    project.
  - Tell me the estimated credit cost of the run and my remaining balance.

Constraints:
  - At most 10 images this session.
  - Do not touch any image outside the audit batch.
  - Workflow visualization blocks return base64 images that will overflow your context.
    Do not include one; if a response contains image data, write it to disk and report
    the path.
```

**Why YOLO-World and not SAM3.** `roboflow_core/sam3@v3` is zero-shot *segmentation*. For
an object-detection project you would be paying segmentation cost for box output and
inheriting mask-boundary noise on the conversion back. Grounding DINO (round 3) and
YOLO-World (here) are the text → box models; SAM segments *things* and hands back regions
that still need a label.

**Why it stops at 10 images.** `workflows_run` handles one static image per call, and it
bills as hosted inference execution seconds. Scaling this would mean Roboflow batch jobs
(1 credit/hour CPU, 1 credit per 15 minutes GPU) or a local inference server — and the
local server is metered too, at 1 credit per 3,000 images. Nothing here is free at volume,
which is worth knowing before Lesson 06 proposes automating it.

---

## What good output looks like

- A prediction in round 1 that names specific classes and gives reasons, made before any
  spend
- Prompt iteration visible in the 4-image preview, not skipped
- The ledger updated **before** the billed run, with the estimate, and after it, with the
  actual
- A per-class table with counts, not just rates — recall 0.5 on four instances is noise
- Model error and convention differences separated in the prose

## Reject and re-run if

- **The agent claims to have run Auto Label.** It cannot; that is a UI action
- Any run touches more than 100 images
- The agent reports agreement rates without instance counts
- The comparison runs before you have confirmed the audit images are excluded from
  version 1
- The optional workflow round writes annotations before showing you the raw predictions
  and both coordinate formats
