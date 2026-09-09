# Lesson 02 — Deliverables checklist

Tick this after each step. The [README](../../README.md) says *why* each item matters and
is not repeated here; this file only records what must be true when you are done.

**Required** is what Lesson 03 starts from. **Extra** is optional — nothing in Lessons
03–05 reads it, so tick "skipped deliberately" rather than leaving a block blank. A blank
block cannot be told apart from an oversight.

---

## Required

### Prerequisites

- [ ] `ROBOFLOW_WORKSPACE` was copied from the browser address bar, not typed or read off a display name
- [ ] `/plugin` shows `roboflow` enabled and `/mcp` shows it connected
- [ ] `projects_list` returns the same projects your browser shows at `app.roboflow.com/<workspace>`
- [ ] `git check-ignore .env` prints `.env`
- [ ] `uv sync --extra dataset` succeeded, and the SUN RGB-D download finished (~20 GB free disk)

### Step 1 — credit harness

- [ ] `docs/credit-budget.md` records the workspace slug, the project ID, the dashboard URL, and a starting balance **you read in a browser**
- [ ] The Lesson 02 allocation row was revised to the path you are taking, and says which path that is
- [ ] `.claude/settings.json`: `ask` on `trainings_create`, `models_infer`, `versions_generate`, `workflows_run`; `deny` on `datasource_trigger` and `connect_cloud_storage` — both tool spellings present
- [ ] You ran the drill and watched `credit_gate.py` **block** a billed call, not prompt for it

### Step 2 — taxonomy

- [ ] `docs/taxonomy.md` exists, no `<...>` placeholders left in the class list
- [ ] The class list is alphabetical, numbered from 0, and an ADR records the decision
- [ ] `## Class list` is the only `| <id> | <name> |` table in the file
- [ ] Every source label the converter reported is mapped, dropped labels are listed with reasons, and every class is reachable from some mapping
- [ ] Annotation conventions written down (door/window extent, cabinet scope, occlusion)
- [ ] No class below ~50 instances, or the exception is deliberate and noted

### Step 3 — converter

- [ ] `scripts/convert_sunrgbd.py` committed; acquisition path recorded in an ADR
- [ ] The conversion report shows `records read = written + skipped`
- [ ] Skips are **characterized, not just counted** — random or systematic, and you can say which
- [ ] No unmapped source label was silently guessed at
- [ ] The subsample is deterministic (fixed seed) and spread across capture sessions
- [ ] **You opened the preview images with boxes drawn on them and looked at them**
- [ ] *If you fell back:* `docs/` records that you took the fallback artifact and where it came from

### Steps 4–5 — project, upload, tags

- [ ] Project created as **Object Detection** (immutable), licence chosen deliberately and recorded
- [ ] Both the workspace slug and the project ID are in `docs/credit-budget.md`
- [ ] Uploaded image count matches the converted set minus duplicates
- [ ] Tags applied in a separate pass after upload, and `NOT tag:sun-rgbd` **matches zero** — you ran the query
- [ ] You asked for counts with example IDs, not for a listing
- [ ] Splits rebalanced before generating, and the per-split sum reconciles against the annotated image count
- [ ] The Dataset Engineer showed you parameters before every mutating call, and deleted or modified nothing without approval

### Step 6 — version, export, verify, reconcile

- [ ] A version generated from `tag:sun-rgbd AND NOT tag:audit`
- [ ] Counts read from **`versions_get`**, not from the `versions_generate` response
- [ ] Preprocessing: Auto-Orient, resize 640×640 *fit within*, Modify Classes from `docs/taxonomy.md`
- [ ] No vertical flip, no 90° rotation; augmentation in the train split only
- [ ] Per-split counts recorded, roughly 70/20/10, summing to the version total
- [ ] The class list is alphabetical and matches `docs/taxonomy.md` exactly
- [ ] Exported YOLO into `data/v<N>/`, with `data.yaml` beside `train/`, `valid/`, `test/`
- [ ] `uv run python scripts/verify_export.py data/v<N> --taxonomy docs/taxonomy.md` passes — and if it failed on class order, the **document** was fixed, not the check
- [ ] If a version was discarded, every reference to its number was updated
- [ ] `docs/credit-budget.md` has an estimate **and** an actual for every billed row, reconciled against the usage dashboard, with **Remaining ≥ 3.0**
- [ ] Any gap between estimate and actual is investigated and written into the Notes table

### Decisions and hygiene

- [ ] ADRs for: the acquisition path, depth as inference-only, the class ID order, and the workspace visibility / plan choice
- [ ] Every remaining ⚠️ OPEN item has a line in the course `TODO.md`
- [ ] `git status` shows no `data/`, no `.env`, no raw archives; scripts committed, data not
- [ ] `git grep -iE 'rf_[A-Za-z0-9]{20}|ROBOFLOW_API_KEY *= *[^ ]' -- . ':!*.example'` returns nothing

### The one that isn't mechanical

- [ ] **You opened twenty random annotated images in the Roboflow UI and looked at them.**

---

## Extra — optional

### E1 — annotation quality review

- [ ] Skipped deliberately, *or:* the review ran read-only before any version was generated, `max-annotations:0` and `max-annotations:1` counts were explained rather than recorded, and you distinguished converter bugs from data-quality issues

### E2 — Auto Label audit

- [ ] Skipped, **and if you wrote a dataset card it says "not run" with the reason** — *or* every box below

- [ ] The 100-image holdout came out of the same seeded pass as the training pool, so the two are disjoint by construction
- [ ] Holdout images **and** labels at `data/audit-gt/`; `tag:audit` matched 0 before E2 began
- [ ] The holdout was uploaded **unlabeled** and tagged `audit`; the ground-truth labels stayed on disk
- [ ] The agent predicted in writing which classes would be unreliable, before any spend
- [ ] The free 4-image test was run and iterated on; per-class confidence thresholds set; `door`/`window` convention written into the class description
- [ ] The 1-credit estimate was in the ledger **before** the run, and the actual was appended after
- [ ] Exactly 100 images were auto-labeled, and they are in **no** dataset version
- [ ] `compare_autolabel.py` produced a per-class table, recorded together with the configuration that produced it
- [ ] The reading separates model error from annotation-convention difference, and flags classes under 10 ground-truth instances as noise rather than quoting rates
- [ ] Round 1's prediction was compared against the measurement
- [ ] You confirmed the batch in the browser and the charge on the dashboard rather than accepting "I ran Auto Label" — see the OPEN item in [`04-autolabel-audit.md`](../prompts/04-autolabel-audit.md)

*Agent-driven variant:* at most 10 images, raw predictions shown before `annotations_save`, the coordinate conversion stated explicitly, no pre-existing annotations overwritten.

### E3 — one isolated MCP write

- [ ] Exactly one image, tagged `mcp-demo`; payload and coordinate format shown before approval; result retrieved and confirmed; nothing tagged `sun-rgbd` or `audit` touched

### E4 — dataset card

- [ ] One card per generated version, **named after the version number Roboflow assigned**
- [ ] Conversion arithmetic reconciles; provenance recorded (script, commit SHA, records in/out/skipped, skips random or systematic)
- [ ] Class distribution filled in; depth section states inference-only with the relative-inverse-depth consequence
- [ ] Auto Label table and its configuration recorded — or "not run" and why
- [ ] **Limitations written by you, not generated**, and anything unverified marked ⚠️ OPEN rather than filled in plausibly — the licence especially
