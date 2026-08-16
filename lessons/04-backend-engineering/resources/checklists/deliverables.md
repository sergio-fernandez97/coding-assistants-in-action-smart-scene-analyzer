# Lesson 04 — Deliverables checklist

## Before you start

- [ ] Model V1 weights exist under `runs/`
- [ ] `check_depth_ordering.py` passes on five scenes
- [ ] `docs/credit-budget.md` reconciled
- [ ] The locally trained `best.pt` is on disk — a hosted-only model cannot be exported

## Roles

- [ ] `ml-engineer.md`, `qa.md`, `integration.md` all read
- [ ] You can say which agent owns a quantization bug and which owns a coordinate-space bug
- [ ] The tests were written by `qa`, not by the agent that wrote the code
- [ ] You can state why `mobile` will consume artifacts in Lesson 05 but never re-export them

## Artifact contract — written before the export

- [ ] The **Exported artifact** table in each model card is filled in, marked INTENDED
- [ ] Input shape, dtype, and layout (NCHW vs NHWC) stated
- [ ] Normalization mean and std stated, per channel
- [ ] Output tensor count and order stated — the app decodes positionally
- [ ] Label order has **exactly one** named source of truth
- [ ] The depth field name carries "relative"
- [ ] **No public name contains** `meter`, `metre`, `mm`, `cm`, or `distance`
- [ ] Boxes documented as `xyxy` in absolute pixels of a **named** space
- [ ] The naming constraint is enforced by a test that walks the surface programmatically
- [ ] You can name the observable symptom of each contract row being wrong

## Fusion layer

- [ ] Coordinate spaces established from **real printed output**, on a non-square image
- [ ] `src/smart_scene_analyzer/fusion.py` exists
- [ ] A mismatched depth-map shape **raises** rather than being silently resized
- [ ] Region reduction uses the **median**, justified in the docstring
- [ ] All four degenerate cases defined and documented: zero-area, partly outside,
      entirely outside, empty after clipping
- [ ] No `NaN` can reach a caller — `None` plus a quality flag, in every degenerate case
- [ ] The module is **pure** — no model loading, no file reads, no HTTP, no Roboflow
- [ ] Verified on a real scene: the visibly nearest object has the largest value
- [ ] Ordering is stable when the same scene is given at a different aspect ratio

## Export

- [ ] `scripts/export.py` exists and is re-runnable, with `--force` protection
- [ ] Both artifacts are in `app/assets/models/`
- [ ] Reported tensor shapes were **read back from the exported files**, not from the config
- [ ] Coordinate format (normalized vs input-pixel) determined from data, method stated
- [ ] The int8 **calibration set is named**, and its effect on the parity number acknowledged
- [ ] The depth sign convention (larger = nearer) was verified **on the export**
- [ ] Every contract row reconciled against reality; INTENDED markings removed
- [ ] Where card and artifact disagreed, the **artifact won** and the change was noted
- [ ] Both file sizes recorded in `docs/artifact-budget.md`
- [ ] Any export failure was **reported**, not worked around by changing model or recipe

## Tests

- [ ] `uv run pytest` passes in **seconds**
- [ ] Verified offline by actually hiding the weights, not by reading the code
- [ ] Image fixtures generated in code; **no committed binaries**
- [ ] A known-gradient depth fixture makes fusion assertions exact
- [ ] **The "fusion actually uses the depth map" test exists**
- [ ] All four degenerate box cases covered
- [ ] Boundary cases: empty results, grayscale, 1×1
- [ ] `tests/fixtures/fusion_cases.json` is **plain JSON** a TypeScript suite could load
- [ ] The Python suite loads that same file, so the two can never silently diverge
- [ ] Integration tests carry the `integration` marker and are excluded by default
- [ ] No assertion was loosened to make a test pass

## Export parity

- [ ] Compared against the **original PyTorch weights**, not the export in another runtime
- [ ] Marked `integration`; the default suite still passes with no weights on disk
- [ ] Box IoU tolerance stated and justified, not chosen to fit the results
- [ ] **Per-class** confidence delta reported, not just an aggregate
- [ ] Depth checked by **ordering**, never by comparing values numerically
- [ ] The sign convention asserted on both sides
- [ ] An inverted ranking would fail loudly rather than being negated into agreement
- [ ] Results recorded in the model card
- [ ] A plain ship / do-not-ship verdict was written

## Execution target comparison

- [ ] Every availability claim carries a URL and a check date, not memory
- [ ] Targets unavailable in the iOS Simulator are flagged
- [ ] Silent-fallback behaviour described per target
- [ ] Unmeasurable rows marked **UNMEASURED** — not estimated, not omitted
- [ ] The **cloud rows were kept** as contrast, not deleted
- [ ] Costs stated in both currencies: credits *and* megabytes/device floor/release cycle
- [ ] A default backend recommended per platform, with the device floor it implies
- [ ] The question "could this have pointed back to cloud?" is answered plainly

## Decisions

- [ ] `/adr inference target: ...` — closes the Lesson 01 open decision
- [ ] The ADR's Context contains **numbers you measured**, not a general argument
- [ ] It records that hosted-trained weights are not downloadable on the free plan, and
      therefore **cannot be exported at all**
- [ ] It names what got **harder**: two runtimes, a second fusion implementation, an
      app-store release cycle for model updates
- [ ] It states what would change the decision

## Ledger

- [ ] Lesson 04 spend is 0
- [ ] Running total across Lessons 02–04 at or under 7
- [ ] Reconciled against the Roboflow usage page

## Hygiene

- [ ] `uv run ruff check .` passes
- [ ] `uv run mypy src` passes
- [ ] `git status` shows no `.pt`, no `data/`, no `.env`
- [ ] This returns **nothing**:
      `grep -riE 'depth_m|meter|metre|distance' src/ | grep -v 'NOT metres'`

## The one that isn't mechanical

- [ ] **You photographed a real room with your phone, ran the exported model on it, and
      compared the result against the PyTorch original.**

Every test image so far came from one dataset, one sensor, one set of rooms. The first
genuinely out-of-distribution image tells you more about the system than the entire test
suite — and this is the last cheap chance to learn it before Lesson 06 automates the whole
pipeline.
