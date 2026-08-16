# On-device latency report

> A latency figure without its measurement conditions is not a measurement. This template
> puts the conditions above the numbers so they cannot be quoted apart from them.

## Prediction, written before measuring

> Fill this in **first** and do not edit it afterwards. The gap between prediction and
> measurement is the most useful line in this report.

| Phase | Predicted p50 |
|---|---|
| Cold load — detection | |
| Cold load — depth | |
| Preprocess | |
| Detection inference | |
| Depth inference | |
| Decode + NMS | |
| Fusion | |
| Render | |
| Peak memory, both models loaded | |

## Measurement conditions

| | Run A | Run B |
|---|---|---|
| Device or simulator, exactly | `<iPhone 15 Pro \| iOS Simulator on M2 MacBook Air>` | |
| OS version | | |
| Build type | `<debug \| release>` | |
| JS dev server attached | `<yes \| no>` | |
| Detection backend | `<CPU \| NNAPI \| CoreML \| GPU delegate>` | |
| Depth backend | `<XNNPACK \| CoreML>` | |
| Image used | `<filename, W×H>` | |
| Warm runs, n | | |
| Date | | |

> **Simulator and device figures never share a table.** The iOS Simulator has no Neural
> Engine and runs on your Mac's CPU; it is faster than a phone at some phases and slower
> at others, so it is not even uniformly wrong. A debug build with the dev server attached
> can be several times slower than release.

## Cold model load — reported separately

Happens once per launch. The user watches it. It is not part of the per-image distribution
and averaging it in corrupts both numbers.

| Artifact | Load time | n |
|---|---|---|
| Detection `.tflite` | | |
| Depth `.pte` | | |
| **Total, first usable frame** | | |

## Per-image latency, warm

| Phase | p50 | p95 | Notes |
|---|---|---|---|
| Preprocess | | | Decode, letterbox, normalize |
| Detection inference | | | |
| Decode + NMS | | | In TypeScript |
| Depth inference | | | Usually the expensive one |
| Fusion | | | |
| Render | | | |
| **Total** | | | Image selected → boxes on screen |

## Memory

| Measurement | Value | Method |
|---|---|---|
| Baseline, no models loaded | | |
| Both models loaded, idle | | |
| **Peak during inference** | | |

> This is the figure that decides which phones are excluded, and it is the one nobody
> measures until a crash report arrives. Two runtimes hold their own weights and their own
> intermediate tensors, and they do not share an allocator.

## Comparison with Lesson 04

| Measurement | Value | What it tells you |
|---|---|---|
| Python reference, this machine | | How fast the algorithm is |
| On-device p95 | | How fast the product is |

The gap is the device, and the device was never optional.

## Analysis

**Dominant phase:** `<which>`, `<N>`% of p95.

**What code can actually change:**

| Phase | Changeable? | Lever |
|---|---|---|
| Cold load | Yes | Smaller artifact; lazy-load depth until first use |
| Preprocess | Yes | Is it on the JS thread? Should it be? |
| Detection | Yes | Input size, quantization |
| Depth | Partly | The ViT is what it is — a smaller checkpoint is the main lever |
| Decode + NMS | Check first | Often assumed significant and is not |
| Render | Marginal | |

**Prediction versus measurement:** `<Did they agree? If not, what did you have wrong?>`

## Recommendation for N1

`<p95 < N ms, on <named device>, <release> build, <W×H> input.>`

**Cold start:** `<in scope for N1, or excluded with a stated reason?>`

## What was not measured

`<Other devices. Other images — a busy scene and an empty wall are not the same work.
Thermal throttling over sustained use. Low-battery states.>`

`<Say what a reader should not conclude from this report.>`
