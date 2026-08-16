# Prompt — prove the export is still the model

**When:** Lesson 04, step 6.

**Which agent:** `qa`, with `ml-engineer` interpreting the result.

**Credits: zero.**

---

Step 4 produced files that load and run. This step asks the different question: **do they
still behave like the models you trained?**

The two claims are separated by quantization, a resize implementation, and a normalization
step — any of which can be subtly wrong in a way that produces output no smoke test would
flag.

---

## Round 1 — the harness

```
Use the qa agent.

Write tests/test_export_parity.py:

  - Load a small, fixed set of test images (5-10, committed as a fixture list of paths,
    not as binaries).
  - Run each through the ORIGINAL PyTorch model and through the EXPORTED artifact.
  - Mark the whole module with the `integration` marker — it needs weights on disk, so
    the default suite must still pass without it.

Assert nothing yet. Print both result sets.
```

**Compare against PyTorch, never against the export run in a second runtime.** Comparing an
artifact to itself confirms only that two libraries can read one file. The question is
whether the file still matches the training.

---

## Round 2 — detection parity, per class

```
Assert detection parity:

  - Classes must match.
  - Boxes must match within an IoU tolerance. State the tolerance and justify it.
  - Confidences will NOT match exactly — int8 shifts them. Assert a bound on the shift
    rather than equality.

Report the PER-CLASS delta, not just the aggregate. Produce a table:
class, PyTorch detections, exported detections, mean IoU, mean confidence delta.
```

**Aggregate mAP is the wrong instrument here.** int8 quantization can destroy one class
while barely moving the aggregate, and a single number is exactly what hides that. The
per-class table is the deliverable; the aggregate is a summary of it.

---

## Round 3 — depth parity is an ordering check

```
Assert depth parity:

  - Do NOT compare depth values numerically. The output is relative inverse depth with an
    arbitrary scale; magnitudes across two runtimes are not comparable and an assertion
    on them is meaningless even when it passes.
  - Instead: for each test image, take several regions and assert that their near-to-far
    RANKING is identical between PyTorch and the export.
  - Assert the sign convention explicitly: larger is nearer, on both.

If the ranking inverts, fail loudly. Do not add a negation to make it pass.
```

**This is the only correctness property depth has.** There is no ground truth and no unit,
so ordering is not a weaker check than a numeric one — it is the whole of what "correct"
can mean here.

---

## Round 4 — record it where it will be read

```
Write the results into the model card's "Exported artifact" table:

  - The parity tolerance accepted, for each model
  - The worst per-class confidence delta, and which class
  - Whether depth ordering is preserved

Then state plainly: is the exported model good enough to ship? If a class regressed badly
enough that you would not ship it, say so and say what you would do — re-export at fp16,
change the calibration set, or accept it with the regression documented.
```

---

## What good output looks like

- Compared against the PyTorch original, not the export in another runtime
- Marked `integration`; the default suite still passes without weights
- Tolerances stated and justified, not chosen to fit
- A per-class delta table, not just an aggregate
- Depth checked by ranking, with the sign convention asserted
- Results recorded in the model card
- A plain ship / do-not-ship verdict

## Reject and re-run if

- The exported artifact was compared against itself in two runtimes
- Depth values were compared numerically
- An inverted depth ranking was fixed with a negation rather than reported
- Only aggregate metrics are reported
- The tolerance was set after seeing the results, without saying so
- The test module runs in the default suite and breaks it on a machine with no weights
