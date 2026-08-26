#!/usr/bin/env python3
"""Watch detection + depth + fusion run on your webcam, live, in a browser.

The continuous sibling of `check_fusion_live.py`. That script grabs one frame and writes
PNGs; this one runs a loop and streams annotated frames to `http://127.0.0.1:8000`.

## Why a browser and not a window

The project depends on `opencv-python-headless`, which has no GUI backend — `cv2.imshow`
raises. That is a deliberate dependency choice: a GUI stack is bytes and platform
breakage nobody needs. So this script serves MJPEG from `http.server`, which is in the
standard library, and your browser does the drawing.

**This server is a development-time viewer and nothing else.** It binds to loopback only,
it is not part of the app, and nothing about it goes near the inference path the app
ships — that path runs on the handset with no network at all. See `docs/decisions/`
ADR 0003.

## Why depth does not run on every frame

Detection is cheap and depth is not. Running Depth Anything V2 on every frame drags the
whole loop down to a few frames per second, which makes the boxes look broken when the
boxes are fine. So detection runs every frame and depth runs every `--depth-every` frames,
with the most recent map reused in between.

**That reuse is visible and deliberate.** The overlay prints how many frames old the
depth map is. A stale map on a moving scene produces exactly the failure this project
cares about — a plausible number for the wrong pixels — so it is labelled rather than
hidden. Pass `--depth-every 1` if you want it honest and slow.

## Units

**Relative inverse depth. Larger is nearer. No unit, no scale, comparable only within one
frame.** The rank is the part that means something; never read a value as a distance.

## Resolution and legibility

Frames are downscaled to `--max-width` (default 960) before inference, because depth cost
grows with pixel count. The browser then scales that frame to fill the window, so the
picture is as large as your display regardless. `--font-size` sets the caption size and
the box outline thickness scales with it.

Raise `--max-width` for sharper boxes and pay for it in frame rate; lower it for the
reverse. Neither changes what the model sees on the phone — this is a viewer.

Usage:
    uv run python scripts/watch_fusion_live.py --camera 0
    uv run python scripts/watch_fusion_live.py --camera 0 --depth-every 1
    uv run python scripts/watch_fusion_live.py --camera 0 --max-width 1280 --font-size 28
    uv run python scripts/watch_fusion_live.py --camera 0 --port 8080 --max-width 480

Stop it with Ctrl-C.
"""

from __future__ import annotations

import argparse
import sys
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    import numpy.typing as npt

    from smart_scene_analyzer.fusion import Detection, FusedDetection

PROJECT_WEIGHTS = Path("runs/detect/runs/v1-baseline/weights/best.pt")
FALLBACK_WEIGHTS = "yolo11n.pt"

BOUNDARY = "frameboundary"

#: Outline colour per quality flag. `ok` is ranked warm-to-cool by depth instead.
QUALITY_COLOUR = {
    "unavailable": (140, 140, 140),
    "fallback_full_box": (120, 180, 255),
    "mixed_region": (255, 80, 200),
}


class FrameBuffer:
    """The single most recent encoded frame, shared between the worker and the server."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._jpeg: bytes | None = None
        self._ready = threading.Event()

    def publish(self, jpeg: bytes) -> None:
        with self._lock:
            self._jpeg = jpeg
        self._ready.set()

    def latest(self, timeout: float = 5.0) -> bytes | None:
        """Return the newest frame, waiting for the first one if none exists yet."""
        if not self._ready.wait(timeout):
            return None
        with self._lock:
            return self._jpeg


def default_weights() -> str:
    """Return the project's own weights if present, else the COCO checkpoint."""
    return str(PROJECT_WEIGHTS) if PROJECT_WEIGHTS.exists() else FALLBACK_WEIGHTS


def to_detections(result: Any) -> list[Detection]:
    """Turn one ultralytics result into `fusion.Detection` records.

    Boxes are ``xyxy`` in absolute pixels of the **SOURCE** frame — the same space the
    depth map is in, which is the precondition `fuse_detections_with_depth` asserts.
    """
    from smart_scene_analyzer.fusion import Detection

    detections: list[Detection] = []
    for box in result.boxes:
        class_id = int(box.cls[0])
        x1, y1, x2, y2 = (float(v) for v in box.xyxy[0].tolist())
        detections.append(
            Detection(
                class_id=class_id,
                class_name=str(result.names[class_id]),
                confidence=float(box.conf[0]),
                bbox=(x1, y1, x2, y2),
            )
        )
    return detections


#: Font files worth trying before falling back to Pillow's bundled bitmap face. Pillow's
#: default font is fixed at a size nobody can read on a 960px frame across a room, which
#: is the whole reason this list exists.
FONT_CANDIDATES = (
    "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
    "/System/Library/Fonts/Supplemental/Arial.ttf",
    "/System/Library/Fonts/Helvetica.ttc",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
)


def load_font(size: int) -> Any:
    """Return a font at `size` px, preferring a real TrueType face."""
    from PIL import ImageFont

    for path in FONT_CANDIDATES:
        if Path(path).exists():
            try:
                return ImageFont.truetype(path, size)
            except OSError:
                continue
    # Pillow >= 10.1 sizes its bundled face; older versions ignore the argument.
    try:
        return ImageFont.load_default(size=size)
    except TypeError:
        return ImageFont.load_default()


def draw_overlay(
    frame: npt.NDArray[Any],
    fused: list[FusedDetection],
    status: str,
    font: Any,
    status_font: Any,
) -> npt.NDArray[Any]:
    """Draw ranked boxes and a status line. Returns a new RGB array."""
    import numpy as np
    from PIL import Image, ImageDraw

    image = Image.fromarray(frame)
    draw = ImageDraw.Draw(image)

    line_height = max(font.size if hasattr(font, "size") else 14, 12)
    box_width = max(2, round(line_height / 5))

    for rank, item in enumerate(fused, 1):
        colour = QUALITY_COLOUR.get(item.depth_quality)
        if colour is None:
            # Nearest gets the warmest outline, so the ordering reads at a glance.
            shade = int(255 * (1 - (rank - 1) / max(len(fused), 1)))
            colour = (255, shade, 0)
        x1, y1, x2, y2 = (int(v) for v in item.detection.bbox)
        draw.rectangle((x1, y1, x2, y2), outline=colour, width=box_width)
        caption = f"#{rank} {item.detection.class_name} {item.detection.confidence:.2f}"
        if item.relative_depth is not None:
            caption += f" d={item.relative_depth:.2f}"
        if item.depth_quality != "ok":
            caption += f" [{item.depth_quality}]"

        # Caption above the box where there is room, inside it where there is not, on a
        # filled strip so it stays readable over a bright wall or a dark chair alike.
        text_w = draw.textlength(caption, font=font)
        pad = max(2, line_height // 6)
        strip_h = line_height + 2 * pad
        top = y1 - strip_h if y1 - strip_h >= 0 else y1
        draw.rectangle((x1, top, x1 + text_w + 2 * pad, top + strip_h), fill=colour)
        draw.text((x1 + pad, top + pad), caption, fill=(0, 0, 0), font=font)

    status_h = (status_font.size if hasattr(status_font, "size") else 14) + 10
    draw.rectangle((0, 0, image.width, status_h), fill=(0, 0, 0))
    draw.text((6, 5), status, fill=(0, 255, 128), font=status_font)
    return np.asarray(image)


def encode_jpeg(rgb: npt.NDArray[Any], quality: int = 80) -> bytes:
    """Encode an RGB array as JPEG bytes."""
    import cv2

    ok, buffer = cv2.imencode(".jpg", rgb[:, :, ::-1], [int(cv2.IMWRITE_JPEG_QUALITY), quality])
    if not ok:
        raise RuntimeError("cv2.imencode failed")
    return bytes(buffer)


def worker(args: argparse.Namespace, buffer: FrameBuffer, stop: threading.Event) -> None:
    """Capture, infer, fuse, annotate, publish — until `stop` is set."""
    import cv2

    from smart_scene_analyzer import depth as depth_module
    from smart_scene_analyzer.fusion import fuse_detections_with_depth, sort_near_to_far

    try:
        from ultralytics import YOLO
    except ImportError:
        print("FAIL   ultralytics is not installed. Run: uv sync --extra ml --extra depth")
        stop.set()
        return

    font = load_font(args.font_size)
    status_font = load_font(max(12, round(args.font_size * 0.8)))

    weights = args.weights or default_weights()
    model = YOLO(weights)
    print(f"  weights={weights}  conf={args.conf}  depth every {args.depth_every} frame(s)")

    capture = cv2.VideoCapture(args.camera)
    if not capture.isOpened():
        print(
            f"FAIL   Could not open camera {args.camera}.\n"
            "       On macOS the terminal needs camera permission: System Settings ->\n"
            "       Privacy & Security -> Camera."
        )
        stop.set()
        return

    depth_map = None
    depth_age = 0
    # Two counters on purpose: `tick` drives the depth cadence and never resets, while
    # `frames_this_second` is zeroed every report. Sharing one would make the depth
    # interval jump every time the fps line refreshed.
    tick = 0
    frames_this_second = 0
    last_report = time.monotonic()
    fps = 0.0

    try:
        while not stop.is_set():
            ok, bgr = capture.read()
            if not ok:
                time.sleep(0.05)
                continue

            # cv2 hands back BGR; everything downstream assumes RGB. A silent swap here
            # produces a depth map that is subtly wrong everywhere and obviously wrong
            # nowhere.
            frame = bgr[:, :, ::-1]
            if args.max_width and frame.shape[1] > args.max_width:
                scale = args.max_width / frame.shape[1]
                frame = cv2.resize(
                    frame,
                    (args.max_width, max(1, round(frame.shape[0] * scale))),
                    interpolation=cv2.INTER_AREA,
                )
            frame = frame.copy()
            height, width = frame.shape[:2]

            results = model.predict(frame, conf=args.conf, verbose=False)
            detections = to_detections(results[0]) if results else []

            if (
                depth_map is None
                or tick % args.depth_every == 0
                or depth_map.shape != (height, width)
            ):
                depth_map = depth_module.estimate_relative_inverse_depth(frame)
                depth_age = 0
            else:
                depth_age += 1

            fused = sort_near_to_far(
                fuse_detections_with_depth(
                    detections,
                    depth_map,
                    image_height=height,
                    image_width=width,
                )
            )

            tick += 1
            frames_this_second += 1
            now = time.monotonic()
            elapsed = now - last_report
            if elapsed >= 1.0:
                fps = frames_this_second / elapsed
                frames_this_second = 0
                last_report = now

            flagged = sum(1 for f in fused if f.depth_quality != "ok")
            status = (
                f"{width}x{height}  {fps:4.1f} fps  {len(fused)} obj  "
                f"{flagged} flagged  depth {depth_age} frame(s) old  "
                f"relative inverse depth, larger = nearer"
            )
            buffer.publish(encode_jpeg(draw_overlay(frame, fused, status, font, status_font)))
    finally:
        capture.release()


def make_handler(buffer: FrameBuffer, stop: threading.Event) -> type[BaseHTTPRequestHandler]:
    """Build the request handler bound to this run's frame buffer."""

    page = (
        b"<!doctype html><title>fusion live</title>"
        # The stream fills the viewport rather than rendering at its native pixel size —
        # a 960px frame in the middle of a 27" display is unreadable across a desk.
        b"<style>html,body{margin:0;height:100%;background:#111}"
        b"img{display:block;width:100%;height:100%;object-fit:contain}</style>"
        b'<img src="/stream">'
    )

    class Handler(BaseHTTPRequestHandler):
        protocol_version = "HTTP/1.1"

        def log_message(self, *_args: Any) -> None:
            pass

        def do_GET(self) -> None:
            if self.path in ("/", "/index.html"):
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.send_header("Content-Length", str(len(page)))
                self.end_headers()
                self.wfile.write(page)
                return

            if self.path != "/stream":
                self.send_error(404)
                return

            self.send_response(200)
            self.send_header("Content-Type", f"multipart/x-mixed-replace; boundary={BOUNDARY}")
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            try:
                while not stop.is_set():
                    jpeg = buffer.latest()
                    if jpeg is None:
                        continue
                    self.wfile.write(f"--{BOUNDARY}\r\n".encode())
                    self.wfile.write(b"Content-Type: image/jpeg\r\n")
                    self.wfile.write(f"Content-Length: {len(jpeg)}\r\n\r\n".encode())
                    self.wfile.write(jpeg)
                    self.wfile.write(b"\r\n")
                    time.sleep(0.03)
            except (BrokenPipeError, ConnectionResetError):
                # The browser tab closed. Normal, not an error.
                pass

    return Handler


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Stream detection + depth + fusion from your webcam to a browser."
    )
    parser.add_argument("--camera", type=int, default=0, help="Camera index, usually 0")
    parser.add_argument(
        "--weights",
        default=None,
        help=f"Detection weights. Default: {PROJECT_WEIGHTS} if present, else {FALLBACK_WEIGHTS}.",
    )
    parser.add_argument("--conf", type=float, default=0.25, help="Confidence threshold")
    parser.add_argument("--port", type=int, default=8000, help="Port to serve on")
    parser.add_argument(
        "--depth-every",
        type=int,
        default=5,
        help="Run depth every Nth frame and reuse the map in between. 1 = every frame.",
    )
    parser.add_argument(
        "--max-width",
        type=int,
        default=960,
        help="Downscale frames wider than this before inference. 0 disables. Higher is "
        "sharper and slower — depth cost grows with pixel count.",
    )
    parser.add_argument(
        "--font-size",
        type=int,
        default=22,
        help="Caption size in pixels. Box outline thickness scales with it.",
    )
    args = parser.parse_args()

    if args.depth_every < 1:
        sys.exit("FAIL   --depth-every must be at least 1.")

    stop = threading.Event()
    buffer = FrameBuffer()

    thread = threading.Thread(target=worker, args=(args, buffer, stop), daemon=True)
    thread.start()

    # Loopback only. This viewer has no business being reachable from the network.
    server = ThreadingHTTPServer(("127.0.0.1", args.port), make_handler(buffer, stop))
    server.daemon_threads = True
    print(f"\n  Open http://127.0.0.1:{args.port}   (Ctrl-C to stop)\n")
    try:
        while not stop.is_set():
            server.handle_request()
    except KeyboardInterrupt:
        print("\n  Stopping.")
    finally:
        stop.set()
        server.server_close()
        thread.join(timeout=5)
    return 0


if __name__ == "__main__":
    sys.exit(main())
