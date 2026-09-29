# Prompt — port the fusion layer to TypeScript

**When:** Lesson 05, step 10 — after the session.

**Which agent:** `mobile`.

**Credits: zero.**

---

You are about to create the second implementation of an algorithm this project already
has. That is a correctness risk, permanently, and the only thing that makes it survivable
is that both implementations answer to the same fixtures.

Treat the fixtures as the deliverable. The port is the easy part.

---

## Round 1 — extract the fixtures first

```
Use the mobile agent.

Read src/smart_scene_analyzer/fusion.py and its tests.

Then produce tests/fixtures/fusion_cases.json — a language-neutral fixture file that both
suites can load. Each case:

  {
    "name": "...",
    "why": "what this case exists to catch",
    "depthMap": { "width": N, "height": N, "values": [...] },
    "boxes": [[x1, y1, x2, y2], ...],
    "expected": [<per-box relative depth>, ...]
  }

Cover at minimum:
  - A normal box over a depth gradient with a known median
  - A zero-area box
  - A box partly outside the image
  - A box entirely outside the image
  - A box containing no valid depth values
  - A box of exactly one pixel

Generate the expected values by RUNNING the Python reference, not by reasoning about
what it should produce. Then make the Python suite load this file too, and confirm it
still passes.

Plain JSON only. No pickles, no .npy — TypeScript has to read this.
```

**Make the Python suite consume the fixtures before writing any TypeScript.** If the
reference does not pass its own extracted fixtures, the extraction is wrong, and you want
to know that now rather than while debugging a port.

---

## Round 2 — port it

```
Write app/src/fusion/index.ts:

  export function fuseDetectionsWithDepth(
    detections: DetectionModelInputPixels[],
    depthMap: DepthMap,
  ): FusedDetection[]

Requirements:
  - MEDIAN reduction over the box region, matching the reference exactly. Not the mean.
  - Every degenerate case from the fixtures has a defined result. No NaN reaches a caller.
  - Pure: arrays and boxes in, structure out. No model, no I/O, no React.
  - The depth field is named relativeDepth. Nothing in this file may imply a unit.

Then write app/src/fusion/index.test.ts that loads tests/fixtures/fusion_cases.json —
the SAME file the Python suite uses — and asserts each expected value.
```

**Watch the median definition on even-length inputs.** NumPy averages the two middle
values; a naive TypeScript median often takes the lower one. On a four-pixel box that is a
real difference, and it is exactly the kind of discrepancy this fixture set exists to
surface.

---

## Round 3 — make them disagree on purpose

```
Temporarily change the TypeScript median to take the lower middle value instead of
averaging. Run both suites. Show me the failure.

Then revert it.

Explain in two sentences why this exercise is worth the two minutes.
```

A test suite nobody has watched fail is a suite nobody knows is connected. This one spans
two languages and two runtimes, which is exactly the kind of wiring that silently is not.

---

## Round 4 — the boundary

```
Confirm you have not edited anything under src/.

If the port and the reference disagree anywhere, report the disagreement — which case,
which values, and which side you believe is wrong. Do not change the fixture to make both
pass.
```

**Adjusting a fixture until both implementations agree destroys the only signal this
arrangement produces.** If they disagree, one of them is wrong, and that is information
worth more than a green suite.

---

## What good output looks like

- Fixtures extracted by running the reference, in plain JSON
- The Python suite loads the same fixture file and still passes
- Median matches the reference including the even-length case
- Every degenerate case has a defined, tested result
- The port was watched failing before being trusted
- `src/` untouched
- Any disagreement reported rather than reconciled

## Reject and re-run if

- Expected values were reasoned about rather than generated from the reference
- The fixture format cannot be loaded by both languages
- The two suites use different fixtures
- A fixture was adjusted to make both sides pass
- `NaN` can reach a caller in any case
- The mean was used instead of the median
- Anything under `src/` was edited
