# Lesson 02 — Dataset Engineering

> Notion Week 2. **No live session.** You do this lesson at your own machine, in your own
> time: about **3 hours 15 minutes** of work, after a ~6 GB download that runs unattended.
> Everything beyond that is optional and marked as such.

## Session goal

Produce one dataset version you can prove is correct, and hand it to Lesson 03.

That is a smaller goal than it sounds. The dataset itself is nearly free — uploads and
version generation together cost a fraction of a credit. What costs you is that **every
way this goes wrong is silent**. Roboflow returns a plausible number, you interpret it
with an assumption that happens to be false, and nothing errors. A reordered class list
trains a model on scrambled labels. An untagged upload produces a version filtered down to
nothing. An empty search result means your key points at a different workspace than your
browser does. None of those raise an exception; all of them cost hours later.

So the required path here is six steps, and four of them are checks that turn a number
into something falsifiable. The engineering content is not "how to use Roboflow" — it is
**what you accept as proof** that a data artifact is what you think it is.

## Prerequisites

Nine steps, **in this order** — the slug before the key, the key before the connection
test, the connection test before anything you are willing to trust. About 30 minutes of
your attention, plus a download that runs unattended.

**1. Finish Lesson 01.** The harness, `docs/`, and `.claude/` must already exist in your
own repo; everything below writes into them.

**2. Start the SUN RGB-D v2 download — first, because it runs while you do the rest.**
Get it from <https://rgbd.cs.princeton.edu/>. You need the image data **and** the toolbox
containing `SUNRGBDMeta.mat`; the MATLAB metadata is where the source boxes live.

**Expected result:** ~6 GB downloading, and ~20 GB free disk to unpack into.

**3. Install the conversion dependencies** while that downloads.

```bash
uv sync --extra dataset
```

**Expected result:** exit code 0. This is the only toolchain-fragile install in the
lesson, which is why it happens now — a failure here costs you a retry rather than your
step 3.

**4. Create a Roboflow account** at <https://app.roboflow.com>. Signing up also creates
your **workspace**; you do not need a second one. Read the slug out of the address bar:

```text
app.roboflow.com/my-workspace-a1b2c
                 └────────┬───────┘
                 this is your workspace slug
```

Copy it from the address bar. Do not type it from memory, and do not use the display name
shown on the page — the two are often different. Everywhere this lesson writes
`<workspace>`, that is what it means.

**5. Create a personal API key** at `app.roboflow.com/<workspace>/settings/api`.

**6. Export both in the shell that starts Claude Code.**

```bash
export ROBOFLOW_API_KEY=<your-key>
export ROBOFLOW_WORKSPACE=<workspace>
```

**Expected result:** `echo $ROBOFLOW_WORKSPACE` prints your slug. Never commit the key or
a `.env` file.

**7. Install the Roboflow plugin.** It carries two different things, and the difference
matters for the rest of the course: **skills**, which are written guidance the agent
reads, and an **MCP server**, which makes live authenticated calls against your workspace.

![Claude Code talks MCP over HTTP to the Roboflow MCP server, which authenticates with your API key and calls the Roboflow platform on your behalf.](resources/images/roboflow-mcp-workflow.png)

```bash
claude plugin marketplace add roboflow/computer-vision-skills
claude plugin install roboflow
```

Then, in Claude Code — restart it if the plugin does not appear:

```text
/plugin
/mcp
```

**Expected result:** `/plugin` lists `roboflow` installed **and enabled**, and `/mcp`
shows `roboflow` **connected**. Fix this before step 1; every platform step below depends
on it.

**8. Prove your key and your slug point at the same workspace.** No MCP tool lists
workspaces, so the check is to ask the agent what it can see and compare that with your
browser.

```text
Use projects_list and report the project names you can see. Do not create anything.
```

Then open `app.roboflow.com/<workspace>` and compare the two lists.

**Expected result:** the same projects in both places. A brand-new account shows an empty
list in both — that is a pass. If the lists differ, your key and your slug point at
different workspaces, and you fix that now. In the reference run this cost forty minutes
and a false report that 1,504 uploaded images had vanished; the upload was fine, the slug
was not.

**9. Read `.claude/agents/dataset-engineer.md` and `.claude/agents/data-pipeline.md`.**
One owns the platform, the other owns local files. Knowing which is which is the whole
reason there are two.

## Deliverables

Tick these off step by step in
[`resources/checklists/deliverables.md`](resources/checklists/deliverables.md), which
carries the per-step detail behind each line below.

### Required — Lesson 03 does not start without these

- [ ] `docs/credit-budget.md`, with your workspace, your project ID, a starting balance
      read off the dashboard, and a reconciled **Remaining**
- [ ] `docs/taxonomy.md`, class list in **alphabetical order**, source mappings filled in
- [ ] `scripts/convert_sunrgbd.py` and its conversion report, with `read = written + skipped`
- [ ] Preview images with boxes drawn on them, **which you have looked at**
- [ ] A Roboflow object-detection project, every image carrying the `sun-rgbd` tag
- [ ] `data/v<N>/` — a YOLO export of an immutable version, passing `verify_export.py`

### Optional — Part 2

- [ ] An annotation-quality review report (E1)
- [ ] A 100-image audit holdout, an Auto Label audit, and a per-class comparison (E2)
- [ ] One isolated `annotations_save` read → approve → write → verify cycle (E3)
- [ ] `docs/dataset-card-v<N>.md` (E4)

## Step-by-step

## Part 1 — Required (≈ 3 h 15)

| # | Step | Estimate |
|---|---|---:|
| 1 | Set up the credit harness | 15 min |
| 2 | Draft the taxonomy, alphabetically | 15 min |
| 3 | Convert SUN RGB-D, and look at the boxes | 90 min |
| 4 | Create the project through MCP | 15 min |
| 5 | Upload, tag, and count | 30 min |
| 6 | Generate the version, export, verify, reconcile | 30 min |
| | **Total** | **3 h 15** |

**If you are short of time**, shorten step 1's drill first, then step 2's discussion.
**Never shorten step 3's preview check or step 6's `verify_export.py`.** Those two are the
only things in the lesson that catch a silently wrong dataset, and both failures they
catch are invisible until Lesson 03 has trained on them.

### 1. Set up the credit harness — 15 minutes

You have **20 Roboflow credits for the entire course**. There is no top-up. The ledger
exists so the agent can answer "can I afford this?" before it spends anything, and
`credit_gate.py` exists because a rule nobody reads is not a control.

**Do:** Copy the ledger into your project and fill in the header.

```bash
cp <path-to-course-repo>/template/docs/credit-budget.md docs/credit-budget.md
```

Replace `<path-to-course-repo>` with the absolute path to this course repository. Then set
**Workspace** to your slug, and **Starting balance** and **Remaining** to the number you
read at `app.roboflow.com/<workspace>/settings/usage`.

**Read that balance yourself, in the browser.** No MCP tool and no documented REST
endpoint returns it on the free plan. The reference run spent fifteen minutes watching an
agent try five routes that do not exist. Reconciliation in this course is a human step by
construction.

**Do:** Revise the **Planned allocation** row for Lesson 02. The shipped table budgets 4.0
credits, which assumed two dataset versions and the Auto Label audit. The required path
below spends a small fraction of that; the reference run measured **~0.4 credits for the
whole of Lesson 02 including the audit**. Set the row to match the path you are taking and
note which path that is.

**Do:** Confirm the permission rules the scaffold ships with are actually present.

```bash
grep -n 'versions_generate\|trainings_create\|datasource_trigger' .claude/settings.json
```

**Expected result:** `versions_generate` and `trainings_create` appear under `ask`,
`datasource_trigger` under `deny`, in both the `mcp__roboflow__` and
`mcp__plugin_roboflow_roboflow__` spellings — the tool name differs depending on whether
you installed the plugin or a `.mcp.json` server, so the scaffold lists both.

**Do:** Run the drill. Ask for a billed operation with no ledger row and watch what happens.

```text
Generate a dataset version. I have not written anything in the ledger.
```

**Expected result:** the call is **blocked by `credit_gate.py`**, not merely prompted for
permission, and the message tells you a ledger row with an estimate is missing. That is
the distinction worth feeling: the `ask` rule would have let you click through. The hook
does not block expensive spending — you can still spend the whole budget. It blocks
*unaccounted* spending.

### 2. Draft the taxonomy, alphabetically — 15 minutes

**Do:** Copy the template and settle the class list.

```bash
cp <path-to-course-repo>/lessons/02-dataset-engineering/resources/templates/taxonomy.md docs/taxonomy.md
```

> **Roboflow sorts class names alphabetically when it exports a version.** This is not
> configurable, and it is the *export* — not the project — that decides. YOLO label files
> store the class as an integer index into that list, so if your document is numbered in
> any other order, every label index in your training data refers to the wrong class and
> nothing errors anywhere. `verify_export.py` catches it at step 6, which is the right
> place to catch it and a terrible place to first learn it, after a converter has run and
> a version has been generated.
>
> The consequence for later: **adding a class is an insertion, not an append.** It
> renumbers everything after it and invalidates every label file and every checkpoint
> produced before it. There is no incremental path.

**Do:** Keep the `## Class list` table the **only** `| <id> | <name> |` table in the file.
`parse_taxonomy()` in `verify_export.py` scopes to that section when it exists, but a
second lookalike table elsewhere in the document is a trap the reference run fell into.

Leave the source-label mappings incomplete for now — step 3 round 1 tells you what the
real SUN RGB-D labels are, and you fill them in against that rather than from memory.

**Expected result:** `docs/taxonomy.md` exists, the class list is alphabetical and
numbered from 0, and no `<...>` placeholder remains in the class list.

### 3. Convert SUN RGB-D, and look at the boxes — 90 minutes

This is the longest step and the only fragile one. It runs entirely on your machine and
costs **zero credits** — which is the reason this course converts rather than auto-labels.
Auto-labelling 2–3k images would have cost 20–30 credits, the entire course budget.

**Do:** Work through the [SUN RGB-D converter prompt](resources/prompts/01-sunrgbd-converter.md),
rounds 1 to 3. Round 1 inspects the file before any code is written; round 2 writes the
converter and the reconciliation report; round 2b subsamples deterministically; round 3
draws the boxes on the pixels.

**Skip round 2b's audit carve-out** unless you intend to do [E2](#e2--the-auto-label-audit--1-credit-60-min).
The required path produces one set, not two.

> ⏱ **Timebox this to 60 minutes of iteration.** The prompt warns it will not one-shot;
> three or four rounds is normal, and the format documentation disagreeing with the actual
> file *is* the lesson. But it is also the only toolchain-fragile thing left in Lesson 02,
> and it must not be what stops you reaching Lesson 03. If the preview images still do not
> look right after an hour, take the fallback below and move on. You can come back to the
> converter afterwards; you cannot come back to a week you spent blocked.

> ⚠️ **OPEN — the fallback artifact does not exist yet.** The escape hatch this step needs
> is a pre-converted SUN RGB-D YOLO set. It cannot be committed to this repository (dataset
> artifacts are not committed here) so it has to be published somewhere. The two branches
> are (a) publish the reference run's dataset version publicly on Roboflow Universe and
> fork it, which keeps the fallback on the same platform this step teaches, or (b) a zip on
> external storage, which needs a URL nobody owns yet. Until one exists, ask your instructor.
> Tracked in the course `TODO.md`.

**Expected result:**

- `data/sunrgbd-yolo/` containing `images/`, `labels/`, and `classes.txt`
- a conversion report in which **records read = images written + records skipped**, with
  the skips itemized by reason
- no source label silently guessed at — an unmapped label stops the run
- ~20 preview images with boxes drawn on them **that you have opened and looked at**

That last one is not decoration. Every automated assertion in round 2 passes on a dataset
whose boxes are uniformly shifted by ten pixels, or whose y-axis is flipped. Only your eyes
catch that, and only before it has trained a model.

### 4. Create the project through MCP — 15 minutes

**Do:** Have the agent show you the parameters before it creates anything. Fill in
`<workspace>` with your slug.

```text
Use the dataset-engineer agent. In workspace <workspace>, show the exact parameters for a
new project named smart-scene-analyzer, type Object Detection, annotation group object.
Do not call projects_create until I approve the displayed parameters.
```

Review the type before you approve it. **Project type is set at creation and cannot be
changed afterwards** — a wrong one is a new project, not an edit.

⚠️ **OPEN — the licence.** Project creation asks for one. A free Public workspace declares
a licence whether or not you checked it against SUN RGB-D's own terms, and you are
republishing a derived dataset. The reference run defaulted to CC BY 4.0 with nobody
checking. Decide deliberately and record what you chose. Tracked in the course `TODO.md`.

**Do:** Approve, then verify through a separate read.

```text
Create the approved project. Then use projects_get or projects_list to report the project
ID, project type, and class state. Do not change anything else.
```

**Expected result:** MCP confirms a new object-detection project, and you have its **project
ID**. Write both the workspace slug and the project ID into `docs/credit-budget.md` now.
A ledger that records a workspace and no project is what made the reference run's
wrong-workspace failure take forty minutes to diagnose instead of two.

### 5. Upload, tag, and count — 30 minutes

**Do:** Upload the converted training pool.

```bash
roboflow import -w <workspace> -p <project-id> data/sunrgbd-yolo
```

**Do:** Tag every uploaded image `sun-rgbd`. **The CLI import does not apply tags**, and no
documented MCP tool does either — this is a separate pass and it does not happen on its
own. In the Roboflow web app: **Images** → select all → **Images Selected** → **Apply tags**
→ `sun-rgbd`.

Skipping this does not fail here. It fails in step 6, where the version filter selects on
the tag and quietly matches nothing.

**Do:** Verify with counts, not with confidence.

```text
Use the dataset-engineer agent. In project <project-id>, use images_search with RoboQL to
report the count for tag:sun-rgbd and the count for NOT tag:sun-rgbd. Report counts and at
most five example image IDs per query — do not enumerate records. Do not modify anything.
```

**Expected result:** `tag:sun-rgbd` matches your uploaded image count and
`NOT tag:sun-rgbd` matches **zero**. You ran the query; you did not assume.

> **The rule that governs the rest of this lesson:** when a count from the platform
> disagrees with what you expected, suspect your assumption before you suspect the
> platform. Zero images means the wrong workspace before it means a failed upload. Every
> expensive mistake in the reference run was a plausible number believed too quickly, and
> not one of them raised an error.

Note also why the prompt asks for *counts, with example IDs* rather than a listing: an
agent given a live API and a broad question will fetch everything. The reference run lost
a subagent to pulling 1,504 records into its context.

### 6. Generate the version, export, verify, reconcile — 30 minutes

**Do:** Rebalance the splits **before** generating. Generation rebalances only within what
it selects; it does not repair a project whose split assignment is already skewed, and
unannotated images sit outside every split entirely.

```text
Use the dataset-engineer agent. Rebalance the train/valid/test splits on project
<project-id> to 70/20/10, then report the resulting per-split counts and how they sum
against the project's annotated image count. Do not generate a version yet.
```

**Do:** Write the estimate into the ledger, then follow the
[dataset-version prompt](resources/prompts/02-dataset-version.md). Version generation is
billed, so `credit_gate.py` blocks it until the row exists — that is step 1's drill firing
for real.

**Expected result:** an immutable version whose counts you read from **`versions_get`**,
not from the `versions_generate` response. That response reports the project's total image
count, before the tag filter and before augmentation; the reference run read 3,261 there,
announced the filter had been ignored, and was wrong.

**Do:** Export the version in YOLO format to `data/v<N>/`, where `<N>` is the number
Roboflow actually assigned. Then verify it.

```bash
cp <path-to-course-repo>/lessons/02-dataset-engineering/resources/scripts/verify_export.py scripts/
uv run python scripts/verify_export.py data/v<N> --taxonomy docs/taxonomy.md
```

**Expected result:** exit code 0. If it fails on class order, **fix the document, not the
check** — the export is what your training data actually says.

> **Refer to your version by its number, never as "the latest".** Version numbers are not
> reused. If you discard version 1, the replacement is version 2 and every document saying
> "v1" now points at nothing — including Lesson 03's commands, which read `data/v1/`.
> Fix the references rather than remembering the difference.

**Do:** Reconcile. Open `app.roboflow.com/<workspace>/settings/usage`, compare the actual
spend against your estimates, and update **Remaining** and **Last reconciled**.

**Expected result:** `docs/credit-budget.md` has an estimate and an actual for every billed
row, and at least **3 credits remaining** — Lesson 03's prerequisite. Any gap between
estimate and actual goes in the Notes table. A gap you did not chase is a cost you will
meet again in Lessons 03–05 with less budget to absorb it.

---

## Part 2 — Extra (optional)

**Nothing in Lessons 03, 04, or 05 reads any of this.** Lesson 06 would use E2's output,
and Lesson 06 is not written yet. Do these because they are interesting, not because you
are behind without them.

### E1 — Annotation quality review — free, ~20 min

Run the [annotation-review prompt](resources/prompts/03-annotation-review.md) before you
generate a version. It is a read-only sweep of unannotated images, single-annotation
images, and class distribution.

The judgment it asks for is the point: **a converter bug and a data-quality issue look
identical in a class distribution and have completely different responses.** A dataset that
genuinely contains few lamps is a modelling problem. A converter that dropped the lamps is
a bug.

### E2 — The Auto Label audit — ~1 credit, ~60 min

**Prerequisite:** you must have carved the audit holdout during step 3, using round 2b of
the [converter prompt](resources/prompts/01-sunrgbd-converter.md). If you did not, redo
that round before starting — the holdout has to come out of the same seeded pass as the
training pool, or a disagreement is ambiguous between the model and your pipeline.

![The converter produces a training pool and a separate 100-image audit holdout. Only the holdout is auto-labelled; the training version filters it out, and the predictions are compared locally against the human labels you kept on disk.](resources/images/audit-control-flow.svg)

Follow the [Auto Label audit prompt](resources/prompts/04-autolabel-audit.md): predict in
writing which classes will fail, iterate on the free four-image preview, record the
one-credit estimate, run the full 100, then compare against your own labels.

```bash
cp <path-to-course-repo>/lessons/02-dataset-engineering/resources/scripts/compare_autolabel.py scripts/
uv run python scripts/compare_autolabel.py data/audit-export data/audit-gt --report
```

**What you are actually measuring:** you did not auto-label your dataset — you wrote a
converter and kept the human annotations. This spends one credit to find out what that
decision was worth. The number is only obtainable because you have human labels to compare
against.

**Expected result:** a per-class table with instance counts, not just rates, and a reading
that separates **model error** (a missed lamp, a box around a whole room) from
**convention difference** (the model including a door frame the annotator excluded).
Neither label is wrong in the second case, and the two have different consequences.

The audit images must be excluded from every dataset version — `tag:sun-rgbd AND NOT
tag:audit`. A control group that trained the model is not a control group.

### E3 — One isolated MCP write — free, ~15 min

The full read → approve → write → verify cycle against a live platform, on exactly one
image you have marked for the purpose.

```text
Use the dataset-engineer agent. For the single image tagged mcp-demo, show me the
annotations_save payload for one bounding box, including its class and the coordinate
format it expects. Wait for my approval. After approval, save it only on that image,
retrieve the image, and confirm the result. Do not touch any other image.
```

**Expected result:** you have seen the coordinate format stated explicitly before anything
was written. A silent coordinate mismatch here writes plausible-looking garbage into your
project — plausible enough that no check catches it but your eyes.

### E4 — The dataset card — free, ~20 min

```bash
cp <path-to-course-repo>/lessons/02-dataset-engineering/resources/templates/dataset-card.md docs/dataset-card-v<N>.md
```

Name it after the version number Roboflow actually assigned. It records the source, the
conversion provenance (script, commit SHA, records in/out/skipped, and whether the skips
were random or systematic), the class distribution, and the known limitations.

**Write the limitations yourself.** They require having looked at the images, which is why
a generated version of this section is worthless. Lesson 03's error analysis reads this
card as evidence when the confusion matrix surprises you.

### E5 — Run it under VoiceMode — free

```text
/voicemode:converse
```

Have the agent read the parameters of each platform operation back to you out loud before
it acts. A wrong project type or a wrong workspace is easier to catch by ear than in a wall
of text you have already scrolled past.

## Verification

Run all three. The first two must succeed; the third must print `clean`.

```bash
uv run python scripts/verify_export.py data/v<N> --taxonomy docs/taxonomy.md
grep -A2 'Remaining' docs/credit-budget.md
git status --porcelain | grep -E '\.pt$|mlflow\.db|^\?\? data/|\.env$' && echo "LEAK" || echo "clean"
```

Replace `<N>` with your actual version number.

Then confirm by hand:

- [ ] `NOT tag:sun-rgbd` matches zero images — you ran the query
- [ ] Per-split counts came from `versions_get`, not the `versions_generate` response
- [ ] `docs/credit-budget.md` records the workspace slug **and** the project ID
- [ ] Every billed row has both an estimate and an actual, and **Remaining** is ≥ 3.0
- [ ] `docs/taxonomy.md`'s class list is alphabetical and matches the export exactly
- [ ] No API key in any committed file:
      `git grep -iE 'rf_[A-Za-z0-9]{20}|ROBOFLOW_API_KEY *= *[^ ]' -- . ':!*.example'`
      returns nothing

And the one that is not mechanical:

- [ ] **You opened twenty random annotated images in the Roboflow UI and looked at them.**

Same reason as step 3, one platform later: ten minutes here saves a training run in
Lesson 03 spent diagnosing a model that was never the problem.

## Open items

⚠️ **The step 3 fallback artifact does not exist.** A pre-converted SUN RGB-D YOLO set has
to be published — Roboflow Universe fork, or a hosted zip — before the timebox in step 3
has anywhere to send you. Until then the escape hatch is your instructor.

⚠️ **Auto Label is reachable from MCP after all.** `autolabel_start` and `autolabel_job_get`
were verified against the live server on 2026-09-02. Earlier versions of this lesson taught
that Auto Label was web-app-only and used that as the surface boundary students should
reason about. That claim is now false, and E2 and
[`resources/prompts/04-autolabel-audit.md`](resources/prompts/04-autolabel-audit.md) still
describe the browser path. The open question is whether the boundary becomes a deliberate
cost-and-approval boundary instead of a capability one — do not rely on either framing until
it is settled.

⚠️ **The dataset licence.** See step 4.

⚠️ **Version generation billing.** Whether it is billed on the source image count or the
post-augmentation count is only partially measured. Record what you actually observe.

Every item above has a matching entry in the course `TODO.md` (instructor-maintained;
it is not part of the student checkout).

## Further reading

Local, checked source material — verify Roboflow facts here rather than from memory, since
model IDs, credit rates, RoboQL syntax, and tool names change upstream:

- `computer-vision-skills/skills/data-management/SKILL.md` — projects, upload methods,
  tags, RoboQL, immutable versions, and the MCP tool list
- `computer-vision-skills/skills/data-management/labeling.md` — Auto Label and
  annotation-batch capabilities
- `computer-vision-skills/skills/plans-and-pricing/SKILL.md` — current credit-rate guidance

Note that the Roboflow surface is larger than any single reference document describes. The
reference run twice declared a real API parameter a hallucination after failing to find it
in three separate sources. **Absence from the docs is not evidence of absence** — but it is
also not licence to write a command from memory.

External documentation, checked **2026-08-31**:

- [Claude Code — Connect Claude Code to tools via MCP](https://code.claude.com/docs/en/mcp)
- [Claude Code — Configure permissions](https://code.claude.com/docs/en/permissions)
- [SUN RGB-D](https://rgbd.cs.princeton.edu/)
- [Roboflow credits](https://roboflow.com/credits)

**Previous:** [Lesson 01](../01-project-definition-and-system-design/) ·
**Next:** [Lesson 03 — Model Development](../03-model-development/)
