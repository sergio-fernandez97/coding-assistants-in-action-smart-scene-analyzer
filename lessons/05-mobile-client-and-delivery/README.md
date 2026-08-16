# Lesson 05 — On-Device Inference & Mobile Delivery

> Notion Week 5. Estimated time: 5–6 hours.

## Session goal

Put the system in someone's hand — and put the models in there with it. By the end of this
session both models run on the phone, fused on the phone, with no network call anywhere on
the inference path.

The real subject is not the app. It is the **artifact contract**. For four lessons the
models were things you called: a function, then a process, then a service. Here they become
*files you ship*, and a file cannot be asked what shape it expects. The app assumes an
input tensor layout, an output tensor order, a label ordering, and a pair of normalization
constants. Nothing validates any of them at runtime. Get one wrong and you get boxes —
confident, well-formed, in the wrong place, or named after the wrong class.

Two things surface that no amount of server-side testing produces. The first is
**quantization**: an int8 model is a different model, and "it still runs" is not the same
claim as "it still works". The second is **the device**: memory that a laptop never
noticed, a cold model load the user watches, and a Neural Engine that the simulator does
not have.

## Prerequisites

- [ ] Lesson 04 complete: both models exported, `app/assets/models/` populated
- [ ] `uv run pytest` passes with no GPU and no weights on disk, **including export parity**
- [ ] `docs/artifact-budget.md` exists, with the two model file sizes recorded
- [ ] The model card's **Exported artifact** table is filled in — you will be reading its
      input shape, label order, and normalization constants all session
- [ ] Node.js 20+ — `node --version`
- [ ] **Android Studio** with an API 33+ (Android 13+) emulator — `adb --version`
- [ ] **Xcode 16+** with an iOS 17+ runtime, if you are on a Mac — `xcodebuild -version`
- [ ] `docs/credit-budget.md` reconciled

> **Roboflow credits needed: zero** — and this time it is structural rather than
> disciplined. The app ships with no API key and no network code on the inference path, so
> a metered call is not something you must remember to avoid. It is something you would
> have to add.

> ⚠️ **You need Xcode, Android Studio, or both.** Earlier versions of this course ran the
> client in Expo Go specifically so that no student needed a Mac. On-device inference makes
> that impossible: both ML runtimes are native modules, and Expo Go cannot load native
> modules. **Android-only is a complete path** — the emulator is free, its camera works,
> and nothing in this lesson requires iOS. If you have a Mac, do both.

## Deliverables

- [ ] `.claude/agents/mobile.md` in use
- [ ] `docs/artifact-budget.md` filled in: model sizes, install size, peak memory
- [ ] `app/` — an Expo **development build** running on the iOS Simulator and/or the
      Android Emulator
- [ ] Both models loading and running on-device from `app/assets/models/`
- [ ] `app/src/fusion/` — the TypeScript port, passing the **same fixtures** as the Python
      reference
- [ ] `app/src/geometry/toScreen.ts` — one named function, both coordinate spaces in its
      signature, with tests
- [ ] `docs/latency-report.md` — on-device cold load and per-inference timings, with the
      device and the build type stated
- [ ] `docs/parity-report.md` — the same image through the app and through Python
- [ ] `docs/requirements.md` N1 filled in, no longer a placeholder
- [ ] Both budgets reconciled

Verify with [`resources/checklists/deliverables.md`](resources/checklists/deliverables.md).

## Step-by-step

### 1. Meet the Mobile Engineer

**Do:** Read the role definition. It changed shape in this architecture, and the change is
the point.

```bash
$EDITOR .claude/agents/mobile.md
```

The role used to own presentation: capture a photo, upload it, draw what came back. It now
owns **numerics**. The models run inside its process, the depth tensor is reduced to a
number by its code, and no server is going to catch a mistake in it.

| Constraint | Why it is there |
|---|---|
| **Never claim metric depth** | Unchanged since Lesson 01 — but `units_guard` now blocks it in `app/*.ts` too, because this is where the number is *computed* rather than merely displayed |
| **Do not re-export the models** | The ML Engineer owns the artifacts. When the device disagrees with the reference, that disagreement is the finding — a role that could silently re-export would resolve it by changing whichever side was easier to reach |

**Expected result:** you can state both constraints without looking, and say which hook
enforces which.

---

### 2. Set the artifact budget before you bundle anything

**Do:** Copy the budget into your project and read it.

```bash
cp <path-to-course-repo>/template/docs/artifact-budget.md docs/artifact-budget.md
$EDITOR docs/artifact-budget.md
```

This is the course's third kind of constraint, and it behaves like neither of the others:

| | Roboflow credits | The artifact budget |
|---|---|---|
| How you exceed it | Spend more than you have | Ship a file that is too big |
| What happens | The operation **fails** — `credit_gate.py` refuses | The build fails, or the app crashes **on somebody else's device** |
| Who tells you | A hook, before the money moves | Nobody. A bug report, weeks later |

**Do:** Record the two model sizes now, before either is bundled.

```bash
ls -l app/assets/models/
```

**Expected result:** `docs/artifact-budget.md` has both artifact sizes with today's date,
and you have written down a target install size you have not yet measured.

> **This is the step where the two-runtime decision becomes a number.** This project ships
> `react-native-fast-tflite` *and* `react-native-executorch` — two sets of native
> libraries, because detection went to TFLite and depth went to ExecuTorch. That was a
> deliberate choice with a cost, and this is where the cost stops being theoretical.

---

### 3. Build the development build and bring up a simulator

**Do:** Scaffold the app and install the runtimes.

```bash
mkdir -p app && cd app
npx create-expo-app@latest . --template blank-typescript
npx expo install react-native-fast-tflite react-native-nitro-modules \
                react-native-executorch react-native-executorch-expo-resource-fetcher \
                expo-file-system expo-asset expo-image-picker
```

**Do:** Tell Metro that model files are assets. Without this the bundler silently omits
them and the app fails at load with a missing-file error that names nothing useful.

```js
// app/metro.config.js
const { getDefaultConfig } = require('expo/metro-config');
const config = getDefaultConfig(__dirname);
config.resolver.assetExts.push('tflite', 'pte', 'bin');
module.exports = config;
```

**Do:** Build it. This compiles native code and takes minutes — the first time only.

```bash
npx expo run:android        # to a running API 33+ emulator
npx expo run:ios            # to the iOS Simulator (Mac only)
```

**Expected result:** the app launches on at least one simulator and hot-reloads a text
change without rebuilding.

> **Why a still image, not the live camera.** The iOS Simulator has no camera at all — not
> a poor one, none — and the free workarounds do not cover it. Feeding inference from a
> bundled asset or `expo-image-picker` runs identically on both simulators, costs nothing,
> **and is deterministic**, which is exactly what step 9's parity check needs. Live camera
> capture via `react-native-vision-camera` is the real-device path and is step 10.

> ⚠️ **Simulator inference is unverified.** Whether both runtimes execute in the iOS
> Simulator — which has no Neural Engine — and how far simulator latency diverges from a
> real handset, has not been confirmed on a clean machine. If a runtime refuses to load in
> the simulator, use the Android Emulator and say so in your report. Do not quote simulator
> timings as device timings under any circumstances.

---

### 4. Bundle the models and watch the drift hook fire

**Do:** Load both artifacts and confirm they initialize. Use
[`resources/prompts/01-model-loading.md`](resources/prompts/01-model-loading.md) with the
`mobile` agent.

**Do:** Prove the hook works. Touch the export config and watch what happens.

```bash
touch scripts/export.py
```

**Expected result:** `artifact_drift.py` warns that the bundled artifacts are older than
what produced them — and does **not** block.

This is the same warn-versus-block distinction Lesson 04 raised, pointed at the seam that
exists now:

| Hook | Behaviour | Why |
|---|---|---|
| `units_guard.py` | **Blocks** | Writing `depth_meters` is not legitimate work. There is no version of it that is correct |
| `artifact_drift.py` | **Warns** | Retraining and editing an export config are entirely legitimate. Re-exporting mid-edit would cost minutes of quantization to fix a problem you may be two keystrokes from causing again |

Choosing correctly between *wrong* and *has a consequence* is most of hook design.

---

### 5. Detection on-device

**Do:** Use [`resources/prompts/02-detection-decode.md`](resources/prompts/02-detection-decode.md).

The runtime hands you a raw output tensor. Everything a server used to do for you —
decoding, thresholding, non-maximum suppression — is now yours, in TypeScript.

> ⚠️ **Read the real output layout before writing the decoder.** Open the model card's
> **Exported artifact** table, and if it disagrees with what the tensor actually contains,
> trust the tensor and fix the card. YOLO's exported shape and whether its coordinates are
> normalized or in input-pixel space are exactly the details that change between versions,
> and a decoder written from memory produces boxes that are plausibly wrong.

**Expected result:** a bundled test image produces detections whose classes and rough
positions you can sanity-check by eye.

---

### 6. Depth on-device

**Do:** Use [`resources/prompts/03-depth-inference.md`](resources/prompts/03-depth-inference.md).

Depth has no prebuilt hook in `react-native-executorch` — there is no `useDepthEstimation`.
You use the generic `ExecutorchModule`, which loads a `.pte` and runs
`forward(TensorPtr[]) → TensorPtr[]`. Preprocessing and postprocessing are yours.

That is more work than the detection path and it is the honest shape of the problem: the
library ships hooks for the tasks it has models for, and this is not one of them.

**Expected result:** a depth map whose values rank a foreground object nearer than the wall
behind it. **Ordering is the only property you can check**, because the output has no unit
and no scale — which is the whole reason `units_guard` exists.

---

### 7. Port the fusion layer, and keep it honest

**Do:** Use [`resources/prompts/04-fusion-port.md`](resources/prompts/04-fusion-port.md).

`src/smart_scene_analyzer/fusion.py` is the reference. `app/src/fusion/` must reproduce it
**on the same fixtures** — median reduction, every degenerate box case, no `NaN`.

Two implementations of one algorithm is a standing correctness risk, and the shared fixture
set is the only thing that makes it survivable.

> **If the port and the reference disagree, that disagreement is the finding.** Do not edit
> the fixtures until both pass. A fixture adjusted to make two implementations agree
> destroys the only signal this arrangement produces.

**Expected result:** the same fixtures pass under `uv run pytest` and under `npm test`.

---

### 8. Coordinate spaces — three, not four

**Do:** Use [`resources/prompts/05-overlay-geometry.md`](resources/prompts/05-overlay-geometry.md).

| Space | Units | Notes |
|---|---|---|
| Source image | pixels | What the picker or camera gave you |
| **Model input** | pixels | Letterboxed to a square. Has a scale factor **and an offset** — the offset is what people forget |
| Screen | density-independent points | Not pixels. Varies per device |

The upload space is gone; the letterbox space replaced it. That is not simpler, it is
differently shaped: an uploaded image was uniformly scaled, and a letterboxed one has bars.
A transform that ignores the offset is correct exactly when the image is already square.

**Do:** Write it as **one named function** in `app/src/geometry/toScreen.ts` with both
spaces in its signature, and unit-test it against hand-computed values.

**Expected result:** boxes land on objects at more than one aspect ratio. Test with a
portrait image and a landscape one.

---

### 9. Measure on-device, and separate the phases

**Do:** Use [`resources/prompts/06-latency-measurement.md`](resources/prompts/06-latency-measurement.md), then

```bash
cp <path-to-course-repo>/lessons/05-mobile-client-and-delivery/resources/templates/latency-report.md docs/latency-report.md
```

Measure five phases separately, over at least 20 runs:

| Phase | Why separately |
|---|---|
| **Cold model load** | Once per launch, seconds long, and the user watches it. It is not part of the per-image distribution and averaging it in hides both numbers |
| Preprocess | Decode, letterbox, normalize — pure CPU, and often larger than people expect |
| Detection | |
| Depth | The ViT is usually the expensive one. Knowing *which* model dominates is what tells you where to spend effort |
| Fusion + render | |

**Do:** Also record peak memory with both models loaded. That figure decides which phones
are excluded, and it is the one nobody measures until a crash report arrives.

**Expected result:** `docs/latency-report.md` with p50/p95 per phase, the device or
simulator named, and the build type stated. Then fill in N1 in `docs/requirements.md`.

> **Simulator numbers are not device numbers.** The iOS Simulator runs on your Mac's CPU
> and has no Neural Engine. Report them in separate tables or not at all.

---

### 10. Parity — the device against the reference

**Do:** Use [`resources/prompts/07-parity-check.md`](resources/prompts/07-parity-check.md), then

```bash
cp <path-to-course-repo>/lessons/05-mobile-client-and-delivery/resources/templates/parity-report.md docs/parity-report.md
```

Run **the same bundled image** through the app and through `src/`. Compare the classes, the
boxes, and the depth *ordering*.

This is the strongest artifact in the lesson, and it exists only because the model moved.
When the two disagree you have four candidates, and telling them apart is the skill:

| Candidate | Typical signature |
|---|---|
| **Preprocessing** | Boxes systematically offset or scaled — a letterbox or normalization mismatch |
| **Decoding** | Boxes plausible but classes wrong, or confidences oddly distributed — label order or tensor order |
| **Quantization** | One or two classes degraded, everything else fine |
| **The port** | Detections identical, depth values differ — fusion, not inference |

**Expected result:** `docs/parity-report.md` naming which of the four you found, or stating
the tolerance within which they agree.

---

### 11. Optional — the live camera, on a real device

**Do:** Add `react-native-vision-camera` and drive inference from frames rather than a
picked image.

This is optional and it is real-device work: the iOS Simulator has no camera, and the
Android Emulator's VirtualScene is a rendered room rather than a scene your model has
opinions about. Everything before this step stands without it.

---

### 12. Reconcile and commit

**Do:**

1. Confirm the Roboflow ledger is **unchanged** — this lesson spends zero.
2. Record final artifact and install sizes in `docs/artifact-budget.md`.
3. Run everything:

```bash
uv run ruff check . && uv run mypy src && uv run pytest
cd app && npx tsc --noEmit && npm test; cd ..
git status   # confirm: no node_modules/, no *.tflite, no *.pte, no app/ios/, no app/android/
```

**Expected result:** both suites green, and a `git status` containing no build outputs.

## Verification

- [ ] The app launches on a simulator and runs both models from bundled artifacts
- [ ] `artifact_drift.py` was **observed** warning after a real export-config edit
- [ ] `units_guard.py` was **observed** blocking a `depth_meters` write to a `.ts` file
- [ ] The TypeScript and Python fusion suites pass the same fixtures
- [ ] Boxes land correctly in portrait **and** landscape
- [ ] Zero detections renders as a success, distinguishable from "model failed to load"
- [ ] Peak memory with both models loaded is recorded
- [ ] Cold load is reported separately from per-inference latency
- [ ] Simulator and device figures are never mixed in one table

The manual units check, now a backstop rather than the only defence:

```bash
grep -riE 'meter|metre|\bcm\b|\bmm\b|distance|away|feet|inches' app/src/
```

Review it hit by hit. `units_guard` catches the identifiers; it does not catch prose that
separates a unit from its noun — "roughly 2 m away" passes the hook and fails this grep.
That gap is known and recorded in `TODO.md`.

**And the check no list can make:** take the app somewhere your dataset has never been, and
turn off the network first. The second half is new, and it should be uneventful — that it
is uneventful is the entire point of this architecture.

## Open items

- ⚠️ **Simulator inference viability** (step 3) — whether both runtimes execute in the iOS
  Simulator, and how far simulator latency diverges from a handset. Unverified.
- ⚠️ **Two native ML runtimes in one binary** (step 2) — measured app size and build
  stability on both platforms. If the combined size proves unacceptable, consolidating onto
  one runtime is the fix, and both directions are unverified.
- ⚠️ **Xcode / Android Studio as per-student prerequisites** — this replaces the deleted
  "no Mac required" promise and is a real accessibility regression. Android-only works;
  whether that is an acceptable supported path for a cohort is not decided.
- ⚠️ **The device floor** — `react-native-executorch` requires iOS 17+ / Android 13+. The
  memory ceiling measured in step 9 will move that upward, and nobody has measured it.
- ⚠️ **Instructor dry run** on one clean machine, both simulators, and one real device per
  platform. The figures in this lesson are arithmetic and documentation, not measurement.

All tracked in the course `TODO.md`.

## Further reading

- [React Native ExecuTorch — getting started](https://docs.swmansion.com/react-native-executorch/docs/fundamentals/getting-started) — checked 2026-08-12
- [`ExecutorchModule` — generic model execution](https://docs.swmansion.com/react-native-executorch/docs/typescript-api/ExecutorchModule) — the depth path
- [react-native-fast-tflite](https://github.com/mrousavy/react-native-fast-tflite) — v3.0.1, checked 2026-08-12
- [Expo — development builds](https://docs.expo.dev/develop/development-builds/introduction/) — why Expo Go cannot run this app
- [Ultralytics — TFLite export](https://docs.ultralytics.com/modes/export/)

---

**Next:** Lesson 06 — CI / CD / CT *(not yet written; its deploy half needs redesign — see
`TODO.md`)*
