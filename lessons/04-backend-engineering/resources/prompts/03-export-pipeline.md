# Prompt — export both models reproducibly

**When:** Lesson 04, step 4.

**Which agent:** `ml-engineer`.

**Credits: zero.** Export runs entirely on your machine.

---

⚠️ **Neither toolchain is verified against this project's models.** The commands below are
current as of 2026-08-12. Whether YOLO11 exports cleanly to int8 TFLite here, and whether
Depth Anything V2's ViT survives the ExecuTorch recipe at usable speed, has not been
confirmed. **If one fails, that failure is the finding** — record what broke rather than
quietly substituting a different model.

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
Export the detection model to int8 TFLite:

  yolo export model=runs/<run>/weights/best.pt format=tflite int8=True data=<data.yaml>

Then report:
  - The output tensor shape, read from the exported file
  - Whether coordinates are normalized or in input-pixel space, and HOW you determined it
  - The file size, both int8 and fp32, and the ratio

State which calibration data int8 used. If it was the val split, say so explicitly and
note that this makes the parity number in step 6 optimistic — you are measuring
quantization error on the data that chose the quantization parameters.
```

**The calibration set is a real decision, not a flag.** Calibrating on the validation split
is the obvious default and it is also the one that makes your parity measurement flattering.
Either use a held-out slice or accept the optimism knowingly.

---

## Round 3 — depth

```
Export the depth model to ExecuTorch:

  optimum-cli export executorch \
    --model depth-anything/Depth-Anything-V2-Small-hf \
    --task depth-estimation --recipe xnnpack \
    --output_dir app/assets/models/

Then report:
  - Input and output tensor shapes and dtypes, read from the .pte
  - The file size
  - Whether the exported model still outputs relative inverse depth with the same sign
    convention — larger means nearer. Verify this, do not assume it.

If the export fails, report the actual error. Do not substitute a different checkpoint,
a different recipe, or a different task without saying so.
```

**Verify the sign convention on the exported model specifically.** A convention flipped
somewhere in the export produces a system that is confidently backwards and passes every
check that does not test ordering.

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
- The calibration set named, and its effect on step 6 acknowledged
- The depth sign convention verified on the export
- Every contract row reconciled, with differences resolved in the artifact's favour
- Both sizes in `docs/artifact-budget.md`

## Reject and re-run if

- Export happened as ad-hoc shell commands with no script
- Reported shapes came from the config rather than the exported file
- A failing export was worked around by silently changing model, recipe, or task
- The calibration set is unnamed
- The contract table was updated to match without noting what changed
- Artifact sizes were not recorded
