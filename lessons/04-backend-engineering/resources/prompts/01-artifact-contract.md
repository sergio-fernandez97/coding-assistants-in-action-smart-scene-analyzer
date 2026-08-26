# Prompt — define the artifact contract before exporting

**When:** Lesson 04, step 2.

**Which agent:** `ml-engineer`.

**Credits: zero.**

---

For three lessons the models were things you called, and Python checked their inputs and
outputs at every boundary. From here they are **files**, and a file makes promises nothing
verifies.

Write the promises down first. An export that surprises you is information; an export whose
contract you invented afterwards to match what it produced is not.

---

## Given, before you start: the input geometry is already decided

Two of the rows you are about to fill in are **course facts, not exercises**. They are
fixed here because getting them wrong costs a re-export, and because one of them is
arithmetic rather than judgement.

| Space | Size | Fed to |
|---|---|---|
| `MODEL_INPUT` | **640 × 640**, letterboxed | YOLO11 detection |
| `DEPTH_INPUT` | **518 × 518**, letterboxed | Depth Anything V2 |

Both are the same letterbox — aspect preserved, centre-padded, never stretched — of the
same `SOURCE` image, at two edge lengths.

**Why two squares and not one.** Depth Anything V2 Small is a ViT-**S/14**: every input
edge must be a multiple of 14, and `640 / 14 = 45.71`. The detection square is not a legal
input to the depth model. The nearest square legal for both is 672 (`14 × 48 = 32 × 21`),
and it was rejected: 672² is 2,304 patches against 518²'s 1,369 — 68% more work on the
slower of the two models, on every inference — and it would re-export detection at a size
the model was never evaluated at.

**Why the second square is affordable.** The two differ by one uniform factor and nothing
else, because the padding scales with the image:

```
scale_depth = scale_model × (518 / 640)
padX_depth  = padX_model  × (518 / 640)
padY_depth  = padY_model  × (518 / 640)
```

So a depth raster resampled from 518² to 640² lands in exact `MODEL_INPUT` geometry — a
uniform resize, **with no offset term to forget**. That resize belongs to the depth
boundary, not to fusion. Fusion still asserts and never converts.

Take both as given. Everything else in this prompt is yours to determine.

---

## Round 1 — what does the app actually need to know?

```
Use the ml-engineer agent.

Before exporting anything, list every fact about an exported model that a consuming
application must know and CANNOT determine at runtime.

For each one, say what goes wrong if it is wrong — specifically. "It breaks" is not an
answer; "boxes appear at half scale" is.

Do not write export code yet.
```

The point of doing this before the export exists is that afterwards you will be reading
values off a file, and it is much harder to notice that a fact is *missing* than that a
value is wrong.

---

## Round 2 — write it into the model card

```
Fill in the "Exported artifact" table in docs/model-card-<name>.md for BOTH models, with
what you intend to produce:

  - Artifact filename and format
  - Input tensor: shape, dtype, layout (NCHW or NHWC)
  - Normalization: mean and std, per channel
  - Output tensors: how many, in what order, what each contains
  - Label order, and the single source of truth for it
  - Quantization, and the calibration set

Mark every value as INTENDED. Step 4 replaces them with what the export actually did.
```

**Label order needs one source of truth and one only.** It exists in `docs/taxonomy.md`, in
the training data YAML, and it will exist in the app. Three copies drift; name which one is
authoritative and derive the rest.

---

## Round 3 — the failure modes, concretely

```
For each of these, state the symptom a developer would actually observe:

  - NCHW artifact, NHWC assumed by the consumer
  - ImageNet normalization applied to a model expecting [0, 1]
  - Output tensors decoded in the wrong order
  - Label list off by one
  - Coordinates assumed normalized when they are in input pixels

Then say which of the five would be caught by a type checker, and which would not.
```

The answer to the last question is "none of them", and that is the point of the exercise.
This is the contract the type system cannot defend, which is exactly why it is written in
prose and checked by hand.

---

## What good output looks like

- The list in round 1 names a specific observable symptom per fact
- Both model cards have a complete **Exported artifact** table, marked INTENDED
- Label order has exactly one named source of truth
- The student can state why no type checker catches any of the five failures

## Reject and re-run if

- Export code was written before the contract
- Any contract row is left blank without being flagged
- Label order is described as living in more than one authoritative place
- The failure modes are described as "it breaks" rather than by symptom
