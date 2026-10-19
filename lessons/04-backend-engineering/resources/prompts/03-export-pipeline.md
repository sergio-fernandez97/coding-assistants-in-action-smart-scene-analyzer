# Prompt — export both models reproducibly

**When:** Lesson 04, step 3. **Before the session.**

**Which agent:** `ml-engineer`.

**Credits: zero.** Export runs entirely on your machine.

---

⚠️ **The detection export is not verified against this project's model.** Its command is
current as of 2026-08-12, but whether YOLO11 exports cleanly to int8 TFLite here has not been
confirmed. **The depth lowering in Round 3 is verified** (2026-09-29: executorch 1.5.1,
torch 2.13, transformers 5.15). **If an export fails, that failure is the finding** — record
what broke rather than quietly substituting a different model.

---

## Round 1 — one script, not two shell invocations

```
Use the ml-engineer agent.

Write scripts/export.py that exports both models reproducibly:

  uv run python scripts/export.py --all
  uv run python scripts/export.py --detection
  uv run python scripts/export.py --depth

Requirements:
  - Takes the checkpoint path and output directory as arguments, with the project
    defaults baked in as defaults rather than hardcoded.
  - Prints, for every artifact it produces: the output path, the file size, and the
    ACTUAL input and output tensor shapes read back from the exported file.
  - Fails loudly if an output file already exists, unless --force is passed.
  - Logs the export config to MLflow against the run that produced the checkpoint.

Do not run it yet — show me the script first.
```

**A script rather than two commands in a README**, because this runs again every time the
model is retrained, and because `artifact_drift.py` tells students to run
`scripts/export.py` by name. Two shell invocations in a lesson become two slightly
different shell invocations six weeks later.

---

## Round 2 — detection

```
Export the detection model to int8 LiteRT (.tflite):

  yolo export model=runs/<run>/weights/best.pt format=litert quantize=8 data=<data.yaml>

  (format=tflite int8=True is deprecated since Ultralytics 8.4.83 and forwards to this.)

Then report:
  - The output tensor shape, read from the exported file
  - Whether coordinates are normalized or in input-pixel space, and HOW you determined it
  - The file size, both int8 and fp32, and the ratio

State which calibration data int8 used. If it was the val split, say so explicitly and
note that this makes the parity number in step 8 optimistic — you are measuring
quantization error on the data that chose the quantization parameters.
```

**The calibration set is a real decision, not a flag.** Calibrating on the validation split
is the obvious default and it is also the one that makes your parity measurement flattering.
Either use a held-out slice or accept the optimism knowingly.

---

## Round 3 — depth

```
Export the depth model to ExecuTorch by lowering it directly. Do not use optimum-cli
and do not install optimum-executorch: it has no depth-estimation task, and it
downgrades transformers to 4.56.

The depth half of scripts/export.py:
  1. Load depth-anything/Depth-Anything-V2-Small-hf with
     transformers.AutoModelForDepthEstimation, in eval mode.
  2. Wrap it in a torch.nn.Module whose forward(pixel_values) returns
     model(pixel_values=pixel_values).predicted_depth, a single tensor, not the
     HF output object.
  3. torch.export.export the wrapper with a fixed example torch.randn(1, 3, 518, 518),
     under torch.no_grad().
  4. Lower with executorch.exir.to_edge_transform_and_lower(exported,
     partitioner=[XnnpackPartitioner()]). The partitioner comes from
     executorch.backends.xnnpack.partition.xnnpack_partitioner. Then call
     .to_executorch().
  5. Write program.buffer to a staging path, NOT app/assets/models/. Read the shapes
     back with executorch.runtime.Runtime (load_program, load_method("forward"),
     .metadata). Move the file into app/assets/models/ only if the input is exactly
     [1, 3, 518, 518].

The artifact must accept a FIXED [1, 3, 518, 518] input — the DEPTH_INPUT square from
the contract in step 2. Not a dynamic shape, and not the aspect-preserving non-square
raster depth.py's reference preprocessing produces. If the recipe gives you a dynamic
or differently-shaped graph, say so rather than working around it.

Then report:
  - Input and output tensor shapes and dtypes, read from the .pte
  - The file size
  - Whether the exported model still outputs relative inverse depth with the same sign
    convention — larger means nearer. Verify this, do not assume it.
  - Confirm the output is the model's NATIVE 518x518 raster and that no resize happens
    inside the graph. The resize to MODEL_INPUT is the app's job, at the depth boundary.

If the export fails, report the actual error. Do not substitute a different checkpoint,
a different recipe, or a different task without saying so.
```

**Verify the sign convention on the exported model specifically.** A convention flipped
somewhere in the export produces a system that is confidently backwards and passes every
check that does not test ordering.

**The fixed 518² input is settled, not a choice you are making here.** It comes from step
2's contract: `518 = 14 × 37` is a legal ViT-S/14 edge and `640` is not. If the export
tool insists on something else, that is a finding for the model card — record it, and note
that `depth.py`'s own preprocessing constants now describe the *reference's* recipe rather
than the artifact's, which is a reconciliation this step owns.

---

## Round 4 — reconcile against the contract

```
Compare what the export actually produced against the INTENDED table you wrote in step 2.

For every row, mark: matches / differs / was not knowable in advance.

Where they differ, the ARTIFACT is right and the card is wrong — update the card and say
what you had assumed. Then remove the INTENDED marking.

Finally, record both file sizes in docs/artifact-budget.md with today's date.
```

**Where they differ, that difference is the most valuable output of this step.** It is a
fact about your toolchain that you now know and would otherwise have discovered in Lesson
05, in TypeScript, while debugging a decoder.

---

## What good output looks like

- One script, re-runnable, with `--force` protection
- Tensor shapes read back from the exported files, not from the export config
- Coordinate format determined from data, with the method stated
- The calibration set named, and its effect on step 8 acknowledged
- The depth sign convention verified on the export
- Every contract row reconciled, with differences resolved in the artifact's favour
- Both sizes in `docs/artifact-budget.md`

## Reject and re-run if

- Export happened as ad-hoc shell commands with no script
- Reported shapes came from the config rather than the exported file
- A failing export was worked around by silently changing model, recipe, or task
- The `.pte` was produced outside `scripts/export.py`, for example by a scratch script in `/tmp`
- The calibration set is unnamed
- The contract table was updated to match without noting what changed
- Artifact sizes were not recorded
