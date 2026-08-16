# Lesson 05 — deliverables checklist

## Before you start

- [ ] Lesson 04 complete: both artifacts exist in `app/assets/models/`
- [ ] `uv run pytest` passes with no GPU and no weights on disk, **including export parity**
- [ ] The model card's **Exported artifact** table is filled in — input shape, dtype,
      layout, normalization constants, output tensor order, label order
- [ ] Node.js 20+
- [ ] Android Studio with an API 33+ emulator, and/or Xcode 16+ with an iOS 17+ runtime
- [ ] `docs/credit-budget.md` reconciled

## Roles

- [ ] `.claude/agents/mobile.md` read
- [ ] You can state both hard constraints without looking
- [ ] You can say why the role now owns numerics rather than only presentation
- [ ] Nothing under `src/` was edited by the `mobile` agent

## The artifact budget — before bundling anything

- [ ] `docs/artifact-budget.md` copied into the project
- [ ] Both model file sizes recorded, with today's date, **before** the first build
- [ ] A target install size written down before it was measured
- [ ] You can say why a hook cannot enforce this budget the way `credit_gate.py` enforces
      the credit one

## The development build

- [ ] `metro.config.js` includes `tflite` and `pte` in `assetExts`
- [ ] The app builds and launches on at least one simulator
- [ ] A TypeScript edit hot-reloads without a native rebuild
- [ ] You can state why Expo Go cannot run this app
- [ ] `app/ios/` and `app/android/` are gitignored, not committed

## Loading the models

- [ ] Loaded tensor shapes were **read from the runtime** and compared against the model
      card — not assumed from it
- [ ] Any disagreement between the two was reported, not silently accommodated
- [ ] Both models load **once**, cached. No per-image loading
- [ ] Cold load time logged separately for each
- [ ] An explicit loading state is visible to the user
- [ ] **`artifact_drift.py` was observed warning** after a real export-config edit
- [ ] You can explain why it warns while `units_guard` blocks

## Detection

- [ ] The raw output tensor was inspected — shape, length, min/max — **before** any
      decoder was written
- [ ] The coordinate format was determined from the data, not assumed
- [ ] The source format is named in a comment, with how it was determined
- [ ] Boxes are returned in a **named** space, not `number[]`
- [ ] The label order is imported from one place; no inline label array anywhere
- [ ] NMS is **per class**, not global, with the threshold stated
- [ ] NMS tested on both the same-class and the cross-class case
- [ ] Detection count compared against the Python reference

## Depth

- [ ] The image is **letterboxed**, not stretched
- [ ] Preprocessing returns its scale and padding rather than discarding them
- [ ] Tensor layout (NCHW vs NHWC) confirmed against the loaded model
- [ ] Normalization constants come from the model card
- [ ] Ordering verified on a real image with a visible foreground and background
- [ ] The sign convention (larger = nearer) was confirmed, not assumed
- [ ] Any inverted sign was **recorded**, not silently corrected

## The fusion port

- [ ] Fixtures extracted by **running** the Python reference, not by reasoning
- [ ] `tests/fixtures/fusion_cases.json` is plain JSON, loadable by both languages
- [ ] The **Python** suite loads the same fixture file and still passes
- [ ] Median matches the reference, including the even-length case
- [ ] Every degenerate case has a defined result; no `NaN` reaches a caller
- [ ] The suite was **watched failing** before being trusted
- [ ] No fixture was adjusted to make both implementations agree
- [ ] `src/` untouched

## Geometry

- [ ] All six real numbers printed before any transform was written
- [ ] Scale and padding come from preprocessing, not recomputed
- [ ] Exactly one exported transform in `toScreen.ts`
- [ ] Both spaces named in the signature, not `number[]`
- [ ] The letterbox offset is undone explicitly
- [ ] **A non-square test case proves the padding subtraction** — square-only tests pass
      with the bug present
- [ ] Tests assert hand-computed values, not snapshots
- [ ] Boxes land in portrait, landscape, and a second aspect ratio
- [ ] Pure function: no React, no hooks

## Latency

- [ ] A prediction was written down **before** measuring, and left unedited
- [ ] Every phase timed separately
- [ ] **Cold load is in its own table**, not averaged into per-image numbers
- [ ] n ≥ 20 warm runs; p50 and p95 reported, not the mean
- [ ] Device or simulator named exactly, with OS version and build type
- [ ] **Simulator and device figures never share a table**
- [ ] Peak memory with both models loaded is recorded, with the method
- [ ] The dominant phase is named with its share of p95
- [ ] Timing code is gated behind `__DEV__`
- [ ] `docs/requirements.md` N1 is filled in and names its device

## Parity

- [ ] Compared against the **PyTorch reference**, not the exported artifact in Python
- [ ] Every difference classified as preprocessing / decoding / quantization / port
- [ ] The distinguishing test for each category was actually run, not guessed
- [ ] Depth compared by **ordering**, not by value
- [ ] Tolerances stated, with whether they were set before or after seeing the data
- [ ] Untested scope named explicitly
- [ ] A plain verdict — including "not confirmed" if that is the honest answer

## The units rule

- [ ] **`units_guard` was observed blocking** a `depth_meters` write to a `.ts` file
- [ ] The manual grep over `app/src/` was reviewed hit by hit
- [ ] **No distance, unit, or raw depth number reaches the screen**
- [ ] Depth conveyed by ordering and shading, with a "nearer / farther" legend
- [ ] You can state what the hook catches and what it does not — it catches identifiers,
      not prose that separates a unit from its noun

## Reconciliation

- [ ] **Roboflow ledger unchanged** — Lesson 05 spends zero
- [ ] You can say why that zero is now structural rather than disciplined
- [ ] Final artifact and install sizes recorded in `docs/artifact-budget.md`
- [ ] `uv run ruff check . && uv run mypy src && uv run pytest` passes
- [ ] `cd app && npx tsc --noEmit && npm test` passes
- [ ] `git status` clean of `node_modules/`, `*.tflite`, `*.pte`, `app/ios/`,
      `app/android/`, `.env`
- [ ] Committed and pushed

## The check no list can make

- [ ] You took the app somewhere your dataset has never been — **with the network off** —
      and looked at what happened.

That second half should be uneventful. That it is uneventful is the entire point of this
architecture, and it is the one property no test in this list can demonstrate.
