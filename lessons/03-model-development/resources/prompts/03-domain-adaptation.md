# Prompt — domain adaptation and the V1-vs-V2 comparison

**When:** Lesson 03, step 6.

**Which agent:** `ml-engineer` to train, `evaluation` to compare. Keep them separate.

**Credits: zero.**

---

## The experiment

V2 stands in for newly acquired production data. The question the whole course is built
around: **does adapting the model to it help, and what does adapting cost?**

That is two questions, and answering only the first is how models get shipped that are
better on the new data and worse on everything else.

---

## Round 1 — export v2 and train

```
Use the ml-engineer agent.

Export dataset version 2 to data/v2/, then verify it before training:
  uv run python scripts/verify_export.py data/v2 --taxonomy docs/taxonomy.md

Confirm explicitly that data/v2/data.yaml's class list is identical to data/v1/data.yaml's
in NAME and ORDER. If it is not, stop — the comparison is invalid and no amount of
training fixes it.

Then fine-tune from model V1's weights, not from COCO:

  uv run python scripts/train.py \
    --data data/v2/data.yaml \
    --model runs/v1-baseline/weights/best.pt \
    --epochs 50 --name v2-adapted

Log to MLflow with the base checkpoint recorded as the V1 run, not as a file path — I
want to trace the lineage from the run record.
```

**Why fine-tune from V1 rather than from COCO.** Training from COCO on v2 gives you a
second independent model, which answers a different and less interesting question. The
production scenario is: you have a deployed model, new data arrives, you adapt. Starting
from V1's weights is what makes this domain *adaptation* rather than a second baseline.

---

## Round 2 — the three comparisons

```
Use the evaluation agent.

Compare model V1 (runs/v1-baseline/weights/best.pt) and model V2
(runs/v2-adapted/weights/best.pt) on BOTH test splits.

Produce three tables, each with its measurement conditions stated:

  1. Both models on the v1 test split  — did adaptation break the original domain?
  2. Both models on the v2 test split  — did adaptation work?
  3. A side-by-side summary of the trade-off

For each, report aggregate mAP@50 and mAP@50-95, and per-class deltas.

Then give me a plain-language verdict of at most five sentences. It must address:
  - Did V2 improve on the new domain, and by how much
  - Did V2 degrade on the old domain, and by how much
  - Whether the trade is worth it, and under what deployment assumption
  - Whether any difference is large enough to be meaningful given the test-split sizes

"No significant difference" is a valid and useful verdict. Say it if it is true. Do not
manufacture a story out of a 0.4-point move on 150 test images.
```

**Catastrophic forgetting is the thing to watch for.** A model fine-tuned on a new domain
routinely loses ground on the old one — sometimes a lot, and the loss does not appear
anywhere in the metrics you would naturally look at, because you would naturally look at
the new domain's numbers. Table 1 exists to make it impossible to miss.

---

## Round 3 — what actually differed

```
The two datasets differ in two ways: the images (sensors, rooms, lighting) and the
annotation conventions (different annotators, different granularity).

Lesson 02's taxonomy mapping was supposed to hold the second constant so this experiment
measures the first. Check whether it did:

  - For the three classes with the largest V1-to-V2 metric change, look at the taxonomy
    mapping rows for both source datasets. Could a mapping difference explain the change
    rather than a domain shift?
  - Are per-class instance counts comparable between the two test splits? A class with
    200 instances in v1 test and 12 in v2 test cannot be compared across them.

Report anything that would make the comparison measure something other than domain shift.
```

**This is the round most likely to invalidate a satisfying result**, which is exactly why
it is in the prompt rather than left to the reader's conscience. A metric change caused by
`night_stand` mapping to `table` in one dataset and `cabinet` in the other is a bookkeeping
artifact wearing a domain-shift costume.

---

## What good output looks like

- `verify_export.py` passed on v2, and the class-list identity was checked explicitly
- V2 was fine-tuned from V1's weights, with the lineage traceable in MLflow
- **All three** comparison tables present — not just the flattering one
- Per-class deltas, not only aggregates
- The verdict names both the gain and the loss
- Test-split sizes are stated, so the reader can judge whether a delta is signal
- Round 3 either clears the taxonomy of responsibility or names a specific suspect row

## Reject and re-run if

- Only the v2 test split is reported. This is the most common failure and it always
  favours V2
- The class lists were assumed identical rather than checked
- V2 was trained from COCO, making it a second baseline rather than an adaptation
- A verdict of "V2 is better" appears without a forgetting number next to it
- Per-class deltas are quoted for classes with a handful of test instances
- The agent explains a metric change by domain shift without ruling out the taxonomy
