# Lesson 04 — Export, Quantization & Numerical Parity

> Notion Week 4. Estimated time: 5–6 hours.

## Session goal

Turn two models into two files that run on a phone — and prove they still behave like the
models you trained.

Two roles arrive: `integration` owns the fusion between detection and depth, `qa` owns the
proof that any of it works. `ml-engineer`, which you met in Lesson 03, gains a second job:
export. The split matters because the hardest bug in this lesson lives in exactly one of
those seams. Two models, two coordinate spaces, two resolutions, and one silent mismatch
that produces numbers that look completely reasonable.

The other thread is what export actually costs you. An exported model is not the model you
trained — it is a quantized approximation of it, produced by a toolchain with its own
opinions about tensor layouts. "It loads and runs" is not the same claim as "it still
works", and the distance between those two claims is measured here rather than discovered
in Lesson 05.

## Prerequisites

- [ ] Lesson 03 complete: model V1 (and V2) trained, weights under `runs/`
- [ ] `src/smart_scene_analyzer/depth.py` passing `check_depth_ordering.py`
- [ ] `docs/credit-budget.md` reconciled
- [ ] `uv sync --extra ml --extra depth` runs cleanly
- [ ] The locally trained `best.pt` is on disk — **a hosted-only model cannot be exported**

> **Roboflow credits needed: zero.** Export runs entirely on your machine. Nothing in this
> lesson touches a metered endpoint.

## Deliverables

- [ ] `.claude/agents/ml-engineer.md`, `qa.md`, and `integration.md` in use
- [ ] `src/smart_scene_analyzer/fusion.py` — per-object depth, units stated, pure
- [ ] `scripts/export.py` — reproducible export of both models
- [ ] `app/assets/models/` — the detection `.tflite` and the depth `.pte`
- [ ] `tests/fixtures/fusion_cases.json` — language-neutral fixtures Lesson 05 will reuse
- [ ] A test suite passing with **no GPU, no network, no weights on disk**
- [ ] `tests/test_export_parity.py` — exported artifacts vs the PyTorch reference
- [ ] The model card's **Exported artifact** table filled in
- [ ] `docs/execution-target-comparison.md` — on-device backends, measured
- [ ] An ADR for the inference target, closing the Lesson 01 open decision
- [ ] `docs/artifact-budget.md` started, with both file sizes

Verify with [`resources/checklists/deliverables.md`](resources/checklists/deliverables.md).

---

## Step-by-step

### 1. Meet the roles

**Do:** Read all three definitions.

```bash
$EDITOR .claude/agents/ml-engineer.md .claude/agents/qa.md .claude/agents/integration.md
```

They have overlapping tool lists. The boundary between them is not capability — it is
**responsibility**, and it is drawn where the failure modes differ:

| Role | Owns | Characteristic failure |
|---|---|---|
| `ml-engineer` | Training **and export** | An artifact that runs and no longer matches the model |
| `integration` | Fusing boxes with depth | A coordinate-space mismatch that produces plausible numbers |
| `qa` | Proving it works | A test that passes on the bug it was written to catch |

**Expected result:** you can say which agent owns "the int8 export lost the `lamp` class"
(`ml-engineer` — quantization) and which owns "the depth value is sampled from the wrong
region" (`integration`).

> Lesson 03 split `ml-engineer` from `evaluation` because one agent should not both build
> and grade. The same principle applies here, one layer down: `qa` writes the tests, and
> `qa` did not write the code under test.

> **`ml-engineer` gaining export is deliberate rather than convenient.** Whoever trained
> the model knows what it is supposed to do, and export is where that knowledge is needed.
> Note the boundary this creates with `mobile` in Lesson 05: the app consumes artifacts and
> never re-exports them, so that when the device disagrees with the reference, *which side
> is wrong* stays a question somebody has to answer rather than a thing somebody quietly
> fixes.

---

### 2. Define the artifact contract first

**Do:** Before exporting anything, use
[`resources/prompts/01-artifact-contract.md`](resources/prompts/01-artifact-contract.md)
to decide and write down what the exported models will promise.

For three lessons the models were things you called — a function, a process. Their inputs
and outputs were checked by Python at every boundary. That stops next week.

**An artifact makes promises nothing verifies.** A `.tflite` file does not announce that
its input is NCHW, that its coordinates are normalized, or that class 7 is `lamp`. The app
assumes all of it. A mismatch produces boxes: confident, well-formed, and wrong.

So the contract is written down before the export exists, in the model card:

| Field | Why the app cannot infer it |
|---|---|
| Input shape, dtype, layout | `[1,3,H,W]` float32 and `[1,H,W,3]` uint8 are both plausible and produce garbage when swapped |
| Normalization mean/std | ImageNet-normalized input to a `[0,1]` model yields a smooth, wrong depth map |
| Output tensor count and order | The app decodes positionally |
| Label order | An off-by-one here reads as a model problem for a long time |

**This is the same lesson the response schema used to teach**, moved to where the contract
now lives. The old schema at least had a type system defending it at runtime. This has
nothing — which makes writing it down more important, not less.

**Expected result:** the **Exported artifact** table in your model card is filled in with
what you intend to produce. Step 4 will check the real export against it, and any
disagreement is a finding.

---

### 3. Build the fusion layer

**Do:** Use [`resources/prompts/02-fusion-layer.md`](resources/prompts/02-fusion-layer.md)
with the `integration` agent to write `src/smart_scene_analyzer/fusion.py`.

**This is where the real bugs live.** YOLO11 runs at 640×640. Depth Anything V2 has its
own input size. The source image has a third. Three coordinate spaces, and a box indexed
into the wrong one returns a number — the wrong number, in range, for the wrong region.

**Write it knowing it will be ported.** In Lesson 05 this exact algorithm is reimplemented
in TypeScript to run on the phone, and the two copies are kept honest by shared fixtures.
That makes purity and explicit degenerate cases load-bearing rather than tidy: anything
this function does implicitly is something the port will do differently.

Non-negotiables, all of which the prompt enforces:

- **Reconcile resolutions explicitly.** Never index a depth map with box coordinates
  without having proven they share a space. If the depth map is returned at input
  resolution (as Lesson 03 required), say so and assert it.
- **Median, not mean**, for reducing a box region — an occluder in front of the object
  skews the mean, and box corners routinely contain background.
- **Every degenerate case has a defined result**: zero-area box, box partly outside the
  image, box entirely outside, empty region after clipping. `NaN` reaching a caller is not
  a defined result.
- **Keep it pure.** Arrays and boxes in, structure out. No model loading, no file reads,
  no network. That is what lets `qa` test it exhaustively without a GPU — and what makes
  it portable to TypeScript at all.
- **Fixtures are plain JSON.** Write `tests/fixtures/fusion_cases.json` so that a
  TypeScript suite can load the same cases. A fixture in a pickle or a `.npy` tests half
  the system.

**Expected result:** `fusion.py` with a function taking detections and a depth map and
returning fused results, tested on a real image where you can see that the foreground
object reads as nearer.

---

### 4. Export both models

**Do:** Use [`resources/prompts/03-export-pipeline.md`](resources/prompts/03-export-pipeline.md)
with the `ml-engineer` agent to write `scripts/export.py`.

Two models, two toolchains, two output formats:

```bash
# Detection — Ultralytics to int8 TFLite. int8 needs calibration data.
uv run yolo export model=runs/<run>/weights/best.pt format=tflite int8=True data=<data.yaml>

# Depth — HuggingFace checkpoint to an ExecuTorch .pte
uv run optimum-cli export executorch \
  --model depth-anything/Depth-Anything-V2-Small-hf \
  --task depth-estimation --recipe xnnpack \
  --output_dir app/assets/models/
```

**Do:** Immediately check the real artifacts against the contract you wrote in step 2.

**Expected result:** both files in `app/assets/models/`, their sizes recorded in
`docs/artifact-budget.md`, and the model card's **Exported artifact** table updated with
what the export *actually* produced — not what you intended.

> **Where the two disagree, the artifact wins and the card is wrong.** Exported tensor
> layouts differ between toolchain versions, and the two details most often wrong are
> whether coordinates are normalized or in input-pixel space, and the output tensor
> ordering. Lesson 05 writes a decoder against this table; a wrong row there becomes a
> confidently misplaced box there.

> ⚠️ **Neither command is verified against this project's models.** The formats and flags
> are current as of 2026-08-12, but that YOLO11 exports cleanly to int8 TFLite here, and
> that Depth Anything V2's ViT survives the ExecuTorch recipe at acceptable speed, has not
> been confirmed on a clean machine. If one fails, that failure is the finding — record
> what broke rather than substituting a different model quietly.

---

### 5. Test it properly

**Do:** Use [`resources/prompts/04-test-suite.md`](resources/prompts/04-test-suite.md)
with the `qa` agent, and invoke the `offline-suite` skill.

**The default suite runs with no GPU, no network, and no weights on disk, in seconds.**
That constraint is not about speed; it is about whether the suite runs at all in CI, and
whether anyone runs it locally often enough to notice a break.

Priorities, in order:

- **The fusion layer, exhaustively.** It is pure, so there is no excuse not to. Every
  degenerate case from step 3, plus the signature test: *does this function actually use
  its depth argument?* A fusion that ignores the depth map and returns a constant passes a
  surprising number of naive tests.
- **The artifact contract**, asserted rather than assumed: label order matches the
  taxonomy, and no field name anywhere implies metres.
- **Fixtures generated in code or stored as JSON**, never committed as binaries.

**Expected result:** `uv run pytest` green in seconds. Verify the offline claim rather than
trusting it:

```bash
mv runs runs.hidden && uv run pytest; mv runs.hidden runs
```

---

### 6. Prove the export is still the model

**Do:** Use [`resources/prompts/05-export-parity.md`](resources/prompts/05-export-parity.md)
to write `tests/test_export_parity.py`.

This is the step that separates "the export produced a file" from "the export produced a
model". They are not the same claim, and only one of them is worth shipping.

Run the same fixtures through the exported artifact and through the **original PyTorch
weights**, and compare:

| Model | What must agree | What will not |
|---|---|---|
| Detection | Classes, and boxes within an IoU tolerance | Confidences exactly — int8 shifts them |
| Depth | The **ordering** of near versus far | The values. There is no scale to compare |

**Report the per-class delta, not the aggregate.** int8 quantization can destroy one class
while leaving mAP almost unmoved, and an aggregate number is exactly the wrong instrument
for finding that.

> **Depth parity is an ordering check.** The output has no unit and no scale, so comparing
> magnitudes across two runtimes is meaningless. If the near-to-far ranking survives, the
> export works. If it inverted, say so — do not silently negate it.

**Expected result:** `tests/test_export_parity.py` passing with a stated tolerance, and the
per-class quantization delta recorded in the model card.

---

### 7. Compare the on-device execution targets

**Do:** Use [`resources/prompts/06-execution-target-comparison.md`](resources/prompts/06-execution-target-comparison.md), then

```bash
cp <path-to-course-repo>/lessons/04-backend-engineering/resources/templates/execution-target-comparison.md docs/execution-target-comparison.md
```

An exported model can run several ways on a phone, and they are not interchangeable:

| Target | Available on | Trade |
|---|---|---|
| XNNPACK / CPU | Everywhere | Slowest, and the only one guaranteed to exist |
| Android NNAPI | Android, vendor-dependent | Fast when the vendor implemented it well; silently falls back when not |
| CoreML / ANE | iOS | Fastest on Apple silicon. **Not available in the Simulator** |
| GPU delegate | Both, model-dependent | Good for some ops, worse for others |

**Do:** Keep the cloud rows from the previous architecture in the table, as contrast. The
comparison "0 credits per 1,000 images on-device versus 1 credit per 1,000 hosted" is worth
seeing next to "and the on-device one needs a 40 MB download and excludes phones older than
2021". Neither column is free; they are expensive in different currencies.

**Expected result:** `docs/execution-target-comparison.md` with a recommended default
backend per platform, and the device floor that choice implies.

---

### 8. Close the Lesson 01 open decision

Lesson 01 recorded ⚠️ OPEN: **cloud service vs. on-device ONNX / Core ML / TFLite.** You
now have the evidence to close it — and to close it in the direction Lesson 01 listed as
the hardest.

**Do:**

```
/adr inference target: on-device, TFLite detection and ExecuTorch depth
```

The ADR must state what you learned rather than what you assumed:

- Export works, at a measured cost: the parity tolerance from step 6, and the per-class
  quantization delta
- Both artifact sizes, and what they imply for install size and the device floor
- The execution-target trade from step 7, and the default backend you chose per platform
- On the free plan you cannot download hosted-trained weights — **so a hosted-trained
  model cannot be exported at all**, and local training was never merely the cheaper option
- What would change the decision

**Be honest that this decision costs more than it saves.** It removes a hosting bill and a
network dependency, and in exchange it adds an export toolchain, two native runtimes, a
second implementation of the fusion layer, and an app-store release cycle for what used to
be a deploy. An ADR that lists only the benefits is an advertisement.

**Write the *Revisit when* clause carefully.** Lesson 05 measures on-device latency and
memory on real hardware, so at least one of your trigger conditions is about to fire on
schedule. An ADR whose revisit condition occurs and is never revisited has stopped being a
decision and become a piece of history.

Note also what your step 6 and 7 numbers are and are not. They were measured on your
machine, against exported artifacts, not on a phone. Lesson 05 measures the device, and
the gap between those two is the whole reason step 9 of that lesson exists.

**Expected result:** an ADR whose Context section contains numbers you measured, and whose
Consequences section names what got harder.

> The `/adr` command tells the agent: *"If you do not know why this decision was forced,
> ask me rather than writing a plausible-sounding rationale. A fabricated Context is worse
> than a blank one, because it will be believed."* This is the ADR where that instruction
> pays off — you have real measurements, and the temptation is to write the general
> argument for on-device instead of your specific one.

---

### 9. Reconcile and commit

**Do:**

1. Open `app.roboflow.com/<workspace>/settings/usage`
2. Compare against `docs/credit-budget.md`
3. Update **Remaining** and **Last reconciled**

**Expected result:** Lesson 04 spend is **0** — export runs entirely on your machine.
Running total across Lessons 02–04 unchanged from Lesson 03. Lesson 05 also spends
nothing; Lesson 06 is allocated 4.

```bash
uv run ruff check . && uv run mypy src && uv run pytest
git add -A
git status   # confirm: no *.pt, no *.tflite, no *.pte, no data/, no .env
git commit -m "Lesson 04: fusion layer, model export, quantization parity"
git push
```

---

## Verification

Work through
[`resources/checklists/deliverables.md`](resources/checklists/deliverables.md).

```bash
# Offline, no GPU, no weights on disk, seconds
uv run pytest

# Prove the offline claim rather than trusting it
mv runs runs.hidden && uv run pytest; mv runs.hidden runs

# Quality gates
uv run ruff check . && uv run mypy src

# The artifacts exist and their sizes are recorded
ls -l app/assets/models/

# Nothing leaked
git status --porcelain | grep -E '\.(pt|tflite|pte|onnx)$|^\?\? data/|\.env$' && echo "LEAK" || echo "clean"
```

The check that matters most, and which no command performs:

```bash
grep -riE 'depth_m|meter|metre|distance' src/ | grep -v 'NOT metres'
```

**This must return nothing.** Any identifier implying absolute distance is a bug, because
the project cannot produce one. Lesson 02 decided it, Lesson 03 built it, and this is where
it would be baked into an artifact that ships to a phone.

Then read:

- Every model-card contract row is filled in from the **real** export, not the intended one
- Boxes are documented as `xyxy` in absolute pixels of a **named** space
- The fusion layer has no model loading, file reads, or network calls
- `tests/fixtures/fusion_cases.json` is plain JSON that TypeScript could load
- The parity test states a tolerance and reports per-class deltas
- `docs/execution-target-comparison.md` names a device floor
- The inference-target ADR cites measurements and names what got harder

The qualitative check: **run the exported model on a photo of a real room, and compare it
against the PyTorch original.** Your test images come from one dataset with one sensor. The
first genuinely out-of-distribution image usually tells you more than the whole test suite
— and if quantization hurt a class, this is where it shows up first.

---

## Open items

- ⚠️ **The export commands are unverified against this project's models** (step 4). Formats
  and flags are current as of 2026-08-12, but that YOLO11 exports cleanly to int8 TFLite
  here, and that Depth Anything V2's ViT survives the ExecuTorch recipe at usable speed,
  has not been confirmed on a clean machine. This is the single largest risk in the lesson.
- ⚠️ **The export toolchain is not yet in `pyproject.toml`.** `ultralytics` TFLite export
  and `optimum-executorch` pull large, platform-sensitive dependency trees. Confirm both
  install cleanly on macOS and Linux before a cohort.
- ⚠️ **The int8 calibration set is unspecified.** Using the val split is the obvious default
  and also the one that makes the parity number optimistic. Decide deliberately and say so.
- ⚠️ **MLflow in CI** — Lesson 06 needs CI to read runs it did not create. Carried from
  Lesson 03.
- ⚠️ **Free-plan credit allowance unconfirmed** — carried from Lesson 02.

> **Resolved since this lesson was written:** *mobile app scope*. It is a real app — an Expo
> development build for iOS and Android, running both models on-device, built in Lesson 05
> against the artifact contract you defined in step 2. Which is why that step asks you to
> write the contract down before the export exists: nothing at runtime will check it.

## Further reading

- [Ultralytics — model export](https://docs.ultralytics.com/modes/export/) — TFLite and int8, checked 2026-08-12
- [Optimum ExecuTorch — export guide](https://huggingface.co/docs/optimum-executorch/en/guides/export) — the `depth-estimation` task, checked 2026-08-12
- [ExecuTorch — export and lowering](https://docs.pytorch.org/executorch/stable/using-executorch-export.html) — what `.pte` actually is
- [react-native-fast-tflite](https://github.com/mrousavy/react-native-fast-tflite) — the runtime Lesson 05 loads the detection artifact into
- [React Native ExecuTorch](https://docs.swmansion.com/react-native-executorch/) — the runtime for depth

---

**Next:** [Lesson 05 — On-Device Inference & Mobile Delivery](../05-mobile-client-and-delivery/)
