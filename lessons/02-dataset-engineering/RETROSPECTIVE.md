# Lesson 02 — Retrospective from the first live run

**Run date:** 2026-08-13 / 2026-08-14 · **Workspace:** `sergios-workspace-rdowu` ·
**Project:** `smart-scene-analyzer-gc2rv` · **Plan:** free Public

This is the instructor-side record of running Lesson 02 end to end against a real
Roboflow account for the first time. It is not part of the student path. It exists so
that the next cohort does not pay for the same discoveries, and so that the edits made
to `README.md` on 2026-08-14 can be traced back to the thing that caused them.

**Read the [Headline](#headline) and the [Fix table](#what-changed-in-the-lesson) if you
are short on time.** The rest is evidence.

---

## Headline

| | Planned | Actual |
|---|---|---|
| Credits spent | ~4.0 | **0.40** |
| Credits wasted on a mistake | 0 | **~0.16** (a version generated against the wrong source set) |
| Dataset versions generated | 2 (SUN RGB-D, NYU) | 1 usable (SUN RGB-D, version 2 — version 1 was discarded) |
| Steps completed as written | 18 | 12 |
| Steps skipped by decision | 0 | 2 (step 10, step 14) |
| Steps that could not be completed as written | 0 | **4** (steps 1, 4, 9, 13 — see below) |

Two findings dominate everything else:

1. **The lesson's credit model is wrong by an order of magnitude, in the safe
   direction.** The whole lesson costs about **0.4 credits**, not 4. The budget harness
   is still the right pedagogy — but the stated figure has been teaching students that
   dataset work is expensive when the actual lesson of the rate table is that *data
   operations are nearly free and compute is not*. The number now matches the argument.

2. **Every credit actually wasted was wasted on a misunderstanding, not on an expensive
   operation.** 0.16 of the 0.40 went on regenerating a version after I destroyed the
   control group. No forbidden operation was ever attempted; the hooks never had to
   block anything real. The budget was never at risk from the things the lesson warns
   about. It was at risk from ambiguous instructions.

That second point is what reshaped the edits. Hardening beats warning.

---

## Failures, in the order they cost time

Each entry: what happened, what it cost, the root cause, and where it is now fixed.

### F1 — The wrong workspace, and an agent that concluded the work had never happened

**What happened.** A pre-flight agent read the workspace slug out of
`docs/credit-budget.md`, queried it, found zero images, and reported that the upload in
step 9 had never run. The upload had run. The slug in the ledger was a different
workspace belonging to the same person.

**Cost.** ~40 minutes, one dead subagent, and a genuine scare about 1,504 lost uploads.
Resolved only when the student pasted the project URL into the chat.

**Root cause.** Step 1 asks for `ROBOFLOW_WORKSPACE` "from `app.roboflow.com/<workspace-slug>`",
which is right, but nothing ever *verifies* that the slug resolves to the project the
work is happening in. The ledger records a workspace and no project. An account with two
workspaces — which is the normal state after any experimentation — produces a slug that
authenticates fine, lists fine, and is empty.

The compounding failure is the agent's: **zero results were read as "the operation never
happened" rather than "I am looking in the wrong place."** An empty list from a live API
is ambiguous and the agent resolved the ambiguity in the most alarming direction without
saying it was a guess.

**Fixed in:** step 1 now round-trips the slug from the browser URL; step 3 resolves
workspace *and* project and writes both into the ledger; the troubleshooting table gains
a "zero images" row that names the wrong-workspace cause first.

---

### F2 — Step 9 tells you to tag, and gives you a command that cannot tag

**What happened.** Step 9 says "Tag the source at upload time… Tag the SUN RGB-D images
`sun-rgbd`". The command it gives is `uv run roboflow ... import`, which applies no tags.
The images went up untagged. This was discovered at step 13, when
`tag:sun-rgbd` matched zero images and the version filter had nothing to select.

**Cost.** ~30 minutes, plus a scripted back-fill over 1,504 images.

**Root cause.** A **Do** with no runnable command under it, in a lesson whose own style
rule is that every command must be runnable verbatim. The instruction is correct in
intent and impossible as written.

**Fixed in:** step 9 now states plainly that the CLI import does not tag, gives the
back-fill as the normal path rather than the recovery path, and ends with a count query
whose expected result is a number the student can compare.

---

### F3 — The audit holdout: the lesson describes two incompatible designs

**What happened.** This is the expensive one, and the only failure in the run that
destroyed something.

- Step 9 says: "Hold back 100 images for step 10. Upload them **unlabeled**, tagged
  `audit`."
- `resources/checklists/deliverables.md:47` says: "The 100-image audit set is **disjoint
  from the uploaded set**."
- `resources/prompts/02-dataset-version.md:5-8` says the 100 `audit` images must be
  filtered *out* of every version.

Read together, those three do not tell you where the 100 images are at any given moment.
The coherent design — the one now written into the lesson — has the holdout move:
converted to disk in step 7, **not** part of step 9's upload, uploaded and tagged
`audit` only in step 10 where Auto Label needs to reach them, and excluded from every
version by step 13's filter. Their *labels* never leave the disk at all. Because step 10
was skipped in this run, the images were never uploaded, and the only `audit`-tagged
images in the project were the **4** left by a free preview.

I queried `tag:audit`, got **4**, and concluded the tagging step had failed the same way
`sun-rgbd` had. So I selected 100 images from the training pool and tagged them `audit`
— manufacturing a "control group" out of data that was already in the dataset — then
generated version 1 with those 100 excluded.

**Cost.** ~0.16 credits, one discarded dataset version, and roughly an hour: removing
the tags, soft-deleting the version, and regenerating as version 2. The recovery itself
hit a second bug (F6).

**Root cause, two layers.**

*The lesson's:* three files describe the holdout and no two agree on whether those 100
images are in the project. Step 10's UI walkthrough — "Images → Annotate → your `audit`
batch" — reinforces the wrong reading, because it implies a batch of audit images exists
on the platform.

*Mine:* **a count that disagrees with an assumption is evidence about the assumption.**
I had just been burned by F2, so "a tag is missing" was the available explanation and I
took it without checking the other one. `docs/taxonomy.md` said "a 1,500-image upload
**plus** a 100-image audit holdout" in plain language, in a file I had already read.

**Fixed in:** step 7 now carves both sets in one seeded pass and tracks where the
holdout *is* at each step; step 9 says explicitly that `tag:audit` matching 0 (or 4) at
that point is correct; step 10 owns the upload and says so. The prompt file's filter
note is rewritten. A general rule about ambiguous counts is added to step 3.

---

### F4 — Roboflow alphabetizes class names on export, and the course never says so

**What happened.** `docs/taxonomy.md` was numbered in the template's order —
`chair, table, sofa, bed, cabinet, lamp, door, tv`. Roboflow's export wrote
`bed, cabinet, chair, door, lamp, sofa, table, tv`. `verify_export.py` failed with
*"Same class names in a DIFFERENT ORDER. Every label index in this export refers to the
wrong class."*

**Cost.** ~90 minutes: an ADR, a renumber across five files, a converter re-run, and a
verification that the re-run was a pure permutation.

**Root cause.** The word "alphabetical" appears **nowhere in the course repository**.
The course teaches, correctly and at length, that class order is a contract that fails
silently — the taxonomy template has a whole section on it — and then hands the student
a numbered list that the platform will silently renumber. `verify_export.py` catches it
at step 17, which is the right place to catch it and a terrible place to *first learn*
it, because by then a version has been generated and a converter has run.

The sorting is not configurable, and it is the export, not the project, that decides.

**This was the single most valuable thing the run discovered**, because it is a trap that
every student hits and nothing warns about.

**Fixed in:** step 12 now says it before the list is numbered, the taxonomy template
ships alphabetically ordered with the reason stated, and the "append only" rule is
corrected — under alphabetical ordering, adding a class is an *insertion*, which
renumbers, which invalidates every artifact. Recorded as
`smart-scene-analyzer/docs/decisions/0004-class-id-order-follows-the-export.md`.

---

### F5 — `versions_generate` reports a pre-filter image count

**What happened.** The immediate response to `versions_generate` reported
`images: 3261`. The tag filter should have selected 3,021. I announced that the filter
had been ignored and the version was contaminated. It had not been; `versions_get` on
the finished version reported the correct figure. The number in the create response is
the project's image count, before filtering and before augmentation.

**Cost.** ~10 minutes and one wrong statement to the student, corrected in the same turn.

**Root cause.** Undocumented response semantics, believed on sight. The prompt file asks
the agent to report "actual per-split image counts" but does not say *from where*.

**Fixed in:** step 13 and the prompt file both now say the create response is not the
answer, and name `versions_get` as the check.

---

### F6 — Splits, and images that belong to no split at all

**What happened.** During the version-1 recovery, generated splits came out wrong. The
project's images were not distributed across train/valid/test the way generation
assumed, and unannotated images — including the 4 genuine preview images — sat outside
the splits entirely. `datasets_rebalance_splits` had to be called before generation
would produce sane per-split counts.

**Cost.** ~20 minutes.

**Root cause.** Step 11's blockquote — "Roboflow *rebalances* splits during version
generation… the rebalance is harmless and the question does not arise" — is true about
the risk it addresses (mixing trusted and untrusted labels) and misleading about
mechanics. Generation rebalances *within* what it selects; it does not fix a project
whose split assignment is skewed to begin with, and unannotated images are not in the
pool at all.

**Fixed in:** step 13 gains an explicit rebalance-then-verify sub-step before generation,
and the step 11 blockquote is corrected to separate the two claims.

---

### F7 — Offset pagination on `/search` returns duplicate rows

**What happened.** Removing the wrongly-applied `audit` tags by filename matched 64 of
100. Paging `POST /search` with `limit`/`offset` returns overlapping and repeated
records; the project also contains duplicate filenames across distinct image IDs, so
filenames are not a key.

**Cost.** ~25 minutes and one failed cleanup pass.

**Root cause.** Not a lesson bug — the lesson never asks anyone to page the API. It
became relevant only because F3 created work the lesson does not contemplate. Worth
recording because any future scripted cleanup will hit it.

**Rule that resolved it:** key on image `id`, never on `name`, and use a *semantic*
discriminator rather than a list you built earlier. The one that worked: genuine preview
images are unannotated, everything wrongly tagged came from the annotated pool.

**Fixed in:** noted in this document and in the credit ledger's Notes table. No student
step changes.

---

### F8 — A subagent died pulling 1,504 records into context

**What happened.** The first pre-flight agent was asked to inventory the project. It
enumerated every image and exhausted its context.

**Cost.** One wasted agent invocation, ~10 minutes.

**Root cause.** An agent given a live API and a broad question will fetch everything.
The fix is to ask for counts, not records — `images_search` with a RoboQL query returns
a total; step 11 is already written this way and is the model to follow.

**Fixed in:** step 11's framing ("report counts per query with example image IDs") is
now called out as a deliberate pattern rather than incidental phrasing.

---

### F9 — `verify_export.py` scans the whole file for class-ID rows

**What happened.** After renumbering the class list, `verify_export.py` still failed.
The cause was a *second* table in `docs/taxonomy.md` — the step 10 audit-prompt table —
whose first two columns also look like `| <int> | <name> |`. `parse_taxonomy()` scans
every line in the file and keeps the last match per ID, so the audit table silently
overrode the class list.

**Cost.** ~20 minutes chasing a check that was right about there being a problem and
wrong about which table had it.

**Root cause.** The parser is unscoped. It is a verification helper shipped by the
course, so this is the course's bug, not the student's.

**Fixed in:** `resources/scripts/verify_export.py` now parses the `## Class list`
section when one exists and reports which section it used. The whole-file scan remains
as a fallback so existing taxonomies keep working.

---

### F10 — Credit reconciliation cannot be automated on the free plan

**What happened.** Step 4 asks the agent to "Open app.roboflow.com/<workspace>/settings/usage
and tell me my current credit balance". There is no MCP tool and no documented REST
endpoint for usage on this plan. The balance was obtained by the student taking a
screenshot of the dashboard.

**Cost.** ~15 minutes of the agent trying routes that do not exist: five separate
attempts across MCP tools, the REST API, and a WebFetch of an authenticated page.

**Root cause.** A prompt written as if the capability existed. This is the same class of
error step 10 already teaches about — "there is **no `auto_label` MCP tool**… an agent
that reports having run it has not" — applied to a different tool and not noticed.

**Fixed in:** step 4 now tells the student to read the number off the dashboard
themselves, and step 18 says the reconciliation is a human step by construction. The
five dead routes are recorded in the ledger so nobody re-walks them.

---

### F11 — `filter-tags` is real, and I said twice that it was not

**What happened.** I quoted a `filter-tags` parameter from a fetched summary, then
retracted it as a hallucination after failing to find it in the Python SDK docstring, in
`llms-full.txt`, or from Roboflow's own agent. It is a real parameter.

**Cost.** ~15 minutes and two contradicting statements to the student.

**Root cause.** Absence of evidence treated as evidence of absence, twice, across three
sources that are each individually incomplete. Recorded here mainly as a caution: the
Roboflow surface is larger than any single reference document describes, which is
exactly why `CLAUDE.md` says to verify against `computer-vision-skills/skills/` rather
than from memory — and in this case the skills did not have it either.

---

## What was skipped, and what that cost

| Step | Decision | Saved | Given up |
|---|---|---|---|
| **10** — Auto Label audit | Skipped by the student | 1 credit, ~45–60 min | The per-class agreement table. Nothing downstream in Lessons 03–05 reads it; Lesson 06 (unwritten) would have |
| **14** — NYU Depth V2 → version 2 | Dropped entirely | ~2–3 hours | **Lesson 03's entire V1-vs-V2 domain-adaptation comparison.** This is not a small cut |

Both are now marked optional in the README with those consequences stated. The NYU cut
is routed to `TODO.md` as a **blocking** decision for Lesson 03, because Lesson 03 is
marked Ready and is written assuming two dataset versions exist.

---

## What the lesson got right

Worth recording, because the edits below should not damage any of it.

- **The four-layer budget harness (step 4) is the best thing in the lesson** and needs no
  change. The `credit_gate.py` drill — attempt a billed call, watch it be *blocked*
  rather than prompted, add the ledger row, watch it pass — landed exactly as written.
- **Path A over auto-labeling (step 7)** was correct, and the reasoning holds: the run
  cost ~0.4 credits where path D would have cost 20–30.
- **`verify_export.py` earned its place.** It caught F4, which nothing else would have
  caught before Lesson 03's confusion matrix.
- **Splitting `dataset-engineer` from `data-pipeline`** paid off. The platform-side
  mistakes were the irreversible ones, exactly as step 5 predicts.
- **The `qa` agent caught a real defect in code I had written** — `Final[dict]` blocks
  rebinding but not mutation — that I had reviewed and passed.

---

## What changed in the lesson

| Finding | Change | Where |
|---|---|---|
| F1 | Verify the workspace slug against the browser URL; record workspace **and** project in the ledger; new troubleshooting row for "zero images" | README steps 1, 3 |
| F2 | State that CLI import does not tag; give the tagging command; verify with a count | README step 9 |
| F3 | One unambiguous description of the holdout: 100 images, on disk, never uploaded, `tag:audit` matches 4 | README steps 9, 10; prompt 02; checklist |
| F4 | Warn that Roboflow alphabetizes on export, **before** the class list is numbered; ship the template alphabetized; correct the "append only" rule | README step 12; `templates/taxonomy.md` |
| F5 | The `versions_generate` response count is pre-filter; confirm with `versions_get` | README step 13; prompt 02 |
| F6 | Rebalance splits and verify before generating; correct the splits blockquote | README steps 11, 13 |
| F8 | Ask agents for counts, not records | README step 11 |
| F9 | Scope `parse_taxonomy()` to the `## Class list` section | `scripts/verify_export.py` |
| F10 | Reconciliation is a human step; no tool exists | README steps 4, 18 |
| Budget | Stated spend corrected from ~4 credits to **~0.4** | README, throughout |
| Speed | Steps 10 and 14 optional; step 6 compressed | README steps 6, 10, 14 |

**Net effect on the student path:** the required work drops from eighteen steps to
fifteen, and the two longest optional items — a ~2–3 hour HDF5 converter and a ~1 hour
labeling audit — move out of the critical path. The steps that remain gain roughly
sixty lines of verification, because the failures above were all *silent* ones: in every
case the platform returned a plausible number and nothing errored.

---

## The one paragraph worth carrying to Lessons 03–06

Every failure in this run except F8 has the same shape. **A live platform returned a
number, the number was plausible, and the assumption used to interpret it was wrong.**
Zero images meant the wrong workspace, not a failed upload. Four audit tags meant the
design was correct, not that tagging had failed. 3,261 images meant pre-filter, not
contaminated. None of them raised an error, and none of them would have been caught by a
more careful *reading* of the lesson — only by a check that turns the number into
something falsifiable.

That is the argument for the harness, and it is a stronger argument than the credit
budget, which turned out to be in no danger at all.
