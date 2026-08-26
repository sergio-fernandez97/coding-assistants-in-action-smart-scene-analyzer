# Lesson 03 — Retrospective

Written after the first full run-through of this lesson, against a real project, with the
harness live. Everything below is something that actually happened, not something that
might. Each entry names the evidence, the fix, and whether the fix has landed.

The lesson's own rule is that a student who cannot tell whether a step succeeded is
looking at an incomplete step. Several steps here failed that test.

---

## 1. Two commands in the README do not run

**What happened.** Both commands the lesson gives for `check_depth_ordering.py` fail
immediately when typed as written.

| Where | Command | Result |
|---|---|---|
| Step 9 | `check_depth_ordering.py <image> --boxes <detections.json>` | `error: unrecognized arguments: --boxes` |
| Verification | `check_depth_ordering.py data/v1/test/images/<sample>.jpg` | `error: Give an image and at least two --box values` |

The script takes `--box` — singular, repeated, nearest first — or `--cases`. There is no
`--boxes` flag and never was, and an image with no boxes has nothing to compare.

**Why it matters more than a typo.** `CLAUDE.md` requires that every command be runnable
verbatim. A student hitting an argparse error on the *verification* step cannot tell
whether they broke the depth module or the lesson is wrong, and the natural assumption is
that they broke something. This is the most expensive kind of documentation bug: it costs
confidence, not just minutes.

**Fixed.** Both commands corrected, and the lesson now points at a `--cases` file so the
five-scene requirement is a single invocation rather than five.

---

## 2. `data/v1/` does not exist for a student who used one dataset

**What happened.** The run-through used SUN RGB-D only, producing `data/v2/`. The README
and checklist reference `data/v1/` in prerequisites, in the verification block, and in the
depth check. None of those paths resolve.

**The real problem is the assumption, not the path.** The lesson assumes two dataset
versions exist by the time step 9 runs, because steps 4 and 6 built them. With training
moved to homework (§7 below), that assumption is now false *during the session* as well.

**Fixed.** Paths are written against `data/v2/` where a concrete example is needed, and
every step that requires a trained model or a second dataset version is marked as
depending on homework rather than assumed present.

---

## 3. The lesson's own helper crashes on the case it exists to report

**What happened.** `check_depth_ordering.py:131` formats the reduced value:

```python
print(f"    {str(box):<28} {value:>10.4f}")
```

Its `None` check is on line 136, five lines later. `region_relative_depth` returns `None`
by design for a degenerate box — that behaviour is a graded deliverable in this very
lesson — so the script raises `TypeError: unsupported format string passed to
NoneType.__format__` instead of printing the failure it was written to print.

**Confirmed by running it**, not by reading it.

**Why it matters.** The lesson teaches that degenerate boxes must return `None` rather
than `NaN`, and then hands the student a checker that cannot survive a `None`. A student
who does the exercise correctly gets a stack trace.

**Fixed.** The format is guarded and the `None` branch reports the box instead of dying.
Both the lesson copy and the note in step 5 now say what a `None` row means.

---

## 4. A prompt asked for something the harness forbids

**What happened.** `05-depth-inference.md` required the docstring to state:

> larger = nearer, scale is arbitrary, **NOT metres**

`units_guard.py` greps the **entire file content**, not just identifiers, for
`\b(?:meters?|metres?)\b`. Writing the docstring the prompt specified got the write
rejected — in a sentence whose only purpose was to deny metric scale.

**This is the most interesting failure in the lesson and it should not be removed.** The
hook is right: it cannot read intent, and a rule that exempted "but I'm denying it"
exempts every plausible-looking violation. The prompt was wrong to specify wording it had
not tested against the harness that governs it.

**Fixed, deliberately as a teaching moment rather than a silent edit.** The prompt now
asks for the *claim* and leaves the *wording* to the student, and step 5 uses the
collision as the worked example of the lesson's own rule: when a hook blocks you, satisfy
it or stop — never edit it. The phrasing that passes is `Not a distance, in any unit.`

---

## 5. The model-card template cites an ADR that was never written

**What happened.** `resources/templates/model-card.md` says:

> See `docs/decisions/` → *depth scope: inference only*. This is a recorded decision, not
> an oversight.

There is no such file. `docs/decisions/` holds 0001–0004 and none of them is it. The
decision is real and recorded in `docs/requirements.md`, but the template sends the reader
to a file nobody wrote — while asserting it exists.

**Why it matters.** This is precisely the failure the course's "never invent a step" rule
exists to prevent, committed by the course's own template. A confidently wrong reference
is worse than a missing one, because the reader assumes they failed to find it.

**Partly fixed.** The template now cites `docs/requirements.md`, which is where the
decision actually lives, and flags the missing ADR as an open item rather than papering
over it. **Writing the ADR is still open** — see Open items in the README.

---

## 6. The offline suite was not actually offline

**What happened.** `pyproject.toml` declared an `integration` marker and documented that
it existed so slow tests "can be deselected with `-m 'not integration'`". Nothing
deselected them. `addopts` was `-q --strict-markers`, so `uv run pytest` ran everything.

This went unnoticed because the repo had no integration tests until this run-through added
the first one. The moment it did, the default suite tried to download a checkpoint — and
would have failed in CI, on a machine with no weights and no network, which is the exact
scenario `.claude/skills/offline-suite` exists to protect.

**Fixed in the run-through project.** `addopts` now carries `-m "not integration"`.
`template/pyproject.toml` still ships the original and is outside this lesson's scope —
carried in Open items. Verified by breaking it: with
`HF_HOME` empty and `HF_HUB_OFFLINE=1`, the suite passes in under half a second, and the
integration test genuinely fails under the same conditions — so it is not passing
vacuously.

**The general lesson**, which is worth more than the fix: a marker nobody has exercised is
a marker that does not work. The skill's instruction to *verify the offline claim by
breaking it* is there because reading the config is not evidence.

---

## 7. The lesson taught a true statement as if it were a different, false one

**What happened.** The lesson states there is no depth ground truth in this project, so N5
cannot be measured and no depth metric can be reported.

The first half is true about **Roboflow**, which stores images and annotations and not
depth maps. It is false about the **dataset on disk**. SUN RGB-D is an RGB-D dataset:
every capture under `data/SUNRGBD/<sensor>/<capture>/` ships a sensor raster next to the
RGB frame. All 136 test images resolve to their source capture, and the export applied an
aspect-preserving fit with no augmentation to that split — verified by comparing each
exported image against its source and its mirror, not assumed from the export notes.

N5 was measurable the whole time. Measured: **95.4%** over 5,588 pairs.

**Why it matters.** The lesson's stance on depth units is correct and load-bearing, and
this error was standing next to it wearing the same clothes. "No absolute scale exists" is
true. "Therefore nothing can be measured" does not follow, and teaching the two together
trains students to stop looking one step too early. The right lesson is narrower and more
useful: *you cannot calibrate, but you can always check ordering, and you should.*

**Fixed.** Step 7 is the new Reference Depth Calibration step. The dataset-reference
measurement is homework, with `scripts/measure_depth_ordering_rate.py` as its deliverable.

---

## 8. "At least five real scenes" with no scenes and no tooling

**What happened.** Step 9 required the ordering check to pass on five real scenes and gave
the student nothing to build them from: no way to find scenes with usable object pairs, no
box coordinates, no cases file, no worked example. Producing them meant writing an ad-hoc
script to list annotated boxes, rendering the images with the boxes drawn, eyeballing each
one, and hand-writing the JSON. That is 30–40 minutes of undocumented work inside a step
budgeted for a fraction of it.

**Fixed.** The scene-selection helper is folded into the new step 6/7 flow, which uses the
student's own webcam instead — no dataset spelunking, and a scene they can physically
rearrange, which is a better check anyway.

---

## 9. A background agent was killed mid-task and its result was silently queued

**What happened.** The depth work was dispatched to a background `ml-engineer` agent. The
agent was stopped partway through Round 2. Its completion notification landed in the
session queue and was never processed, so the work sat finished-but-unreported: `depth.py`
written and verified, the checking script copied, and nothing run.

**Why it matters for a 90-minute session.** A long-running background agent is a poor fit
for a timeboxed class. If it finishes after the session ends, nobody reads the result; if
it is killed, the state is ambiguous and recovering it means reading a transcript.

**Fixed.** In-session steps are sized to run in the foreground and finish while the
student watches. Anything that takes longer than a few minutes is homework, where a
background agent is the right tool and there is time to read what it produced.

---

## 10. The lesson was scoped at 4–5 hours

**What happened.** The header said "4–5 hours, most of it waiting for training runs." The
sessions are 90 minutes.

**Fixed, and now a standing constraint.** See **Session budget** in the README. The split
is not "cut steps until it fits" — it is that **waiting is not teaching**. Training runs,
which are mostly waiting, are homework. The session keeps the parts that need a room:
decisions with trade-offs, the harness blocking something, and looking at output with your
own eyes.

---

## What worked, and should not be changed

- **The Evaluation Agent having no `Edit` tool.** It held. No evaluation step ever
  proposed a change to training code.
- **`units_guard.py` firing on real code.** It caught a genuine collision (§4) at the
  exact moment the lesson predicts: writing a module about depth, where every natural
  identifier is a metric one.
- **The credit gate.** Zero credits were spent unintentionally across the run-through.
- **Insisting on rendering a depth map and looking at it.** The numbers alone would not
  have distinguished a correctly-ordered map from a structurally broken one.
- **The 30-instance noise floor.** It correctly flagged `door` at 22 instances before
  anyone could build a story on its 9.9% ordering rate — which turned out to measure the
  reference sensor's failure on dark doorways, not the model's.

---

## Still open

- **The depth-scope ADR does not exist** (§5). The template and now the model card both
  point at `docs/requirements.md` instead. Someone should write the ADR.
- **`check_depth_ordering.py`'s `zip()` and f-string lint findings** are unfixed in the
  lesson copy. Cosmetic, but the file is the one students are told to copy verbatim.
- **N5 has a measured value but no target.** `docs/requirements.md` N5 states how it is
  measured and now what it measured; it still does not say what would be good enough.
- **The reference sensor's reliability is unquantified per class.** Doors are ~47%
  hole-filled, TVs ~53%. Those two behave completely differently and nobody has
  characterised why beyond one worked example.
