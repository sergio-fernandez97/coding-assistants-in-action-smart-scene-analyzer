# Prompt — both models, on your own camera

**When:** Lesson 03, step 6. **In session.** Budget 20 minutes.

**Which agent:** `evaluation` for the write-up. The capture itself is you and a script.

**Credits: zero.** Everything here runs locally on a frame that never leaves your machine.

---

## Why this step exists

Every number this lesson has produced so far came from the test split — images captured by
the same sensor family, in the same kind of room, annotated by the same process. That is a
comfortable place to be wrong.

Your webcam is none of those things. A model that scores well on the split and falls apart
on your desk has told you something no metric in this lesson would have, and it takes
ninety seconds to find out.

This is also the first time detection and depth run on the same pixels and produce one
answer. That fusion is the whole product, and Lesson 04 exports it. Seeing it work — or
not — on a real frame is worth more than reading about it.

---

## Round 1 — capture and look

```bash
uv run python scripts/check_live_capture.py --camera 0
```

No webcam, or the camera permission is a fight? Use any photo instead:

```bash
uv run python scripts/check_live_capture.py --image <some-photo>.jpg
```

It writes `live_capture_annotated.png` and `live_capture_depth.png`. **Open both.** The
script does not open a window — the project depends on `opencv-python-headless`, which has
no GUI backend, and that is a deliberate dependency choice rather than an oversight.

**Expected result:** a table of detections sorted near to far, and two PNGs.

---

## Round 2 — the two questions no metric answers

Look at the annotated image and answer these out loud before reading further:

1. **Are the boxes on the right things, and what is missing?**
2. **Is the near-to-far order right?** Nearer surfaces should be brighter in the depth PNG.

You are running **COCO-pretrained** weights, which know five of this project's eight
classes under their own names (verified against `yolo11n.pt`'s class list):

| ours | `bed` | `chair` | `sofa` | `table` | `tv` | `cabinet` | `door` | `lamp` |
|---|---|---|---|---|---|---|---|---|
| COCO | `bed` | `chair` | `couch` | `dining table` | `tv` | — | — | — |

`cabinet`, `door`, and `lamp` have no COCO equivalent and will not appear at all. Nor will
a coffee table, which COCO's `dining table` does not reliably fire on.

**That gap is the argument for fine-tuning**, and seeing your own desk half-labelled makes
it in a way a mAP table does not.

---

## Round 3 — write down what you saw

```
Use the evaluation agent.

I ran scripts/check_live_capture.py on a live frame with COCO-pretrained yolo11n and the
depth module from step 4. Here is the output: <paste the table>. The annotated image is at
<path>.

Write docs/live-validation.md. State:
  - The capture conditions: camera or file, resolution, lighting, what was in frame
  - Which taxonomy classes were findable with COCO weights and which cannot be
  - Whether the depth ORDERING matched what I can see, box by box
  - Any detection that got a `none` depth value, and which degenerate case caused it

Do not report an accuracy figure. One frame is not a rate, and a number here would be
read as one. This is a qualitative check and the document should say so in its first line.
```

**Expected result:** a short document that will read as evidence in three weeks, when
somebody asks whether the on-device path was ever tried on real input.

---

## After your homework training

Run the identical command against your own weights:

```bash
uv run python scripts/check_live_capture.py --camera 0 --weights runs/v1-baseline/weights/best.pt
```

Put the two annotated images side by side. The classes COCO could not see should now
appear, and the classes it could see may well be *worse* — 1,500 indoor images is a
narrower world than COCO, and narrowing is the trade you made. Both directions are worth
noticing, and the comparison belongs in `docs/model-card-v1.md` under known failure modes.

---

## What good output looks like

- Two PNGs written, and you opened them
- You can name a class the model cannot possibly find, and say why
- The near-to-far ordering was checked against your own eyes, not assumed
- `docs/live-validation.md` states its conditions and reports no accuracy figure
- Any `none` depth value is explained by a specific degenerate case from step 4

## Reject and re-run if

- The write-up quotes a percentage. One frame is not a rate
- The depth values are described as distances, or compared against another frame
- "It worked" appears without a box-by-box statement of what was found and missed
- The frame is near-black — the camera had not finished auto-exposing. Run it again
