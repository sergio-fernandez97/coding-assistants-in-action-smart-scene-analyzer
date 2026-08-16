# Execution target comparison

> Where the exported models can run, what each option costs, and in which currency.
> Cloud rows are retained as contrast, not as live options — see the inference-target ADR.

## Availability

Every claim needs a source and a date. Delegate availability and fallback behaviour both
move upstream.

| Target | Platforms | Our artifacts can use it? | On unavailable | Source, checked |
|---|---|---|---|---|
| XNNPACK / CPU | | | — always available | |
| Android NNAPI | | | `<silent CPU fallback? error?>` | |
| CoreML / ANE | | | | |
| GPU delegate | | | | |

**Not available in the iOS Simulator:** `<which>`

> A target that silently falls back to CPU produces a benchmark that looks fine and a
> device population where many users get a fraction of the speed.

## Measured latency

Measured on `<machine>`, `<date>`, n = `<N>`, image `<W×H>`.

| Target | Detection p50 | Detection p95 | Depth p50 | Depth p95 |
|---|---|---|---|---|
| XNNPACK / CPU (this machine) | | | | |
| Android NNAPI | UNMEASURED | UNMEASURED | UNMEASURED | UNMEASURED |
| CoreML / ANE | UNMEASURED | UNMEASURED | UNMEASURED | UNMEASURED |
| GPU delegate | | | | |

> **UNMEASURED is not an omission.** This machine has no Neural Engine, and NNAPI
> behaviour is vendor-specific. An estimated number here would be quoted later as if it
> had been measured. Lesson 05 fills these in on real hardware.

## Cost, in both currencies

| Option | Credits / 1,000 images | Bytes shipped | Network needed | Model update cycle | Device floor |
|---|---|---|---|---|---|
| **On-device** *(chosen)* | **0** | `<N MB>` | none | app-store release | `<iOS N / Android N>` |
| Hosted serverless *(contrast)* | ~1 | 0 | every request | a deploy | any |
| Self-hosted server *(contrast)* | ~0.33 | 0 | every request | a deploy | any |
| Local in-process, cloud-hosted *(contrast)* | 0 | 0 | every request | a deploy | any |

**Neither column is free.** The on-device row spends no credits and no network; it spends
megabytes, a device floor, and a week of app review to fix a model bug. The cloud rows
spend the opposite. This table exists so that trade is visible rather than asserted.

## Recommendation

| Platform | Default backend | Why | Device floor it implies |
|---|---|---|---|
| iOS | | | |
| Android | | | |

## Could this have pointed back to cloud?

`<Is there a measurement in this table that would have reversed the inference-target
decision? If yes, which, and at what value? If no, say so plainly — evidence that could
never have pointed the other way should be labelled as such.>`

## What was not measured

`<Real devices. Thermal throttling. Sustained inference. Low-memory devices. Vendor NNAPI
implementations.>`
