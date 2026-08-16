# Export parity report — the device against the reference

> The question this answers: **is the app running a model that still behaves like the one
> you trained?** Not "does it run", and not "does it produce plausible output".

## What was compared

| | Path A | Path B |
|---|---|---|
| Where | The app, on `<device/simulator>` | Python, on this machine |
| Weights | `app/assets/models/<...>` | The original PyTorch checkpoint |
| Runtime | `<fast-tflite / ExecuTorch>` | `<ultralytics / transformers>` |
| Image | `<filename, W×H>` | same |

> **Path B must use the PyTorch weights, not the exported artifact.** Running the export
> through Python and comparing it to the same export on the phone will agree, and proves
> only that two runtimes can read one file.

**Why this image:** `<what makes it a reasonable test — and what it does not exercise>`

## Detections

| # | Class (A) | Class (B) | IoU | Conf A | Conf B | Verdict |
|---|---|---|---|---|---|---|
| 1 | | | | | | |
| 2 | | | | | | |

| Summary | A | B |
|---|---|---|
| Detection count | | |
| Classes present | | |

## Depth

Depth is compared by **ordering**, not by value. The output has no scale, so comparing
magnitudes across two runtimes is meaningless.

| Object | Rank in A (near→far) | Rank in B | Match? |
|---|---|---|---|
| | | | |

**Ordering preserved:** `<yes / no / partially — which pairs inverted>`

## Differences, classified

For each difference, the category and the distinguishing test you actually ran.

| Difference | Category | Distinguishing test | Result |
|---|---|---|---|
| | `<preprocessing / decoding / quantization / port>` | | |

Reference for the four categories:

| Category | Signature | Test |
|---|---|---|
| **Preprocessing** | Boxes systematically offset or scaled | Does the offset scale with the letterbox padding? |
| **Decoding** | Boxes plausible, classes wrong or confidences oddly distributed | Is it a constant class-index shift? |
| **Quantization** | One or two classes degraded, rest fine | Does an fp32 export agree where int8 does not? |
| **The port** | Detections identical, depth values differ | Do the shared fusion fixtures still pass? |

## Tolerances

| Quantity | Tolerance | Set before or after seeing the data? |
|---|---|---|
| Box IoU | | |
| Confidence delta | | |
| Depth ordering | Exact match required | — |

**Justification:** `<why these numbers>`

> A tolerance chosen after seeing the results is a description, not a threshold. If you
> set one to fit what you measured, say so here rather than letting the number imply
> otherwise.

## Verdict

`<Is the app running a model that still behaves like the one you trained?>`

`<"Not confirmed" is a valid and sometimes correct answer. Write it if it is true.>`

## What was not tested

- Other images — one image is one sample, and a busy scene and an empty wall are not the
  same work
- Other devices or backends — `<NNAPI / CoreML / GPU delegate all untested?>`
- `<Scenes outside the training distribution>`

`<Say what a reader should not conclude from this report.>`
