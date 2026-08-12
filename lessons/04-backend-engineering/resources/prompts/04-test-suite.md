# Prompt — the test suite

**When:** Lesson 04, step 5.

**Which agent:** `qa`. Not `backend` — the agent that wrote the code does not grade it.

**Which skill:** `offline-suite`. It carries the no-GPU/no-network/no-weights constraint,
the fixture strategy, and the "does this code use the input it claims to use" test. This
file carries what is specific to *this* service — the endpoints, the status codes, the
degenerate box cases.

**Credits: zero.**

---

## The constraint that shapes everything

**The default suite runs with no GPU, no network, and no weights on disk, in seconds.**

This is not fastidiousness. Lesson 06 puts these tests in GitHub Actions, where there is
no GPU and no `best.pt`. A suite that needs either is a suite that does not run in CI,
and a suite that does not run in CI stops being maintained within a month.

---

## Round 1 — fixtures and the mocking boundary

```
Use the qa agent.

Write tests/conftest.py.

Fixtures:
  - sample_image        an RGB PIL image, generated with numpy/pillow at test time.
                        Do NOT commit binary fixtures.
  - sample_image_nonsquare  same, at a different aspect ratio
  - fake_depth_map      an HxW float32 array with a KNOWN gradient, so I can assert
                        exactly which region should read as nearer
  - fake_detections     canned detections with known boxes
  - mock_models         patches the detector and depth model so no weights load and no
                        GPU is touched
  - client              a TestClient with mock_models applied

Mock at the model boundary, not at the fusion boundary. Fusion is the logic I most want
tested; mocking it would leave the interesting part unexercised.
```

**The fake depth map is the key fixture.** A known gradient means every fusion assertion
can be exact rather than "seems plausible" — you can compute the expected median for a
given box by hand and assert equality.

---

## Round 2 — the tests that matter

```
Write the suite. In priority order:

tests/test_fusion.py
  - Correct depth value for a box over a known region of the gradient
  - Near-to-far ordering matches the gradient
  - THE IMPORTANT ONE: the fused output CHANGES when the depth map changes. A fusion
    function that ignores its depth argument passes every other test in this file.
  - All four degenerate boxes: zero-area, partly outside, entirely outside, empty after
    clipping
  - A depth map whose shape does not match the image raises, and does not silently resize
  - Ordering is stable when the same scene is given at a different aspect ratio

tests/test_schemas.py
  - No field name contains meter, metre, mm, cm, or distance. Walk fields
    programmatically; do not hardcode the current list.
  - The depth field's description mentions "not metres" and "nearer"
  - Boxes are documented as xyxy absolute pixels

tests/test_api.py
  - POST /analyze with a valid image -> 200, schema-valid body
  - Oversized upload -> 413
  - Undecodable bytes -> 415
  - Missing file field -> 422
  - Zero detections -> 200 with an empty list, not an error
  - Grayscale image -> handled, not a crash
  - 1x1 image -> handled
  - GET /health -> 200 with a model version
  - GET /ready -> reflects whether models are loaded

Mark anything needing a running service or real weights with the `integration` marker.
`uv run pytest` must pass without them.

For every test, assert on the CONTRACT — status code, schema, units, ordering — not on
implementation details. A test asserting a specific detection confidence breaks on every
retrain, and a suite that cries wolf gets ignored.
```

---

## The test worth arguing about

```python
def test_fusion_actually_uses_the_depth_map(fake_detections, fake_depth_map):
    """A fusion function that ignores its depth argument passes everything else."""
    first = fuse(fake_detections, fake_depth_map)
    second = fuse(fake_detections, fake_depth_map * -1.0 + fake_depth_map.max())
    assert [d.relative_depth for d in first] != [d.relative_depth for d in second]
```

Every other test in the file passes on a `fuse()` that returns `0.5` for everything. The
schema is valid, the status codes are right, the ordering assertions can be satisfied by
accident on a single fixture. This one cannot.

**Look for this shape of test elsewhere too.** "Does the code use the input it claims to
use" is a question worth asking of any function that takes an expensive argument.

---

## Round 3 — check the suite is honest

```
Report:
  - How long the default suite takes
  - Confirmation it passes with no GPU and no weights present — actually move or rename
    the weights file and re-run, do not assert this from reading the code
  - What is NOT covered, and why that is acceptable
```

**Do:** Verify the offline claim yourself. It is the one claim in this lesson that is easy
to believe and easy to get wrong — an import at module scope that quietly loads a model
will not show up until CI, where the failure is far more expensive to diagnose.

```bash
mv runs runs.hidden && uv run pytest; mv runs.hidden runs
```

---

## What good output looks like

- Default suite passes in seconds with weights genuinely absent
- Image fixtures generated in code, not committed
- The known-gradient depth fixture makes fusion assertions exact
- The "fusion actually uses the depth map" test exists
- All four degenerate box cases covered
- Schema naming test walks fields programmatically
- Boundary tests for 413, 415, 422, and empty results
- Integration tests marked and excluded from the default run

## Reject and re-run if

- Any default-suite test needs a GPU, a network, or a weights file
- Binary image fixtures are committed
- Fusion is mocked — that removes the logic most worth testing
- Tests assert specific confidences or coordinates that a retrain would change
- An assertion was loosened to make a test pass, rather than the disagreement being
  resolved and stated
- The offline claim was asserted from reading the code rather than by hiding the weights
