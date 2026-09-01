# Prompt — Generate a dataset version

**When:** Lesson 02, post-session homework H4.

**Which agent:** `dataset-engineer`.

**Before you run this, two things must already be true:**

1. **Every image carries its source tag.** `NOT tag:sun-rgbd` must match zero images.
   The CLI import does not apply tags — step 9 tags as a separate pass — and a version
   generated against a partially-tagged project is quietly missing whatever was missed.
2. **The splits have been rebalanced.** `datasets_rebalance_splits` first, then generate.
   Generation rebalances only within what it selects; it does not repair a skewed
   project, and unannotated images sit outside every split.

⚠️ **Filter the audit images out of every version.** Use
`tag:sun-rgbd AND NOT tag:audit` as the source filter. If you did step 10, the 100
`audit` images are the control group for its measurement, and a control group that
trained the model is not a control group. If you skipped step 10 nothing carries the
tag and the clause is a no-op — **leave it in anyway**, so the same prompt is correct on
both paths.

---

```
Use the dataset-engineer agent.

Generate dataset version <N> of the smart-scene-analyzer Roboflow project.

Consult the roboflow:data-management skill for the exact preprocessing and
augmentation semantics before you call versions_generate. Do not work from memory —
I would rather you read than guess.

Source selection:
- Filter by tag: sun-rgbd AND NOT tag:audit
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

After generating, call versions_get on the new version and report from THAT — not
from the versions_generate response, whose image count is the project total before
the tag filter and before augmentation:
- The version number
- Actual per-split image counts, and their sum
- The final class list, in order
- Per-class instance counts per split
```

---

## Review the class list before you accept the version

**Order matters and is easy to miss.** YOLO label files store integer class IDs. If one
version's class list is `[bed, chair, table]` and another's is `[chair, table, bed]`,
every label in one of them means something different from what you think — and nothing
will error. Every version must produce **identical class lists in identical order**.

**Expect that order to be alphabetical.** Roboflow sorts class names on export and it is
not configurable, so `docs/taxonomy.md` must be numbered alphabetically to match (Lesson
02 step 12). If the version's class list is alphabetical and your taxonomy is not, the
taxonomy is the thing to fix.

Check the per-class counts too. A class with fewer than ~50 instances will not train
well; better to merge or drop it now, in the taxonomy, than to discover it in
Lesson 03's confusion matrix.

## Reject and re-run if

- The class list order differs from another version, or from `docs/taxonomy.md`
- A class appears that is not in `docs/taxonomy.md`
- Augmented images appear in the valid or test split
- The agent generated without showing you the parameters first
- Per-split counts are wildly off from the requested 70/20/10, or do not sum to the
  version total
- The agent reported counts from the `versions_generate` response rather than from
  `versions_get`

## If you have to discard a version

Soft-delete it and generate again. **Version numbers are not reused** — if you discard
version 1, the replacement is version 2, and every document that says "v1" now points at
nothing. Name dataset cards and export directories after the number you actually ended
up with, and fix the references rather than leaving them to be discovered in Lesson 03.
