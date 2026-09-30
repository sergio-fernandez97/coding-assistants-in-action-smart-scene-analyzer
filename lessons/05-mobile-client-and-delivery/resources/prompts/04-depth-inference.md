# Prompt — run Depth Anything V2 through the generic ExecuTorch module

**When:** Lesson 05, step 7 — in the session.

**Which agent:** `mobile`.

**Credits: zero.**

---

There is no `useDepthEstimation` hook. `react-native-executorch` ships prebuilt hooks for
the tasks it has models for, and depth estimation is not one of them.

So this path uses the react-native-executorch **0.10 core API**: `loadModel(path)`,
`tensor(...)`, and `model.execute('forward', [input], [output])`. `ExecutorchModule` and
`initExecutorch` are the `/legacy` API in 0.10; do not use them. Preprocessing and postprocessing are yours.
That is more work than the detection path, and it is the honest shape of the problem
rather than a detour.

---

## Round 1 — build the input tensor deliberately

```
Use the mobile agent.

Write app/src/inference/preprocess.ts:

  export function toModelInput(
    pixels: RGBPixels,
    target: { width: number; height: number },
    norm: { mean: [number, number, number]; std: [number, number, number] },
  ): { data: Float32Array; scale: number; padX: number; padY: number }

Requirements:
  - LETTERBOX, do not stretch. Return the scale and the padding you applied — they are
    needed to invert the transform later, and recomputing them elsewhere is how the two
    copies drift.
  - Produce the layout the model actually declares. State in a comment whether it is
    [1,3,H,W] NCHW or [1,H,W,3] NHWC and how you confirmed it.
  - Apply (pixel/255 - mean) / std with the constants from the model card.
  - Pure and tested: a known 2x2 input produces hand-computed output values.
```

**Normalization constants are not decoration.** Feeding a model ImageNet-normalized input
when it expects `[0, 1]` produces a depth map that is smooth, plausible, and wrong — and
nothing in the pipeline will object.

---

## Round 2 — run it

```
Write app/src/inference/depth.ts:

  - setTelemetryEnabled(false) at module load. The library sends download analytics by
    default, and this project sends nothing off the device
  - Resolve the bundled .pte to a local file path with expo-asset (Asset.loadAsync, then
    localUri without the file:// prefix), then loadModel(path), once, cached
  - execute('forward', [inputTensor], [outputTensor]) and report the OUTPUT tensor's
    shape and dtype verbatim
  - Reshape to a 2D depth map, stating the dimensions

Print the min, max, and mean of the output. Do not interpret them yet.
```

---

## Round 3 — the only property you can check

```
Run the depth model on a bundled indoor image where you can see, by eye, that one object
is in front of another.

Report the median depth value inside each of the two regions, and state which the model
says is nearer.

That is the ONLY correctness check available here. There is no ground truth, no unit, and
no scale — the output is relative inverse depth. If the ordering is right, the model is
working. If it is inverted, say so; do not silently negate it without recording that you
did and why.
```

**Larger means nearer.** Confirm that against the model card rather than assuming, because
a sign convention flipped somewhere in the export produces a system that is confidently
backwards and passes every test that does not check ordering.

---

## Round 4 — name it correctly, everywhere

```
Review every identifier, comment, type name, and string you have written in this file
and in preprocess.ts.

The value is relative inverse depth: no unit, no scale, comparable only within one image.
Nothing may imply otherwise — not a variable, not a docstring, not a log line.

Then deliberately try to write `const depth_meters = ...` into this file and show me what
happens.
```

The last part is not a joke. `units_guard` now reaches `app/*.ts`, and seeing it block is
the point — this is where depth is *computed* now, and it is the first time in the course
that the hook has guarded the thing rather than the description of the thing.

---

## What good output looks like

- Letterboxing returns its scale and padding rather than discarding them
- Tensor layout confirmed against the loaded model, stated in a comment
- Normalization constants come from the model card
- Output tensor shape reported verbatim before being reshaped
- Ordering verified on a real image with a visible foreground and background
- The sign convention is confirmed, not assumed
- `units_guard` observed blocking a metric identifier in a `.ts` file

## Reject and re-run if

- The image was stretched to the input size rather than letterboxed
- Scale and padding are recomputed somewhere else instead of returned
- Normalization was guessed, or skipped
- The depth map was interpreted as a distance in any form
- Ordering was never checked on a real image
- An inverted sign was silently corrected without being recorded
