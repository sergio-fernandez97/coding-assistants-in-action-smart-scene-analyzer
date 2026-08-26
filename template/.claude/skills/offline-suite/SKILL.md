---
name: offline-suite
description: Use when writing or reviewing tests for code that wraps an expensive dependency — a model, a paid API, a GPU, a network service. Enforces a default suite that runs with no GPU, no network, and no weights on disk, and adds the "does this function actually use its expensive argument" test. Invoke whenever asked to write tests, fix a slow or flaky suite, or check that tests will pass in CI.
---

# The offline suite

Run this with the `qa` role. **Not the role that wrote the code** — the agent that wrote it does not
grade it. **Credits: zero.**

## The constraint that shapes everything

**The default suite runs with no GPU, no network, and no weights on disk, in seconds.**

This is not fastidiousness. The CI lesson puts these tests in GitHub Actions, where there
is no GPU and no `best.pt`. A suite that needs either is a suite that does not run in CI,
and a suite that does not run in CI stops being maintained within a month.

## Fixtures

Generate everything in code. **Do not commit binary fixtures.**

| Fixture | What it is |
|---|---|
| `sample_image` | An RGB image built with numpy/pillow at test time |
| `sample_image_nonsquare` | The same at a different aspect ratio |
| `fake_depth_map` | An HxW float32 array with a **known gradient** |
| `fake_detections` | Canned detections with known boxes |
| `mock_models` | Patches the expensive models so no weights load and no GPU is touched |
| `fusion_cases` | Loaded from `tests/fixtures/fusion_cases.json` — **plain JSON**, because a TypeScript suite loads the same file |

**Mock at the model boundary, not at the logic boundary.** Mocking the fusion layer would
remove the part most worth testing.

The known-gradient depth map is the key fixture. It makes every assertion exact — you can
compute the expected median for a given box by hand and assert equality — rather than
"seems plausible".

## The test worth arguing about

```python
def test_fusion_actually_uses_the_depth_map(fake_detections, fake_depth_map):
    """A fusion function that ignores its depth argument passes everything else."""
    first = fuse(fake_detections, fake_depth_map)
    second = fuse(fake_detections, fake_depth_map * -1.0 + fake_depth_map.max())
    assert [d.relative_depth for d in first] != [d.relative_depth for d in second]
```

Every other test in the file passes on a `fuse()` that returns `0.5` for everything. The
schema is valid, the status codes are right, and ordering assertions can be satisfied by
accident on a single fixture. This one cannot.

**Generalize it.** "Does this code use the input it claims to use?" is worth asking of any
function that takes an expensive argument — a model, a config, a dataset version, a depth
map. Write that test first.

## Coverage priorities

- **Logic under test**: exact values against the known gradient; ordering; all degenerate
  input cases (zero-area, partly outside, entirely outside, empty after clipping); a
  shape mismatch **raises** rather than silently resizing; ordering stable across aspect
  ratios.
- **Schemas**: walk fields **programmatically** and assert no name contains a banned unit
  substring — do not hardcode the current field list. Assert the documented units and
  coordinate convention are present in the descriptions.
- **Boundaries**: **zero results → an empty list, not `None` and not an exception**;
  grayscale and 1×1 inputs handled; a shape mismatch raises rather than silently resizing.
- **Export parity** — the case this suite exists to make possible at all. See below.

Assert on the **contract** — tensor shapes, label order, units, ordering — never on
implementation details. A test asserting a specific detection confidence breaks on every
retrain, and a suite that cries wolf gets ignored.

Mark anything needing real weights on disk with the `integration` marker.
`uv run pytest` must pass without them.

## Export parity: the test that needs the expensive thing

Everything above keeps the expensive dependency *out*. Export parity is the one case that
cannot: it exists precisely to compare the cheap artifact against the expensive original.

That makes it the exception that proves the rule, and it has its own discipline:

- **Marked `integration`.** The default suite must still pass on a machine with no weights.
  A parity test that breaks the fast suite gets deleted within a month.
- **Compare against the ORIGINAL**, never the exported artifact loaded by a second
  runtime. Comparing an artifact to itself confirms that two libraries can read one file.
- **State a tolerance and justify it.** Exports do not match bit-for-bit and are not
  supposed to. A tolerance chosen after seeing the results is a description, not a
  threshold — if you do that, say so.
- **Report per-class deltas.** Quantization can destroy one class while leaving the
  aggregate almost unmoved, and an aggregate is exactly the wrong instrument for finding it.
- **For anything with no scale — depth — compare ORDERING, not values.** Comparing
  magnitudes across two runtimes is meaningless even when the assertion passes.

The signature question, in the same spirit as "does this function use its depth argument":
**would this test fail if the export were broken?** A parity test that only checks the
artifact loads and returns the right *shape* will pass on a model that has been quantized
into uselessness.

## Verify the offline claim by breaking it

Do not assert this from reading the code. An import at module scope that quietly loads a
model will not show up until CI, where it is far more expensive to diagnose.

```bash
mv runs runs.hidden && uv run pytest; mv runs.hidden runs
```

Then report how long the default suite takes, that it passed with weights genuinely
absent, and **what is not covered and why that is acceptable**.

## What good output looks like

- Default suite passes in seconds with weights genuinely moved away
- Image fixtures generated in code, not committed
- The known-gradient fixture makes assertions exact
- The "actually uses its expensive argument" test exists
- Every degenerate input case covered
- Schema naming test walks fields programmatically
- Integration tests marked and excluded from the default run

## Reject and re-run if

- Any default-suite test needs a GPU, a network, or a weights file
- Binary fixtures are committed
- The logic under test is itself mocked
- Tests assert specific confidences or coordinates that a retrain would change
- An assertion was loosened to make a test pass, rather than the disagreement being
  resolved and stated
- The offline claim was asserted from reading the code rather than by hiding the weights
