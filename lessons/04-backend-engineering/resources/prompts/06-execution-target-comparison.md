# Prompt — compare the on-device execution targets

**When:** Lesson 04, step 10.

**Which agent:** `ml-engineer`.

**Credits: zero.**

---

An exported model can run several ways on a phone. They differ in speed by multiples, in
availability by platform and vendor, and in whether they exist at all in a simulator.
Choosing without knowing is how a project discovers in Lesson 05 that its fast path does
not exist on the device it was demoing on.

---

## Round 1 — what is actually available

```
Use the ml-engineer agent.

For each execution target, state: which platforms support it, whether the exported
artifacts as built in step 3 can use it, and what happens when it is unavailable.

  - XNNPACK / CPU
  - Android NNAPI
  - CoreML / Apple Neural Engine
  - GPU delegate

Cite the source for each claim with a URL and the date you checked it. Do not write these
from memory — delegate availability and fallback behaviour both move.

Flag explicitly which of the four are NOT available in the iOS Simulator.
```

**The silent-fallback question is the important one.** A target that quietly falls back to
CPU when unsupported produces a benchmark that looks fine and a device population where
half the users get a third of the speed.

---

## Round 2 — measure what you can

```
Measure inference latency for each target you can actually run on this machine, on a
fixed image, n >= 20, reporting p50 and p95.

Be explicit about what you CANNOT measure here:
  - A phone's CPU is not your laptop's CPU
  - The Neural Engine does not exist on this machine
  - NNAPI behaviour is vendor-specific and unknowable from here

Mark every unmeasurable row as UNMEASURED. Do not estimate it, and do not omit the row —
an omitted row reads as "not applicable" rather than "unknown".
```

**An UNMEASURED row is more useful than an estimated one**, because it tells Lesson 05
exactly what to go and find out.

---

## Round 3 — the comparison table

```
Fill in docs/execution-target-comparison.md.

Keep the CLOUD rows from the previous architecture as contrast — hosted serverless and
self-hosted, with their credit rates. Do not delete them.

Then add a row for what each option costs in a currency the other does not use:

  - Cloud: credits per 1,000 images, network dependency, and a privacy question
  - On-device: megabytes shipped, a device floor, and an app-store release cycle for
    every model update

State a recommended default backend per platform, and the device floor it implies.
```

**Keeping the cloud rows is the point of the table.** "Zero credits per 1,000 images" reads
as unambiguously better until it sits next to "and a 40 MB download, and no phone older
than 2021, and a week of app review to fix a model bug". Neither column is free; they are
expensive in different currencies, and the table exists so the trade is visible rather than
asserted.

---

## Round 4 — the honest summary

```
In two paragraphs: which target should this project default to on each platform, and what
would have to be true to change that?

Then answer directly: is there any measurement in this table that could change the
inference-target decision back to cloud? If yes, say which and what value it would have to
take. If no, say so — an ADR whose evidence could never have pointed the other way is
worth being explicit about.
```

---

## What good output looks like

- Every availability claim carries a URL and a check date
- Simulator-unavailable targets flagged
- Silent-fallback behaviour described per target
- Measured rows separated from UNMEASURED ones, with nothing estimated
- Cloud rows retained for contrast
- Costs stated in both currencies
- A recommended default per platform, with the device floor it implies

## Reject and re-run if

- Availability was written from memory without sources
- Unmeasurable values were estimated or the rows omitted
- The cloud rows were deleted
- The table compares only latency, with no size or device-floor column
- No default is recommended, or one is recommended without naming its floor
