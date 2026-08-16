# Prompt — the scene understanding layer

**When:** Lesson 04, step 3.

**Which agent:** `integration`.

**Credits: zero.**

---

## Where the bug lives

Three coordinate spaces are in play at once:

| Producer | Resolution |
|---|---|
| The source image | Whatever the camera or the picker gave you |
| YOLO11 | 640×640 internally, boxes usually rescaled back |
| Depth Anything V2 | Its own input size, output resized by your Lesson 03 module |

A box indexed into the wrong space **returns a number**. It is in range. It is the wrong
region of the image, and nothing in the type system, the schema, or a smoke test will
notice. This is the single most likely defect in the project, and the whole reason
`integration` is a separate role.

---

## Round 1 — establish the spaces before writing anything

```
Use the integration agent.

Before writing fusion code, establish the facts. Read
src/smart_scene_analyzer/depth.py and the ultralytics prediction path, then tell me:

  - What resolution does estimate_relative_inverse_depth return? Prove it by running it
    on two images of different sizes and printing the shapes alongside the input shapes.
  - What coordinate space do ultralytics boxes come back in — model input space, or
    original image space? Print a real prediction on a non-square image and check the
    box values against the image dimensions.
  - Do those two spaces match?

Do not write fusion code yet. I want the shapes printed from real runs, not inferred
from documentation.
```

**Why print rather than reason.** Both libraries do the sensible thing, and "the sensible
thing" is exactly what people assume without checking. A non-square test image is
essential — with a square one, a transposed or mis-scaled mapping still produces
plausible-looking indices.

---

## Round 2 — write the fusion

```
Now write src/smart_scene_analyzer/fusion.py.

Primary function: take a list of detections (each with an xyxy box in ABSOLUTE pixels of
the ORIGINAL image) and an HxW relative-inverse-depth map, and return fused results with
one depth value per detection.

Requirements:

1. Assert that the depth map's shape matches the image dimensions the boxes are expressed
   in. Do not silently resize to make it fit — raise with a message naming both shapes.
   A silent resize here is the bug this module exists to prevent.

2. Reduce each box region with the MEDIAN, not the mean. Justify it in the docstring: an
   occluder in front of the object skews the mean, and box corners routinely contain
   background.

3. Define and document the result for every degenerate case:
     - zero-area box
     - box partly outside the image (clip it — and say so)
     - box entirely outside the image
     - region empty after clipping
   Returning NaN is not a defined result — it propagates through comparison silently and
   sorts unpredictably. Decide, document, and make the choice visible to the caller.

4. Units, in every signature and docstring: relative inverse depth, larger = nearer,
   arbitrary scale, NOT metres, comparable only within one image. No identifier may
   contain meter, metre, mm, cm, or distance.

5. Keep the module PURE. Arrays and boxes in, structure out. No model loading, no file
   reads, no network, no Roboflow. That purity is what lets qa test it exhaustively without
   a GPU.

Add a helper that sorts detections near-to-far, since that is the one derived quantity
this data legitimately supports.
```

---

## Round 3 — prove it on a real scene

```
Run the full pipeline on a real test image with at least two objects at visibly different
distances. Show me:
  - the detections with their boxes
  - the relative depth value for each
  - the near-to-far ordering

Then run it again on the same image resized to a different aspect ratio, and confirm the
ORDERING is unchanged. The values may differ; the ordering must not.
```

**The aspect-ratio re-run is the real test.** If a coordinate-space mismatch exists, it
usually survives a square image and breaks on a non-square one — or produces an ordering
that flips when the aspect ratio changes. A single happy-path image proves almost nothing
here.

**Do:** Look at the numbers yourself. The object you can see is closest must have the
largest value.

---

## What good output looks like

- Round 1 printed real shapes from real runs, on a non-square image
- The shape assertion raises rather than resizing
- Median reduction, justified in the docstring
- All four degenerate cases defined and documented
- Units stated in every signature; no distance-implying identifier
- The module imports no model, touches no file, makes no request
- Ordering is stable across an aspect-ratio change

## Reject and re-run if

- Fusion code appears before the coordinate spaces were established from real output
- A mismatched depth map is silently resized to fit
- The reduction is a mean, or a median with no justification
- Degenerate boxes return `NaN` with no documented handling
- The module loads a model or reads a file — it is then untestable without a GPU, and
  `qa` will write worse tests as a direct consequence
- Verification used only one square image
