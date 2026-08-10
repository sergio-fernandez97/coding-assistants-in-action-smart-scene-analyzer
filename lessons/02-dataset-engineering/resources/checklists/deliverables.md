# Lesson 02 — Deliverables checklist

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
- [ ] `scripts/convert_nyu.py` committed
- [ ] Both conversion reports show `records read = written + skipped`
- [ ] **You looked at preview images with boxes drawn on them** — for both datasets
- [ ] NYU: the instance/class keying question was answered from the data, not assumed
- [ ] NYU: the HDF5 axis order was verified by writing an image out and looking at it
- [ ] NYU: minimum component area and the disconnected-component rule are stated
- [ ] `classes.txt` from both converters is byte-identical
- [ ] No unmapped source label was silently guessed at
- [ ] Subsample is deterministic (fixed seed) and spread across capture sessions
- [ ] The 100-image audit set is disjoint from the uploaded set

*If you fell back:*

- [ ] Path B: the mirror's class list, image count, and license were verified against the original
- [ ] Path C: the substitution and its reason are recorded in the dataset card
- [ ] Path C: you accepted, deliberately, that the domain-adaptation pairing is gone

## Auto Label audit

One credit, 100 images, step 10.

### Before spending

- [ ] The 100 audit images are uploaded **unlabeled**, tagged `audit`
- [ ] Their ground-truth labels are on disk at `data/audit-gt/`
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
- [ ] The table **and the configuration that produced it** are in `docs/dataset-card-v1.md`
- [ ] Actual cost appended to the ledger

*Optional agent-driven variant:*

- [ ] At most 10 images processed
- [ ] The agent showed raw predictions before calling `annotations_save`
- [ ] The coordinate conversion between model output and `annotations_save` was stated explicitly
- [ ] No pre-existing annotations were overwritten

## Taxonomy

- [ ] `docs/taxonomy.md` exists with a numbered class list — no `<...>` placeholders left
- [ ] Class count recorded
- [ ] Source-label → class mapping filled in for **both** source datasets
- [ ] Dropped labels listed with reasons
- [ ] Every class is reachable from both source mappings
- [ ] Annotation conventions (door/window extent, cabinet scope, occlusion) written down
- [ ] No class has fewer than ~50 instances (or the exception is deliberate and noted)

## Roboflow project

- [ ] Project created as **Object Detection** (immutable — confirm it is right)
- [ ] Images uploaded and the count matches the converted dataset minus duplicates
- [ ] Source tags applied (`sun-rgbd`, `nyu-v2`) so the versions stay separable
- [ ] Annotation review run; report read before any version was generated
- [ ] `max-annotations:0` and `max-annotations:1` counts explained, not just recorded
- [ ] You distinguished converter bugs from genuine data-quality issues

## Dataset versions

- [ ] Version 1 generated from `tag:sun-rgbd AND NOT tag:audit`
- [ ] Version 2 generated from `tag:nyu-v2`
- [ ] Neither version contains any `audit`-tagged image
- [ ] **Both class lists identical in name AND order** — check this explicitly
- [ ] Auto-Orient applied
- [ ] Resize 640×640 using *fit within*, not *stretch*
- [ ] Modify Classes applied from `docs/taxonomy.md`
- [ ] No vertical flip, no 90° rotation
- [ ] Augmentation present in the train split only
- [ ] Per-split counts recorded and roughly 70/20/10

## Export

- [ ] Version 1 exported in YOLO format into `data/v1/`
- [ ] `data/v1/data.yaml` exists alongside `train/`, `valid/`, `test/`
- [ ] `uv run python scripts/verify_export.py data/v1 --taxonomy docs/taxonomy.md` passes
- [ ] `git status --porcelain data/` is empty — no image data staged

## Documentation

- [ ] `docs/dataset-card-v1.md` and `docs/dataset-card-v2.md` complete
- [ ] Conversion report arithmetic reconciles in both cards
- [ ] Class distribution tables filled in
- [ ] **Known limitations written by you, not generated** — they require having looked at the images
- [ ] Conversion provenance recorded: script, commit SHA, records in/out/skipped
- [ ] Depth section states inference-only, with the relative-inverse-depth consequence spelled out
- [ ] Auto Label audit table and its configuration in `docs/dataset-card-v1.md`

## Ledger reconciled

- [ ] `docs/credit-budget.md` has one row per billed operation
- [ ] Estimated **and** actual recorded for the Auto Label run
- [ ] Reconciled against `app.roboflow.com/<workspace>/settings/usage`
- [ ] Total spend at or under 4 credits
- [ ] **Remaining** and **Last reconciled** updated
- [ ] Any gap between estimate and actual investigated and written into the Notes table

> A gap you did not chase is a cost you will meet again in Lessons 03–05, with less
> budget left to absorb it.

## Decisions recorded

- [ ] ADR for the dataset acquisition path
- [ ] ADR for the depth scope: inference only, no ground-truth evaluation
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
