# Lesson 02 — Deliverables checklist

Items marked **[opt]** belong to the two optional steps (10 and 14). If you skipped
them, that is a valid finish — but tick the "skipped deliberately" boxes rather than
leaving a block blank, so the next person can tell a decision from an oversight.

## Before you start

Five minutes here, and each one is a failure that cost the reference run real time.

- [ ] `ROBOFLOW_WORKSPACE` was copied **from the browser address bar**, not typed from
      memory or read off a display name
- [ ] You listed **every** workspace your key can see, and there is exactly one you
      intend to use — if there are several, you have chosen deliberately
- [ ] `docs/credit-budget.md` records the workspace slug, the **project ID**, and the
      dashboard URL
- [ ] You have read the current credit balance **yourself, in a browser**. No tool can
      fetch it
- [ ] ~20 GB free disk, and the SUN RGB-D download is already running
- [ ] You know which of steps 10 and 14 you are doing, before you start rather than when
      you run out of time

> **The rule that governs the whole session:** when a count from the platform disagrees
> with what you expected, suspect the assumption before the platform. Zero images means
> the wrong workspace before it means a failed upload. Every expensive mistake in the
> reference run was a plausible number believed too quickly, and not one of them raised
> an error.

## Harness

- [ ] `claude plugin marketplace add roboflow/computer-vision-skills` succeeded
- [ ] `claude plugin install roboflow` succeeded
- [ ] `/plugin` shows `roboflow` installed **and enabled**
- [ ] `/mcp` shows `roboflow` **connected**
- [ ] The skills list includes `roboflow:data-management`, `roboflow:training-and-evaluation`, `roboflow:inference`, `roboflow:universe`
- [ ] A read-only call (list workspaces) returns your real workspace
- [ ] You can state the difference between what the MCP server provides and what the skills provide
- [ ] `ROBOFLOW_API_KEY` is exported in the shell that launches `claude`
- [ ] `git check-ignore .env` prints `.env`

## Credit budget

Set up in step 4, **before** anything touched the platform.

- [ ] `docs/credit-budget.md` has a workspace, a starting balance, and a per-lesson allocation
- [ ] You read the rate table and can say which two operations could consume the whole budget
- [ ] `.claude/settings.json` has `ask` on `trainings_create`, `models_infer`, `versions_generate`, `workflows_run`
- [ ] `.claude/settings.json` has `deny` on `datasource_trigger` and `connect_cloud_storage`
- [ ] You tested that a training request now produces a permission prompt
- [ ] You read the forbidden-operations table in `CLAUDE.md`, including the RF-DETR NAS entry
- [ ] You can say why the project overrides a recommendation made by Roboflow's own skill

## Agents

- [ ] `.claude/agents/dataset-engineer.md` and `data-pipeline.md` both used this session
- [ ] You can say which agent owns a platform operation and which owns a local conversion
- [ ] The Dataset Engineer showed you parameters **before** every mutating call
- [ ] No agent deleted or modified anything on the platform without your approval

## Acquisition — the converters

- [ ] Acquisition path recorded (`/adr dataset acquisition path for SUN RGB-D`)
- [ ] `scripts/convert_sunrgbd.py` committed
- [ ] The conversion report shows `records read = written + skipped`
- [ ] **Skips are characterized, not just counted** — you can say whether they were
      random or systematic (e.g. "all had zero boxes")
- [ ] **You looked at preview images with boxes drawn on them**
- [ ] No unmapped source label was silently guessed at
- [ ] Subsample is deterministic (fixed seed) and spread across capture sessions
- [ ] The 100-image audit holdout came out of the **same seeded pass** as the training
      pool, so the two are disjoint by construction
- [ ] The holdout's images **and** labels are at `data/audit-gt/`, and neither was part
      of the step 9 upload
- [ ] **[opt]** `scripts/convert_nyu.py` committed, with its own conversion report
- [ ] **[opt]** NYU: the instance/class keying question was answered from the data, not assumed
- [ ] **[opt]** NYU: the HDF5 axis order was verified by writing an image out and looking at it
- [ ] **[opt]** NYU: minimum component area and the disconnected-component rule are stated
- [ ] **[opt]** `classes.txt` from both converters is byte-identical
- [ ] *Or:* step 14 was **skipped deliberately**, and your instructor knows which
      Lesson 03 variant you are running

*If you fell back:*

- [ ] Path B: the mirror's class list, image count, and license were verified against the original
- [ ] Path C: the substitution and its reason are recorded in the dataset card
- [ ] Path C: you accepted, deliberately, that the domain-adaptation pairing is gone

## Auto Label audit — **[opt]**, step 10

One credit, 100 images, ~45–60 minutes. Skipping is fine:

- [ ] *Either* step 10 was skipped, **and `docs/dataset-card-*.md` says "not run" with
      the reason** — not left blank — and the holdout is still on disk for a later session
- [ ] *Or* every box below is ticked

### Before spending

- [ ] The 100 holdout images are uploaded **unlabeled**, tagged `audit` — this is the
      step that puts them on the platform, and the only one
- [ ] Their ground-truth labels stayed on disk at `data/audit-gt/` and were **not**
      uploaded
- [ ] The agent predicted **in writing** which classes would be unreliable, before any spend
- [ ] The free 4-image test was run and iterated on
- [ ] `door` / `window` box convention decided and written into the class description
- [ ] Per-class confidence thresholds set, not left at the default for every class
- [ ] The 1-credit estimate was recorded in the ledger **before** the run

### After

- [ ] Exactly 100 images were auto-labeled — no more
- [ ] `compare_autolabel.py` ran and produced a per-class table
- [ ] The audit images are in **neither** dataset version
- [ ] Model error and annotation-convention differences are separated in the reading
- [ ] Classes with fewer than 10 ground-truth instances are flagged as noise, not quoted as rates
- [ ] Round 1's prediction was compared against the measurement
- [ ] The table **and the configuration that produced it** are in the dataset card
- [ ] Actual cost appended to the ledger

*Optional agent-driven variant:*

- [ ] At most 10 images processed
- [ ] The agent showed raw predictions before calling `annotations_save`
- [ ] The coordinate conversion between model output and `annotations_save` was stated explicitly
- [ ] No pre-existing annotations were overwritten

## Taxonomy

- [ ] `docs/taxonomy.md` exists with a numbered class list — no `<...>` placeholders left
- [ ] **The class list is in alphabetical order**, because that is what the export will
      be, and an ADR records the decision
- [ ] **The `## Class list` table is the only `| <id> | <name> |` table in the file**, or
      it is the only one under that heading — a second one silently overrides it
- [ ] Class count recorded
- [ ] Source-label → class mapping filled in for every source dataset you used
- [ ] Dropped labels listed with reasons
- [ ] Every class is reachable from the source mappings
- [ ] Annotation conventions (door/window extent, cabinet scope, occlusion) written down
- [ ] No class has fewer than ~50 instances (or the exception is deliberate and noted)
- [ ] The "present in both datasets" inclusion criterion is ticked **or explicitly
      retired** if you skipped step 14

## Roboflow project

- [ ] Project created as **Object Detection** (immutable — confirm it is right)
- [ ] Images uploaded and the count matches the converted dataset minus duplicates
- [ ] Source tags applied in a **separate pass after upload** — `roboflow import` cannot
      tag, so this does not happen on its own
- [ ] **`NOT tag:sun-rgbd` matches zero images.** You ran the query; you did not assume
- [ ] Splits rebalanced **before** generating, and the per-split sum reconciles against
      the project's annotated image count
- [ ] Annotation review run; report read before any version was generated
- [ ] `max-annotations:0` and `max-annotations:1` counts explained, not just recorded
- [ ] You distinguished converter bugs from genuine data-quality issues

## Dataset versions

- [ ] A version generated from `tag:sun-rgbd AND NOT tag:audit`
- [ ] **[opt]** A version generated from `tag:nyu-v2`
- [ ] No version contains any `audit`-tagged image
- [ ] Counts were read from **`versions_get`**, not from the `versions_generate`
      response — that one reports the project total, before filtering and augmentation
- [ ] The class list is alphabetical and matches `docs/taxonomy.md` exactly
- [ ] **[opt]** Both class lists identical in name AND order — check this explicitly
- [ ] Auto-Orient applied
- [ ] Resize 640×640 using *fit within*, not *stretch*
- [ ] Modify Classes applied from `docs/taxonomy.md`
- [ ] No vertical flip, no 90° rotation
- [ ] Augmentation present in the train split only
- [ ] Per-split counts recorded, roughly 70/20/10, and summing to the version total
- [ ] If a version was discarded, **every reference to its number was updated** —
      numbers are not reused, so "v1" may now point at nothing

## Export

- [ ] The version exported in YOLO format into `data/<version>/`
- [ ] `data.yaml` exists alongside `train/`, `valid/`, `test/`
- [ ] `uv run python scripts/verify_export.py data/<version> --taxonomy docs/taxonomy.md`
      passes
- [ ] If it failed on class order, **the document was fixed, not the check**
- [ ] `git status --porcelain data/` is empty — no image data staged

## Documentation

- [ ] A dataset card exists per generated version, **named after the version number
      Roboflow actually assigned**
- [ ] Conversion report arithmetic reconciles in every card
- [ ] Class distribution tables filled in
- [ ] **Known limitations written by you, not generated** — they require having looked at the images
- [ ] Conversion provenance recorded: script, commit SHA, records in/out/skipped, and
      whether the skips were random or systematic
- [ ] Depth section states inference-only, with the relative-inverse-depth consequence spelled out
- [ ] Auto Label audit table and its configuration recorded — **or "not run" and why**
- [ ] Anything you could not verify is marked ⚠️ OPEN rather than filled in plausibly.
      **The dataset licence is the usual one:** a public workspace declares one whether or
      not you checked it against the source dataset's terms

## Ledger reconciled

- [ ] `docs/credit-budget.md` has one row per billed operation
- [ ] Estimated **and** actual recorded for every row, including where they agreed
- [ ] Reconciled against `app.roboflow.com/<workspace>/settings/usage`, **read by you in
      a browser** — no tool can fetch it
- [ ] Total spend at or under ~0.5 credits (~1.5 with step 10)
- [ ] **Remaining** and **Last reconciled** updated
- [ ] Any gap between estimate and actual investigated and written into the Notes table
- [ ] Any line on the dashboard you cannot attribute to a step is named in the Notes
      table rather than absorbed silently

> A gap you did not chase is a cost you will meet again in Lessons 03–05, with less
> budget left to absorb it.

## Decisions recorded

- [ ] ADR for the dataset acquisition path
- [ ] ADR for the depth scope: inference only, no ground-truth evaluation
- [ ] **ADR for the class ID order following the export** (alphabetical), including the
      consequence that adding a class is a retrain rather than an append
- [ ] Roboflow plan / workspace visibility decision noted
- [ ] Every remaining ⚠️ OPEN item has a line in the course `TODO.md`

## Hygiene

- [ ] `git status` shows no `data/`, no `.env`, no raw dataset archives
- [ ] No API key appears in any committed file:
      `git grep -iE 'rf_[A-Za-z0-9]{20}|ROBOFLOW_API_KEY *= *[^ ]' -- . ':!*.example'` returns nothing
- [ ] Scripts committed; data not

## The one that isn't mechanical

- [ ] **You opened twenty random annotated images in the Roboflow UI and looked at them.**

Every automated check in this list passes on a dataset whose boxes are systematically
offset by a fixed amount, or whose class mapping is subtly wrong. Only your eyes catch
that. Ten minutes here saves a full training run in Lesson 03 spent diagnosing a model
that was never the problem.
