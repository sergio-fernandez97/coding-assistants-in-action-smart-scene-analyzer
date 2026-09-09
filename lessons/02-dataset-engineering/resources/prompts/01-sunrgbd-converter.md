# Prompt — SUN RGB-D → YOLO converter

**When:** Lesson 02, step 3 (required).

**Which agent:** `data-pipeline`. This is local file work, not platform work.

**Which skill:** `annotation-conversion`. Invoke it first — it carries the method
(inspect → assert → verify against pixels) and the acceptance criteria. This file carries
what is specific to SUN RGB-D: where its metadata lives, how it loads, and the audit-set
carve-out. The skill is the procedure; this is one run of it.

**Credits: zero.** Everything here runs on your machine. That is the entire reason this
course converts rather than auto-labels. Auto-labelling 2–3k images would have
cost 20–30 credits, the entire course budget.

⚠️ This is the hardest prompt in the lesson and it will not one-shot. Expect three or
four rounds. That is the lesson — real annotation conversion is iterative because the
format documentation and the actual file never quite agree.

---

## Before you start

Download and unpack SUN RGB-D from
[rgbd.cs.princeton.edu](https://rgbd.cs.princeton.edu/) (~6 GB). You need both the
image data and the toolbox containing `SUNRGBDMeta.mat`.

```bash
uv sync --extra dataset     # installs scipy and h5py
```

---

## Round 1 — inspect, do not convert

```
Use the data-pipeline agent.

I have SUN RGB-D unpacked at <path>. Before writing any conversion code, inspect the
actual structure of the annotation metadata and report what you find.

Load SUNRGBDMeta.mat and tell me:
- How the file loads (scipy.io.loadmat vs h5py — MATLAB v7.3 files need h5py, and
  which one this is is not documented, so try and report)
- The top-level keys and their shapes
- For ONE record, printed in full: every field, its type, its shape
- Where the 2D bounding boxes live, and their format (xyxy? xywh? absolute?
  normalized? which corner is the origin?)
- Where the class label lives and whether it is a string or an index into a list
- How the record references its RGB image file on disk
- The total record count
- The complete set of distinct class labels, with counts

Do NOT write a converter yet. I want to see the real structure first.
```

**Why this round exists.** A converter written from the format documentation rather
than from the file is the single most common way to lose a day here. SUN RGB-D's
metadata is a nested MATLAB struct array whose layout differs between the toolbox
versions, and `scipy.io.loadmat` represents nested structs as nested object arrays that
do not look like anything you would design. Look first.

---

## Round 2 — write the converter

Once you have seen the structure:

```
Now write scripts/convert_sunrgbd.py converting SUN RGB-D annotations to YOLO format.

Output layout:
  <out>/images/*.jpg
  <out>/labels/*.txt      one line per object: <class_id> <cx> <cy> <w> <h>
                          all four coordinates normalized to [0, 1]
  <out>/classes.txt       one class name per line, order defines the integer IDs

Requirements:
- Read the class mapping from docs/taxonomy.md. If a source label has no mapping
  there, do NOT guess — collect every unmapped label, and at the end print them with
  their counts and stop. I will decide the mapping.
- Assert every normalized coordinate is within [0, 1] after conversion, and that
  w > 0 and h > 0. Report any record that fails and skip it with the reason logged.
- Handle records with zero objects explicitly: state whether you write an empty
  label file or skip the image, and why.
- Count inputs, outputs, and skips, and reconcile them. A converter that finishes
  silently having dropped a third of the dataset is the worst outcome here.
- --dry-run flag: report what would happen, write nothing.
- --limit N flag: process the first N records, for fast iteration.
- Idempotent and resumable — skip records whose output already exists.
- Never modify the source directory. Read from it, write to a new one.

At the end, print a conversion report:
  records read, images written, records skipped by reason,
  per-class instance counts, and the smallest and largest box areas seen.

Run it with --dry-run --limit 50 and show me the report before doing a full run.
```

---

## Round 2b — subsample (required)

You do not need all ~10,335 images, and storage bills monthly.

```
Add a --sample N flag that selects N records spread across the capture sessions rather
than taking the first N — sample deterministically with a fixed seed so the selection is
reproducible, and report which sessions are represented.

Then produce:
  data/sunrgbd-yolo/    1500 images with labels — this is what gets uploaded
```

**Stop here unless you are doing the optional Auto Label audit (E2).** The required path
produces one set. Round 2c below exists only to support that audit, and carving a holdout
you never use is the single most confusing thing you can do to this dataset — the reference
run destroyed a control group precisely because three files disagreed about where those
100 images were supposed to live.

---

## Round 2c — the audit holdout (optional — only for E2)

Skip this unless you intend to run the [Auto Label audit](04-autolabel-audit.md).

```
In the same seeded pass, produce a second output:
  data/audit-gt/        100 further images with labels, DISJOINT from data/sunrgbd-yolo/

Confirm the two sets share no image IDs.
```

**Where these images live, at every point.** This is the one thing to get unambiguously
right, because the reference run got it wrong and it cost a discarded dataset version:

| Stage | The 100 holdout images | Their labels |
|---|---|---|
| After this round | on your disk, `data/audit-gt/` | on your disk |
| During Lesson 02 step 5 | **not uploaded** — the required upload is `data/sunrgbd-yolo/` only | on your disk |
| During E2 | uploaded **unlabeled**, tagged `audit` — this is the only step that puts them on the platform | still on your disk, never uploaded |
| In every dataset version | excluded by `NOT tag:audit` | — |

So `tag:audit` matching **0** before you start E2 is correct, not a failed tagging pass.

**Why the audit set has to come from the same converter.** You are measuring the
auto-labeler against *your* ground truth, under *your* class mapping. If the comparison
set were produced any other way, a disagreement would be ambiguous — the model, or the
pipeline? Same converter means the only variable is the labeler.

---

## Round 3 — verify against pixels

The report can be perfectly consistent and the boxes still wrong. Coordinate-convention
errors do not raise exceptions; they just train a worse model.

```
Write scripts/preview_annotations.py that takes the converted dataset, samples N
random images, draws the YOLO boxes on them with class labels, and writes the
results to a directory I can open.

Run it for 20 images.
```

**Then look at the images.** This is the only check that catches a y-axis flip, an
off-by-one in the origin, or a systematic offset. Every automated assertion in round 2
passes on a dataset whose boxes are uniformly shifted by ten pixels.

---

## What good output looks like

- Round 1 report shows *actual* printed structure, not a description of what SUN RGB-D
  "typically" contains
- Unmapped labels cause a stop, not a guess
- Skip counts are itemized by reason
- The preview images show boxes tightly around the right objects

## Reject and re-run if

- The agent writes the converter before inspecting the file
- A class mapping appears that is not in `docs/taxonomy.md`
- Skipped records are counted but not explained
- Input and output counts do not reconcile
- The preview step is skipped — "the assertions pass" is not verification here
