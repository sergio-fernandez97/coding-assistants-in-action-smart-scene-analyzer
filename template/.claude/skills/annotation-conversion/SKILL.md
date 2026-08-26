---
name: annotation-conversion
description: Use when converting a third-party annotation format into YOLO — SUN RGB-D .mat metadata, NYU Depth V2 instance masks, COCO JSON, Pascal VOC XML, or any dataset whose labels must be remapped onto docs/taxonomy.md. Enforces inspect-before-you-write, assert-every-coordinate, and verify-against-pixels. Invoke whenever asked to write or debug a dataset converter, or when converted boxes look wrong.
---

# Annotation conversion

Run this with the `data-pipeline` role — local file work, not platform work. **Credits:
zero.** Converting is the reason this project can afford human ground truth at all;
auto-labeling the same images would cost more than the entire course budget.

Expect three or four rounds. This never one-shots, and that is the lesson: format
documentation and the actual file never quite agree.

## Round 1 — inspect. Do not write a converter yet.

A converter written from the format's documentation rather than from the file in front
of you is the most common way to lose a day here.

Load the metadata and report, from the real file:

- **How it loads.** MATLAB v7.3 is HDF5 and needs `h5py`; earlier versions need
  `scipy.io.loadmat`. Which one a given release is, is not documented — try and report.
  HDF5 also stores arrays transposed relative to what MATLAB shows you.
- The top-level keys and their shapes
- **One record printed in full** — every field, its type, its shape
- Where the 2D boxes live and their exact format: `xyxy` or `xywh`? absolute or
  normalized? which corner is the origin?
- Where the class label lives, and whether it is a string or an index into a list
- How a record references its image file on disk
- Total record count
- The complete set of distinct source labels, with counts

That last item is what makes the taxonomy mapping a table to fill in rather than a guess.

## Round 2 — write the converter

Output layout:

```
<out>/images/*.jpg
<out>/labels/*.txt      one line per object: <class_id> <cx> <cy> <w> <h>
                        all four coordinates normalized to [0, 1]
<out>/classes.txt       one name per line; order defines the integer IDs
```

Non-negotiable requirements:

- **Read the class mapping from `docs/taxonomy.md`.** If a source label has no mapping,
  do **not** guess. Collect every unmapped label, print them with counts at the end, and
  stop. The mapping is a human decision.
- **Assert every normalized coordinate is within [0, 1]**, and that `w > 0` and `h > 0`.
  Log and skip any record that fails, with the reason.
- **Handle zero-object records explicitly** — state whether you write an empty label file
  or skip the image, and why.
- **Reconcile counts.** Records read, images written, records skipped by reason. A
  converter that finishes silently having dropped a third of the dataset is the worst
  outcome available.
- `--dry-run` (report, write nothing), `--limit N` (fast iteration), `--sample N`
  (deterministic, fixed seed, spread across capture sessions rather than the first N).
- Idempotent and resumable — skip records whose output already exists.
- **Never modify the source directory.** Read from it, write to a new one.

Run `--dry-run --limit 50` and read the report before any full run.

Where the project needs a held-out audit set, produce it from **the same converter** with
the same conventions and confirm the two sets share no image IDs. If the comparison set
were produced any other way, a later disagreement would be ambiguous — the model, or the
pipeline?

When a second dataset must join an existing one, its `classes.txt` must match the first
**byte for byte**. Same names, same order. A version generated from two datasets whose
class lists differ in order is silently mislabeled and nothing will tell you.

## Round 3 — verify against pixels

The report can be perfectly consistent and the boxes still wrong. Coordinate-convention
errors do not raise exceptions; they train a worse model.

Write a preview script that samples N images, draws the converted boxes with class
labels, and writes them somewhere openable. Run it for 20 images. **Then look at them.**

This is the only check that catches a y-axis flip, an origin off-by-one, or a systematic
offset. Every assertion in round 2 passes on a dataset whose boxes are uniformly shifted
by ten pixels.

## What good output looks like

- Round 1 shows *actual printed structure*, not a description of what the format
  "typically" contains
- Unmapped labels cause a stop, not a guess
- Skip counts are itemized by reason
- Input and output counts reconcile
- The preview images show boxes tightly around the right objects

## Reject and re-run if

- The converter was written before the file was inspected
- A class mapping appears that is not in `docs/taxonomy.md`
- Skipped records are counted but not explained
- Input and output counts do not reconcile
- The preview step was skipped — "the assertions pass" is not verification here
- A second dataset's `classes.txt` differs from the first in names or order
