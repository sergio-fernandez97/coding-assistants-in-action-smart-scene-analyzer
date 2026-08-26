# Prompt — Depth Anything V2, inference only

**When:** Lesson 03, step 4. **In session.** Budget 20 minutes.

**Which agent:** `ml-engineer`.

**Credits: zero.** This is a pretrained model you run locally. There is no training and
no Roboflow involvement — Roboflow does not store depth maps, which is why Lesson 02
scoped depth to inference only.

---

## The constraint that defines this module

Depth Anything V2 outputs **relative inverse depth**:

- **Larger values are nearer.** The sign convention is the opposite of distance, and
  getting it backwards produces perfectly plausible output.
- **The scale is arbitrary.** It is not metres, not millimetres, not any unit.
- **There is no ground truth in this project**, so there is nothing to calibrate against
  and no absolute error to report.

Everything below follows from that. The deliverable is not the inference call — that is
about fifteen lines. The deliverable is a module that cannot be misread downstream.

---

## Round 1 — the module

```
Use the ml-engineer agent.

Write src/smart_scene_analyzer/depth.py: monocular depth estimation with Depth Anything V2
via transformers, for INFERENCE ONLY. No training, no fine-tuning.

Requirements:

- Load the model once, lazily, and cache it. Model loading must sit behind an interface a
  test can replace — the default suite runs with no network and no weights on disk.
- Auto-detect device (cuda / mps / cpu), overridable.
- The main function takes a PIL Image or an HxWx3 uint8 numpy array and returns an HxW
  float32 array at the SAME resolution as the input image.
- The model's own raster is NOT that resolution. Depth Anything V2 Small is a ViT-S/14,
  so its input edges must be multiples of 14; this module resizes the model's raster back
  to the source resolution before returning, so that fusion can assert one shape and
  reduce in one space. Keep that resize as its own named step, and state both spaces.
  Lesson 04 compares the RAW raster — before your resize — against the exported artifact,
  so it must be reachable rather than buried inside the public function.

Units, and this is the actual point of the exercise:

- Name the function so its output is unambiguous. `estimate_depth` returning `depth` is
  ambiguous and therefore wrong. The name must carry "relative inverse depth".
- The docstring must make four claims: larger = nearer; the scale is arbitrary; the
  output is not a distance in any unit; and this project has no ground truth to calibrate
  against.

  **Choose the wording yourself, and expect `units_guard.py` to reject your first
  attempt.** The hook greps the whole file, not just identifiers, so the obvious phrasing
  for "this is not measured in metres" contains the very word it blocks. That is the hook
  working, not a bug: it cannot read intent, and a rule that let a denial through would
  let every plausible-looking violation through. Satisfy it — do not edit it, and do not
  route around it. `Not a distance, in any unit.` passes and says the same thing.
- No identifier anywhere in this module may contain "meter", "metre", "mm", "cm", or
  "distance". Grep for them before you finish.
- Type hints on every public function, with the array shape and dtype in the docstring.

Also provide a helper that reduces a depth map region inside a bounding box to a single
value:
  - Box format is xyxy in ABSOLUTE pixels, per CLAUDE.md.
  - Use the MEDIAN of the region, not the mean. Justify it in the docstring: an occluding
    object in front of the target skews the mean, and box corners frequently contain
    background.
  - Define the result for: a zero-area box, a box partly outside the image, a box entirely
    outside the image, and a box whose region is empty after clipping. Returning NaN and
    letting it propagate into a JSON response is not a defined result — decide and
    document.

Keep this module pure: no file reads, no HTTP, no Roboflow. Model loading is the only
side effect.

The two public functions must be named EXACTLY as follows, because the course's
verification script imports them by name and Lesson 04 depends on the same contract:

  estimate_relative_inverse_depth(image) -> np.ndarray
      image: PIL.Image or HxWx3 uint8 array
      returns: HxW float32, larger = nearer, arbitrary scale, NOT metres

  region_relative_depth(depth_map, box) -> float
      depth_map: HxW float32 from the function above
      box: (x1, y1, x2, y2) xyxy in ABSOLUTE pixels
      returns: the median of the clipped region, or the documented degenerate result

You may add other helpers. These two names are fixed.
```

**Why median rather than mean**, since the agent will otherwise reach for the mean: the
box around a chair contains the chair *and* whatever is visible around it — floor, wall,
the table in front. The mean mixes those. The median is dominated by whichever surface
occupies most of the box, which is usually the object. Neither is correct in general;
median is more robust, and the reason belongs in the docstring so the next person can
disagree with it knowingly.

---

## Round 2 — prove the sign convention

An inverted sign convention produces output that looks entirely reasonable. Every value is
in range, the map has structure, the visualization looks like a depth map. It is simply
backwards, and nothing downstream will tell you.

```
Write scripts/check_depth_ordering.py.

Given an image and two or more bounding boxes with a stated expected ordering, it:
  - runs depth estimation
  - reduces each box to its per-object value
  - asserts the ordering matches
  - prints the values and exits non-zero on mismatch

Then run it on at least five real test images where I can tell by eye which object is
nearer — a chair in front of a wall, a table in front of a window. Show me the values.
```

**Look at the numbers yourself.** The nearer object must have the *larger* value. If it
does not, you have found the bug this script exists for, and you have found it before it
reached the API.

**Do:** Also render one depth map as a grayscale image and open it. Nearer surfaces should
be brighter. This takes thirty seconds and catches what the numbers alone will not — a map
that is structurally wrong rather than merely inverted.

---

## Round 3 — say what you cannot do

```
Write the depth section of docs/model-card-v1.md.

State plainly:
  - The model and its version
  - That output is relative inverse depth: larger = nearer, arbitrary scale, not metres
  - That NO quantitative evaluation was performed, and why: there is no depth ground truth
    in this project (Roboflow does not store depth maps; see the depth scope ADR)
  - What validation WAS performed: relative-ordering checks on N images
  - What a downstream consumer must not do with this output

Do not hedge and do not pad. "No absolute depth error is reported because no ground truth
exists" is a complete sentence and a complete answer.
```

**Why this matters more than it looks.** Silence about units invites assumption, and the
natural assumption is metres. The first consumer who treats this as metres will build
something that works in testing and is wrong in the world. The model card is where that
gets prevented, and it costs one paragraph.

---

## What good output looks like

- Function names carry "relative inverse depth"; no identifier mentions metres or distance
- Docstrings state shape, dtype, sign convention, and the absence of ground truth
- The median reduction is used and justified
- All four degenerate box cases have defined, documented results
- The ordering check passes on five real scenes and you have looked at the values
- A rendered depth map was opened and inspected
- The model card states what was not evaluated, and why

## Reject and re-run if

- Any identifier or docstring implies a metric unit, a distance, or an absolute scale
- The module was written by weakening, editing, or bypassing `units_guard.py`
- The reduction is a mean without justification
- Degenerate boxes return `NaN` with no documented handling
- The model loads inside the inference function rather than being cached
- The ordering check is skipped because "the values look reasonable" — that is precisely
  the failure mode it exists to catch
- The module reaches for Roboflow, the filesystem, or the network
