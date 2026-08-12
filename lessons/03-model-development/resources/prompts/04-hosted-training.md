# Prompt — the one hosted training run

**When:** Lesson 03, step 8. **Optional.**

**Which agent:** `ml-engineer`.

**Budget: 2 credits.** GPU training bills at **1 credit per 30 minutes**.

> ⛔ **Do not run this with fewer than 3 credits remaining.** Check
> `docs/credit-budget.md` first. Skipping this step costs you one comparison row and no
> deliverable. Overrunning the budget costs you Lesson 06.

---

## What this is for

You have a locally trained model. This step trains the same architecture on Roboflow's
infrastructure so you can compare the two paths on evidence rather than assumption — and
so that Lesson 04 has a hosted endpoint to benchmark against.

It is also the one moment in this course where the permission rule you wrote in Lesson 02
step 4 fires on something that genuinely matters. Pay attention to how that feels.

---

## Round 1 — the estimate, before anything is called

```
Use the ml-engineer agent.

I want ONE hosted training run on Roboflow, dataset version 1, for comparison against my
local YOLO11 fine-tune. Before you call any tool, give me:

  1. The exact model_id, read from roboflow:training-and-evaluation. I want yolov11s to
     match my local architecture — confirm that is the correct ID string and not a guess.
  2. The epoch count you propose, and your reasoning for it.
  3. The expected wall-clock time, and how you estimated it.
  4. The credit cost: show the arithmetic against the 1-credit-per-30-minutes rate.
  5. My remaining balance, read from docs/credit-budget.md.
  6. What happens if the estimate is wrong in the expensive direction, and how I would
     stop it.

Constraints:
  - Cap the run so wall time stays under one hour. Two credits is the ceiling.
  - Do NOT use RF-DETR NAS. Do not propose it. See the Credit budget section of CLAUDE.md.
  - Do not call trainings_create in this round.
```

**Expected result:** six answers, with arithmetic shown. If the agent proposes NAS despite
the constraint, that is worth noticing — it means the skill's default is strong enough to
override a written project rule, which is precisely why the rule is also in
`.claude/settings.json` where it cannot be argued with.

---

## Round 2 — record, then approve

**Do:** Write the estimate into `docs/credit-budget.md` *before* approving anything.

| Date | Lesson | Operation | Rate | Estimated | Actual | Remaining |
|---|---|---|---|---|---|---|
| `<date>` | 03 | Hosted training, `yolov11s`, `<N>` epochs | 1 cr / 30 min | 2.0 | | |

Recording the estimate first is not bureaucracy. It is what makes the estimate falsifiable
— a number written after the fact is a description, not a prediction, and you learn
nothing from it.

**Do:** Then let the agent proceed.

```
Start the run.
```

Your permission rule fires. **Read the prompt before approving.** You are looking at a
specific, billed, irreversible operation with a cost attached. Approving it should feel
different from approving a file write.

---

## Round 3 — monitor, and know your stop buttons

```
Poll the training status with models_get_training_status every few minutes and report
progress. Tell me the elapsed time against your estimate as you go.

If elapsed time passes your estimate by more than 25%, stop reporting progress and tell
me directly, with the credit implication.
```

Know these before you need them:

| Control | Effect | Billing |
|---|---|---|
| **Cancel Training** | Stops the job, **no weights saved** | Refund if cancelled early |
| **Early Stopping** | Stops the job, **saves weights** | Charges for credits used |

If the curves converge at epoch 30 of 100, **Early Stopping** is what you want — it keeps
the model and stops the meter. Cancelling throws the model away. These are not
interchangeable and the difference is not obvious at 11pm.

---

## Round 4 — compare, and hit the wall deliberately

```
Report the hosted model's metrics and compare them against my local V1 run on the same
dataset version. Note where the comparison is not apples-to-apples: different training
code, different augmentation handling, different default hyperparameters.

Then tell me how I would load these hosted weights into my local FastAPI service in
Lesson 04. Check roboflow:plans-and-pricing for what my plan permits before answering.

Finally: append the ACTUAL credit cost to docs/credit-budget.md and reconcile it against
the estimate. If they differ, say why.
```

**Expected result:** the agent reports that **weight downloads are a Core-plan feature**
and that on the free Public plan the hosted model is reachable only through the hosted API.

**That is the intended outcome, not a failure.** It is why Lesson 04's service loads local
weights and benchmarks the hosted endpoint over HTTP instead of collapsing the two into
one. A constraint you discovered by asking is a design input; the same constraint
discovered in Lesson 04 with the service half-built is a rewrite.

---

## What good output looks like

- The `model_id` was read from the skill and quoted exactly, not recalled
- Arithmetic shown for the credit estimate, against the stated rate
- The estimate is in the ledger *before* the run starts
- The agent surfaced elapsed-vs-estimate during the run without being asked again
- Actual cost recorded and reconciled, with an explanation of any gap
- The weight-download limitation was found by consulting the skill, not by failing

## Reject and re-run if

- Any tool is called in round 1
- RF-DETR NAS is proposed, started, or described as the recommended option
- The estimate is given without arithmetic, or without your remaining balance
- The run is started before the estimate is in the ledger
- The uncapped epoch default (200 for some architectures) is accepted unexamined
- The agent reports the hosted weights as downloadable without checking the plan
