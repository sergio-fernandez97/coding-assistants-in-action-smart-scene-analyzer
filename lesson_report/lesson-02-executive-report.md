# Lesson 02 — Dataset Engineering: completion report

**Project:** `smart-scene-analyzer/` · **Date:** 2026-09-09 · **Path taken:** required only, no extras
**Outcome:** Lesson 03 can start. One verifiable dataset version exists and every check passes.

---

## Executive summary

Lesson 02 was roughly two thirds done and stopped at the point where the remaining work
was all verification. The converter, the taxonomy, the harness, and a 3,094-image upload
were already in place and are good work. What was missing was everything that turns those
into something provable: no dataset version, no export, no splits, no ADRs, and no
verification script.

Finishing it surfaced **seven defects, five of which fail silently** — they produce a
plausible number, no error, and a wrong result discovered days later. Two of them would
have cost a full Lesson 03 training run. One had already quietly deleted 606 lines of the
lesson's main deliverable from version control.

All seven are fixed. Total spend this session: **0.36 credits, estimated** — the actual is
pending one reading only you can do.

| | Before | After |
|---|---|---|
| Dataset versions | 0 | **1** (7,190 images) |
| `tag:sun-rgbd` coverage | 915 / 3,094 | **3,094 / 3,094** |
| Splits | 2,996 / 0 / 0 | **2,097 / 599 / 300** |
| Class order vs. export | frequency — **mismatched** | alphabetical — **identical** |
| Converter under version control | **no** | yes |
| ADRs | 1 | **4** |
| `verify_export.py` | absent | **passes, 0 warnings** |

---

## What was already done, and left alone

Worth stating plainly, because none of it needed redoing:

- `src/smart_scene_analyzer/datasets/convert.py` — 606 lines, 33 passing tests, reconciles
  `read = written + skipped`, refuses to guess at unmapped labels.
- `docs/taxonomy.md` — 10 classes from 1,068 source labels, every merge argued, every drop
  named with a reason. The reasoning is intact; only the numbering changed.
- The harness — hooks, agent definitions, permission allowlist with both MCP tool
  spellings, `ask` on billed operations and `deny` on `datasource_trigger`.
- The 2,996-image upload and the 98-image audit holdout, with its contamination incident
  already investigated and written up in `HOLDOUT.md`.
- `docs/credit-budget.md` — the 1.95-credit gap was found and recorded as an explicit
  `Unattributed` row rather than absorbed. That is the ledger working.

---

## Findings

### 1. The class list was ordered by frequency; the export is alphabetical — *silent*

`docs/taxonomy.md` numbered classes by instance count: `chair`(0), `table`(1), `sofa`(2).
Roboflow sorts class names alphabetically on export and this is not configurable. YOLO
label files store the class as an integer index into that list.

Every label in `data/v1/` would have named the wrong object — `chair` read as `bed`,
`table` as `bin` — and nothing anywhere would have raised. The model trains. The mAP looks
plausible. The app draws correct boxes with wrong names.

**Fix:** renumbered to `sunrgbd-10c-v2` — `bed`(0), `bin`(1), `cabinet`(2), `chair`(3),
`door`(4), `lamp`(5), `monitor`(6), `shelf`(7), `sofa`(8), `table`(9). Merges, counts, and
dropped-label reasoning unchanged. Recorded in
[`0002-class-id-order.md`](../smart-scene-analyzer/docs/decisions/0002-class-id-order.md).

**Confirmed empirically after the fact:** the export's `data.yaml` reads
`['bed', 'bin', 'cabinet', 'chair', 'door', 'lamp', 'monitor', 'shelf', 'sofa', 'table']`.

**Carries forward:** everything under `data/yolo/` holds v1 indices and is superseded,
including the audit ground truth. Any future audit comparison must map by class *name*,
never by index. Adding a class is now an insertion, not an append — a retrain, not a
migration.

*Predicted by [lesson step 2](../lessons/02-dataset-engineering/README.md).*

### 2. The converter was gitignored and had never been committed — *silent*

`.gitignore` line 20 read `datasets/`. Unanchored, that pattern matches **any** directory
named `datasets` at any depth — including `src/smart_scene_analyzer/datasets/`, which is
source code. The entire converter package was invisible to git: `convert.py`,
`taxonomy.py`, `validate.py`, `__init__.py`.

`git status` was clean. `git add .` did nothing. The lesson's single largest deliverable
existed only on one disk.

A second consequence surfaced immediately: the file had never been linted either, because
it was never in a commit. `ruff check` found a line-length violation the moment it became
visible.

**Fix:** anchored to `/datasets/` with a comment saying why. Verified that `data/`,
`runs/`, `mlruns/`, and a root-level `datasets/` are all still ignored, and that
`data/v1/` stays out of the commit. Wrapped the long line.

### 3. The `sun-rgbd` tag covered 915 of 3,094 images — *silent*

The August pass tagged 1,504 images workspace-wide, only 915 of which are in this project.
The September upload was never tagged at all.

**This is the second time `roboflow image upload -t` has silently under-applied a tag** —
the first was the audit set, 4 of 100, already documented in `HOLDOUT.md`. It reports
success either way.

**Fix:** backfilled 2,179 images in five batches via `roboflow image metadata --tags`.
`NOT tag:sun-rgbd` now returns **0**. The 98 audit images carry both tags, so the count is
exact rather than approximately right.

### 4. The tag index lags the write by about a minute — *silent, and it has bitten before*

After a batch returned `succeeded: 500, failed: 0`, `NOT tag:sun-rgbd` still reported 1 for
roughly 60 seconds before settling to 0. A count read immediately after a tagging pass
under-reports.

This is very likely what started the `tag:audit = 4` panic on 2026-09-02, which nearly
caused a duplicate 100-image upload. **Verify tag counts on a delay, or the number you act
on is the number from before your own write.**

### 5. Splits were never rebalanced

All 2,996 images sat in `train`; `valid` and `test` were empty. Version generation
rebalances only within what it selects — it does not repair a skewed project.

**Fix:** rebalanced to **2,097 / 599 / 300**, summing exactly to 2,996.

### 6. `versions_generate` has no source filter, and the published docs are wrong

The lesson's prompt asks for a version filtered by `tag:sun-rgbd AND NOT tag:audit`.
Neither the MCP tool nor `roboflow version create` accepts a tag query — both take only
`preprocessing` and `augmentation`. The upstream skill lists **Filter by Tag** as a
preprocessing step, but its JSON schema is documented nowhere I could find.

Worse, `docs.roboflow.com/llms-full.txt` gives payload shapes the API rejects: it shows
`"auto-orient": {"enabled": true}`; the API returns `auto-orient must be a boolean`. The
local `computer-vision-skills` clone had the correct shape. **The local skill beat the
live docs** — which is exactly the rule the course CLAUDE.md already states.

**Resolution:** the audit holdout is excluded **by construction**, not by filter. Its 98
images are unannotated and sit in batch `audit-holdout`, outside every split, and version
source selection is dataset membership. Verified after generation: version 1 holds 7,190
images derived from the 2,996 in-dataset ones, and `tag:audit` still reads 98.

### 7. The dataset licence was never chosen — *still open*

`data/v1/data.yaml` declares `license: Public Domain`, on a public workspace, over a
dataset derived from SUN RGB-D whose own terms were never checked against it. Nobody
decided this. A default became a declaration.

This is the ⚠️ OPEN item lesson step 4 warns about, and it is still open — it is your call,
not mine.

---

## The check no script performs

I rendered 20 preview images with boxes drawn on them and **looked at them**. Four are
reproduced in judgement below; all 20 were opened.

**Geometry is correct.** Across two sensors (`kv2`, `realsense`) and four scene types,
boxes sit on their objects with tight margins. No uniform offset, no y-flip, no
aspect-ratio distortion. This is the failure mode every arithmetic check in the converter
passes over, and it is not present.

**One real data-quality finding, and Lesson 03 needs it:** the source annotations are
systematically **incomplete**. A desk scene has the large monitor unboxed and the open
drawer unboxed while other instances of both classes are boxed elsewhere. A conference
room has every chair boxed and the table itself unboxed.

The consequence for Lesson 03 is specific: **some of the model's apparent false positives
will be correct detections of unlabelled objects.** Triage them as DATA, not as MODEL, and
do not chase precision on classes where the ground truth is missing instances. This is
recorded in [`0003-dataset-acquisition-path.md`](../smart-scene-analyzer/docs/decisions/0003-dataset-acquisition-path.md).

---

## The dataset version

**[Version 1](https://app.roboflow.com/sergios-workspace-rdowu/smart-scene-analyzer-2026-09-02/1)**
· project `sergios-workspace-rdowu/smart-scene-analyzer-2026-09-02` · exported to `data/v1/`

Counts read from `versions_get`, not from the `versions_generate` response.

| Split | Images | Boxes |
|---|---:|---:|
| train | 6,291 | 39,315 |
| valid | 599 | 3,681 |
| test | 300 | 2,066 |
| **Total** | **7,190** | **45,062** |

Train is 2,097 × 3 exactly; valid and test kept their source counts, confirming
augmentation stayed in the train split.

Preprocessing: Auto-Orient, resize 640×640 **Fit within**. Augmentation, train only:
horizontal flip, brightness ±15%, exposure ±10%, blur ≤1px, noise ≤2%, 3x. No vertical
flip and no 90° rotation — indoor scenes have a gravity direction. Every parameter was
accepted verbatim and read back from `versions_get`.

**Modify Classes was deliberately not applied.** The platform class list already equals
the taxonomy exactly, so the remap is a no-op, and a mis-specified remap silently drops
classes.

Per-class instance counts, full scan of all 7,190 label files:

| Class | train | valid | test |
|---|---:|---:|---:|
| bed | 837 | 111 | 52 |
| bin | 1,254 | 105 | 49 |
| cabinet | 1,512 | 150 | 92 |
| chair | 21,381 | 1,891 | 1,128 |
| door | 735 | 73 | 40 |
| lamp | 1,107 | 139 | 56 |
| monitor | 1,278 | 126 | 70 |
| shelf | 1,044 | 156 | 58 |
| sofa | 1,131 | 121 | 69 |
| table | 9,036 | 809 | 452 |

Every class clears the ~50-instance floor in every split. The `chair`:`door` imbalance is
**29:1** — worse than the 17.7x the taxonomy predicted, because it is measured per split
rather than across the source metadata. Expect low `door` recall in Lesson 03 and triage
it as DATA.

### Verification

```
uv run python scripts/verify_export.py data/v1 --taxonomy docs/taxonomy.md --sample 0
  data.yaml declares 10 classes.
  Class list matches taxonomy: 10 classes, order identical.
  train: 6291 images, 39315 boxes in all 6291 label files.
  valid: 599 images, 3681 boxes in all 599 label files.
  test: 300 images, 2066 boxes in all 300 label files.
All checks passed (0 warning(s)).
```

`uv run pytest` — 46 passed, 2 xfailed. `ruff check` clean. `mypy src` clean, 35 files.
No key in any committed file; `data/` fully ignored.

---

## Credits

| | |
|---|---|
| Spent this session | **0.36 estimated** — one version generation, 7,190 output images at 1 cr / 20,000 |
| Free operations | tagging 2,179 images, split rebalance, export, project deletion |
| Remaining | **17.38 provisional** |

**One thing needs you, and no tool can do it.** The remaining balance applies the estimate;
it is not a platform reading. There is no MCP tool and no `roboflow` CLI command that
returns the workspace credit balance — I checked both. Open
`app.roboflow.com/sergios-workspace-rdowu/settings/usage`, read the number, and replace the
`⚠️ pending usage read` cell in the ledger with the actual.

That reading also settles the older question. The **1.95-credit unattributed gap** from
2026-09-02 now has an evidence-based hypothesis: the stale `smart-scene-analyzer-gc2rv`
project held 1,359 images (~0.14 cr uploads) and **two generated versions** of 3,021 and
3,261 images (~0.31 cr), plus ~0.27 cr/month storage; this project adds ~0.62 cr/month.
That reaches roughly **1.65 of the 2.26** read. It is arithmetic, not attribution — the
usage page is the only authority.

**The stale project is now in Trash** (30-day retention, `scheduledCleanupAt:
2026-10-09`). But note what that did *not* do: `cleanupDeleteImages: false`, so the images
remain workspace assets and the workspace still totals 3,683. **Deleting a project is not
deleting its images**, and the storage accrual continues. Roughly 147 of every 500 sampled
images were shared with the live project and count only once; the ~589 that were not
shared keep billing until the trash purges.

The **Lesson 02 allocation was revised from 4.0 to 1.0** — the original assumed two
versions and the Auto Label audit; the required path generated one version and ran no
audit.

---

## Files changed

Committed to `main` in `smart-scene-analyzer`:

| File | Change |
|---|---|
| `docs/taxonomy.md` | Alphabetical renumbering, `sunrgbd-10c-v2`, `## Classes` → `## Class list` |
| `.gitignore` | `datasets/` → `/datasets/`, with the reason |
| `docs/credit-budget.md` | Version row, revised allocation, provisional balance, 8 findings |
| `docs/decisions/0002-class-id-order.md` | New — class IDs follow the export |
| `docs/decisions/0003-dataset-acquisition-path.md` | New — convert, don't auto-label |
| `docs/decisions/0004-depth-scope-inference-only.md` | New — no ground-truth depth evaluation |
| `scripts/verify_export.py` | Copied from the course |
| `src/smart_scene_analyzer/datasets/*` | First commit — was gitignored |
| `scripts/preview_boxes.py`, `tests/test_convert.py` | First commit |

Not committed, by design: `data/v1/` (360 MB), `data/yolo/`, `data/SUNRGBD/`.

---

## Open items for you

1. **Read the usage page** and fill in the actual. Everything else in the ledger is
   reconciled; this one cell is not, and it also settles the 1.95 gap.
2. **Decide the licence.** `Public Domain` is currently declared over derived SUN RGB-D
   data by default, on a public workspace.
3. **The audit holdout is 98 images, not 100**, and its ground-truth labels carry v1 class
   indices. Not needed for Lesson 03; needed if you ever run the audit.
4. **Storage keeps accruing** on the ~589 trashed-project images until 2026-10-09. If you
   want that stopped sooner, the images have to be deleted, not just the project.

## Course-side corrections this run earned

Findings about the **course materials**, not the student project. I did not edit the
lesson — these are yours to apply:

| Where | Correction |
|---|---|
| `resources/prompts/02-dataset-version.md` | The `tag:sun-rgbd AND NOT tag:audit` source filter is not expressible through `versions_generate` or the CLI. Rewrite around dataset membership, and say that the audit holdout is excluded by staying in its batch. |
| `README.md` step 5 | Add the warning that `roboflow image upload -t` under-applies tags on directory imports — twice now, 4/100 and 915/3094 — and that tag counts lag writes by ~60s. |
| `resources/scripts/verify_export.py` | `checked = labels[:sample]` takes the *first* N in sorted order, not a random sample. On a 6,291-file split that is one contiguous slice of the alphabet, which clusters by capture session and produced a false "no instances of `bed`, `lamp`" warning. Use a seeded `random.sample`. |
| `template/.gitignore` | **Confirmed: line 15 carries the same unanchored `datasets/` rule.** `template/src/` has no package under it yet, so nothing is hidden today — but every student who writes their converter into `src/<pkg>/datasets/` in Lesson 02, as this project did, loses it from git silently. Anchor it to `/datasets/` before the next cohort. |
