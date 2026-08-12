# Prompt — client-observed latency

**When:** Lesson 05, step 8.

**Which agent:** `mobile` for the instrumentation; `evaluation` for the report.

**Credits: zero.**

---

## Round 1 — predict before you measure

```
Do not run anything yet. Answer with arithmetic:

  1. My prepared upload is <N> KB. At 5 Mbit/s, how long is the upload alone?
  2. At 50 Mbit/s?
  3. Lesson 04 measured server-side processing at <M> ms on loopback. What
     end-to-end latency does that predict on each link?
  4. Which stage dominates on each?
  5. Which of these can the code affect at all?
```

**Predicting first is the point of the round.** Once numbers are on the screen it is very
easy to explain whatever they turned out to be. A prediction you wrote down first turns a
surprise into a finding.

The arithmetic to expect:

```
250 KB at 5 Mbit/s  =  250 × 8 / 5000  ≈  400 ms
                        ...before the server has seen a single byte
```

If upload dominates, no amount of server optimization moves the number a user experiences
— and that reframes what "make it faster" means for the rest of the project.

---

## Round 2 — instrument the stages

```
Use the mobile agent.

Instrument the client to record, per request:

  t0  shutter pressed
  t1  on-device preparation complete
  t2  request sent
  t3  first byte of response received
  t4  response parsed
  t5  overlay rendered

Report the five deltas plus the total, and the server's own processing time from the
response if it carries one.

Add a debug screen showing the last 20 requests and p50/p95 of each stage. Gate it
behind __DEV__ — this is instrumentation, not a feature.
```

**Stages, not a total.** A single end-to-end number tells you the system is slow and
nothing about what to do. The transit/compute split is the entire finding here, and it is
only visible if you measure the boundary between them.

`t3 − t2` includes upload, queueing, server work, and the start of the download. Server
processing from the response body is what lets you separate transit from compute — if the
response does not carry it, say so; that is a finding about the schema.

---

## Round 3 — measure on real links

```
Collect at least 20 requests on each:

  A. Wi-Fi, warm container
  B. Cellular, warm container       (turn Wi-Fi off — actually off, not just disconnected)
  C. Cold start, either link        (leave it idle first; report SEPARATELY, n=3 is fine)

For each, record the measured link speed from a speed test at the time of measurement,
the device, and the OS version.

Do not merge cold starts into the warm distribution. A p95 contaminated by three cold
starts describes a system nobody is using.
```

---

## Round 4 — the report

```
Use the evaluation agent.

Write docs/latency-report.md from the template. It must contain:

  - Measurement conditions FIRST: device, OS, link, measured speed, image size,
    container size, warm or cold, n
  - Per-stage p50 and p95 for Wi-Fi and cellular
  - Cold start reported separately and labelled
  - Lesson 04's loopback number, labelled as what it measured
  - Which stage dominates on each link
  - A recommendation for N1 in docs/requirements.md: either restate it as
    client-observed with a pinned link, or as server-observed with a separate
    transit budget. Say which and why.

Do not average across links. A mean of Wi-Fi and cellular describes no situation
that has ever occurred.
```

`evaluation` writes this for the same reason it writes the model reports: the role that
built the thing is not the role that reports on how well it works. `evaluation` also has no
`Edit` tool, so it cannot quietly adjust the client to improve a number it dislikes.

---

## What good output looks like

- Round 1's prediction is written down before any measurement
- Stages are separated; the transit/compute split is explicit
- Measurement conditions precede every number, including the measured link speed
- Cold start is separate and labelled
- Lesson 04's loopback figure appears, labelled as measuring the code and not the product
- A concrete, defensible recommendation for N1

## Reject and re-run if

- Only a total latency is reported
- Cold starts are inside the warm distribution
- The link is described as "Wi-Fi" or "4G" without a measured speed
- Wi-Fi and cellular are averaged together
- n is under 20 for the warm cases
- The report recommends a server optimization on a link where upload dominates —
  the arithmetic in round 1 already ruled that out
- N1 is left as a placeholder. This lesson exists to fill it
