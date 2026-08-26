#!/usr/bin/env python3
"""Reference Depth Calibration — check the depth model against something you measured.

Lesson 03, step 7. You put objects at positions you measured yourself, photograph them,
and find out what the model's numbers do and do not track.

## What "calibration" means here, and what it cannot mean

In metrology, calibrating an instrument means checking it against a reference standard.
That is exactly what this step does, and it is the sense the name is used in.

It does **not** mean deriving a conversion from the model's output to a physical
distance. That is impossible here and the impossibility is the point of the exercise:
Depth Anything V2 emits relative inverse depth on an **arbitrary per-image scale**, so any
conversion you fit is a property of one photograph and not of the model. `--transfer`
exists to prove that to you rather than assert it: fit on one scene, apply to another,
watch it fall apart.

If you take one thing from this step, take this. A number that survives a check on one
scene and breaks on the next has not been validated — it has been flattered.

## The unit question, which this script sidesteps on purpose

Measure your object positions however you like: a tape, floor tiles, paces, the edges of
a table. **This script never converts your measurements into anything.** It uses only
their ORDER and their RATIOS, so any consistent scale works and no unit ever enters the
project. That is why nothing here, and nothing in `src/`, may name a unit — the
`units_guard.py` hook enforces the same rule on every write.

## What it reports

  1. **Pairwise ordering accuracy** — the same claim N5 makes, on a scene you built
  2. **Rank correlation** — whether the model's ranking tracks your reference monotonically
  3. **Fit quality within one scene** — relative inverse depth against 1/position
  4. **`--transfer`: whether that fit survives contact with a second scene** — it will not

## The cases file

```json
[
  {
    "name": "desk, three objects",
    "image": "captures/scene_a.jpg",
    "objects": [
      {"label": "mug",    "box": [310, 220, 400, 330], "position": 0.6},
      {"label": "monitor","box": [120, 90, 520, 400],  "position": 1.4},
      {"label": "door",   "box": [40, 20, 180, 430],   "position": 3.9}
    ]
  }
]
```

`position` is your measurement, larger meaning farther, in any consistent scale.
`box` is xyxy in absolute pixels of that image, per `CLAUDE.md`.

Three objects is the minimum worth doing; five is better. Spread them out — objects at
similar positions have no correct answer and only measure noise.

Usage:
    python check_reference_depth.py --cases reference_scenes.json
    python check_reference_depth.py --cases reference_scenes.json --transfer
"""

from __future__ import annotations

import argparse
import itertools
import json
import sys
from pathlib import Path

REQUIRED = ("estimate_relative_inverse_depth", "region_relative_depth")

#: Two objects closer together than this, as a fraction of the nearer position, are not
#: graded. They have no defensible correct answer, and grading them measures your tape.
MIN_SEPARATION = 0.15


def load_depth_module():
    """Import the depth module from step 5 and check the agreed contract."""
    try:
        from smart_scene_analyzer import depth
    except ImportError as exc:
        sys.exit(
            f"FAIL   Could not import smart_scene_analyzer.depth: {exc}\n"
            "       Run from the project root with `uv run python`, after step 5."
        )
    missing = [name for name in REQUIRED if not hasattr(depth, name)]
    if missing:
        sys.exit(f"FAIL   smart_scene_analyzer.depth is missing: {', '.join(missing)}")
    return depth


def spearman(first: list[float], second: list[float]) -> float:
    """Rank correlation between two sequences, without a scipy dependency.

    Args:
        first: any real-valued sequence.
        second: the same length.

    Returns:
        Spearman's rho in ``[-1, 1]``, or ``nan`` if either side is constant.

    Rank correlation rather than Pearson because the relationship between a position and
    its inverse is monotonic but **not** linear. Pearson would report a mediocre number
    for a model that had ranked every object perfectly, which is the wrong instrument for
    the only claim this output supports.
    """
    import numpy as np

    def ranks(values):
        order = np.argsort(np.argsort(np.asarray(values, dtype=float)))
        return order.astype(float)

    a, b = ranks(first), ranks(second)
    if a.std() == 0 or b.std() == 0:
        return float("nan")
    return float(np.corrcoef(a, b)[0, 1])


def measure_scene(depth, scene: dict) -> dict | None:
    """Run the model on one scene and pair each object with its reference position."""
    from PIL import Image

    image_path = Path(scene["image"])
    if not image_path.exists():
        print(f"  FAIL   {image_path} does not exist.")
        return None

    image = Image.open(image_path).convert("RGB")
    depth_map = depth.estimate_relative_inverse_depth(image)
    if depth_map.shape != (image.height, image.width):
        print(f"  FAIL   depth map {depth_map.shape} != image {(image.height, image.width)}")
        return None

    rows = []
    for entry in scene["objects"]:
        value = depth.region_relative_depth(depth_map, tuple(entry["box"]))
        if value is None:
            print(f"  WARN   '{entry['label']}' reduced to None — degenerate box, skipped.")
            continue
        rows.append((entry["label"], float(entry["position"]), value))

    if len(rows) < 2:
        print("  FAIL   Need at least two usable objects.")
        return None
    return {"name": scene.get("name", image_path.name), "rows": rows}


def report_scene(measured: dict) -> tuple[int, int]:
    """Print one scene's table, its ordering accuracy, and its rank correlation."""
    rows = sorted(measured["rows"], key=lambda r: r[1])  # nearest reference first
    print(f"\n  {measured['name']}")
    print(f"    {'object':<16} {'your position':>13} {'model value':>12}   (larger = nearer)")
    for label, position, value in rows:
        print(f"    {label:<16} {position:>13.3g} {value:>12.3f}")

    correct = graded = 0
    for (a_label, a_pos, a_val), (b_label, b_pos, b_val) in itertools.combinations(rows, 2):
        near, far = (
            ((a_pos, a_val), (b_pos, b_val)) if a_pos <= b_pos else ((b_pos, b_val), (a_pos, a_val))
        )
        if (far[0] - near[0]) / near[0] < MIN_SEPARATION:
            continue
        graded += 1
        # The reference-nearer object must carry the LARGER model value: the model returns
        # inverse depth, so the two conventions point opposite ways.
        if near[1] > far[1]:
            correct += 1
        else:
            print(f"    MISS   '{a_label}' vs '{b_label}' — ranked backwards")

    if graded:
        print(f"    ordering  {correct}/{graded} = {correct / graded:.0%}")
    else:
        print("    ordering  no pairs far enough apart to grade — spread the objects out")

    rho = spearman([r[1] for r in rows], [r[2] for r in rows])
    print(f"    rank correlation  {rho:+.3f}   (want close to -1: farther = smaller value)")
    return correct, graded


def fit_inverse(rows) -> tuple[float, float]:
    """Least-squares fit of ``value ~ a * (1 / position) + b`` for one scene.

    Returns:
        ``(a, b)``. Meaningful **only** for the scene it was fitted on, which is the
        entire point of `--transfer`.
    """
    import numpy as np

    x = np.array([1.0 / r[1] for r in rows])
    y = np.array([r[2] for r in rows])
    a, b = np.polyfit(x, y, 1)
    return float(a), float(b)


def report_transfer(measured_scenes: list[dict]) -> None:
    """Fit a conversion on scene 1 and apply it to the others. Watch it fail."""
    import numpy as np

    if len(measured_scenes) < 2:
        print("\n  --transfer needs at least two scenes in the cases file. Skipped.")
        return

    source, *rest = measured_scenes
    a, b = fit_inverse(source["rows"])

    print(f"\n{'=' * 68}")
    print("Does the fit transfer to another scene?")
    print(f"{'=' * 68}")
    print(f"  Fitted on '{source['name']}':  value = {a:.3f} * (1/position) + {b:.3f}")

    def residual(rows):
        predicted = np.array([a * (1.0 / r[1]) + b for r in rows])
        actual = np.array([r[2] for r in rows])
        spread = actual.max() - actual.min()
        return float(np.sqrt(np.mean((predicted - actual) ** 2))) / (spread if spread else 1.0)

    own = residual(source["rows"])
    header = "error, as a share of the scene range"
    print(f"\n  {'scene':<34} {header:>33}")
    print(f"  {source['name']:<34} {own:>32.1%}  <- fitted here")
    for other in rest:
        print(f"  {other['name']:<34} {residual(other['rows']):>32.1%}")

    print("\n  If the error on the other scenes is much larger than on the fitted one, you")
    print("  have shown the thing this step exists to show: the fit describes ONE")
    print("  photograph. There is no conversion from these values to a position that")
    print("  survives a change of scene, so the app may order and shade by them and must")
    print("  never print one as a measurement.")
    print("\n  If the errors happen to be similar, do not conclude the opposite. Two scenes")
    print("  shot from a similar spot at a similar range will agree by coincidence. Move")
    print("  the camera properly and run it again.")


def main() -> int:
    parser = argparse.ArgumentParser(description="Check depth output against your own reference.")
    parser.add_argument("--cases", type=Path, required=True, help="JSON file of reference scenes")
    parser.add_argument(
        "--transfer",
        action="store_true",
        help="Fit a conversion on the first scene and apply it to the rest",
    )
    args = parser.parse_args()

    depth = load_depth_module()
    payload = json.loads(args.cases.read_text())
    scenes = payload if isinstance(payload, list) else [payload]

    print(f"Checking {len(scenes)} reference scene(s).")
    measured, correct, graded = [], 0, 0
    for scene in scenes:
        result = measure_scene(depth, scene)
        if result is None:
            continue
        measured.append(result)
        scene_correct, scene_graded = report_scene(result)
        correct += scene_correct
        graded += scene_graded

    if not measured:
        print("\nNo usable scenes.")
        return 1

    print(f"\n{'=' * 68}")
    print(
        f"Ordering across all scenes: {correct}/{graded} = {correct / graded:.0%}"
        if graded
        else "No gradeable pairs across any scene."
    )
    print(f"{'=' * 68}")

    if args.transfer:
        report_transfer(measured)

    print("\n  What you have shown: the model RANKS your objects correctly (or does not).")
    print("  What you have not shown, and cannot: any absolute position. The scale is")
    print("  arbitrary and per-image. See docs/model-card-v1.md.")
    return 0 if (graded and correct == graded) else 1


if __name__ == "__main__":
    sys.exit(main())
