# Lesson 02 — Dataset Engineering

> Notion Week 2. Estimated time: 4–5 hours, plus dataset download time (SUN RGB-D is
> ~6 GB; start the download before the session).

## Session goal

Extend the harness with a **live external system**. Lesson 01's agents worked only on
local files; this session connects Claude Code to the Roboflow MCP server, so the
assistant can create projects, inspect annotations, and generate dataset versions on a
real platform.

That changes the stakes twice over. A file edit is reversible with `git checkout`. A
deleted Roboflow version is not — and unlike a bad file edit, some platform operations
**cost money**. This session is as much about scoping an agent's authority over a live,
metered system as it is about datasets.

By the end you have two versioned datasets — V1 from SUN RGB-D as the initial training
set, V2 from NYU Depth V2 standing in for newly acquired production data — sharing one
taxonomy, ready for the fine-tuning story in Lesson 03. You will have spent about **4 of
your 20 credits** getting there, and you will be able to say exactly where they went.

## Prerequisites

- [ ] Lesson 01 complete; your `smart-scene-analyzer` repo exists and is pushed
- [ ] A Roboflow account — [app.roboflow.com](https://app.roboflow.com)
- [ ] ~20 GB free disk for raw dataset downloads
- [ ] `uv sync --extra dataset` runs cleanly (installs `roboflow`, `h5py`, `scipy`)

> **Read this before creating your account.** The free **Public** plan makes your
> datasets and trained models publicly visible. That is fine for a course project built
> from public datasets, and it is what the lesson assumes. Confirm it is acceptable to
> you before uploading anything. See `roboflow:plans-and-pricing`.

> **This course has a hard budget of 20 Roboflow credits per student, for all five
> lessons.** There is no top-up. Step 4 sets up the ledger and the permission rules that
> enforce it, and it comes before any operation that touches the platform. Do not skip
> it — Lesson 06 is spending the credits you save here.

## Deliverables

- [ ] Roboflow plugin installed; `/mcp` shows `roboflow` connected
- [ ] `docs/credit-budget.md` filled in, with a starting balance and a planned allocation
- [ ] `.claude/settings.json` carries the credit-gating permission rules
- [ ] `.claude/agents/dataset-engineer.md` and `data-pipeline.md` in use
- [ ] A Roboflow object-detection project for the Smart Scene Analyzer
- [ ] `docs/taxonomy.md` — the class list, shared by both dataset versions
- [ ] `scripts/convert_sunrgbd.py` and `scripts/convert_nyu.py`, with conversion reports
- [ ] Dataset **version 1** generated from SUN RGB-D
- [ ] Dataset **version 2** generated from NYU Depth V2
- [ ] The Auto Label audit result — per-class agreement between Grounding DINO and the
      human annotations, recorded in the dataset card
- [ ] `docs/dataset-card-v1.md` and `docs/dataset-card-v2.md`
- [ ] Export of version 1 in `data/`, passing `verify_export.py`
- [ ] The ledger reconciled against the Roboflow usage page
- [ ] ADRs recording the acquisition path and the depth scope decision

Verify with [`resources/checklists/deliverables.md`](resources/checklists/deliverables.md).

---

## Step-by-step

### 1. Get your Roboflow API key

**Do:** Open [app.roboflow.com/settings/api](https://app.roboflow.com/settings/api),
copy the **Private API Key**, and export it in the shell you launch `claude` from.

```bash
export ROBOFLOW_API_KEY=<your-key>
export ROBOFLOW_WORKSPACE=<your-workspace-slug>   # from app.roboflow.com/<workspace-slug>
```

Also record it in your gitignored `.env`:

```bash
cp .env.example .env      # if you have not already
# edit .env, fill ROBOFLOW_API_KEY and ROBOFLOW_WORKSPACE
git check-ignore .env     # must print: .env
```

**Expected result:** `echo $ROBOFLOW_API_KEY` prints your key, and `git check-ignore
.env` confirms it is ignored.

> The MCP server reads the key from the **environment of the process that launches
> Claude Code** — not from `.env` directly. If you keep it only in `.env`, source it
> first: `set -a && source .env && set +a && claude`. Persist the export in `~/.zshrc`
> if you would rather not think about it again.

---

### 2. Install the Roboflow plugin

**Do:** Register the marketplace and install the plugin. This is one command each, run
once per machine.

```bash
claude plugin marketplace add roboflow/computer-vision-skills
claude plugin install roboflow
```

**Expected result:** both commands succeed and report the `roboflow` plugin installed.

**What you just installed** — and why it is two things, not one:

| Component | What it provides |
|---|---|
| **MCP server** (`https://mcp.roboflow.com/mcp`) | Live, authenticated *tools*: `projects_*`, `images_*`, `versions_*`, `models_*`, `universe_*` |
| **Skills** (`roboflow:data-management`, `roboflow:training-and-evaluation`, …) | Durable *knowledge*: exact model IDs, RoboQL syntax, credit costs, preprocessing semantics |

This split is worth internalizing, because it generalizes past Roboflow. The MCP server
gives an agent the ability to *act*. The skills give it the knowledge to act
*correctly*. An agent with tools and no domain knowledge calls `versions_generate` with
plausible-looking parameters that quietly produce a bad dataset. The skills are what
stop that.

It does not, however, stop everything. In step 4 you will override one of the skills'
own recommendations, because knowledge that is correct in general can be wrong for your
budget.

<details>
<summary><b>Alternative A — install from the local clone (offline / classroom)</b></summary>

The course repo already contains a clone at `computer-vision-skills/`:

```bash
cd <path-to-course-repo>
claude plugin marketplace add ./computer-vision-skills
claude plugin install roboflow
```

Or, for a throwaway session that does not touch your installed-plugins list:

```bash
cd <path-to-course-repo>/computer-vision-skills
claude --plugin-dir .
```
</details>

<details>
<summary><b>Alternative B — MCP server only, no plugin</b></summary>

Your project already has `.mcp.json` from the Lesson 01 template, pointing at the same
server. Starting `claude` in the project directory connects it — you get the tools but
**not** the skills.

Useful if plugin installation is blocked in your environment. Understand what you are
giving up: the agent will be calling a live platform API without the reference material
that tells it what the parameters mean.
</details>

<details>
<summary><b>Per-project API keys</b></summary>

If you work across multiple Roboflow workspaces:

```bash
claude plugin install roboflow --scope local
```

Local scope installs into the current project only and reads the key from that
project's environment.
</details>

---

### 3. Verify the harness before using it

**Do:** Start Claude Code in your project and run all three checks.

```bash
claude
```

```
/plugin
/mcp
```

**Expected result:**

- `/plugin` lists `roboflow` as installed and enabled
- `/mcp` lists `roboflow` with status **connected**
- The skills list includes `roboflow:data-management`, `roboflow:training-and-evaluation`, `roboflow:inference`, `roboflow:universe`, and others

**Do:** Confirm authentication with a read-only call.

```
List my Roboflow workspaces and projects.
```

**Expected result:** your workspace name appears. An empty project list is correct if
this is a new account.

**Troubleshooting:**

| Symptom | Cause | Fix |
|---|---|---|
| `/mcp` shows `roboflow` failed | Key not in the launching shell's environment | `export ROBOFLOW_API_KEY=...`, then restart `claude` |
| Tools present, skills missing | MCP configured but plugin not installed | Run step 2 |
| 401 / unauthorized | Wrong key type — the *publishable* key is not the *private* key | Re-copy from the settings page |
| Plugin listed but disabled | Not enabled after install | Enable it in `/plugin` |

> Do not continue until `/mcp` reports connected. Every remaining step depends on it,
> and an agent that cannot reach the platform will explain what it *would* do in a way
> that reads almost exactly like having done it.

---

### 4. Set your credit budget

**This step comes before any platform operation, and that ordering is the lesson.** A
budget written after the first surprise is an incident report.

Roboflow is metered. Most of what you will do today is effectively free — uploads,
version generation, tags, RoboQL queries — but a handful of operations are not, and two
of them can consume your entire course allowance in a single call.

**Do:** Open the ledger that shipped with your scaffold.

```bash
$EDITOR docs/credit-budget.md
```

Fill in your workspace slug, confirm the starting balance, and read the rate table. Then
check what you actually have:

```
Open app.roboflow.com/<workspace>/settings/usage and tell me my current credit balance
and this month's consumption.
```

**Expected result:** the ledger has a workspace, a starting balance, a planned
allocation per lesson, and a date.

#### What one credit buys

Verified against `roboflow:plans-and-pricing`. Read the skill yourself — these rates
change upstream, and the skill is re-read from disk every session while this table is not.

| Operation | 1 credit | What that means here |
|---|---|---|
| Uploads | 10,000 images | 3,000 images ≈ **0.3** |
| Storage | 5,000 images/month | 3,000 images ≈ **0.6/month** |
| Version generation | 20,000 images | two versions ≈ **0.5** |
| **Auto Label** | **100 images** | **the expensive one** |
| **Model training (GPU)** | **30 minutes** | 2 credits/hour — Lesson 03's risk |
| Hosted serverless inference | 500 seconds | ~1,000 images ≈ 1 credit |
| Self-hosted inference | 3,000 images | cheaper than hosted, **not free** |
| Dedicated deployment (GPU) | 1 hour of **uptime** | 24 credits/day if you forget it |

Free, and worth knowing precisely because it shapes the whole lesson: Auto Label's
**4-image "Generate Test Results" preview**, Roboflow **Instant** training, Universe
search, RoboQL, tags, splits, and workflow authoring. Only *running* a workflow bills.

**Notice the shape of that table.** Data operations are nearly free; compute is not.
Uploading ten thousand images costs one credit. Labeling ten thousand images costs a
hundred. That asymmetry is the single most important fact in this lesson, and step 7 is
where it decides your architecture.

#### Encode the budget in the harness — all four layers

A budget you agreed to is a prompt. A budget the tool enforces is a harness. Lesson 01
step 3 named four layers; this is the first thing in the course that uses all of them, on
one subject, and it is worth watching them stack.

**Layer 1 — the rule.** `CLAUDE.md` already carries the cap, the rate table, and the
forbidden-operations list. You will read it in a moment.

**Layer 2 — the permission policy.** Add these rules to `.claude/settings.json`:

```jsonc
"ask": [
  "mcp__roboflow__trainings_create",     // 2 credits/hour
  "mcp__roboflow__models_infer",         // hosted inference, billed per second
  "mcp__roboflow__versions_generate",    // cheap, but a version is immutable
  "mcp__roboflow__workflows_run"         // billed as hosted inference seconds
],
"deny": [
  "mcp__roboflow__datasource_trigger",
  "mcp__roboflow__connect_cloud_storage"
]
```

The two `deny` entries are there because `datasource_trigger` starts a billed
cloud-storage mirror run and its `trigger` parameter **defaults to true**. You do not
need cloud storage in this course; the safest configuration for a tool you will not use
is one that cannot be called.

> ⚠️ **Check the tool names against your own install.** MCP tools are named
> `mcp__<server>__<tool>`, and a tool provided by a *plugin* is named
> `mcp__plugin_<plugin>_<server>__<tool>` — so `mcp__roboflow__trainings_create` and
> `mcp__plugin_roboflow_roboflow__trainings_create` are different strings, and a rule
> written for one does not fire for the other. Step 2 offered you two install paths. The
> scaffold lists both spellings for exactly this reason. Confirm with `/permissions`
> after a real tool call, and if a billed call went through without prompting, the rule
> is not matching — fix the name rather than trusting it.

**Layer 3 — the procedure.** Open the project skill that encodes the ritual:

```bash
$EDITOR .claude/skills/credit-ledger/SKILL.md
```

**Do:** Bring it up to date against what you just read, and make it yours. Two things
need to be true that only you can make true:

1. The **rate table** in it must agree with `roboflow:plans-and-pricing` *today*. Read
   the vendor skill, compare, and correct the project skill where they differ.
2. The **forbidden-operations table** must reflect *your* plan and *your* budget, not the
   general case.

This is what authoring a project skill actually is. You have just installed nine skills
written by Roboflow, and they are good — they will tell you exactly what a version
generation costs. What they cannot tell you is that you have twenty credits, that four of
them are allocated to today, and that this project has decided against the architecture
their own skill recommends. **A vendor skill encodes the vendor's defaults. Yours encodes
your circumstances, and that is the only reason it can win an argument with theirs.**

**Layer 4 — enforcement.** Layers 1–3 all depend on being read. This one does not:

```bash
$EDITOR .claude/hooks/credit_gate.py
```

It is about a hundred lines and worth reading all of them. It fires before any billed
Roboflow tool call, parses `docs/credit-budget.md`, and exits 2 — which blocks the call —
unless the ledger contains a row with an estimate and no actual.

**Do:** Prove it, before you need it. Ask for a version generation without recording
anything first.

```
Generate dataset version 1 now.
```

**Expected result:** the call is **blocked**, not prompted. The message names what is
missing: a ledger row with the date, lesson, operation, rate, and estimated cost.

Now add the row by hand to `docs/credit-budget.md`, leaving `Actual` blank:

```
| 2026-08-11 | 02 | Version generation, ~3000 images | 1 cr / 20k images | 0.15 |  | 0.15 | 19.85 |
```

Ask again. This time the hook passes and the `ask` permission rule fires — and *now* the
prompt you are approving has an estimate attached to it, which is the only condition under
which approving it means anything. Decline it; you generate the real version in step 13.

> Compare the two experiences. Without the hook, "estimate before you spend" is advice,
> and the moment it matters most is the moment a confident assistant is most likely to
> skip it. With the hook, the estimate is a **precondition of the call existing**. The
> ledger stops being documentation of what happened and becomes the thing that lets it
> happen.
>
> This is also why the hook does not simply block everything expensive. It blocks
> *unaccounted* spending. You can still spend the whole budget — you just cannot do it
> without having written down what you expected it to cost, which is the only part that
> was ever really at risk.

**Do:** Then read the new `## Credit budget` section of your `CLAUDE.md`, in particular
the forbidden-operations table. One entry deserves attention:

> **Never start an RF-DETR NAS run.** `roboflow:training-and-evaluation` recommends
> Neural Architecture Search as its *default first choice*. It trains dozens of child
> models over hours at 2 credits/hour — one upstream example produced **76 child models
> from a 289-image dataset** — and it fails outright on non-Core plans.

Sit with that for a second. The skill is not wrong; NAS genuinely does produce the best
model, and for a team with a budget it is good advice. It is wrong *for you*, and
nothing in the skill knows that. **This is what a project constraint layer is for.**
Vendor knowledge encodes the vendor's defaults; `CLAUDE.md` encodes yours, and when they
conflict, yours wins because it is the one that knows your circumstances.

**Expected result:** `.claude/settings.json` contains the rules above and a `hooks` block
pointing at `credit_gate.py`; `.claude/skills/credit-ledger/SKILL.md` has a rate table you
have personally reconciled against `roboflow:plans-and-pricing`; and a billed call
attempted with an empty ledger is **blocked** rather than prompted.

---

### 5. Put the Dataset Engineer to work

**Do:** Open `.claude/agents/dataset-engineer.md` (it came with the Lesson 01 template)
and read the `tools` line:

```yaml
tools: Read, Grep, Glob, Write, Edit, Bash, Skill, mcp__roboflow__*
```

That wildcard is the agent's authority over your Roboflow workspace. Then read the
**Constraints** section, which is where the authority is scoped back down: confirm
project type before creating, get explicit approval before destructive operations,
never print the key, and — new since step 4 — state the estimated cost and remaining
balance before any billed call.

Notice the division of labour between the two dataset roles:

| Agent | Operates on |
|---|---|
| `dataset-engineer` | The Roboflow **platform** — projects, annotations, versions, exports |
| `data-pipeline` | **Local files** — converters, validation, preprocessing scripts |

Two agents rather than one because the failure modes are different. Platform mistakes
are irreversible and cost credits; local mistakes are a `git checkout` away. Different
risk profiles deserve different constraint sets.

**Expected result:** you can say which of the two owns "convert SUN RGB-D annotations
to YOLO format" (`data-pipeline`) and which owns "generate version 1 with 640×640
resize" (`dataset-engineer`).

---

### 6. Survey what already exists on Roboflow Universe

**Do:** Before building a dataset, look for one. Ask the Dataset Engineer:

```
Search Roboflow Universe for indoor scene object detection datasets covering
furniture and household objects — chairs, tables, sofas, beds, lamps, doors.
For each candidate report: image count, class list, license, and whether it looks
suitable as a base for the Smart Scene Analyzer taxonomy.
```

**Expected result:** a shortlist with counts, classes, and licenses.

Two tools exist and they are not interchangeable:

| Tool | Use when |
|---|---|
| `universe_search` | You want structured JSON to filter or compare programmatically |
| `universe_search_app` | **A human must look before choosing.** Opens the Universe UI with previews, sample images, license, and metrics |

Dataset selection is a judgment call that depends on seeing the images. Use
`universe_search_app` here. A dataset whose "chair" class is 90% office chairs is a
domain-shift problem you will only notice by looking.

Searching and browsing Universe is free. ⚠️ Whether *forking* a Universe dataset into
your workspace bills is not documented in the skills — a fork materializes images in
your workspace, so it plausibly hits the Uploads and Storage rates and is negligible
either way, but do not assume. See [Open items](#open-items).

---

### 7. Acquire SUN RGB-D — write the converter

**The problem.** SUN RGB-D is not a native Roboflow Universe dataset. It is distributed
by Princeton as ~6 GB of raw RGB-D captures plus a MATLAB metadata file
(`SUNRGBDMeta.mat`) holding the annotations. Roboflow ingests images with annotations
in a supported format — it cannot read MATLAB structs. **Something has to convert the
annotations before anything is uploaded.**

**This course writes the converter.** The `data-pipeline` agent turns `SUNRGBDMeta.mat`
into YOLO-format labels, and you upload images that already carry human annotations.

#### Why, given the alternatives

There is an obvious-looking shortcut: skip the `.mat` file entirely, upload the raw
JPEGs, and let a foundation model produce the boxes. It is genuinely tempting — it
deletes the hardest task in the lesson. Here is what it costs, using the rates from
step 4:

| | Approach | Labeling credits | Ground truth | Time |
|---|---|---|---|---|
| **A** ✅ | Write a `.mat` → YOLO converter | **~0** | Human | 60–90 min, may stall |
| B | Find a pre-converted Universe mirror | ~0 | Human, unverified | 20 min if one exists |
| C | Substitute a Universe indoor dataset | ~0 | Human | 20 min |
| D ❌ | Upload raw images, auto-label them | **20–30** | ⚠️ Machine | 45 min |

Auto-labeling a 2,000–3,000 image subsample costs 20–30 credits at 1 credit per 100
images. **That is the entire course budget, spent in one step, before you have trained
anything.** Labeling all ~10,335 SUN RGB-D images would be ~104 credits.

The constraint decides it, but notice that the decision is not actually a sacrifice.
Path A is also the path that gives you **human ground truth**, and that turns out to
matter more than the credits:

> Fine-tuning YOLO11 on model-generated labels is knowledge distillation — a legitimate
> technique, capped at the teacher's accuracy. That is survivable for the training split.
>
> It is **not** survivable for the test split. mAP measured against Grounding DINO's
> output means "agreement with Grounding DINO," not accuracy — and Lesson 03 reads its
> entire V1-vs-V2 comparison off those numbers. Auto-label your test set and every metric
> in the rest of the course is unanchored.

Path A gives you both: no labeling spend, and metrics that mean something. This is worth
noticing as a general pattern — a hard constraint often rules out the option you would
have regretted anyway, and forces you to articulate why.

You are not skipping auto-labeling as a topic. Step 10 spends **one** credit measuring
how good it would have been, which you can only do *because* you have human labels to
compare against.

**Do:** Have the `data-pipeline` agent write the converter. Use
[`resources/prompts/01-sunrgbd-converter.md`](resources/prompts/01-sunrgbd-converter.md).

The prompt runs in three rounds — **inspect, convert, verify against pixels** — and the
first round exists because annotation formats are documented optimistically and
populated inconsistently. The agent will need several passes to get the struct layout
right. Budget 60–90 minutes. This is messy real-world annotation conversion, which is
the daily work of a Dataset Engineer.

**Expected result:** `scripts/convert_sunrgbd.py` produces `images/`, `labels/`, and
`classes.txt`, with a conversion report reconciling records in against records out.

**If you stall past 90 minutes**, take a fallback rather than losing the session:

| Fallback | What you give up |
|---|---|
| **B** — a pre-converted Universe mirror | ⚠️ Unverified: no mirror is confirmed to exist at the quality this course needs. Check class list, count against the ~10,335 original, license, and a visual sample. A bad mirror is worse than no mirror, because the problems surface during training |
| **C** — substitute a Universe indoor dataset | The conversion lesson entirely, and the SUN RGB-D → NYU domain-adaptation pairing the course is built around. Say in your dataset card that you substituted, and why |

Either way, record what you did: `/adr dataset acquisition path for SUN RGB-D`.

#### Subsample before you upload

You do not need all 10,335 images. **1,500 is ample** for a course-scale fine-tune, and
it keeps storage at roughly 0.6 credits/month across both datasets. Sample across the
capture sessions rather than taking the first 1,500, or you will train on one building.

#### Depth: a scope decision, not a storage problem

**Roboflow stores bounding boxes, polygons, keypoints, and image-level labels. It does
not store depth maps.** SUN RGB-D's depth channel cannot be versioned in Roboflow
alongside the boxes.

Earlier drafts of this course treated that as a storage problem to solve — S3, DVC, or
GitHub Releases for the depth arrays, plus a mapping from Roboflow image ID to depth
map. **This course takes the other branch: depth is inference-only.**

Lesson 03 runs Depth Anything V2 and Lesson 04 serves its output, but neither evaluates
it against ground truth. The consequence is specific and you should be able to state it:

- ✅ You can say "the chair is nearer than the wall" — relative ordering
- ❌ You cannot say "the chair is 2.3 m away", and you cannot report depth error

Depth Anything V2 outputs **relative inverse depth** — larger means nearer, the scale is
arbitrary, and it is not metres. Without ground truth there is nothing to calibrate
against, so the honest thing is to carry the relative units all the way to the API
response. Lesson 04 makes that a schema-design problem.

**Do:** Record it: `/adr depth scope: inference only`.

Keeping the original SUN RGB-D and NYU images still matters — if a later cohort wants
quantitative depth, the raw depth channel is still in the download, and only the storage
decision has to be made.

---

### 8. Create the Roboflow project

**Do:** Ask the Dataset Engineer:

```
Create a Roboflow object detection project called "smart-scene-analyzer" in my
workspace, with annotation group "object". Show me the exact parameters before
you call projects_create.
```

**Expected result:** the agent shows the parameters, you approve, and the project is
created. `projects_list` then shows it.

> **Project type cannot be changed after creation.** Object Detection is correct here —
> the Smart Scene Analyzer detects and classifies with YOLO11. If you later want
> segmentation, that is a new project, not an edit. Confirm the type before approving.

---

### 9. Upload the images

**Do:** Choose by dataset size (see `roboflow:data-management`).

| Images | Method |
|---|---|
| < 1,000 | Web UI drag-and-drop at `app.roboflow.com` |
| > 1,000 | The CLI |

Login in to the Roboflow account that owns or has access to `smart-scene-analyzer`
```
uv run roboflow login
```

```bash
uv run roboflow -w $ROBOFLOW_WORKSPACE import -p smart-scene-analyzer <path-to-converted-dataset>
```

**Expected result:** the upload completes and the image count in the web app matches
your converted dataset, minus skipped duplicates.

Limits worth knowing before you start a multi-hour upload: **20 MB per image**,
**16,400 × 10,900 px** maximum, and **duplicate images are skipped automatically** (by
content hash, so re-running an interrupted upload is safe).

**Do:** Tag the source at upload time.

Tags are how you keep V1 and V2 separable inside one project. Tag the SUN RGB-D images
`sun-rgbd` and the NYU images `nyu-v2`. Version generation can then filter by tag,
which is what makes step 14 possible without a second project.

**Do:** Hold back 100 images for step 10. Upload them **unlabeled**, tagged `audit`, and
keep their converter-produced labels on disk at `data/audit-gt/`. They are the control
group, and they must not go into any dataset version.

**Ledger:** ~1,600 images uploaded ≈ 0.16 credits. Round up and record 0.2.

---

### 10. Audit the auto-labeler — 1 credit

You skipped auto-labeling as a *strategy*. Now spend one credit finding out what that
decision was worth, on your own data.

**The question:** if you had taken Path D, how good would the labels have been? Everyone
in this field has an opinion about foundation-model labeling. You are about to have a
number instead, and it is only obtainable because step 7 produced human labels to
compare against.

**Do:** Work through
[`resources/prompts/04-autolabel-audit.md`](resources/prompts/04-autolabel-audit.md).
The shape of the session:

1. **Have the agent draft your class prompts** from `docs/taxonomy.md`, and — more
   usefully — predict which classes will be unreliable *before* you spend anything.
2. **Run the free 4-image test** in the Roboflow UI (Images → Annotate → your `audit`
   batch → Auto Label → Generate Test Results). **No credits, unlimited retries.** This
   is your prompt-engineering loop, and it is why the audit is cheap to get right.
3. **Iterate on class names, descriptions, and per-class confidence** until the four
   results look correct.
4. **Run Auto Label on the 100-image `audit` batch. This costs 1 credit.** Record it in
   the ledger before you click.
5. **Export and compare** against the converter's labels for those same 100 images:

```bash
uv run python scripts/compare_autolabel.py data/audit-export data/audit-gt --report
```

**Expected result:** a per-class table of precision, recall, and IoU-matched agreement
between Grounding DINO and the SUN RGB-D annotators. Record it in `docs/dataset-card-v1.md`.

**What to expect** — and check the predictions from sub-step 1 above against it:

| Reliable | Fuzzy | ⚠️ Hard |
|---|---|---|
| `chair`, `table`, `sofa`, `bed`, `tv` | `cabinet`, `lamp` | `door`, `window` |

`door` and `window` are openings as much as objects, usually partly occluded, and their
box extent is genuinely ambiguous — frame included or not? Also watch for whole-scene
boxes and for stacked duplicates (the same sofa returned as both `sofa` and `chair`);
neither is fixed by a confidence threshold.

**Read the number honestly.** Disagreement is not automatically the model's fault — the
human annotators had conventions too, and where the two disagree about whether a door
frame belongs in the box, neither is *wrong*. That ambiguity is exactly why the number
matters: it tells you which classes a machine-labeled dataset would have quietly
degraded, and it is the evidence base for the active-learning review loop in Lesson 06.

**One constraint the agent cannot route around:** there is **no `auto_label` MCP
tool**. Auto Label is a web-app action. The MCP surface offers `annotations_save`,
`annotation_batches_list`, `annotation_batches_get`, and `annotation_jobs_create` —
enough to write annotations and inspect batches, not to trigger Auto Label. An agent
that reports having run it has not; it has described what it would do. This is worth
noticing as a general property of MCP-backed harnesses: tool coverage is never the
whole product surface, and the gap is not always announced.

<details>
<summary><b>Optional — the agent-driven variant, ~0.05 credits</b></summary>

The prompt file also covers a zero-shot labeling loop driven entirely by the
`dataset-engineer` agent: build a Workflow around the YOLO-World block
(`roboflow_core/yolo_world_model@v1`), validate the spec, run it on **10 images**, and
write the results back with `annotations_save`.

It is capped at 10 images because `workflows_run` handles one static image per call and
bills as hosted inference seconds — roughly 0.05 credits at this size. The point is not
the labels. It is watching an agent complete a full read → infer → write loop against a
live platform, including the coordinate-format conversion between what YOLO-World
returns and what `annotations_save` expects. A silent mismatch there writes
plausible-looking garbage into your project, which is why the prompt makes the agent
state both formats before writing anything.
</details>

---

### 11. Review the annotations

**Do:** Have the Dataset Engineer triage before you trust the data:

```
Review the annotation quality of the smart-scene-analyzer project. Use images_search
with RoboQL to find suspect images:
  - images with no annotations at all
  - images with exactly one annotation (suspicious for indoor scenes)
  - images missing the classes I would expect for their content
  - unusually small or large images

Report counts per query with example image IDs. Do not delete or modify anything.
```

RoboQL syntax you will use here (full reference in `roboflow:data-management`):

| Query | Finds |
|---|---|
| `max-annotations:0` | Unannotated images |
| `max-annotations:1` | Sparsely annotated — usually a conversion bug |
| `class:chair` | Images containing a class |
| `-class:chair` | Images *not* containing it |
| `class:chair>=3` | Three or more instances |
| `min-width:1000` | Dimension filters |
| `tag:sun-rgbd` | Filter by source tag |
| `class:chair AND NOT tag:nyu-v2` | Boolean composition |

**You are looking for converter bugs, not model errors.** That is the difference Path A
makes to this step. A spike in `max-annotations:1` means your converter kept only the
first object per record. A pile of `max-annotations:0` means it dropped annotations
silently. Both are code problems with reproducible causes, findable in an afternoon —
unlike "the foundation model missed some lamps", which is not fixable at all.
[`resources/prompts/03-annotation-review.md`](resources/prompts/03-annotation-review.md)
carries the full symptom → cause table.

**Expected result:** a report with counts. Read it before generating a version — after
generation, the version is frozen and a bad one has to be regenerated.

> **Note the constraint in the prompt: "do not delete or modify anything."** Review and
> mutation are separate operations, and separating them is the point. An agent that
> deletes what it judges to be bad annotations has made a curriculum decision on your
> behalf, irreversibly.

> **A note on splits, if you have read about this elsewhere.** Roboflow *rebalances*
> splits during version generation, which is a problem for anyone mixing trusted and
> untrusted labels in one project — they need their verified images pinned to valid and
> test, and it is not documented whether a manual assignment survives generation. Under
> Path A every label came from the same human-annotated source, so the rebalance is
> harmless and the question does not arise. Worth knowing that you dodged it.

---

### 12. Define the taxonomy

**Do:** Copy the template and fill it in:

```bash
cp <path-to-course-repo>/lessons/02-dataset-engineering/resources/templates/taxonomy.md docs/taxonomy.md
```

The taxonomy is a **contract between two datasets that were annotated by different
people with different conventions**. SUN RGB-D and NYU Depth V2 both label indoor
furniture; they do not agree on granularity. One's `night_stand` may be the other's
`table`. Deciding that mapping is engineering judgment, not a code change — which is
exactly why the `data-pipeline` agent is instructed to ask rather than guess.

Fill in the **source-mapping tables**: for each SUN RGB-D label and each NYU label, the
class it maps to, or an explicit decision to drop it. The agent will produce the list of
distinct source labels; the mapping is yours.

**Do:** Enforce it per-version with the **Modify Classes** preprocessing step, which
remaps or omits classes for one version *without mutating the underlying project*. Both
versions can then present a consistent class list while the raw annotations stay
untouched.

> **The mapping table is the artifact that survives.** A reviewer can read it, disagree
> with a row, and change one line. Compare that to the alternative you rejected in step 7,
> where the "mapping" is a text prompt handed to a detector and the only way to audit it
> is to look at the images. Both approaches make the same judgment calls; only one of them
> writes them down.

⚠️ **OPEN — the class list itself.** `docs/taxonomy.md` ships with a nine-class candidate
list and the mapping tables to fill in. Settle it against the two source label sets before
generating a version. This is Notion Open Decision #1.

**Expected result:** `docs/taxonomy.md` with a numbered class list and a completed
source-label mapping table for both datasets.

---

### 13. Generate Dataset Version 1

**Do:** Use [`resources/prompts/02-dataset-version.md`](resources/prompts/02-dataset-version.md),
with `tag:sun-rgbd AND NOT tag:audit` as the source filter — the audit images are a
control group and must stay out of every version.

Recommended configuration — and the reasoning, because the defaults are not neutral:

| Stage | Setting | Why |
|---|---|---|
| Split | 70 / 20 / 10 | Standard. Roboflow rebalances during generation |
| Preprocess | Auto-Orient | Strips EXIF rotation. Skip it and a fraction of your boxes are rotated relative to their images, which is nearly impossible to debug later |
| Preprocess | Resize 640×640, *fit within* | 640 is YOLO11's native input. *Stretch* distorts aspect ratio and teaches the model wrong object proportions |
| Preprocess | Modify Classes | Applies `docs/taxonomy.md` |
| Augment | Flip horizontal | Indoor scenes are not left-right canonical |
| Augment | Brightness ±15%, Exposure ±10% | Indoor lighting varies enormously |
| Augment | Blur ≤ 1px, Noise ≤ 2% | Approximates phone camera capture |
| Augment | 3× max version size | Source plus two augmented copies |

**Do not** apply vertical flip or 90° rotation. Indoor scenes have a gravity direction;
an upside-down sofa is not a real training example and teaches the model that
orientation carries no information.

**Augmentation applies only to the train split.** Roboflow enforces this. Augmenting
validation would inflate your metrics against images that do not exist.

**Ledger:** version generation is 1 credit per 20,000 images — this run is under 0.25.
Record it anyway. ⚠️ It is not documented whether the count is source or
post-augmentation images; at 3× that is a 3× difference on a small line item. Note which
you assumed.

**Expected result:** version 1 exists, with per-split image counts reported.

> **A version is an immutable snapshot.** Changes to the project afterwards do not
> affect it. Always reference it by number in code and docs — never as "the latest".
> This is the property that makes Lesson 06's continuous training auditable.

---

### 14. Repeat for NYU Depth V2 → Version 2

**Do:** The same flow, abbreviated. Convert, upload with `tag:nyu-v2`, review,
generate version 2 filtered to `tag:nyu-v2`, **applying the same taxonomy**.

**NYU is the harder conversion, and it is worth the time.** It ships as a single ~2.8 GB
HDF5 file (`nyu_depth_v2_labeled.mat`) containing per-pixel instance and class maps —
**and no bounding boxes at all**. Boxes must be derived from the instance masks:
connected components per instance ID, then the tight box around each component.

That derivation is the single hardest piece of local data work in this course, and it
costs zero credits. Use
[`resources/prompts/05-nyu-converter.md`](resources/prompts/05-nyu-converter.md), which
mirrors the three-round structure of the SUN RGB-D prompt.

Two things that will cost you an hour if you learn them the hard way:

- **It is a MATLAB v7.3 file, which is HDF5.** `scipy.io.loadmat` will fail on it; use
  `h5py`. The SUN RGB-D `.mat` may be either format — that is why prompt 01 makes the
  agent detect rather than assume.
- **HDF5 stores these arrays transposed** relative to the image orientation you expect.
  Get it wrong and every box is mirrored across the diagonal, which produces valid-looking
  normalized coordinates and a silently ruined dataset. Round 3's pixel-level visual check
  is what catches it.

NYU's labeled subset is ~1,449 images, so no subsampling is needed.

**Why a second dataset at all:** V2 stands in for newly acquired production data.
Lesson 03 fine-tunes model V1 on it and asks whether the result is better — the
domain-adaptation story the whole course is built around. The two datasets must share a
taxonomy or that comparison is meaningless.

> **What you are measuring, and what you have to keep constant.** Two things differ
> between these datasets: the *images* (different sensors, rooms, lighting) and the
> *annotation conventions* (different people, different granularity). Lesson 03 wants to
> measure the first. The taxonomy mapping in step 12 is what holds the second constant —
> which is why both mapping tables have to resolve to the same class list, with the same
> conventions about what a `cabinet` includes.

**Expected result:** version 2 exists, same class list as version 1, tagged distinctly.

---

### 15. Export version 1 for training

**Do:**

```
Export dataset version 1 of smart-scene-analyzer in YOLOv11 format and give me the
download link and the exact SDK snippet to fetch it into ./data/.
```

The agent uses `versions_export`. Then download:

```bash
uv run python -c "
from roboflow import Roboflow
import os
rf = Roboflow(api_key=os.environ['ROBOFLOW_API_KEY'])
project = rf.workspace(os.environ['ROBOFLOW_WORKSPACE']).project('smart-scene-analyzer')
project.version(1).download('yolov11', location='./data/v1')
"
```

**Expected result:** `data/v1/` contains `data.yaml` and `train/`, `valid/`, `test/`
directories, each with `images/` and `labels/`.

**Do:** Confirm it is not tracked by git.

```bash
git status --porcelain data/     # must be empty
```

---

### 16. Write the dataset cards

**Do:**

```bash
cp <path-to-course-repo>/lessons/02-dataset-engineering/resources/templates/dataset-card.md docs/dataset-card-v1.md
```

Fill it in for version 1, then repeat for version 2. The Documentation Agent can draft
from the version metadata, but **you** supply the known-limitations section — that
requires having looked at the images.

Two sections are specific to the path you took:

- **Conversion provenance** — the script, its commit, records in, records out, and
  records skipped by reason. This is what makes a count discrepancy diagnosable in
  Lesson 03 instead of mysterious.
- **Auto-label audit** — the per-class agreement table from step 10, and the prompts
  that produced it.

**Expected result:** two dataset cards recording source, license, acquisition path,
conversion provenance, class distribution, split sizes, preprocessing, augmentation,
audit results, and known biases.

> The limitations section is the one that matters. When Lesson 03's model
> underperforms on a class, the first question is whether the data supported it. A
> card that records "only 47 instances of `lamp`, mostly ceiling-mounted" answers that
> in seconds. A card that omits it costs an afternoon.

---

### 17. Verify the export

**Do:**

```bash
cp <path-to-course-repo>/lessons/02-dataset-engineering/resources/scripts/verify_export.py scripts/
uv run python scripts/verify_export.py data/v1 --taxonomy docs/taxonomy.md
```

**Expected result:** all checks pass.

The script asserts what actually breaks in practice: `data.yaml` classes match
`docs/taxonomy.md` in **both name and order** (YOLO labels are integer indices — a
reordered class list silently mislabels the entire dataset), every image has a label
file, no split is empty, coordinates are normalized within `[0, 1]`, and every class ID
is within range.

---

### 18. Reconcile the ledger and commit

**Do:** Close the loop on the budget before you close the session.

1. Open `app.roboflow.com/<workspace>/settings/usage`.
2. Compare the platform's total against `docs/credit-budget.md`.
3. Update **Remaining** and **Last reconciled**.

**Expected result:** the two totals agree, at roughly **4 credits or less** spent.

**If they do not agree, that is the most valuable output of this lesson.** It means
something billed that you did not model. Find out what, and write it in the ledger's
Notes table. You are carrying that budget through three more lessons, and an unmodeled
cost compounds.

**Do:**

```bash
git add -A
git status          # confirm: no data/, no .env, no raw datasets
git commit -m "Lesson 02: dataset versions 1 and 2, converters, taxonomy, credit budget"
git push
```

**Expected result:** scripts, taxonomy, dataset cards, and the ledger committed. **No
image data.**

---

## Verification

Work through
[`resources/checklists/deliverables.md`](resources/checklists/deliverables.md).

Fast automated pass:

```bash
uv run python scripts/verify_export.py data/v1 --taxonomy docs/taxonomy.md
git status --porcelain | grep -E '^\?\? data/|\.env$' && echo "LEAK" || echo "clean"
```

Platform-side, confirm in the web app or via the agent:

- Both versions exist and their class lists are **identical**
- Per-split counts are non-zero and roughly 70/20/10
- Augmented images appear only in the train split
- The 100 `audit` images are in **neither** version

Budget-side:

- `docs/credit-budget.md` reconciles against the Roboflow usage page
- Spend is at or under 4 credits, leaving 16 for Lessons 03–05
- `.claude/settings.json` prompts before `trainings_create`

The qualitative check: **open twenty random annotated images in the Roboflow UI and
look at them.** Every automated check above passes on a dataset whose boxes are
systematically offset by a fixed amount, or transposed, or mirrored. Only your eyes catch
that, and catching it before training rather than after is worth the ten minutes.

---

## Open items

- ⚠️ **Object taxonomy** (step 12) — the nine-class list and the source-label mapping
  tables for both datasets. Notion Open Decision #1.
- ⚠️ **Free-plan credit allowance unconfirmed.** `roboflow:plans-and-pricing` describes
  the Public plan as "~$60/mo worth included" and gives no credit count. This course
  assumes 20 credits are available. Confirm at `roboflow.com/credits` before relying on
  the budget.
- ⚠️ **Do Universe forks or downloads consume credits?** (step 6) Not stated in the
  skills. A fork materializes images in your workspace and plausibly bills Uploads and
  Storage; a download to your own machine plausibly bills nothing. Negligible either way,
  but unconfirmed.
- ⚠️ **Is version generation billed on source or post-augmentation image count?**
  (step 13) At 3× augmentation the difference is 3× a small line item.
- ⚠️ **Cohort Roboflow plan** — the free Public plan makes data and models public;
  personal free workspaces vs. a shared paid workspace is undecided.

All tracked in the course [`TODO.md`](../../TODO.md).

---

## Further reading

Local skill sources, in `computer-vision-skills/skills/`:

- `data-management/SKILL.md` — upload, tags, splits, versions, RoboQL, MCP tools
- `data-management/labeling.md` — annotation tools, Auto Label, Label Assist,
  batches, jobs, Review mode. The reference for step 10
- `plans-and-pricing/SKILL.md` — credit costs. The reference for step 4
- `inference/workflows.md` — Workflow authoring and the YOLO-World block
- `universe/SKILL.md` — searching Universe, forking datasets
- `product-navigation/SKILL.md` — where each feature lives in the web app

External:

- [Roboflow MCP server](https://mcp.roboflow.com/)
- [SUN RGB-D](https://rgbd.cs.princeton.edu/)
- [NYU Depth V2](https://cs.nyu.edu/~fergus/datasets/nyu_depth_v2.html)
- [Claude Code — MCP](https://docs.claude.com/en/docs/claude-code/mcp)
- [Claude Code — plugins](https://docs.claude.com/en/docs/claude-code/plugins)

**Previous:** [Lesson 01](../01-project-definition-and-system-design/) ·
**Next:** [Lesson 03 — Model Development](../03-model-development/)
