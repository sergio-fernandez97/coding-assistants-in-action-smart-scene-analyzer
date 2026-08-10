# Prompt — local YOLO11 training with MLflow

**When:** Lesson 03, step 4.

**Which agent:** `ml-engineer`.

**Credits: zero.** Everything runs on your machine. Iterate as much as you like — this
is the phase where free compute is worth the most.

---

## Round 1 — the training script

```
Use the ml-engineer agent.

Write scripts/train.py: fine-tune YOLO11 on an exported Roboflow dataset, tracking the
run in MLflow.

Arguments:
  --data          path to data.yaml (required)
  --model         base checkpoint, default yolo11n.pt
  --epochs        default 50
  --imgsz         default 640
  --batch         default 8
  --device        auto-detect cuda / mps / cpu, overridable
  --name          MLflow run name (required)
  --project       output directory for weights, default runs/

Log to MLflow, and be exhaustive about it — a run I cannot reproduce from its record
did not happen:
  params:   every argument above, plus the resolved device, the dataset version number
            parsed from the data path, the class list, and per-split image counts
  metrics:  mAP@50, mAP@50-95, precision, recall — final and per-epoch
  tags:     the git commit SHA of the working tree
  artifacts: data.yaml, the results plots, and the confusion matrix ultralytics emits

Requirements:
- Read MLFLOW_TRACKING_URI from the environment. Fail with a clear message if it is
  unset, rather than silently logging to ./mlruns.
- If the working tree is dirty, log a tag saying so. A run tagged with a commit that
  does not describe the code that produced it is worse than an untagged run.
- Print the final metrics table to stdout as well as logging it.
- Do NOT commit weights. Confirm runs/ and *.pt are gitignored before finishing.

Do not start a training run yet. Show me the script first.
```

**Why the dataset version is a logged parameter.** In three weeks you will have a model
file and a question about what it was trained on. The answer has to be in the run record,
because it is not in the weights and it is not in the filename you will have renamed.

---

## Round 2 — a short run first

```
Run it for 3 epochs on data/v1/data.yaml with --name smoke-test, and show me the MLflow
run afterwards.
```

**What to check before committing to a real run:**

- The run appears in the MLflow UI with all parameters populated
- The dataset version, class list, and split counts are logged and correct
- The class list matches `docs/taxonomy.md` in name **and** order
- The device resolved to what you expected — a silent fall back to CPU on a GPU machine
  turns a 20-minute run into a 3-hour one

A 3-epoch model is useless and that is fine. You are testing the plumbing, and the cost
of finding a broken parameter now versus 50 epochs from now is the whole point.

---

## Round 3 — the real run

```bash
uv run python scripts/train.py --data data/v1/data.yaml --model yolo11n.pt \
  --epochs 50 --name v1-baseline
```

Sizing, so you do not lose the session to a queue:

| Hardware | Model | Epochs | Batch | Rough time on 1,500 images |
|---|---|---|---|---|
| CPU only | `yolo11n` | 25–50 | 8 | ~1 hour |
| Apple Silicon (`mps`) | `yolo11n` / `yolo11s` | 50 | 16 | ~20–30 min |
| NVIDIA GPU | `yolo11s` | 100 | 16 | ~20 min |

**Start smaller than you think you need.** A finished 25-epoch run tells you more than a
75-epoch run you killed at epoch 40 because the session ended.

**Watch the first five epochs.** If the loss is flat or `NaN`, stop. Common causes, in
order of likelihood: label coordinates outside `[0, 1]` (which `verify_export.py` should
have caught), a class-count mismatch between `data.yaml` and the labels, or a learning
rate that is wildly wrong for the batch size.

---

## What good output looks like

- The script fails loudly on a missing `MLFLOW_TRACKING_URI` rather than logging somewhere
  you will not look
- Dataset version, class list, and split counts are in the run record
- The git SHA is tagged, with a dirty-tree tag when applicable
- The final metrics printed to stdout match what MLflow shows
- `git status` shows no `.pt` files and no `runs/`

## Reject and re-run if

- The dataset path or version is hardcoded — you need to run this again for v2
- MLflow logging is added as an afterthought around a training call, rather than the run
  being the unit of work
- Metrics are logged without the parameters that produced them
- The agent starts a 100-epoch run before you have seen a smoke test
- Weights get committed
