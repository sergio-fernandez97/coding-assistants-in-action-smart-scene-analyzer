# Latency report

> Copy to your project as `docs/latency-report.md` and fill in every `<...>`.
>
> A latency figure without its measurement conditions is not a measurement. This template
> puts the conditions above the numbers so they cannot be quoted apart from them.

## Measurement conditions

| | Wi-Fi | Cellular |
|---|---|---|
| Device | `<model>` | `<model>` |
| OS version | `<version>` | `<version>` |
| Link, measured | `<N>` Mbit/s up, `<N>` down | `<N>` Mbit/s up, `<N>` down |
| Measured with | `<speed test / method>` | `<...>` |
| Prepared image size | `<N>` KB, `<W>`×`<H>` | `<N>` KB, `<W>`×`<H>` |
| Container | `<cpu>` vCPU, `<mem>` GiB, region `<region>` | same |
| Replica state | warm | warm |
| Requests (n) | `<N>` | `<N>` |
| Date | `<YYYY-MM-DD>` | `<YYYY-MM-DD>` |

**The link speeds must be measured, not named.** "Cellular" is not a condition; 12 Mbit/s
up on a named network at a named time is.

## Per-stage latency

Times in milliseconds. Stage boundaries as instrumented in the client.

### Wi-Fi, warm

| Stage | What it covers | p50 | p95 |
|---|---|---|---|
| Capture → prepared | Resize, orient, re-encode on device | | |
| Prepared → sent | Request construction, connection setup | | |
| Sent → first byte | **Upload + server processing + queueing** | | |
| First byte → parsed | Download and JSON parse | | |
| Parsed → rendered | Overlay layout and draw | | |
| **Total** | Shutter → boxes on screen | | |
| *of which server* | From the response's own timing field | | |

### Cellular, warm

| Stage | p50 | p95 |
|---|---|---|
| Capture → prepared | | |
| Prepared → sent | | |
| Sent → first byte | | |
| First byte → parsed | | |
| Parsed → rendered | | |
| **Total** | | |
| *of which server* | | |

### Cold start — reported separately

A revision at `--min-replicas 0` has no replica running when idle. The first request pays
for the container to start and the depth model to load. This is the price of paying nothing
to sit idle, and it does not belong in the warm distribution.

| | Value | n |
|---|---|---|
| Cold total | `<ms>` | `<n>` |
| Warm total, same link | `<ms>` | |
| Difference | `<ms>` | |

## Comparison with Lesson 04

| Measurement | Value | What it measured |
|---|---|---|
| Lesson 04, loopback | `<ms>` | How fast the code is |
| This report, Wi-Fi p95 | `<ms>` | How fast the product is |
| This report, cellular p95 | `<ms>` | How fast the product is on a real link |

Lesson 04's number was not wrong. It answered a different question, and both belong here
labelled — the gap between them is the network, and the network was never optional.

## Analysis

**Which stage dominates?**

| Link | Dominant stage | Share of p95 |
|---|---|---|
| Wi-Fi | | |
| Cellular | | |

The arithmetic that predicts this, from the prompt's round 1:

```
<N> KB × 8 / <link Mbit/s>  =  <N> ms of upload, before the server sees a byte
```

`<Does the measurement agree with the prediction? If not, that gap is the finding.>`

**What can code actually change?**

| Stage | Under our control? | Lever |
|---|---|---|
| Capture → prepared | Yes | Target resolution, JPEG quality |
| Upload | Partly | Fewer bytes. Nothing else |
| Server processing | Yes | Model size, batching, container size |
| Cold start | Yes, but it costs | `--min-replicas 1` removes it and ends the free grant |
| Download, render | Marginal | |

## Recommendation for N1

`docs/requirements.md` N1 has been a placeholder since Lesson 01, written as
*client-observed* with no link specified — which cannot be passed or failed. Choose one:

- [ ] **Client-observed, link pinned.** `p95 < <N> ms, measured on <link> at ≥ <N> Mbit/s
      up, warm container, <N> KB upload.` Honest about the whole product; only meaningful
      against a stated link.
- [ ] **Server-observed, transit budgeted separately.** `Server p95 < <N> ms` plus a stated
      transit allowance. Testable in CI; does not describe what a user experiences.

**Chosen:** `<which, and why>`

**Cold start:** `<in scope for N1, or excluded with a stated reason?>`

## What was not measured

`<Devices not tested. Networks not tested. Times of day. Image content — a busy scene and
an empty wall are not the same server-side work. Say what a reader should not conclude
from this report.>`
