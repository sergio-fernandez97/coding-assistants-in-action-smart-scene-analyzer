# Prompt — Generate a dataset version

**When:** Lesson 02, step 13 (version 1) and step 14 (version 2).

⚠️ **Filter the audit images out of every version.** Use
`tag:sun-rgbd AND NOT tag:audit` as version 1's source filter. The 100 `audit` images are
the control group for step 10's measurement; a control group that trained the model is
not a control group.

**Which agent:** `dataset-engineer`.

---

```
Use the dataset-engineer agent.

Generate dataset version <1|2> of the smart-scene-analyzer Roboflow project.

Consult the roboflow:data-management skill for the exact preprocessing and
augmentation semantics before you call versions_generate. Do not work from memory —
I would rather you read than guess.

Source selection:
- Filter by tag: <sun-rgbd | nyu-v2>
- Split: 70% train / 20% valid / 10% test

Preprocessing (applies to all splits):
- Auto-Orient
- Resize to 640x640, "fit within" (NOT stretch — I do not want aspect ratio
  distorted)
- Modify Classes, applying the mapping in docs/taxonomy.md

Augmentation (train split only):
- Flip horizontal
- Brightness ±15%
- Exposure ±10%
- Blur up to 1px
- Noise up to 2%
- Max version size 3x

Do NOT apply vertical flip or 90° rotation. Indoor scenes have a gravity direction.

Before you generate:
1. Show me the exact parameters you will pass to versions_generate.
2. Tell me how many source images match the tag filter.
3. Tell me the expected image count per split after augmentation.

Wait for my approval. Version generation consumes credits and the result is
immutable — a wrong one has to be regenerated, not edited.

After generating, report:
- The version number
- Actual per-split image counts
- The final class list, in order
- Per-class instance counts per split
```

---

## Review the class list before you accept the version

**Order matters and is easy to miss.** YOLO label files store integer class IDs. If
version 2's class list is `[bed, chair, table]` and version 1's is
`[chair, table, bed]`, every label in one of them means something different from what
you think — and nothing will error. Both versions must produce **identical class lists
in identical order**.

Check the per-class counts too. A class with fewer than ~50 instances will not train
well; better to merge or drop it now, in the taxonomy, than to discover it in
Lesson 03's confusion matrix.

## Reject and re-run if

- The class list order differs from the other version
- A class appears that is not in `docs/taxonomy.md`
- Augmented images appear in the valid or test split
- The agent generated without showing you the parameters first
- Per-split counts are wildly off from the requested 70/20/10
