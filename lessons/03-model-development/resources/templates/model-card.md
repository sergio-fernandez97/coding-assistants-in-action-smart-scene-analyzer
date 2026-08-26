# Model card — `<model name>`

> Copy to your project as `docs/model-card-v1.md` / `docs/model-card-v2.md`.
> One card per trained model. A model referenced anywhere in this project without a card
> is a model nobody can reason about in three months.

## Identity

| Field | Value |
|---|---|
| Model name | `<v1-baseline>` |
| Architecture | `<yolo11n \| yolo11s>` |
| Task | Object detection |
| Base checkpoint | `<yolo11n.pt (COCO) \| runs/v1-baseline/weights/best.pt>` |
| Trained on | Dataset version `<N>` — **by number, never "the latest"** |
| MLflow run | `<run id / name>` |
| Weights | `<runs/.../best.pt>` — not committed |
| Git commit | `<sha of the code that produced this>` |
| Trained | `<YYYY-MM-DD>`, `<local \| Roboflow hosted>` |
| Credits consumed | `<0 \| ___>` |

## Exported artifact

> Filled in by **Lesson 04**, not this lesson. Leave it empty until the export exists —
> an empty row is a to-do, and a guessed row is a lie the app will act on.

The app assumes every value in this table and validates none of them at runtime. A wrong
one produces plausible garbage rather than an error, which is why they live with the model
rather than in the app that consumes them.

| Field | Value |
|---|---|
| Artifact | `<app/assets/models/....tflite \| ....pte>` — not committed |
| Format / backend | `<TFLite int8 \| ExecuTorch xnnpack>` |
| File size | `<N MB>` — also recorded in `docs/artifact-budget.md` |
| Input tensor | `<shape>`, `<dtype>`, `<NCHW \| NHWC>` — **the square is fixed by the course: `MODEL_INPUT` 640×640 for detection, `DEPTH_INPUT` 518×518 for depth. Both letterboxed.** Only the dtype and layout are yours to read off the export |
| Normalization | `mean=<...>`, `std=<...>` |
| Output tensors | `<count and order — the app decodes positionally>` |
| Label order | `<source of truth for class index → name>` |
| Quantization | `<none \| int8>`, calibration set `<which split, how many images>` |
| Parity vs PyTorch | `<tolerance accepted, and the worst per-class delta>` |
| Output raster space | `<depth only: the .pte returns its native 518×518 DEPTH_INPUT raster and does NOT resize inside the graph. The resize to MODEL_INPUT (handset) or SOURCE (reference) belongs to the depth boundary, never to fusion>` |
| Ordering preserved | `<depth only: does the export still rank near vs far correctly?>` |

## Training configuration

| Parameter | Value |
|---|---|
| Epochs | |
| Image size | `<640>` |
| Batch size | |
| Device | `<cpu \| mps \| cuda>` |
| Optimizer / LR | `<defaults, or state the change>` |
| Early stopping | `<yes at epoch N \| no>` |
| Wall time | |

Anything left at the framework default should say "default" rather than be omitted — the
distinction between "we chose this" and "we never looked" matters when someone tries to
improve the model later.

## Metrics

> **Every table states its conditions.** A metric without its split, dataset version, and
> confidence threshold is not a result.

**Measured on:** dataset version `<N>`, **`<test>`** split, `<___>` images,
confidence `<0.25>`, IoU `<0.5>`

| Class | Instances | Precision | Recall | mAP@50 | mAP@50-95 |
|---|---|---|---|---|---|
| `chair` | | | | | |
| `table` | | | | | |
| … | | | | | |
| **All** | | | | | |

Classes with fewer than 30 instances in this split — **rates below are noise, not
findings**: `<list, or "none">`

### Confusion

Top confusion pairs, and what they suggest:

| Predicted → Actual | Count | Reading |
|---|---|---|
| | | |

## Depth

This project's depth channel is **inference only**. It is not part of this trained model.

| Field | Value |
|---|---|
| Depth model | Depth Anything V2 `<size>`, pretrained, not fine-tuned |
| Output | **Relative inverse depth** — larger = nearer, arbitrary scale, **not metres** |
| Quantitative evaluation | **None.** No depth ground truth exists in this project |
| Validation performed | Relative-ordering checks on `<N>` real scenes |

**A downstream consumer must not** convert these values to a distance, compare them
across images, or average them into anything with physical units. Ordering within one
image is the only claim they support.

> Why there is no depth metric **in training**: Roboflow stores images and annotations,
> not depth maps, so no depth term could enter the training loop or a Roboflow-side
> evaluation. Recorded in `docs/requirements.md` — the Out-of-scope entry on metric depth,
> and N5, which replaced a metric-accuracy requirement with pairwise ordering.
>
> ⚠️ **This is not the same as having no reference at all.** If your source dataset ships
> depth (SUN RGB-D does), you can measure N5 — ordering only, never scale. Do not write
> "no evaluation is possible" into a card without checking what is on disk.
>
> ⚠️ **There is no depth-scope ADR**, though earlier drafts of this template claimed
> there was. Cite `docs/requirements.md`, or write the ADR.

## Comparison

Only for v2 and later. **Report both test splits.** A single number here is almost always
the flattering one.

**Conditions:** confidence `<0.25>`, IoU `<0.5>`, both models evaluated identically.

| | v1 test (`<N>` images) | v2 test (`<N>` images) |
|---|---|---|
| Model V1 mAP@50 | | |
| Model V2 mAP@50 | | |
| **Delta** | | |

**Verdict** (five sentences maximum, and it must address forgetting):

`<Did adaptation help on the new domain? Did it cost anything on the old one? Is the
trade worth it, under what deployment assumption? Is the difference large enough to be
meaningful at these split sizes?>`

## Known failure modes

**Write this yourself.** It requires having looked at predictions on real images, and it
is the section that saves the most time when something goes wrong in production.

- **Weakest classes, and why:** `<class — DATA / TAXONOMY / MODEL, with the evidence>`
- **Systematic errors:** `<e.g. boxes consistently loose on large objects>`
- **Confused pairs:** `<e.g. sofa ↔ chair on sectionals>`
- **Domain limits:** `<e.g. residential interiors only; no commercial or industrial>`
- **Lighting / capture:** `<e.g. degrades in low light; trained on one sensor family>`
- **Small objects:** `<e.g. objects under ~40px lost to the 640 resize>`
- **Inherited from the data:** `<point at the dataset card's limitations section>`

## Intended use

- **In scope:** `<indoor scene understanding for the Smart Scene Analyzer demo>`
- **Out of scope:** `<safety-critical use, distance measurement, outdoor scenes,
  anything requiring absolute depth>`

## Reproduction

```bash
uv run python scripts/train.py \
  --data <data/vN/data.yaml> --model <checkpoint> \
  --epochs <N> --name <run name>
```

Dataset version `<N>` is an immutable Roboflow snapshot; re-export it rather than reusing
a local copy of unknown provenance.

**Reproducible from this card alone?** `<yes / no — what is missing>`
