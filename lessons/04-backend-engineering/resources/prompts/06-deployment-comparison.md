# Prompt — measure the deployment options

**When:** Lesson 04, step 7. **Optional.**

**Which agent:** `backend` for the benchmark harness, `dataset-engineer` for anything
touching the Roboflow API.

**Budget: about 1 credit.** Do not run this with fewer than 2 credits remaining.

---

## What this is for

You have a service running local weights at zero marginal cost. Everyone has an intuition
about what the alternatives cost. This step replaces the intuition with a table.

One of those intuitions is reliably wrong, and finding out which is the point.

---

## Round 1 — the rates, before the benchmark

```
Use the dataset-engineer agent.

From roboflow:plans-and-pricing and roboflow:inference, give me the exact billing rate
for each of these, quoting the skill rather than recalling it:

  1. Hosted serverless inference (v2)
  2. Self-hosted inference server (localhost:9001)
  3. Dedicated deployment, GPU
  4. Batch processing, GPU

For each, convert the rate into COST PER 1,000 IMAGES, stating the assumption you used
about per-image execution time. Show the arithmetic.

Then answer directly: is running the inference server on my own hardware free?
```

**Expected result:** the agent reports that **self-hosted is metered at 1 credit per 3,000
images** — roughly 0.33 credits per 1,000. It runs on your hardware and it still bills.
`inference/workflows.md` describes the local cost model as *"metered credits + your
hardware"*.

**That is the correction this step exists to deliver.** "Run it locally and it's free" is
the near-universal assumption, and Lesson 05 automates these calls without a human
watching. An automated pipeline built on a wrong cost model is the classic way a budget
disappears quietly.

Note also that hosted v2 bills by **execution seconds**, not by image count. Slow images
cost more than fast ones, which makes the cost of a batch depend on its content — worth
knowing before you extrapolate from a sample.

---

## Round 2 — benchmark the local service

```
Use the backend agent.

Write scripts/benchmark.py: send a fixed set of images to the local service, measure
per-image latency, and report p50, p95, and throughput.

  --images  directory (use a fixed 200-image set from data/v1/test)
  --url     service base URL, default http://localhost:8000
  --warmup  requests to discard before measuring, default 5

Report: image count, p50, p95, total wall time, images/second, and the hardware it ran on.

The warmup matters — the first requests include model warmup and would otherwise
dominate p95 on a small sample.
```

Run it against your containerized service. **Zero credits.**

---

## Round 3 — the hosted comparison, budgeted

```
Use the dataset-engineer agent.

Before calling anything:
  - The estimated credit cost of running 200 images through hosted serverless inference,
    with the arithmetic and the per-image time assumption
  - My remaining balance from docs/credit-budget.md

Record the estimate in the ledger, then run the benchmark against
serverless.roboflow.com using the model I trained in Lesson 03 step 8.

If I skipped the hosted training run, say so and stop — there is no hosted model to
benchmark, and this row of the table is unavailable rather than zero.

Afterwards, append the ACTUAL cost and reconcile it against the estimate.
```

Your `models_infer` permission rule fires here. It should.

⛔ **Do not create a dedicated deployment.** It bills uptime, not usage: one left running
is 24 credits a day, more than the whole course budget. It belongs in the table as a row
with that reasoning, not as an experiment.

---

## Round 4 — the table

```
Write docs/deployment-comparison.md.

| Option | Measured p50 | Measured p95 | Cost / 1,000 images | Setup | Notes |

Rows: local in-process, self-hosted inference server, hosted serverless, dedicated
(not measured — say why).

Then a recommendation that names its traffic assumption. The right answer genuinely
changes with volume, so a recommendation without a stated assumption is a preference.
Give the crossover: at roughly what request rate does each option become the sensible one?

Finally, state what this benchmark does NOT show:
  - It ran on one machine with one hardware profile
  - Network latency to the hosted API depends on my location
  - 200 images is a small sample, and hosted v2 bills by execution time, so the cost
    depends on image content
```

---

## What good output looks like

- Rates quoted from the skills, with arithmetic, not recalled
- Self-hosted correctly identified as **metered, not free**
- Warmup requests discarded before measuring
- The hosted estimate recorded in the ledger *before* the run
- Actual cost reconciled against the estimate
- Dedicated included as a row with reasoning, and not created
- A recommendation with a stated traffic assumption and a crossover point
- The limitations of the benchmark stated plainly

## Reject and re-run if

- Self-hosted is described as free
- Any call is made before the estimate and balance are stated
- A dedicated deployment is created
- p95 is reported without warmup, on a sample small enough for cold start to dominate
- The recommendation has no traffic assumption attached
- Cost per 1,000 images is quoted for hosted v2 without stating the per-image time
  assumption it depends on
