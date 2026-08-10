# Deployment comparison

> Copy to your project as `docs/deployment-comparison.md`.
> The point of this document is that it contains **measurements**, not opinions. A
> deployment argument without numbers is a preference with a diagram.

## What was measured

| Field | Value |
|---|---|
| Date | `<YYYY-MM-DD>` |
| Benchmark set | `<200 images from data/v1/test>` |
| Warmup requests discarded | `<5>` |
| Local hardware | `<CPU/GPU, RAM, OS>` |
| Model | `<yolo11n, dataset version N>` |
| Network location | `<affects hosted latency — say where you are>` |

## Results

| Option | p50 latency | p95 latency | Cost / 1,000 images | Setup cost | Measured? |
|---|---|---|---|---|---|
| **Local in-process** | | | **0** | Weights on disk | ✅ |
| **Self-hosted inference server** | | | **~0.33 credits** | Docker, `localhost:9001` | `<✅ / ✗>` |
| **Hosted serverless (v2)** | | | **~1 credit** at `<0.5>` s/image | API key only | `<✅ / ✗>` |
| **Dedicated (GPU)** | — | — | 1 credit per hour of **uptime** | Provisioning | ❌ **not created — see below** |

### How each cost was derived

Show the arithmetic. A number nobody can re-derive gets quietly distrusted.

- **Local in-process:** no per-image billing. Cost is hardware and electricity.
- **Self-hosted:** 1 credit = 3,000 images → `1000 / 3000` = **0.33 credits / 1,000**.
- **Hosted serverless v2:** 1 credit = 500 seconds of execution. At `<___>` s/image,
  1,000 images = `<___>` seconds = **`<___>` credits**.
- **Dedicated:** 1 credit per hour of uptime, independent of requests served. Cost per
  image depends entirely on utilization, and is unbounded at low utilization.

> ⛔ **Dedicated was deliberately not created.** It bills uptime rather than usage. One
> deployment left running for a day is 24 credits — more than this project's entire
> 20-credit budget. Included here for completeness, not as an option.

## The finding that surprises people

**Self-hosted inference is metered.** Running the inference server on your own hardware
at `localhost:9001` still bills, at 1 credit per 3,000 images. It is roughly 3× cheaper
per image than hosted serverless, not free.

`inference/workflows.md` describes the local cost model as *"metered credits + your
hardware"* — you pay for both.

**Why this matters beyond this document:** Lesson 05 automates inference inside a CI
pipeline, where no human sees each call. A pipeline built on "local is free" burns budget
invisibly, and the first symptom is a failed run at the end of the month.

## Recommendation

**At `<___>` requests/day, use `<option>`, because `<reason>`.**

Crossover points — where the sensible answer changes:

| Traffic | Option | Why |
|---|---|---|
| < `<___>` req/day | | |
| `<___>`–`<___>` req/day | | |
| > `<___>` req/day | | |

**This project's choice:** `<option>`, recorded in `docs/decisions/` → *inference target*.

## What this benchmark does not show

State the limits, or the numbers will be quoted in contexts they cannot support.

- One machine, one hardware profile. Your production hardware is not this laptop.
- Hosted latency includes network round trip from `<your location>`.
- `<200>` images is a small sample.
- **Hosted v2 bills by execution time, not image count** — cost depends on image content
  and model complexity, so extrapolating from this sample assumes similar images.
- No concurrency testing. These are sequential requests; p95 under load will be worse.
- No cold-start measurement for the hosted path.

## Constraint carried from Lesson 03

On the free Public plan, **model weight downloads are a Core-plan feature**. A
Roboflow-hosted trained model cannot be pulled into the local service — it is reachable
only through the hosted API.

That is why the local option runs *locally trained* weights, and why this comparison is
between genuinely different deployment paths rather than the same model served three
ways. Note it here so the next reader does not assume the rows are interchangeable.
