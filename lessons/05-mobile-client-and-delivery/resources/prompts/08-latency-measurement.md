# Prompt — measure on-device, and separate the phases

**When:** Lesson 05, step 11 — after the session.

**Which agent:** `mobile`.

**Credits: zero.**

---

Lesson 04 measured Python on your laptop. That was a measurement of your CPU. This is a
measurement of the product — and unlike the cloud architecture it replaced, there is no
network in it to blame or to hide behind. Every millisecond here is yours.

---

## Round 1 — predict first

```
Use the mobile agent.

Before instrumenting anything, write down your prediction for each phase, in milliseconds:

  - Cold model load, detection
  - Cold model load, depth
  - Preprocess (decode, letterbox, normalize)
  - Detection inference
  - Depth inference
  - Decode + NMS
  - Fusion
  - Render

Also predict peak memory with both models loaded.

Save this in docs/latency-report.md before you measure. Do not adjust it afterwards.
```

**Write the prediction down where it can embarrass you.** A prediction revised after
measurement teaches nothing; a wrong one preserved is the most useful line in the report,
because the gap is the finding.

---

## Round 2 — instrument

```
Add phase timing:

  - Gate every timing behind __DEV__ so it does not ship.
  - Time each phase separately. One aggregate number hides which of the two models
    dominates, and that is the only thing the number is for.
  - Cold model load is measured ONCE per app launch and belongs in its own table. Do not
    average it into the per-image distribution.
  - Run at least 20 warm inferences on the same bundled image.
  - Report p50 and p95, not the mean. A mean hides the stall.

Also capture peak resident memory with both models loaded, and say how you measured it.
```

**Cold load is not slow inference, it is a different event.** It happens once, the user
watches it, and it is fixed by different work — lazy loading, a smaller artifact, a
loading state that is honest. Averaged into the per-image number it corrupts both.

---

## Round 3 — say where you measured

```
Fill in docs/latency-report.md.

State BEFORE any number:
  - Device or simulator, exactly. "iPhone 15 Pro" and "iOS Simulator on an M2 MacBook Air"
    are not comparable and must never share a table.
  - OS version
  - Debug or release build
  - Which backend each runtime actually used

If you measured on a simulator, label the whole table as simulator measurements and say
plainly that they are not device numbers. The iOS Simulator has no Neural Engine and runs
on your Mac's CPU — it will be wrong in both directions depending on the phase.
```

**A latency figure without its conditions is not a measurement.** That was true of the
network in the previous architecture and it is true of the device now — a debug build with
the JS dev server attached can be several times slower than release, and reporting one as
the other is the easiest mistake in this lesson.

---

## Round 4 — say what could actually change

```
For each phase, state whether code can change it and how:

  Cold load     — smaller artifact? lazy-load depth until first use?
  Preprocess    — is it on the JS thread? should it be?
  Detection     — smaller input size, different quantization
  Depth         — the ViT is usually the expensive one; what are the options?
  Decode + NMS  — is this actually significant, or did you assume it was?
  Render        — almost never the problem

Name the dominant phase and its share of p95. Then answer: does the measurement agree
with your round 1 prediction? If not, that gap is the finding — say what you had wrong.
```

---

## What good output looks like

- A prediction written down before measuring, and left unedited
- Every phase timed separately, cold load in its own table
- n ≥ 20 warm runs, p50 and p95 reported
- Device or simulator named exactly, with build type
- Simulator and device figures never mixed
- Peak memory recorded, with the method
- The dominant phase named, with its share
- The prediction-versus-measurement gap discussed

## Reject and re-run if

- Cold load is averaged into the per-image numbers
- Only an aggregate "inference time" was reported
- The mean was reported instead of p50/p95
- Simulator numbers are presented as device numbers, or the two share a table
- The build type is unstated
- Timing code is not gated behind `__DEV__`
- The prediction was written after the measurement
