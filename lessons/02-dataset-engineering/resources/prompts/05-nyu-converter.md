# Prompt — NYU Depth V2 instance masks → YOLO boxes

**When:** Lesson 02, step 14.

**Which agent:** `data-pipeline`.

**Credits: zero.** All of it runs locally.

⚠️ **This is harder than the SUN RGB-D conversion.** SUN RGB-D at least *has* boxes,
buried in a MATLAB struct. NYU has none at all — it ships per-pixel instance and class
maps, and the boxes have to be derived. That derivation is the single hardest piece of
local data work in this course, and it is the reason the lesson budgets time for it
rather than reaching for an auto-labeler.

---

## Before you start

Download `nyu_depth_v2_labeled.mat` (~2.8 GB) from
[the NYU dataset page](https://cs.nyu.edu/~fergus/datasets/nyu_depth_v2.html). It
contains the ~1,449-image labeled subset — no subsampling needed.

```bash
uv sync --extra dataset     # h5py, scipy
```

**Two facts that will each cost you an hour if you meet them the hard way:**

1. It is a **MATLAB v7.3 file, which is HDF5**. `scipy.io.loadmat` fails on it. Use `h5py`.
2. **HDF5 stores these arrays transposed** relative to the orientation you expect. Get
   that wrong and every box is mirrored across the diagonal — producing coordinates that
   are perfectly valid, perfectly normalized, and completely wrong.

The second one is why round 3 exists and is not optional.

---

## Round 1 — inspect, do not convert

```
Use the data-pipeline agent.

I have nyu_depth_v2_labeled.mat at <path>. Before writing any conversion code, open it
with h5py and report the real structure.

Tell me:
- The top-level keys, each one's shape and dtype
- Which key holds the RGB images, and the axis order (is it (N, 3, W, H)? (N, H, W, 3)?
  Print the shape and say which axis is which — do not assume)
- Which key holds the per-pixel INSTANCE map and which holds the per-pixel CLASS map,
  and how they relate: is an instance ID unique image-wide, or unique only within a class?
- Where the class NAMES live and how a class map value indexes into them. Note that HDF5
  string storage in MATLAB files is often object references to uint16 arrays, not strings
- The image count
- For ONE image: the set of distinct instance IDs, the set of distinct class IDs, and
  the class name for each

Then, to prove the axis order rather than assuming it: write the first RGB image to a PNG
and tell me the path. I will look at it. If it comes out sideways or mirrored, we have
found the transpose before it cost us the dataset.

Do NOT write a converter yet.
```

**Why this round exists.** The instance/class relationship is the thing that decides your
whole algorithm. If instance IDs repeat across classes within an image, then `(class_id,
instance_id)` is the key that identifies an object and instance ID alone is not — and a
converter written on the wrong assumption merges two chairs into one box that spans the
room. You cannot read this off the documentation. Print it.

---

## Round 2 — derive the boxes

```
Now write scripts/convert_nyu.py deriving YOLO bounding boxes from the instance masks.

Algorithm:
  For each image:
    For each object instance (keyed as we established in round 1):
      Take the mask of pixels belonging to that instance
      Find connected components in that mask
      For each component, take the tight bounding box around it

Decisions I want made explicitly and reported, not silently:
  - Minimum component area. A 3-pixel fragment is annotation noise, not an object.
    Propose a threshold and say what it discards.
  - What to do when one instance yields several disconnected components: one box per
    component, or one box spanning all of them? A chair occluded by a table is genuinely
    two regions of one object. State your choice and its consequence for training.
  - Which NYU classes map to our taxonomy. Read docs/taxonomy.md. If a source class has
    no mapping, collect it and STOP at the end with the unmapped list and counts. Do not
    guess. NYU has ~894 classes and most of them are not ours.

Output layout, identical to the SUN RGB-D converter:
  <out>/images/*.png
  <out>/labels/*.txt      <class_id> <cx> <cy> <w> <h>, normalized to [0, 1]
  <out>/classes.txt       same order as the SUN RGB-D classes.txt — verify this

Requirements:
- Assert every coordinate is within [0, 1] and w > 0, h > 0. Log and skip failures.
- Count images read, boxes written, components discarded by reason, and reconcile.
- --dry-run and --limit N flags.
- Idempotent and resumable.
- Never modify the source file.

Report: images processed, boxes written, boxes discarded by reason, per-class instance
counts, and the box-area distribution.

Run with --dry-run --limit 20 and show me the report first.
```

> **`classes.txt` must match version 1's byte for byte.** YOLO labels are integer
> indices. If NYU's class list is `[bed, chair, table]` and SUN RGB-D's is `[chair,
> table, bed]`, every label in one dataset means something different in the other, and
> **nothing will error**. `verify_export.py` checks name *and* order for exactly this
> reason.

---

## Round 3 — verify against pixels

```
Reuse scripts/preview_annotations.py on the NYU output. Sample 20 images, draw the
derived boxes with class labels, write them where I can open them.

Include at least five images that contain a class we mapped from a fuzzy NYU label,
so I can check the mapping visually and not just the geometry.
```

**Then look at them.** You are checking three separate things, and only your eyes catch
any of them:

| Check | What failure looks like |
|---|---|
| Axis order | Boxes mirrored across the diagonal, or the image itself sideways |
| Instance keying | One box spanning two objects of the same class, or the whole room |
| Class mapping | A tight, correct box with the wrong label on it |

The third is the one that survives every automated check and ruins Lesson 03 quietly.

---

## What good output looks like

- Round 1 reports printed shapes and a PNG you actually looked at, not a description of
  what NYU "contains"
- The instance/class keying question is answered from the data, with evidence
- Minimum-area threshold and the disconnected-component decision are stated with their
  consequences
- Unmapped NYU classes cause a stop with a list, never a guess
- `classes.txt` is identical to version 1's
- Preview images show tight boxes with correct labels

## Reject and re-run if

- The agent uses `scipy.io.loadmat` and reports success — it cannot have opened this file
- Boxes are derived without connected-component analysis (a per-instance min/max over a
  disconnected mask silently produces one box spanning both regions)
- The class list order differs from version 1's
- Component discards are counted but not explained
- The preview step is skipped
