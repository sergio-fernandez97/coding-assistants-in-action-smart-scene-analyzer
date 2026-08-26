# Prompt — point the fusion layer at your own room

**When:** Lesson 04, step 3b. **In session.** Budget 15 minutes.

**Which agent:** `integration`.

**Credits: zero.** Your webcam, your machine, your models.

---

You have just written a fusion layer and proved it on a dataset image. Every image in that
dataset came from the same sensor family, in the same kind of room, annotated by the same
process. Your desk is none of those.

`docs/evaluation-v1.md` measures the model. This measures nothing — it shows you a frame
and lets you disagree with it. A model that scores well on the split and falls apart on
your own room has told you something no metric in this lesson would have.

**You are writing this script, not copying it.** It is about fifty lines of wiring, and
the wiring is the point: it is the first code in this project that puts detection, depth,
and fusion on the same pixels and has to get the coordinate space right to produce
anything at all.

---

## Round 1 — write it

```
Use the integration agent.

Write scripts/check_fusion_live.py: run detection, depth, and the fusion layer on ONE
frame from my webcam, and show me the result.

Requirements:

1. Source is --camera N (default 0) or --image PATH. Both, not one.

2. Discard the first several frames before keeping one. Most webcams need a moment to
   finish auto-exposure, and the first frame is routinely near-black. A near-black frame
   produces a confident, meaningless depth map.

3. cv2 hands back BGR. Everything downstream assumes RGB. Convert explicitly and say so
   in a comment — a silent swap here is wrong everywhere and obviously wrong nowhere.

4. Default --weights to the model I actually trained if it is on disk, and fall back to
   the COCO checkpoint if it is not. Print which one it used.

5. Run the REAL fusion layer — fuse_detections_with_depth and sort_near_to_far — not a
   reimplementation of the reduction. Build proper Detection records from the ultralytics
   output. This script exists to exercise that module.

6. Print a near-to-far table with: rank, class, confidence, relative depth value, the
   spread inside the box, the pixel count sampled, and the depth_quality flag. Rank
   first, value second — the rank is the part that means something.

7. Write two PNGs: the frame with boxes drawn and labelled, and the depth map as
   grayscale with nearer brighter.

8. Zero detections is a successful result with an empty list, and must print as one -
   not as an error and not as silence.

The project depends on opencv-python-headless, which has NO GUI backend. cv2.imshow
raises. Write files; do not try to open a window.

Units, in every place a number is printed: relative inverse depth, larger is nearer,
no unit, no scale, comparable only within one frame. No identifier and no printed
string may imply a physical measurement.
```

**Why the script must call the real fusion layer.** A verification script that
reimplements the thing it verifies proves that two pieces of code you wrote in the same
hour agree with each other. Import the module.

---

## Round 2 — run it and disagree with it

```
Run it on my webcam. Then tell me what you see, and separate three things:

  - detections that are wrong (missed object, wrong class, loose box)
  - depth ordering that is wrong
  - depth quality flags that are RIGHT — a box that deserved its mixed_region

Do not summarise these as "it works reasonably well".
```

**Do:** Open both PNGs and look. Three questions, in this order:

1. **The boxes.** Right objects? Anything obvious missed? `cabinet`, `door`, and `lamp`
   are the rare classes and are where you should expect to be disappointed.
2. **The near-to-far ORDER**, not the values. Is the nearest thing ranked first?
3. **The quality flags.** `mixed_region` means the box straddles a real depth
   discontinuity and the layer is disclosing that its single value summarises two
   different things. A frame full of them usually means loose boxes, not broken depth.

---

## Round 3 — write down what you found

```
Fill in the "Known failure modes" section of docs/model-card-v1.md with what we just
saw on real frames, not with what the metrics say. Name the class, the symptom, and
the evidence — the frame it happened on.

Where a failure looks like a data problem rather than a model problem, say so and say
why. Use the error-triage skill's DATA / TAXONOMY / MODEL / EXPORT classification.
```

**This is the section that saves the most time later and the one nobody writes**, because
it is the only part of a model card that cannot be generated from a metrics table. You now
have the one thing it requires: having looked at predictions on real images.

---

## Optional — the live viewer

A continuous version is provided rather than written:
[`resources/scripts/watch_fusion_live.py`](../scripts/watch_fusion_live.py). It streams
annotated frames to `http://127.0.0.1:8000`.

```bash
cp <path-to-course-repo>/lessons/04-backend-engineering/resources/scripts/watch_fusion_live.py scripts/
uv run python scripts/watch_fusion_live.py --camera 0
```

**It is provided because building it teaches nothing this lesson is about.** It is an
MJPEG server, a worker thread, and a frame buffer — real code, and none of it is
detection, depth, fusion, or export. Read it if you like; it is not a deliverable.

> It runs depth every fifth frame by default and reuses the map in between, and prints how
> stale the map is on screen. That is this project's characteristic failure made visible —
> a plausible number computed from the wrong pixels. `--depth-every 1` makes it honest and
> slow.

---

## What good output looks like

- The script imports `fuse_detections_with_depth` rather than reducing boxes itself
- BGR → RGB is explicit and commented
- The table leads with rank, and carries the `depth_quality` flag
- Zero detections prints as a successful empty result
- **Known failure modes** names a class, a symptom, and the frame it was seen on

## Reject and re-run if

- The reduction was reimplemented instead of imported
- `cv2.imshow` appears anywhere
- The output is summarised as "works reasonably well" with no specific failure named
- A printed string calls a depth value a measurement
- **Known failure modes** was filled in from the metrics table rather than from frames
