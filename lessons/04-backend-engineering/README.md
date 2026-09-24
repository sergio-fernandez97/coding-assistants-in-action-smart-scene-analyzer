# Lesson 04 — Export, Quantization & Numerical Parity

> Notion Week 4. **Session: 90 minutes.** Homework: about 1h 45m before, 1h 30m after.

## Session goal

Turn your two models into two files a phone can run — and prove they still behave like the
originals.

"It exported" and "it still works" are different claims. This lesson measures the gap.

**Roboflow credits: zero.** Everything runs on your machine.

| When | Steps | Time |
|---|---|---|
| Before the session | 1–3 | ~1h 45m |
| **In the session** | 4–8 | **85 min** |
| After the session | 9–13 | ~1h 30m |

## Prerequisites

Do these in order, before the session.

1. **Do:** Check your detector weights from Lesson 03.
   **Command:** `ls runs/detect/runs/v1-baseline/weights/best.pt`
   **Expected result:** the file is listed. Weights trained on Roboflow's hosted service
   cannot be downloaded on the free plan, so they cannot be exported.
   ⚠️ **OPEN — no weights of your own:** see [Open items](#open-items).

2. **Do:** Confirm the depth module still orders near and far correctly.
   **Command:** `uv run python scripts/check_depth_ordering.py --cases <cases>.json`
   (`<cases>` is the file you made in Lesson 03 step 5.)
   **Expected result:** exit code 0 and every case `PASS`.

3. **Do:** Install the extra dependencies.
   **Command:** `uv sync --extra ml --extra depth`
   **Expected result:** finishes with no errors.

4. **Do:** Steps 1–3 below, **in that order**. Step 2 must be committed before step 3 runs.
   **Expected result:** the model card's **Exported artifact** table is committed, and two
   model files exist in `app/assets/models/`.

## Deliverables

- [ ] `src/smart_scene_analyzer/fusion.py` — pure, units and coordinate spaces stated
- [ ] `tests/fixtures/fusion_cases.json` — plain JSON, reused by Lesson 05's TypeScript tests
- [ ] `scripts/export.py` — exports both models, reproducibly
- [ ] `app/assets/models/` — the detection `.tflite` and the depth `.pte`
- [ ] `scripts/check_fusion_live.py` — written by you, imports the fusion layer
- [ ] A test suite that passes with **no GPU, no network, no weights on disk**
- [ ] `tests/test_export_parity.py` — exported files vs. the PyTorch originals
- [ ] Model card: **Exported artifact** table and **Known failure modes** filled in
- [ ] `docs/artifact-budget.md` — both file sizes
- [ ] `docs/execution-target-comparison.md` — on-device backends, with a device floor
- [ ] Your inference-target ADR amended with measured numbers

Check them with [`resources/checklists/deliverables.md`](resources/checklists/deliverables.md).

---

## Step-by-step

## Part 1 — Before the session

### 1. Meet the three roles · 15 min

**Do:** Read the three agent definitions.

```bash
$EDITOR .claude/agents/ml-engineer.md .claude/agents/qa.md .claude/agents/integration.md
```

| Role | Owns | Typical failure |
|---|---|---|
| `ml-engineer` | Training **and export** | A file that runs but no longer matches the model |
| `integration` | Combining boxes with depth | Reading depth from the wrong region — the number still looks fine |
| `qa` | Proving it works | A test that passes on the bug it should catch |

`qa` tests code it did not write — the same reason Lesson 03 split `evaluation` from
`ml-engineer`.

**Expected result:** you can answer in one sentence each:
- "The int8 export lost the `lamp` class" → `ml-engineer`
- "Depth is read from the wrong region" → `integration`

### 2. Write the artifact contract — before exporting · 45 min

**Do:** Use [`resources/prompts/01-artifact-contract.md`](resources/prompts/01-artifact-contract.md)
with `ml-engineer`. Fill the model card's **Exported artifact** table with what you
*intend* to produce. Mark every value `INTENDED`.

![Step 2 writes the Exported artifact table with every value marked INTENDED and commits it; step 3 exports a .tflite and a .pte; step 4 diffs the table against the real files, and where they disagree the file is right. Lesson 05 writes its decoder from the table. Swap steps 2 and 3 and the card just copies the file, so the diff finds nothing.](resources/images/contract-before-export.svg)

A model file does not say what it expects. The app has to assume it, and a wrong guess
gives you boxes that look right and are not.

| Field | What goes wrong if the app guesses |
|---|---|
| Input shape, type, layout | `[1,3,H,W]` float32 vs `[1,H,W,3]` uint8 — swapped, you get garbage |
| Normalization | Wrong mean/std gives a smooth, wrong depth map |
| Output order | The app reads outputs by position |
| Label order | Off by one, and it looks like a model problem for weeks |

**Given, not decided by you:** detection input is **640×640**, depth input is **518×518**,
both letterboxed. Depth Anything V2 needs a multiple of 14, and 640 is not one. The
details are in `docs/architecture.md` §2.

**Also decide here:** which images int8 calibration uses. Write it down.
⚠️ **OPEN** — see [Open items](#open-items).

**Label order has one source of truth**: `docs/taxonomy.md`. If your weights came from
somewhere else, compare their class list to it now:

```bash
uv run python -c "from ultralytics import YOLO; print(YOLO('<weights>').names)"
```

(`<weights>` is the path from Prerequisite 1.)

**Expected result:** the table is filled in, marked `INTENDED`, and committed. The class
list printed above matches `docs/taxonomy.md` in the same order — or you have written down
that it doesn't.

### 3. Export both models · 45 min

**Do:** Use [`resources/prompts/03-export-pipeline.md`](resources/prompts/03-export-pipeline.md)
with `ml-engineer` to write `scripts/export.py`. It runs these two commands:

```bash
# Detection → int8 LiteRT (.tflite). int8 needs calibration images.
uv run yolo export model=<weights> format=litert quantize=8 data=<data.yaml>

# Depth → ExecuTorch (.pte)
uv run optimum-cli export executorch \
  --model depth-anything/Depth-Anything-V2-Small-hf \
  --task depth-estimation --recipe xnnpack \
  --output_dir app/assets/models/
```

`<weights>` is your `best.pt`. `<data.yaml>` points to your calibration images from step 2.

> Ultralytics renamed TFLite to **LiteRT** in 8.4.83. The old `format=tflite int8=True`
> still works but prints a deprecation warning. Checked 2026-09-24 against the
> [Ultralytics export docs](https://docs.ultralytics.com/modes/export/) and version 8.4.118.

**Do:** Record both file sizes in `docs/artifact-budget.md`.

**Expected result:** a `.tflite` and a `.pte` in `app/assets/models/`, sizes recorded.
If an export fails, write down what broke — that is a finding, not a failure.
⚠️ **OPEN — no ready-made fallback files yet:** see [Open items](#open-items).

---

## Part 2 — In the session

### 4. Contract vs. reality · 10 min

**Do:** Open your step 2 contract next to what step 3 actually produced. Ask
`ml-engineer` to read the real input/output shapes, types, and label order from both
files and compare them with your table.

**Expected result:** a list of every mismatch. Update the table to match the file. **Where
they disagree, the file is right and the card is wrong.** Lesson 05 writes its decoder from
this table.

### 5. Build the fusion layer · 30 min

**Do:** Use [`resources/prompts/02-fusion-layer.md`](resources/prompts/02-fusion-layer.md)
with `integration` to write `src/smart_scene_analyzer/fusion.py`.

There are four coordinate spaces: the source image, the 640 detection square, the 518
depth square, and the screen. A box read in the wrong one returns a wrong number that
still looks normal. Lesson 03's [raster diagram](../03-model-development/resources/images/depth-raster-spaces.svg)
showed two of them; here are all four.

![The source image is letterboxed to 640×640 for YOLO11 and to 518×518 for Depth Anything V2. Boxes are rescaled and the depth map is resized back into one space before fusion: source pixels in Python, the 640 model input on the handset. Fusion takes the median per box and converts nothing; a 518×518 map reaching it raises. The Lesson 05 overlay draws the result in screen points.](resources/images/fusion-coordinate-spaces.svg)

Rules the prompt enforces:

- **Fusion works in source-image pixels only.** Depth is resized back before fusion. A
  518×518 map arriving here is a bug — raise an error naming both shapes.
- **Use the median, not the mean,** over the box. Box corners often contain background.
- **Every edge case has a defined result:** zero-size box, box partly or fully outside the
  image, empty region. `NaN` is not a result.
- **Keep it pure:** no model loading, no files, no network. That makes it testable, and it
  gets ported to TypeScript in Lesson 05.
- **Fixtures are plain JSON** in `tests/fixtures/fusion_cases.json`, so TypeScript can load
  the same cases.

![A loose box around a bright near chair has dark far wall in its corners. The depth values inside the box form two clusters; the mean falls in the empty gap between them, a value no pixel has, while the median lands on the chair. Two clusters in one box is what a mixed_region flag reports.](resources/images/median-vs-mean-box.svg)

**Expected result:** `fusion.py` returns one depth value per box. On a real photo, the
object in front reads as nearer.

### 6. Point it at your own room · 12 min

**Do:** Use [`resources/prompts/07-live-check.md`](resources/prompts/07-live-check.md) with
`integration` to **write** `scripts/check_fusion_live.py` (about 50 lines). It must
**import** `fuse_detections_with_depth` — a checker that re-implements the thing it checks
proves nothing. Then run it:

```bash
uv run python scripts/check_fusion_live.py --camera 0
```

Using a phone camera (Continuity Camera shows up as another index)? It needs more frames to
focus — the same `--warmup 90` fix as Lesson 03 step 6.

This is Lesson 03 step 6 again, now through your fusion layer. **Re-run a frame that went
wrong in `docs/live-validation.md`** — for example, a big box whose depth came mostly from
the wall behind it. Check three things:

1. **Boxes:** right objects? Anything missed?
2. **Near-to-far order** — not the values. The values have no unit.
3. **Quality flags:** `mixed_region` means the box covers two depths. Lots of them usually
   means loose boxes, not broken depth.

**Expected result:** an annotated PNG, a depth PNG, and a near-to-far table. You can name
one weakness you saw with your own eyes.

**Optional:** a live version, provided ready to run:

```bash
cp <path-to-course-repo>/lessons/04-backend-engineering/resources/scripts/watch_fusion_live.py scripts/
uv run python scripts/watch_fusion_live.py --camera 0
```

**Expected result:** a live view at `http://127.0.0.1:8000`, showing how old the depth
map is. `--depth-every 1` makes it exact and slow.

### 7. Test the fusion layer · 13 min

**Do:** Use [`resources/prompts/04-test-suite.md`](resources/prompts/04-test-suite.md) with
`qa`, and invoke the `offline-suite` skill.

Priority: fusion first, every edge case from step 5. Plus one test that catches a fake:
**does the function actually use the depth map?** A fusion that ignores depth and returns
a constant passes many naive tests.

**Expected result:** `uv run pytest` green in seconds, with no GPU, network, or weights.

### 8. Prove the export is still the model · 15 min

**Do:** Use [`resources/prompts/05-export-parity.md`](resources/prompts/05-export-parity.md)
to write `tests/test_export_parity.py`. Feed the same images to the exported file and to
the original PyTorch model.

| Model | Must agree | Won't match exactly |
|---|---|---|
| Detection | Classes, and boxes within an IoU tolerance | Confidences — int8 shifts them |
| Depth | Near-to-far **order** | The values — there is no scale |

**Report the change per class, not one average.** int8 can wreck one class while the
average barely moves. If depth order comes out [inverted](../03-model-development/resources/images/depth-sign-convention.svg), say so — don't quietly flip it.

**Expected result:** the test passes with a stated tolerance. The per-class change is in
the model card.

---

## Part 3 — After the session

### 9. Finish the test suite · 30 min

**Do:** Add tests for the artifact contract: label order matches `docs/taxonomy.md`, and no
field name implies metres. Then prove the suite really is offline:

```bash
mv runs runs.hidden && uv run pytest; mv runs.hidden runs
```

**Expected result:** `pytest` green with `runs/` hidden.

### 10. Compare the on-device backends · 30 min

**Do:** Use [`resources/prompts/06-execution-target-comparison.md`](resources/prompts/06-execution-target-comparison.md),
starting from the template:

```bash
cp <path-to-course-repo>/lessons/04-backend-engineering/resources/templates/execution-target-comparison.md docs/execution-target-comparison.md
```

| Backend | Runs on | Trade-off |
|---|---|---|
| XNNPACK / CPU | Everywhere | Slowest, but always there |
| Android NNAPI | Android, depends on vendor | Fast when supported; quietly falls back when not |
| CoreML / ANE | iOS | Fastest on Apple chips. **Not in the Simulator** |
| GPU delegate | Both, depends on model | Good for some operations, worse for others |

Keep the old cloud option as a comparison row: 0 credits on-device vs. 1 credit per 1,000
images hosted — but on-device means a bigger download and a minimum phone age.

**Expected result:** the file names a default backend per platform and the oldest phone
that choice supports.

### 11. Amend your inference-target ADR · 20 min

The decision is already made: on-device (see `CLAUDE.md` → *Decisions on record*). Now add
the numbers you measured.

**Do:** Open the ADR `CLAUDE.md` points to and add:

- The parity tolerance and per-class quantization change (step 8)
- Both file sizes, and what they mean for install size and device floor
- The default backend per platform (step 10)
- What got **harder**: an export toolchain, two native runtimes, a second copy of the
  fusion layer, app-store releases
- **Revisit when:** Lesson 05 measures the real phone. Say what result would reopen it.

Don't write general arguments for on-device — write your numbers. They came from your
laptop, not a phone.

**Expected result:** the ADR's Context has your measured numbers, and its Consequences say
what got harder.

### 12. Write the known failure modes · 20 min

**Do:** In `docs/model-card-v1.md`, fill **Known failure modes** from the frames you ran
in step 6: class, what went wrong, which frame, and whether it is DATA, TAXONOMY, MODEL, or
EXPORT.

**Expected result:** the section is filled, with one saved annotated frame as evidence.

### 13. Reconcile and commit · 10 min

**Do:** Open `app.roboflow.com/<workspace>/settings/usage`, compare with
`docs/credit-budget.md`, and update **Remaining** and **Last reconciled**.

**Expected result:** Lesson 04 spent **0** credits.

**Do:** Run the checks and commit.

```bash
uv run ruff check . && uv run mypy src && uv run pytest
git add -A
git status   # no *.pt, *.tflite, *.pte, data/, .env, or personal photos
git commit -m "Lesson 04: fusion layer, model export, quantization parity"
```

**Expected result:** all checks green, and a commit with no model files, data, or secrets.

---

## Verification

Work through [`resources/checklists/deliverables.md`](resources/checklists/deliverables.md), then:

```bash
uv run pytest                                   # offline, seconds
mv runs runs.hidden && uv run pytest; mv runs.hidden runs
uv run ruff check . && uv run mypy src
ls -l app/assets/models/                        # both files, sizes in artifact-budget.md
git status --porcelain | grep -E '\.(pt|tflite|pte|onnx)$|^\?\? data/|\.env$' && echo "LEAK" || echo "clean"
grep -rnsE 'depth_m\b|_meters?\b|_metres?\b' src/ app/src/   # must print nothing
```

**Expected result:** tests green, `clean`, and the last command prints nothing — the
project cannot measure distance, so no name may suggest it.

Then read your own work:

- Every contract row comes from the **real** export
- Boxes are `xyxy` in absolute pixels of a **named** space
- `fusion.py` loads no model, reads no file, calls no network
- The parity test states a tolerance and reports per class
- The execution-target comparison names a device floor
- The ADR cites measurements and names what got harder

Last check: run the exported model on a photo of your own room and compare it with the
PyTorch original. If int8 hurt a class, this is where you'll see it first.

---

## Open items

- ⚠️ **No fallback export files yet** (steps 3, 4). If an export fails at home, the student
  arrives with nothing for step 4. A ready-made `export.py` and both pre-exported files
  need publishing as a course download before a cohort.
- ⚠️ **No fusion skeleton yet** (step 5). 30 minutes assumes students fill in function
  bodies from a provided file (`resources/templates/fusion.py` with signatures and edge
  cases listed). Without it, designing the interface eats the session.
- ⚠️ **No weights of your own** (Prerequisite 1). If a student skipped training, the only
  option today is another project's weights — whose class list may not match
  `docs/taxonomy.md`. Step 2's check catches that, but the course has no approved
  fallback weights.
- ⚠️ **Int8 calibration set undecided** (step 2). Calibrating on the validation split is
  the obvious default, and it makes the parity number look better than it is.
- ⚠️ **Export commands not yet run on this project's models** on a clean machine. The
  syntax is checked against current docs (2026-09-24); the result is not.
- ⚠️ **Ultralytics now exports ExecuTorch directly** (`format=executorch`, listed in
  8.4.118). Exporting detection to `.pte` too would drop one of the two native runtimes in
  the app. Not yet evaluated.

## Further reading

- [Ultralytics — model export](https://docs.ultralytics.com/modes/export/) — LiteRT and `quantize=8`, checked 2026-09-24
- [Optimum ExecuTorch — export guide](https://huggingface.co/docs/optimum-executorch/en/guides/export) — `depth-estimation` task, `xnnpack` recipe, checked 2026-09-24
- [ExecuTorch — export and lowering](https://docs.pytorch.org/executorch/stable/using-executorch-export.html) — what a `.pte` is
- [react-native-fast-tflite](https://github.com/mrousavy/react-native-fast-tflite) — runs the detection file in Lesson 05
- [React Native ExecuTorch](https://docs.swmansion.com/react-native-executorch/) — runs the depth file

---

**Next:** [Lesson 05 — On-Device Inference & Mobile Delivery](../05-mobile-client-and-delivery/)
