# Prompt — the device against the reference

**When:** Lesson 05, step 10.

**Which agent:** `mobile`.

**Credits: zero.**

---

This is the strongest artifact in the lesson, and it exists only because the model moved
onto the device. Under the cloud architecture there was one implementation and nothing to
compare it to; a bug was simply the behaviour of the system. Now there are two, and they
can be asked whether they agree.

---

## Round 1 — one image, both paths

```
Use the mobile agent.

Pick ONE bundled test image. Run it through:

  (a) the app, on the simulator or device
  (b) src/, in Python, with the ORIGINAL PyTorch weights — not the exported artifacts

Emit both results as JSON with the same schema: class, box in source-image pixels,
confidence, relative depth. Save the pair to docs/parity-evidence/.

Do not interpret yet. Show me both.
```

**Compare against the PyTorch reference, not against the exported artifact run in Python.**
Comparing the export to itself will agree, and tells you only that two runtimes read the
same file. The question is whether the thing on the phone still behaves like the model you
trained.

---

## Round 2 — classify the disagreement

```
Compare the two results and classify every difference using this table. State which
category, and the evidence for it.

  Preprocessing  — boxes systematically offset or scaled; a letterbox or normalization
                   mismatch. Test: does the offset scale with the padding?
  Decoding       — boxes plausible but classes wrong, or confidences oddly distributed;
                   label order or output tensor order. Test: is it a constant index shift?
  Quantization   — one or two classes degraded, everything else fine. Test: does the
                   fp32 export agree where the int8 one does not?
  The port       — detections identical, depth values differ. Test: do the fusion
                   fixtures still pass?

Each category has a distinguishing test. Run it rather than guessing.
```

**The four have different fixes and similar symptoms.** Guessing wrong sends you to
retrain a model when the actual defect was an array order — which is exactly the failure
`error-triage`'s EXPORT category was added to prevent.

---

## Round 3 — state a tolerance and defend it

```
Where the two agree, they will not agree exactly. Write down:

  - The box IoU threshold above which you call them the same, and why that number
  - The confidence delta you accept, and why
  - For depth: they will NOT match numerically and are not expected to. What must match
    is the ORDERING of objects near-to-far. State whether it does.

A tolerance chosen after seeing the results is not a tolerance. If you set it now to fit
what you measured, say so explicitly in the report.
```

**Depth parity is an ordering check, not a value check.** The output has no scale, so
comparing magnitudes across two runtimes is meaningless. If the near-to-far ranking of the
detected objects matches, the depth path is working — and if it does not, no tolerance
saves it.

---

## Round 4 — write it down

```
Fill in docs/parity-report.md:

  - The image used, and why that one
  - Both result sets
  - Every difference, classified
  - The tolerances, and whether they were set before or after seeing the data
  - What you did NOT test — other images, other devices, other scenes

Then state plainly: is the app running a model that still behaves like the one you
trained? If the honest answer is "not confirmed", write that.
```

---

## What good output looks like

- Compared against the PyTorch reference, not the export
- Every difference classified with its distinguishing test actually run
- Tolerances stated, with whether they preceded the measurement
- Depth checked by ordering, not by value
- Untested scope named explicitly
- A plain verdict, including "not confirmed" if that is true

## Reject and re-run if

- The exported artifact was compared against itself in two runtimes
- Differences were noted but not classified
- A tolerance was chosen to fit the observed data without saying so
- Depth values were compared numerically as if they had a scale
- One image was tested and the report implies general agreement
- A disagreement was fixed by adjusting the app without identifying which side was wrong
