# Prompt — the overlay and the fourth coordinate space

**When:** Lesson 05, step 6.

**Which agent:** `mobile`.

**Credits: zero.**

---

⚠️ This is Lesson 04's hardest bug, one process boundary later. The fusion layer failed
by mixing three coordinate spaces that all held numbers in the low hundreds. This adds a
fourth, and the same property makes it dangerous: a wrong transform puts boxes somewhere
plausible rather than somewhere obviously broken.

---

## Round 1 — print the spaces before transforming between them

```
Use the mobile agent.

Before writing any overlay code, take one photo and print, for that single request:

  - The camera's captured image dimensions
  - The dimensions of the image AFTER on-device preparation — what was actually uploaded
  - The image dimensions the server reports back, if the response carries them
  - One raw box from the response, verbatim
  - The on-screen size of the view the photo is displayed in, in density-independent
    points, from onLayout
  - The device's pixel ratio

Print all six. Do not write a transform yet.
```

**This is the same round 1 as the fusion prompt, and for the same reason.** Every one of
those numbers is knowable and three of them are routinely assumed. In particular: the
server's boxes are in pixels of the **uploaded** image, which is not the camera's native
resolution once step 7 downscales — and the display view is in points, which are not
pixels on any modern device.

If the response does not carry the image dimensions it processed, that is a finding worth
raising. The client can compute the transform from what it uploaded, but a response that
states its own frame is a response that cannot be misread.

---

## Round 2 — one named function

```
Write app/src/geometry/toScreen.ts with exactly one exported transform:

  export function imagePixelsToScreenPoints(
    box: BoxXYXYImagePixels,
    uploadedImageSize: { width: number; height: number },
    screenViewSize: { width: number; height: number },
  ): BoxXYXYScreenPoints

Requirements:
  - Both coordinate spaces named in the types. Not `number[]`.
  - Handle the letterboxing: the view's aspect ratio will not match the image's, so
    state whether the image is fitted-within or cropped-to-fill, and account for the
    offset. Getting this wrong is a constant pixel shift that looks like a bad model.
  - Clamp to the view bounds; a box partly outside the frame is normal.
  - Pure. No React, no hooks, no side effects.

Then write app/src/geometry/toScreen.test.ts with hand-computed expected values:
  - A square image in a square view — identity scaling
  - A landscape image in a portrait view — letterboxed with a vertical offset
  - A box at the exact image edge lands at the exact view edge
  - A box larger than the image clamps rather than overflowing
```

**Why a separate file for four lines of arithmetic.** Because inline in a render method it
cannot be tested, and this is the calculation most likely to be subtly wrong. Lesson 04
made the same call about `fusion.py` for the same reason: the pure function is the one you
can prove.

---

## Round 3 — render, and say nothing about metres

```
Write app/src/components/DetectionOverlay.tsx:

  - Boxes positioned via imagePixelsToScreenPoints, with the class label
  - Convey relative_depth by ORDERING and SHADING — nearer objects more prominent
  - A legend that says "nearer" and "farther"

Absolutely no distance, no unit, no number that a user would read as one. relative_depth
is relative inverse depth with no scale; it is comparable within one response and
meaningless across two. If you cannot express something without implying a distance,
say so and stop rather than approximating.
```

**The `units_guard` hook does not reach `app/`.** It blocks metric identifiers in `src/`;
here the rule is the same and the enforcement is gone. This is the one place in the whole
project where the constraint reaches a human's eyes, and it is the one place nothing
mechanical is checking it.

---

## Round 4 — rotate the phone

```
Run at these and confirm the boxes still land:
  - Portrait, 4:3 photo
  - Landscape, 4:3 photo
  - Portrait, 16:9 photo

Show me a screenshot of each.
```

A transform that assumes one orientation works perfectly until it is rotated, and the
failure is a uniform offset — which reads as a bad model rather than as bad arithmetic.

---

## What good output looks like

- Round 1 printed all six real numbers from one real request
- One exported transform, both spaces in the signature, pure and tested
- Letterbox offset handled explicitly and named
- Tests assert hand-computed values, not snapshots
- Boxes land at three aspect ratios
- Depth conveyed by ordering and shading, never by a number

## Reject and re-run if

- Coordinate arithmetic appears inline in a component
- The transform takes `number[]` and returns `number[]`
- Letterboxing is unhandled, or handled by assuming the aspect ratios match
- Tests are snapshots rather than computed expectations
- Any distance, unit, or depth value is displayed
- It was only tested in one orientation
