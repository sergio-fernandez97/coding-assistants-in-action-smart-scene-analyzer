#!/usr/bin/env python3
"""Check that a depth module's sign convention is right way round.

Lesson 03, step 9. Depth Anything V2 returns RELATIVE INVERSE depth: larger values are
NEARER. An implementation that inverts this produces output that looks entirely
reasonable — every value in range, the map structured, the visualization plausible — and
is backwards. Nothing downstream will tell you, because there is no ground truth in this
project to disagree with it.

This script is the disagreement. Give it an image and two or more boxes in the order you
can see they are arranged, nearest first, and it fails if the numbers say otherwise.

It imports the following from your project, by name:

    smart_scene_analyzer.depth.estimate_relative_inverse_depth(image) -> HxW float32
    smart_scene_analyzer.depth.region_relative_depth(depth_map, box) -> float

Boxes are xyxy in ABSOLUTE pixels, per CLAUDE.md.

Usage:
    # Two boxes, nearest first — the common case
    python check_depth_ordering.py scene.jpg --box 120,200,400,600 --box 0,0,640,120

    # From a JSON file: {"image": "...", "boxes_near_to_far": [[x1,y1,x2,y2], ...]}
    python check_depth_ordering.py --cases cases.json

    # Also write a grayscale render to look at (nearer should be brighter)
    python check_depth_ordering.py scene.jpg --box ... --box ... --render out.png

Exit code 0 if every case orders correctly, 1 otherwise.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REQUIRED = ("estimate_relative_inverse_depth", "region_relative_depth")


def load_depth_module():
    """Import the student's depth module and check it exposes the agreed contract."""
    try:
        from smart_scene_analyzer import depth
    except ImportError as exc:
        sys.exit(
            f"FAIL   Could not import smart_scene_analyzer.depth: {exc}\n"
            "       Run this from the project root with `uv run python`, and make sure\n"
            "       src/smart_scene_analyzer/depth.py exists."
        )

    missing = [name for name in REQUIRED if not hasattr(depth, name)]
    if missing:
        sys.exit(
            f"FAIL   smart_scene_analyzer.depth is missing: {', '.join(missing)}\n\n"
            "       This script checks the contract Lesson 04 also depends on:\n"
            "         estimate_relative_inverse_depth(image) -> HxW float32\n"
            "         region_relative_depth(depth_map, box) -> float\n\n"
            "       If your functions do the right thing under different names, rename\n"
            "       them. The name is part of the deliverable here — a function called\n"
            "       `estimate_depth` returning `depth` is the ambiguity this lesson is\n"
            "       trying to remove."
        )

    for bad in ("meter", "metre", "distance"):
        offenders = [n for n in dir(depth) if bad in n.lower() and not n.startswith("_")]
        if offenders:
            print(f"  WARN   public name(s) containing '{bad}': {', '.join(offenders)}")
            print("         Output is relative inverse depth on an arbitrary scale.")
    return depth


def parse_box(text: str) -> tuple[int, int, int, int]:
    parts = text.split(",")
    if len(parts) != 4:
        sys.exit(f"FAIL   Box '{text}' needs 4 comma-separated values: x1,y1,x2,y2")
    try:
        x1, y1, x2, y2 = (int(float(p)) for p in parts)
    except ValueError:
        sys.exit(f"FAIL   Box '{text}' contains a non-numeric value.")
    if x2 <= x1 or y2 <= y1:
        sys.exit(f"FAIL   Box '{text}' is not a positive-area xyxy box.")
    return x1, y1, x2, y2


def render(depth_map, path: Path) -> None:
    """Write a grayscale render. Nearer surfaces should come out brighter."""
    import numpy as np
    from PIL import Image

    lo, hi = float(np.min(depth_map)), float(np.max(depth_map))
    if hi - lo < 1e-9:
        print("  WARN   Depth map is constant — nothing to render.")
        return
    scaled = ((depth_map - lo) / (hi - lo) * 255).astype("uint8")
    Image.fromarray(scaled).save(path)
    print(f"  Wrote {path} — open it. Nearer surfaces should be BRIGHTER.")


def check_case(depth, image_path: Path, boxes: list[tuple[int, int, int, int]],
               render_to: Path | None) -> bool:
    from PIL import Image

    if not image_path.exists():
        print(f"  FAIL   {image_path} does not exist.")
        return False

    image = Image.open(image_path).convert("RGB")
    depth_map = depth.estimate_relative_inverse_depth(image)

    shape = getattr(depth_map, "shape", None)
    if shape is None or len(shape) != 2:
        print(f"  FAIL   {image_path.name}: expected an HxW array, got shape {shape}")
        return False
    if shape != (image.height, image.width):
        print(
            f"  FAIL   {image_path.name}: depth map is {shape}, image is "
            f"{(image.height, image.width)} — it must match the input resolution."
        )
        return False

    if render_to:
        render(depth_map, render_to)

    values = [depth.region_relative_depth(depth_map, box) for box in boxes]

    print(f"\n  {image_path.name}   (declared nearest first)")
    for box, value in zip(boxes, values):
        print(f"    {str(box):<28} {value:>10.4f}")

    ok = True
    for i in range(len(values) - 1):
        near, far = values[i], values[i + 1]
        if near is None or far is None or near != near or far != far:  # None or NaN
            print(f"    FAIL   box {i} or {i + 1} produced a non-finite value.")
            ok = False
            continue
        if near <= far:
            print(
                f"    FAIL   box {i} was declared nearer than box {i + 1}, but its value "
                f"({near:.4f}) is not larger ({far:.4f})."
            )
            ok = False

    if ok:
        print("    OK     ordering matches the declared arrangement.")
    return ok


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Verify a depth module's relative-inverse-depth sign convention."
    )
    parser.add_argument("image", nargs="?", type=Path, help="Image to check")
    parser.add_argument(
        "--box",
        action="append",
        default=[],
        metavar="x1,y1,x2,y2",
        help="Box in absolute pixels. Repeat, NEAREST FIRST. At least two.",
    )
    parser.add_argument(
        "--cases", type=Path, help="JSON file of cases, instead of a single image"
    )
    parser.add_argument("--render", type=Path, help="Write a grayscale depth render here")
    args = parser.parse_args()

    depth = load_depth_module()
    cases: list[tuple[Path, list[tuple[int, int, int, int]]]] = []

    if args.cases:
        payload = json.loads(args.cases.read_text())
        entries = payload if isinstance(payload, list) else [payload]
        for entry in entries:
            boxes = [tuple(int(v) for v in b) for b in entry["boxes_near_to_far"]]
            cases.append((Path(entry["image"]), boxes))  # type: ignore[arg-type]
    else:
        if not args.image or len(args.box) < 2:
            parser.error("Give an image and at least two --box values, or use --cases.")
        cases.append((args.image, [parse_box(b) for b in args.box]))

    print(f"Checking {len(cases)} case(s).")
    results = [check_case(depth, img, boxes, args.render) for img, boxes in cases]

    passed = sum(results)
    print(f"\n{passed}/{len(results)} case(s) ordered correctly.")

    if passed < len(results):
        print(
            "\n  If EVERY case is inverted, the sign convention is backwards: Depth\n"
            "  Anything V2 returns relative INVERSE depth, where larger = nearer. Check\n"
            "  whether something in the module negated or reciprocated the raw output.\n"
            "\n  If only some cases fail, look at those images — a box dominated by\n"
            "  background rather than its object will read as whatever is behind it."
        )
        return 1

    print(
        "\n  Sign convention confirmed on real scenes. Note what this does NOT show:\n"
        "  the scale is still arbitrary, and no absolute depth is available in this\n"
        "  project. Ordering is the only claim these numbers support."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
