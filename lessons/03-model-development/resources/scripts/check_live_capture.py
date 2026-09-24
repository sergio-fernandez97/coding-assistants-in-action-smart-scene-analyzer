#!/usr/bin/env python3
"""Run BOTH models on one frame — your webcam, or an image file — and look at the result.

Lesson 03, step 6. This is the first time in the course that detection and depth run on
the same pixels and produce one answer, and it is deliberately the first time you point
them at something that is not a dataset.

A test split is a comfortable place to be wrong. Every image in it was captured by the
same sensor family, in the same kind of room, and annotated by the same process. Your
webcam is none of those things, and a model that scores well on the split and falls apart
on your desk has told you something no metric in this lesson would have.

## What it does

  1. Grabs one frame (`--camera 0`) or opens `--image`
  2. Runs YOLO detection — COCO-pretrained by default, YOUR weights with `--weights`
  3. Runs Depth Anything V2 through `smart_scene_analyzer.depth`
  4. Reduces each detection to one relative depth value with `region_relative_depth`
  5. Writes the raw frame, an annotated PNG, and a grayscale depth PNG, and prints a
     near-to-far table. Step 7 measures the RAW frame — never feed the annotated one back

## It writes files. It never opens a window.

The project depends on `opencv-python-headless`, which has no GUI backend — `cv2.imshow`
raises. That is a deliberate dependency choice (a GUI stack is bytes and platform
breakage nobody needs), and it means this script hands you PNGs to open yourself.

## Before you have trained anything

The default weights are COCO-pretrained `yolo11n.pt`, which already knows five of this
project's eight classes under its own names:

  ours    bed     chair    sofa     table          tv
  COCO    bed     chair    couch    dining table   tv

`cabinet`, `door`, and `lamp` have no COCO equivalent and will not appear. That gap is
the argument for fine-tuning, and seeing it is more convincing than being told it.

Run this again after your homework training with `--weights runs/v1-baseline/weights/best.pt`
and compare the two annotated images side by side.

## Units, since this script prints depth numbers

The values are **relative inverse depth**: larger is nearer, the scale is arbitrary, and
they are comparable only within one frame. The table prints a RANK as well as the value,
because the rank is the part that means something. See `docs/model-card-v1.md`.

Usage:
    python check_live_capture.py --camera 0
    python check_live_capture.py --image photo.jpg
    python check_live_capture.py --camera 0 --weights runs/v1-baseline/weights/best.pt
    python check_live_capture.py --camera 0 --out-dir captures/ --conf 0.35
    python check_live_capture.py --camera 1 --warmup 90   # a phone camera (e.g. Continuity Camera)
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

REQUIRED = ("estimate_relative_inverse_depth", "region_relative_depth")


def load_depth_module():
    """Import the depth module written in step 5 and check the agreed contract."""
    try:
        from smart_scene_analyzer import depth
    except ImportError as exc:
        sys.exit(
            f"FAIL   Could not import smart_scene_analyzer.depth: {exc}\n"
            "       Run this from the project root with `uv run python`, and complete\n"
            "       step 5 first — this script runs the module that step produces."
        )
    missing = [name for name in REQUIRED if not hasattr(depth, name)]
    if missing:
        sys.exit(
            f"FAIL   smart_scene_analyzer.depth is missing: {', '.join(missing)}\n"
            "       Both names are fixed by the artifact contract. Rename rather than\n"
            "       adapting this script — Lesson 04 imports the same two names."
        )
    return depth


def grab_frame(camera: int, warmup: int = 10):
    """Capture one frame from a camera index, as an RGB uint8 array.

    Args:
        camera: device index. 0 is the built-in camera on most machines.
        warmup: frames to read and discard first.

    Returns:
        ``(H, W, 3)`` uint8 RGB.

    The warmup matters and is not superstition: most webcams need several frames to
    finish auto-exposure and white balance, and the first frame is routinely near-black.
    A near-black frame produces a confident, meaningless depth map, which is exactly the
    kind of plausible garbage this lesson is about.
    """
    import cv2

    capture = cv2.VideoCapture(camera)
    if not capture.isOpened():
        sys.exit(
            f"FAIL   Could not open camera {camera}.\n"
            "       On macOS the terminal needs camera permission: System Settings ->\n"
            "       Privacy & Security -> Camera. If you have no webcam, use --image."
        )
    try:
        frame = None
        for _ in range(max(warmup, 1)):
            ok, frame = capture.read()
            if not ok:
                sys.exit(f"FAIL   Camera {camera} opened but returned no frame.")
    finally:
        capture.release()

    # cv2 hands back BGR. Everything downstream assumes RGB, and a silent swap here
    # produces a depth map that is subtly wrong everywhere and obviously wrong nowhere.
    return frame[:, :, ::-1].copy()


def load_image(path: Path):
    """Open an image file as ``(H, W, 3)`` uint8 RGB."""
    import numpy as np
    from PIL import Image

    if not path.exists():
        sys.exit(f"FAIL   {path} does not exist.")
    return np.asarray(Image.open(path).convert("RGB"), dtype=np.uint8)


def detect(frame, weights: str, conf: float):
    """Run YOLO detection on an RGB frame.

    Returns:
        A list of ``(label, confidence, (x1, y1, x2, y2))``, xyxy in absolute pixels of
        the frame. **An empty list is a successful result**, not an error — the project
        treats zero detections as a real answer, and so does this script.
    """
    try:
        from ultralytics import YOLO
    except ImportError:
        sys.exit("FAIL   ultralytics is not installed. Run: uv sync --extra ml --extra depth")

    model = YOLO(weights)
    results = model.predict(frame, conf=conf, verbose=False)
    detections = []
    for result in results:
        for box in result.boxes:
            x1, y1, x2, y2 = (float(v) for v in box.xyxy[0].tolist())
            detections.append((result.names[int(box.cls[0])], float(box.conf[0]), (x1, y1, x2, y2)))
    return detections


def annotate(frame, rows, path: Path) -> None:
    """Draw boxes labelled with class, confidence, and near-to-far rank."""
    from PIL import Image, ImageDraw

    image = Image.fromarray(frame)
    draw = ImageDraw.Draw(image)
    for rank, (label, confidence, box, value) in enumerate(rows, 1):
        # Nearest gets the warmest outline, so the depth ordering is visible at a glance
        # rather than only readable in the table.
        shade = int(255 * (1 - (rank - 1) / max(len(rows), 1)))
        draw.rectangle([int(v) for v in box], outline=(255, shade, 0), width=3)
        caption = f"#{rank} {label} {confidence:.2f}"
        if value is not None:
            caption += f"  d={value:.2f}"
        draw.text((box[0] + 4, box[1] + 4), caption, fill=(255, 255, 0))
    image.save(path)


def render_depth(depth_map, path: Path) -> None:
    """Write the depth map as grayscale. Nearer surfaces come out brighter."""
    import numpy as np
    from PIL import Image

    low, high = float(np.nanmin(depth_map)), float(np.nanmax(depth_map))
    if high - low < 1e-9:
        print("  WARN   Depth map is constant — nothing to render.")
        return
    scaled = ((depth_map - low) / (high - low) * 255).astype("uint8")
    Image.fromarray(scaled).save(path)


def main() -> int:
    from PIL import Image

    parser = argparse.ArgumentParser(description="Run detection and depth on one live frame.")
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--camera", type=int, help="Camera index, usually 0")
    source.add_argument("--image", type=Path, help="Image file, if you have no webcam")
    parser.add_argument(
        "--weights",
        default="yolo11n.pt",
        help="Detection weights. Default is COCO-pretrained; pass your own after training.",
    )
    parser.add_argument("--conf", type=float, default=0.25, help="Confidence threshold")
    parser.add_argument("--out-dir", type=Path, default=Path("."), help="Where to write PNGs")
    parser.add_argument(
        "--warmup",
        type=int,
        default=10,
        help="Camera frames to discard first. Raise to ~90 for a phone camera that must focus.",
    )
    args = parser.parse_args()

    depth = load_depth_module()
    args.out_dir.mkdir(parents=True, exist_ok=True)

    if args.camera is not None:
        frame = grab_frame(args.camera, warmup=args.warmup)
    else:
        frame = load_image(args.image)
    print(f"  frame {frame.shape[1]}x{frame.shape[0]}  weights={args.weights}")

    detections = detect(frame, args.weights, args.conf)
    depth_map = depth.estimate_relative_inverse_depth(frame)

    if depth_map.shape != frame.shape[:2]:
        print(
            f"  FAIL   depth map is {depth_map.shape}, frame is {frame.shape[:2]}.\n"
            "         The map must come back at the input resolution — see step 5."
        )
        return 1

    rows = [
        (label, confidence, box, depth.region_relative_depth(depth_map, box))
        for label, confidence, box in detections
    ]
    # Nearest first. `None` means the reduction had nothing usable in that box; those sort
    # to the end rather than being dropped, because a detection with no depth is a real
    # case the app has to render and not a row to hide.
    rows.sort(key=lambda r: (r[3] is None, -(r[3] or 0.0)))

    # The untouched frame is what step 7 measures. The annotated PNG has boxes burned into
    # exactly the pixels a box reduction reads, so it must never be fed back as an input.
    raw = args.out_dir / "live_capture_raw.png"
    annotated = args.out_dir / "live_capture_annotated.png"
    depth_png = args.out_dir / "live_capture_depth.png"
    Image.fromarray(frame).save(raw)
    annotate(frame, rows, annotated)
    render_depth(depth_map, depth_png)

    if not rows:
        print("\n  Zero detections. That is a successful result with an empty list, not a")
        print("  failure — but check the annotated PNG before believing it. With COCO")
        print("  weights, only bed / chair / couch / dining table / tv are findable.")
    else:
        print(f"\n  {'#':>2}  {'class':<14} {'conf':>5}  {'rel. depth':>10}   (larger = nearer)")
        for rank, (label, confidence, _box, value) in enumerate(rows, 1):
            shown = f"{value:10.3f}" if value is not None else "      none"
            print(f"  {rank:>2}  {label:<14} {confidence:>5.2f}  {shown}")

    print(f"\n  Wrote {raw}")
    print(f"  Wrote {annotated}")
    print(f"  Wrote {depth_png}")
    print("\n  Open both. Two things to check with your own eyes, which no metric here does:")
    print("    1. Are the boxes on the right objects, and is anything obvious missed?")
    print("    2. Is the near-to-far ORDER right? Nearer surfaces brighter in the depth PNG.")
    print("\n  The values are relative inverse depth: no unit, no scale, this frame only.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
