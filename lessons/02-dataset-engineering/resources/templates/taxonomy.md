# Object taxonomy — Smart Scene Analyzer

> Copy to your project as `docs/taxonomy.md`. This file is a **contract**: every
> dataset version, every trained model, and every API response uses exactly this class
> list, in exactly this order.

⚠️ **OPEN.** The class list below is a candidate, not a decision. Settle it against the
distinct source labels your converters report (Lesson 02 step 12) before generating any
dataset version. This is Notion Open Decision #1.

## Why order matters

YOLO label files store the class as an **integer index into this list**. Reordering the
list after any labels exist silently relabels your entire dataset — every `2` that
meant `sofa` now means something else, and nothing errors. Every dataset version must
present an identical list in identical order.

### The order is alphabetical, and it is not your choice

**Roboflow sorts class names alphabetically when it exports a dataset version.** This is
not configurable, and the export is what your training data actually says. Number this
list alphabetically and the document agrees with the artifact by construction; number it
any other way and `scripts/verify_export.py` will fail at Lesson 02 step 17, after a
version has been generated and a converter has run.

**Keep the list sorted whenever you change it.** The rule this replaces was "append
only", which assumed you controlled the order. You do not: inserting `desk` into the
list above puts it at index 3 and shifts five classes down. So —

> **Adding a class is a retrain and a re-export, not an append.** Every label file, every
> trained checkpoint, and every exported artifact produced before the insertion refers to
> the old indices. There is no incremental path.

To retire a class, map it to nothing in the source mappings below. Removing its row
renumbers everything after it, with exactly the same consequences.

## Class list

Alphabetical. Add rows in sorted position and renumber the whole column.

| ID | Class | Notes |
|---|---|---|
| 0 | `bed` | |
| 1 | `cabinet` | Cupboards, dressers, wardrobes, shelving units |
| 2 | `chair` | Includes office chairs, dining chairs, armchairs |
| 3 | `door` | |
| 4 | `lamp` | Floor, table, and ceiling-mounted |
| 5 | `sofa` | Couches, loveseats, sectionals |
| 6 | `table` | Dining, coffee, side, desk |
| 7 | `tv` | Televisions and monitors |
| 8 | `window` | |

**Class count:** `<___>`

> ⚠️ **Keep this the only `| <id> | <name> |` table in the document, or make sure it is
> the only one under a `## Class list` heading.** `verify_export.py` reads this section;
> if the heading is missing it falls back to scanning the whole file, and any other table
> shaped like this one — an Auto Label prompt table, for instance — will override the
> class list and report a class-order failure that is not real.

### Inclusion criteria

A class earns a slot only if it clears all four:

- [ ] At least ~200 instances available in the source data (fewer than ~50 will not train)
- [ ] Present in **both** source datasets, so V1 → V2 fine-tuning is comparable —
      *applies only if you are doing Lesson 02 step 14 (NYU). Mark it satisfied or
      explicitly retired; do not leave it unticked and unexplained*
- [ ] Visually distinguishable from every other class in this list by a human annotator
- [ ] Actually useful to the Smart Scene Analyzer's purpose

The second criterion is the one that quietly breaks the course *when there are two
datasets*. A class present only in the first makes the Lesson 03 comparison between the
two models unreadable — you cannot tell whether a metric moved because of domain
adaptation or because the class vanished. With a single dataset the criterion has
nothing to bite on, which is a reason to record that you retired it rather than to
quietly drop it: a later cohort adding NYU needs to know it was never enforced.

---

## Source mapping — SUN RGB-D

Fill in from the converter's inspection output (Lesson 02 step 7, round 1). Every
distinct source label must appear in exactly one row.

> **This table is the artifact that survives.** A reviewer can read it, disagree with a
> row, and change one line. That is the concrete advantage of converting over
> auto-labeling: the same judgment calls get made either way, but here they are written
> down in a form somebody can argue with.

| Source label | → Taxonomy class | Rationale |
|---|---|---|
| `chair` | `chair` | direct |
| `table` | `table` | direct |
| `desk` | `table` | merged — functionally and visually similar at 640px |
| `night_stand` | `<table? cabinet? dropped?>` | ⚠️ decide |
| `sofa` | `sofa` | direct |
| `bed` | `bed` | direct |
| `dresser` | `cabinet` | merged |
| `bookshelf` | `cabinet` | ⚠️ merged — reconsider if shelves matter to the use case |
| `lamp` | `lamp` | direct |
| `<...>` | | |

### Dropped source labels

Labels present in the source but deliberately excluded, and why. An explicitly dropped
label is a decision; an unlisted one is an oversight.

| Source label | Reason |
|---|---|
| `<...>` | `<too few instances / not relevant / ambiguous>` |

---

## Source mapping — NYU Depth V2

NYU Depth V2 uses a different label set than SUN RGB-D and at finer granularity, so
this table will not mirror the one above. Fill it in from the same inspection process.

| Source label | → Taxonomy class | Rationale |
|---|---|---|
| `<...>` | | |

### Dropped source labels

| Source label | Reason |
|---|---|
| `<...>` | |

---

---

## Audit prompts — the Auto Label configuration

Your dataset is not auto-labeled. This section records the configuration used for the
**100-image audit** in Lesson 02 step 10, where you spend one credit measuring how well
an open-vocabulary detector would have agreed with the human annotations.

Fill it in during the free 4-image test loop, and copy the finished table into
`docs/dataset-card-v1.md` alongside the results. Without the configuration, the agreement
numbers are not reproducible — a later reader cannot tell whether `door` scored badly
because the model is weak or because the description was.

| ID | Class | Prompt text / description | Confidence | Predicted reliability |
|---|---|---|---|---|
| 0 | `chair` | `<text>` | `<0.__>` | good |
| 1 | `table` | | | good |
| 2 | `sofa` | | | good |
| 3 | `bed` | | | good |
| 4 | `cabinet` | | | ⚠️ fuzzy — blurs into dressers, wardrobes, shelving |
| 5 | `lamp` | | | ⚠️ small; ceiling-mounted often missed |
| 6 | `door` | | | ⚠️ box extent ambiguous — frame included? |
| 7 | `window` | | | ⚠️ box extent ambiguous — frame included? |
| 8 | `tv` | | | good |

> The **Predicted reliability** column is filled in *before* the audit runs. Comparing
> your prediction against the measured result is most of what the credit buys.

### Annotation conventions

These are the judgment calls the source annotators made, which your mapping inherits and
your converter must respect. Record them — they are also what separates a genuine model
error from a convention difference when you read the audit results.

- **`door` / `window` box extent:** `<frame included / opening only>`
- **`cabinet` scope:** `<includes / excludes kitchen units, wall-mounted, open shelving>`
- **Occluded objects:** `<boxed to visible extent / to inferred full extent>`
- **Minimum object size kept:** `<___ px>`

---

## Consistency checks

Run these before generating any dataset version:

- [ ] Both source mappings target only classes in the list above
- [ ] Every class in the list is reachable from **both** source mappings
- [ ] No source label appears in two rows of the same table
- [ ] Every distinct source label appears in either the mapping or the dropped table
- [ ] The annotation conventions above are decided and written down
- [ ] `classes.txt` from both converters is byte-identical
- [ ] `verify_export.py` passes against the exported `data.yaml`

---

## Change log

Every change to this file invalidates existing dataset versions. Record it.

| Date | Change | Versions affected |
|---|---|---|
| `<YYYY-MM-DD>` | Initial taxonomy | — |
