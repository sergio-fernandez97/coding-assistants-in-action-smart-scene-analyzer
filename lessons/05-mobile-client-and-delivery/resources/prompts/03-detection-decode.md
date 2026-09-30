# Prompt — decode raw detection output and run NMS

**When:** Lesson 05, step 6 — in the session.

**Which agent:** `mobile`.

**Credits: zero.**

---

⚠️ **This is the step most likely to produce confidently wrong output.** A server used to
decode, threshold, and suppress for you. All three are now yours, in TypeScript, against a
flat tensor of several thousand numbers. Every failure in this file looks like a bad model
rather than bad arithmetic.

---

## Round 0 — turn the picked image into pixels

```
Use the mobile agent.

Write app/src/inference/image.ts:

  export async function decodeImage(uri: string, originalSize: Size, longSide: number): Promise<RGBPixels>

  - Resize natively with expo-image-manipulator (the contextual ImageManipulator API;
    manipulateAsync is deprecated) so the long side is <longSide>, and save as JPEG base64.
  - Decode that small JPEG to RGB with jpeg-js. Drop the alpha channel.
  - Return the decoded size: this decoded image is the SOURCE space from now on.
```

The picker and the camera hand you a **URI**, and neither runtime decodes images: both take
raw tensors. Install the two dependencies first, from `app/`:
`npx expo install expo-image-manipulator jpeg-js`, then rebuild (`expo-image-manipulator`
is native).

---

## Round 1 — look at the actual tensor

```
Use the mobile agent.

Run one inference on a bundled test image and print, without decoding anything:

  - The output tensor's shape and dtype, verbatim from the runtime
  - Its length
  - The first 20 values
  - The min, max, and mean across the whole tensor

Then tell me what layout you think this is, and what evidence in those numbers supports
it. Do not write a decoder yet.
```

**Do not skip this and write the decoder from the model card.** Exported layouts differ
between exporter versions, and the two things most often wrong are whether coordinates are
normalized to `[0, 1]` or in input-pixel space, and whether the tensor is
`[1, features, anchors]` or `[1, anchors, features]`.

The min/max tell you the first of those in one glance: coordinates in `[0, 1]` and
coordinates in `[0, 640]` are not subtle once you look.

---

## Round 2 — decode

```
Write app/src/inference/decode.ts:

  export function decodeDetections(
    raw: Float32Array,
    layout: { anchors: number; features: number },
    inputSize: { width: number; height: number },
  ): DetectionModelInputPixels[]

Requirements:
  - Return boxes in MODEL-INPUT pixel space, xyxy. Name that in the type.
    Do not convert to screen space here — that is toScreen.ts's job in step 8.
  - Convert from whatever the model emits (cxcywh, normalized, or otherwise) explicitly,
    with a comment stating what the source format is and how you determined it.
  - Class index → label via the label order from the model card, imported from one place.
    Never a literal array inline.
  - Pure. No model, no I/O, no React.

Write decode.test.ts with a small hand-built tensor and hand-computed expected boxes.
```

**The label array is a single source of truth or it is a bug.** A second copy drifts the
moment the taxonomy changes, and the symptom is boxes labelled one class off — which reads
as a model problem for a long time before anyone suspects an array.

---

## Round 3 — non-maximum suppression

```
Add NMS:

  export function nms(
    detections: DetectionModelInputPixels[],
    iouThreshold: number,
  ): DetectionModelInputPixels[]

  - Standard greedy NMS, per class rather than across all classes.
  - State the IoU threshold and where the value came from.
  - Test: two heavily overlapping boxes of the same class collapse to one; two
    overlapping boxes of DIFFERENT classes both survive.

Do not reach for a library for this. It is thirty lines and you need to be able to say
what it does.
```

**Per class, not global.** A chair overlapping a table is two correct detections; global
NMS deletes one of them and the result looks like a recall problem in the model.

---

## Round 4 — look at it

```
Render the decoded boxes on the bundled test image and show me a screenshot.

Then run the SAME image through the Python reference and compare the box count and the
classes. Report any difference — do not fix it yet.
```

The comparison is cheap here and expensive later. If the counts already disagree, the
decoder is wrong and step 12's parity check will only tell you the same thing after two
more steps have been built on top of it.

---

## What good output looks like

- Round 1 printed the real tensor stats and reasoned from them to a layout
- The source format is named in a comment, with how it was determined
- Boxes are returned in a named space, not `number[]`
- The label order is imported from one place
- NMS is per class, threshold stated, tested on both the same-class and cross-class cases
- Box counts compared against the Python reference

## Reject and re-run if

- The decoder was written from the model card without inspecting the tensor
- Coordinate format was assumed rather than determined
- A label array appears inline
- NMS is global across classes
- Screen-space conversion happens inside the decoder
- Tests use snapshots rather than hand-computed values
