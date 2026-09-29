# Prompt — the overlay and the letterbox offset

**When:** Lesson 05, step 8 — in the session.

**Which agent:** `mobile`.

**Credits: zero.**

---

⚠️ This is Lesson 04's hardest bug, moved onto the device. The fusion layer failed by
mixing coordinate spaces that all held numbers in the low hundreds. The same property makes
this dangerous: a wrong transform puts boxes somewhere plausible rather than somewhere
obviously broken.

There are three spaces now, not four. The upload space is gone — but the **letterbox**
space replaced it, and that is not a simplification. An uploaded image was uniformly
scaled. A letterboxed one has bars, which means an offset, which is the term people drop.

---

## Round 1 — print the spaces before transforming between them

```
Use the mobile agent.

Before writing any overlay code, run one inference and print, for that single image:

  - The source image dimensions
  - The model's input dimensions
  - The scale factor and the X and Y padding your letterbox applied
  - One raw decoded box, verbatim, in model-input pixels
  - The on-screen size of the view the image is displayed in, in density-independent
    points, from onLayout
  - The device's pixel ratio

Print all six. Do not write a transform yet.
```

**This is the same round 1 as the fusion prompt, for the same reason.** Every one of those
numbers is knowable and three are routinely assumed. In particular: the scale and padding
must come from the preprocessing step that produced them, not be recomputed here. Two
copies of that arithmetic is two chances to be inconsistent.

---

## Round 2 — one named function

```
Write app/src/geometry/toScreen.ts with exactly one exported transform:

  export function modelInputPixelsToScreenPoints(
    box: BoxXYXYModelInputPixels,
    letterbox: { scale: number; padX: number; padY: number },
    sourceImageSize: { width: number; height: number },
    screenViewSize: { width: number; height: number },
  ): BoxXYXYScreenPoints

Requirements:
  - Both coordinate spaces named in the types. Not `number[]`.
  - Undo the letterbox FIRST — subtract the padding, divide by the scale — to get back to
    source-image pixels. Then map source pixels to the view.
  - Handle the view's own letterboxing: its aspect ratio will not match the image's.
    State whether the image is fitted-within or cropped-to-fill.
  - Clamp to the view bounds; a box partly outside the frame is normal.
  - Pure. No React, no hooks, no side effects.

Then write app/src/geometry/toScreen.test.ts with hand-computed expected values:
  - A square image, square model input, square view — identity
  - A landscape image letterboxed into a square model input — vertical padding, and a
    box at the top edge of the CONTENT must not land at the top edge of the view
  - A box at the exact image edge lands at the exact view edge
  - A box larger than the image clamps rather than overflowing
```

**The second test case is the one that matters.** Forgetting the padding subtraction is
correct for square images and wrong for every other shape, which means it passes the first
test and ships.

---

## Round 3 — render, and say nothing about metres

```
Write app/src/components/DetectionOverlay.tsx:

  - Boxes positioned via modelInputPixelsToScreenPoints, with the class label
  - Convey relativeDepth by ORDERING and SHADING — nearer objects more prominent
  - A legend that says "nearer" and "farther"
  - Zero detections renders as a clear success state, visibly different from
    "still loading" and from "the model failed to load"

Absolutely no distance, no unit, no number a user would read as one.
```

**`units_guard` now reaches this file.** It blocks metric identifiers in `app/*.tsx` as
well as `src/`. That is a change from the previous architecture, where the client only
displayed a number computed elsewhere — but the hook catches identifiers, not prose, and a
string like "about 2 m away" will pass it and fail the manual grep in Verification. The
rule is still yours to keep; the hook is a backstop.

---

## Round 4 — rotate it

```
Run at these and confirm the boxes still land:
  - Portrait, 4:3 image
  - Landscape, 4:3 image
  - Portrait, 16:9 image

Show me a screenshot of each.
```

A transform that assumes one orientation works perfectly until it is rotated, and the
failure is a uniform offset — which reads as a bad model rather than as bad arithmetic.

---

## What good output looks like

- Round 1 printed all six real numbers from one real inference
- Scale and padding came from preprocessing, not recomputed
- One exported transform, both spaces in the signature, pure and tested
- The letterbox offset is undone explicitly, and the non-square test case proves it
- Tests assert hand-computed values, not snapshots
- Boxes land at three aspect ratios
- Depth conveyed by ordering and shading, never by a number

## Reject and re-run if

- Coordinate arithmetic appears inline in a component
- The transform takes `number[]` and returns `number[]`
- Letterbox padding is recomputed rather than passed in
- The padding subtraction is missing and only square images were tested
- Tests are snapshots rather than computed expectations
- Any distance, unit, or depth value is displayed
- It was only tested in one orientation
