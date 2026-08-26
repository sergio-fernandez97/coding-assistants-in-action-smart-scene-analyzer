# Prompt — Reference Depth Calibration

**When:** Lesson 03, step 7. **In session.** Budget 20 minutes.

**Which agent:** `ml-engineer` to build the cases file, `evaluation` for the finding.

**Credits: zero.**

---

## What this step is, and what it is not

**It is** calibration in the metrology sense: checking an instrument against a reference
standard you trust. You place objects at positions you measured, photograph them, and find
out whether the model's numbers track your measurements.

**It is not** deriving a conversion from the model's output to a distance. That is
impossible here, and demonstrating the impossibility *is the exercise*. Depth Anything V2
emits relative inverse depth on an **arbitrary per-image scale**, so any conversion you fit
belongs to one photograph and not to the model.

This lesson has asserted that since step 4. Asserting it is weak. In the next twenty
minutes you are going to fit a conversion, watch it work beautifully on the scene it was
fitted to, then apply it to a second scene and watch it fall apart. After that you will not
need to be told.

> **Measure however you like** — a tape, floor tiles, paces, the edge of a desk. The script
> uses only the **order** and the **ratios** of your measurements and never converts them,
> so any consistent scale works and **no unit enters the project**. That is the same rule
> `units_guard.py` enforces on every write to `src/` and `app/`.

---

## Round 1 — build two scenes

Set up **two genuinely different scenes**, three to five objects each:

- Spread the objects out. Two things at nearly the same position have no correct answer,
  and the script will refuse to grade them.
- **Move the camera properly between scenes.** A different room, or at least a different
  distance and angle. Two frames shot from almost the same spot will agree by coincidence
  and teach you the opposite of the lesson.
- Note each object's position as you go. You will not remember afterwards.

```bash
uv run python scripts/check_live_capture.py --camera 0 --out-dir captures/scene_a
uv run python scripts/check_live_capture.py --camera 0 --out-dir captures/scene_b
```

---

## Round 2 — the cases file

```
Use the ml-engineer agent.

I captured two reference scenes. For each, I have the image and a list of objects with the
position I measured, larger meaning farther, on an arbitrary consistent scale:

  Scene A (<path>):  <object> at <position>, <object> at <position>, ...
  Scene B (<path>):  <object> at <position>, <object> at <position>, ...

Write reference_scenes.json in the format scripts/check_reference_depth.py documents in
its module docstring. Get the boxes by running the detector on each image, or read them off
the annotated PNG — but the box must be xyxy in ABSOLUTE pixels of that image.

Do not run the depth model or interpret anything. Build the file, then stop.
```

Then run it yourself:

```bash
uv run python scripts/check_reference_depth.py --cases reference_scenes.json --transfer
```

**Expected result:** per scene, an ordering percentage and a rank correlation; then the
transfer table.

---

## Round 3 — read the three numbers

| Number | What it means | What to expect |
|---|---|---|
| **Ordering accuracy** | Of the pairs far enough apart to grade, how many did the model rank correctly | High. This is the claim the project actually makes |
| **Rank correlation** | Whether the ranking tracks your reference monotonically | Close to **−1**: your positions grow with distance, the model's values shrink |
| **Transfer error** | The fit from scene A, applied to scene B | Several times worse on B than on A |

A worked example, run on two indoor scenes with a sensor as the reference:

```
scene A                 ordering 11/11 = 100%    rank correlation -0.943
scene B                 ordering 13/13 = 100%    rank correlation -1.000

fit on A:  value = 13671.370 * (1/position) + -2.719
  scene A error   5.2%   <- fitted here
  scene B error  57.2%
```

**Perfect ordering. An eleven-fold blow-up in the fit.** Both halves matter: the model is
excellent at the thing this project asks of it and useless at the thing this project has
forbidden since Lesson 01.

> **If your transfer errors come out similar, do not conclude the opposite.** Check that
> you really moved the camera. Similar framing at a similar range produces a coincidental
> agreement, and a coincidence is not a calibration.

---

## Round 4 — put it in the model card

```
Use the evaluation agent.

Here is the output of scripts/check_reference_depth.py --transfer on two reference scenes
I built and measured: <paste>.

Write the "Reference depth calibration" subsection of the Depth section in
docs/model-card-v1.md. State:
  - How the reference was obtained, and that it is my own measurement, not ground truth
  - The ordering accuracy and rank correlation per scene, with the object count
  - The transfer result, with both errors, and what it establishes
  - That no conversion to a position is published, and why one cannot be

Do not name a unit for my measurements anywhere. They were taken on an arbitrary scale and
the script never converted them; the document must not imply otherwise.
```

**Expected result:** a subsection a downstream reader can use to decide what these numbers
may be used for — which is ordering and shading, and nothing else.

---

## What good output looks like

- Two scenes, genuinely different camera positions, three or more objects each
- Ordering accuracy and rank correlation reported per scene, not pooled into one figure
- The transfer test run, and the error on the un-fitted scene clearly worse
- The model card subsection states what cannot be published, not only what can
- No unit appears anywhere, in the JSON, the output, or the document

## Reject and re-run if

- Both scenes were shot from roughly the same spot — the transfer test proves nothing
- Objects are bunched together, and the script graded almost no pairs
- The write-up presents the fitted conversion as usable, with caveats. It is not usable;
  caveats are how an unusable number reaches production
- Any measurement is described with a unit, or the fit is called a calibration curve
- The agent edited `units_guard.py`, or renamed something to get past it
