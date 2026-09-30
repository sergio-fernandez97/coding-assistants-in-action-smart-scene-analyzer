# Lessons 04–05: recipe evaluation and fix plan

**Project:** `smart-scene-analyzer/`, branch `mobile-dev-ios-path` · **Dates:** 2026-09-29 → 30
**Path taken:** Lesson 04 in full (session remainder + homework); Lesson 05 iOS path, steps
1–12 and 14 on the iOS Simulator. Step 13 (physical iPhone) not yet run.
**Evidence:** [`lesson-04-05-recipe-evaluation.md`](lesson-04-05-recipe-evaluation.md)
(33 findings, time log) · [`lesson-05-screenshots/`](lesson-05-screenshots/) (10 key moments)
**Commits:** `7d934cd` (Lesson 04), `5213df3` (Lesson 05)

---

## Executive summary

Both lessons can be completed, and the end state is what the course promises: two models
running on the handset with no network call, a fusion port that agrees with the Python
reference, and parity with the reference within the project's own tolerances. **They
cannot be completed as written.** A student following the READMEs literally stops at six
separate points: four in homework or prerequisites, two inside the live Lesson 05 session
(step 6).

| | Count | Where they bite |
|---|---|---|
| **Blockers**: cannot proceed as written | 6 | Xcode missing (F1) · L04 depth export (F3) · L05 scaffold (F16), iOS 27 crash (F19), image decode (F22), TFLite offset buffers (F23) |
| **Wrong**: instruction incorrect, workaround exists | 12 | Install lines, runtime APIs, hooks, contract expectations, quantization default |
| **Friction** | 11 | Environment, test isolation, template sync, toolchain |
| **Fine, resolved, or minor** | 4 | Simulator inference verified (F32); the mobile-mcp accessibility catch (F29); version drift (F15); a deprecation (F33) |

The dominant cause is **drift, not design**. The lessons' structure held up: contract
before export, parity as a test, one pipeline for both modes, hooks that block. Nearly
every failure is a fact that changed upstream after the lesson was written: a CLI task
that no longer exists, a runtime API moved to `/legacy`, an Xcode that now crashes the Expo
template, a converter that writes a file format the phone runtime can't read. The course's
own rule, *verify against live docs and cite the date*, is the right rule. These lessons
predate the last round of upstream releases.

**Three findings are worth the whole exercise, because no desktop check catches them:**

1. **The exported detector runs everywhere except the phone (F23).** The LiteRT converter
   stores weights by file offset; the TFLite 2.17 inside `react-native-fast-tflite` loads
   the file and fails every inference. Python on the Mac runs the same file perfectly, so
   Lesson 04's parity test passes and Lesson 05 fails at step 6, in the session. Fixed in
   the export (bit-identical outputs) with a guard test.
2. **The default int8 export fails the project's own parity requirement (F7).** −3.3
   mAP@50 against a 2-point bar; four classes lose over 4 points. w8a16 at the same size
   loses 0.6. The lesson presents int8 as the obvious choice.
3. **Live mode's central rule can't be observed (F26).** Inference is synchronous on the
   JS thread, so the "skip, never queue" counter never moves and the UI freezes during
   analysis. The rule is right; the architecture the prompts produce can't exercise it.

**Time:** Lesson 05's native-build homework took **~2.5 hours** of agent time against a
60-minute timebox. A student without an agent to diagnose the iOS 27 crash and the
dependency conflicts would not finish it. With the fixes below, step 3 becomes
`npm install && npx expo run:ios`.

---

## Fix plan

Ordered by what a cohort hits first. Each package lists its findings, the files to change,
and an effort estimate for one author with an agent. **P0 must land before any cohort;
P1 before the next one; P2 when convenient.**

### P0: blockers students hit in the room

| # | Package | Findings | Change | Files | Effort |
|---|---|---|---|---|---|
| **1** | **Known-good app scaffold in the template** | F16, F17, F19, F25, F28, F33 | Ship `template/app/` with a pinned `package.json` (versions verified in this run), `index.ts`, a blank `App.tsx`, `tsconfig.json` (`"types": ["jest"]`), the jest-expo config, `plugins/withSceneLifecycle.js`, and `app.json` with `"orientation": "default"` and the scene plugin. No `react-native-blob-util` plugin entry. Step 3 becomes `cd app && npm install && npx expo run:ios`. The scaffold is plumbing, not solution code; the student still writes every file under `src/` | `template/app/*`, L05 README step 3, `app/README.md` | 2 h |
| **2** | **Export pipeline that produces files the phone can run** | F3, F23, F4, F2 | Depth: replace `optimum-cli … --task depth-estimation` with the `torch.export` → XNNPACK lowering (~25 lines, already in the student repo). Detection: inline offset buffers after `yolo export`, plus the guard test. `uv sync` with all four extras. MLflow URI `127.0.0.1` | L04 README step 3 + prereq 3, `prompts/03-export-pipeline.md`, `prompts/05-export-parity.md`, template `pyproject.toml` (`export` extra), `.env.example` | 2 h |
| **3** | **Publish the fallback artifacts** | Open items L04 + L05; F5 | This run produced them: the inlined `yolo11n_int8.tflite`, the `.pte`, `labels.json`, and a filled model card. Publish them with their SHA-1 as the course download both lessons already point to. Ends the long-standing ⚠️ OPEN in both READMEs | Course release / download location, L04 + L05 Open items, `TODO.md` | 1 h, plus a hosting decision (see Decisions) |
| **4** | **Rewrite the L05 runtime prompts for executorch 0.10 + image decode** | F21, F22, F14 | Prompts 01/04: `loadModel` / `tensor` / `execute`, `setTelemetryEnabled(false)` as a rule, the `expo-asset` → local-path pattern, no resource-fetcher. Prompt 03 + step 3: the decode step (`expo-image-manipulator` + `jpeg-js`) and why none of the runtimes decode images. Fix the 404 link | `prompts/01-model-loading.md`, `03-detection-decode.md`, `04-depth-inference.md`, L05 README (step 3, Further reading) | 2 h |
| **5** | **iOS toolchain prerequisites that actually prepare the machine** | F1, F15, F18, F20 | Move "install Xcode + iOS runtime (~40 GB)" to **Lesson 04's** prerequisites, a week ahead. Exact remedy commands (`xcode-select`, `-license accept`, `-runFirstLaunch`, `-downloadPlatform iOS`). `brew install cocoapods` + `export LANG=en_US.UTF-8`. `mobilecli agent install` in iOS path §3. Record the verified versions (Xcode 27.0, iOS 27.0, Expo 57.0.26, RN 0.86.3) with the check date | `paths/ios.md`, L04 + L05 Prerequisites | 1 h |

### P1: wrong instructions with a workaround

| # | Package | Findings | Change | Effort |
|---|---|---|---|---|
| **6** | **Fix the two hooks, then every lesson that demonstrates them** | F24, F12 | `artifact_drift.py`: emit `{"systemMessage": …}` (visible) instead of bare stdout, which Claude Code sends only to the debug log. README step 4: "edit `scripts/export.py` with the agent", not `touch`. `notify_done.py`: remove the stale `noqa` so `ruff check .` can be green. Per `CLAUDE.md`, a deliberate hook fix plus an update to every lesson that shows it | 1 h |
| **7** | **Quantization: decide, then say it** | F7 | Either make `quantize=w8a16` the default (passes N3a; calibration ~21 min, so the export stays homework), or keep int8 and make its N3a failure the lesson's worked example of "exported ≠ still the model". **Owner decision**, see below | 1 h after the decision |
| **8** | **One letterbox, in Python too** | F9, F31 | Ship `preprocess/letterbox.py` + `normalize.py` implemented in the template (arithmetic, not pedagogy), and route the reference path and the parity test through them. Parity then compares the same input geometry on both sides | 1.5 h |
| **9** | **Move inference off the JS thread, or stop promising the skip counter** | F26, F27 | Prompt 06: require `wrapAsync`/worklets for decode + preprocess + depth, *or* test the skip rule with fake timers and say the on-screen counter needs off-thread inference. Prompt 08 / step 11: copy the latency template first and write the prediction before measuring | 1.5 h |
| **10** | **Template sync and the ledger** | F6, F11 | L05 step 1 copies `mobile.md` **and** merges the mobile-mcp rules into `settings.json` + `.mcp.json` (or prereq 6 stops duplicating `.mcp.json`). Template `credit-budget.md`: Lesson 04 → 0 credits | 30 min |
| **11** | **Contract expectations, for the instructor** | F8, F5 | `RETROSPECTIVE.md` (L04): the three mismatches students *will* find (float32 NCHW, `/255`, normalized boxes), so step 4 is prepared rather than discovered. Check that L05 prompt 03 doesn't assume the INTENDED values | 30 min |

### P2: friction and polish

| # | Change | Findings | Effort |
|---|---|---|---|
| 12 | `offline-suite` skill: import-isolation assertions run in a subprocess; decide whether `addopts` deselects `integration` | F10 | 30 min |
| 13 | L04 step 6 saves to `captures/l04_<name>`, and step 12 reads from there | F13 | 15 min |
| 14 | Artifact budget: how to measure a thinned device `.ipa`; name the depth model (94.5 of 194 MB) as the lever; note ZXingObjC from `expo-camera` | F30 | 30 min |
| 15 | Close the "Simulator inference viability" open item with this run's numbers; add the mobile-mcp accessibility catch (F29) to step 5 as the worked example | F32, F29 | 30 min |
| 16 | Replace `SafeAreaView` in the scaffold once `react-native-safe-area-context` is accepted as a dependency | F33 | 15 min |

**Total: about 16 hours** for P0 + P1 + P2 (P0 alone: ~8 h), plus the verification run
below.

---

## Decisions only you can make

Each becomes a `⚠️ OPEN` line in `TODO.md` until decided.

| Decision | Options | Recommendation |
|---|---|---|
| **Detection quantization** (package 7) | (a) w8a16 default: passes N3a, same size, 21-min calibration · (b) int8 + N3a failure as the worked example | **(a)**, keeping one paragraph on why int8 failed. A course whose default artifact fails its own requirement teaches that requirements are optional |
| **Expo SDK** (package 1) | (a) stay on SDK 57 + the scene plugin · (b) move to SDK 58, which fixes the crash upstream | **(a) now, (b) at the next revision**. The plugin is verified; SDK 58's availability and its effect on the other native deps are not |
| **App scaffold scope** (package 1) | (a) ship plumbing only (deps, entry, config, plugin) · (b) keep `create-expo-app` as a student step with an exact merge command | **(a)**. The scaffold teaches nothing, and it is where 2.5 hours went |
| **Fallback hosting** (package 3) | A course release asset, or external storage | Whichever the Lesson 02 fallback decision picks, so there is one answer for all three lessons |
| **Screenshots in the README** | 10 screenshots include SUN RGB-D test images | Confirm the dataset licence allows it (already a `TODO.md` item) before publishing them in the lesson README |

---

## Screenshots for the Lesson 05 README

Proposed placement. Each goes in `lessons/05-mobile-client-and-delivery/resources/images/`,
linked from its step in the same edit (the orphan rule).

| Screenshot | Step | What it shows the student |
|---|---|---|
| `01-step3-first-launch-ios27.png` | 3 | Expected result: the dev build runs and hot-reloads |
| `02-step4-models-loaded.png` | 4 | The explicit loading state, with cold-load times |
| `03-step5-picker-open.png` | 5 | mobile-mcp driving the flow (picker state) |
| `04-step6-tflite-run-error.png` | 6 | The error state is its own visible text, and what F23 looks like |
| `05-step6-first-ondevice-detections-portrait.png` | 6–7 | Detections + near-to-far list on the device |
| `06`/`07-step8-…-portrait` / `-landscape.png` | 8 | The same photo in both orientations, boxes on objects |
| `08-step9-live-no-camera-on-simulator.png` | 9 | "No camera" ≠ "permission denied" |
| `09-step9-live-test-double-running.png` | 9 | The test double through the real pipeline |
| `10-step9-live-35-frames-0-skipped….png` | 9 | Only if package 9 keeps the counter; otherwise drop it |

---

## Verification after the fixes

The fixes are only as good as a clean run:

1. Fresh clone of `template/`, a Mac with Xcode 27 and the iOS 27 runtime, following the
   READMEs **literally**, no agent diagnosis. Time every step against its estimate.
2. Pass bar: L04 step 3 produces both files with `scripts/export.py --all`; L05 step 3 is
   one `npm install` + one build; step 6 shows detections first time; `pytest` and
   `npm test` green; parity report within N4.
3. Step 13 on one physical iPhone (still outstanding from this run) and the Android path,
   which this run did not touch at all.

## What this run did not cover

- **Android path:** untested. F16, F17, F21–F23, and F26 almost certainly apply there too; F19 does not.
- **Step 13 (physical iPhone):** pending. Device latency, device memory, airplane mode, and a real camera in live mode are all unmeasured.
- **Roboflow reconcile:** the usage page needs your login (`/mcp` to re-authorize). The ledger records 0 spent for both lessons.
