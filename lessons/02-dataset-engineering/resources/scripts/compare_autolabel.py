#!/usr/bin/env python3
"""Measure how well an auto-labeler agrees with human ground truth.

Lesson 02, step 10. You held out 100 images, uploaded them unlabeled, ran Roboflow
Auto Label on them for one credit, and exported the result. This script compares that
export against the labels your own converter produced for the same images.

The output is a per-class table of precision, recall, and IoU-matched agreement — the
evidence for whether an auto-labeled dataset would have been good enough, measured on
your data rather than assumed.

Matching is greedy by descending IoU within a class, which is what the standard
detection metrics do at a single threshold. This is deliberately NOT mAP: mAP integrates
over confidence, and an exported annotation set has no confidence scores left in it.
Precision and recall at a fixed IoU are what the data can actually support.

Both directories must be in YOLO layout:

    <dir>/images/*        (optional — only the label files are read)
    <dir>/labels/*.txt    <class_id> <cx> <cy> <w> <h>, normalized to [0, 1]
    <dir>/classes.txt     one class name per line, order defines the integer IDs

Usage:
    python compare_autolabel.py data/audit-export data/audit-gt
    python compare_autolabel.py data/audit-export data/audit-gt --iou 0.5 --report
    python compare_autolabel.py data/audit-export data/audit-gt --examples 5

Exit code 0 if the comparison ran, 1 if the two sets could not be compared.
"""

from __future__ import annotations

import argparse
import sys
from collections import defaultdict
from pathlib import Path

DEFAULT_IOU = 0.5
DEFAULT_EXAMPLES = 3


class Box:
    """One annotation. Coordinates are normalized xyxy in [0, 1]."""

    __slots__ = ("cls", "x1", "y1", "x2", "y2")

    def __init__(self, cls: int, cx: float, cy: float, w: float, h: float) -> None:
        self.cls = cls
        self.x1 = cx - w / 2
        self.y1 = cy - h / 2
        self.x2 = cx + w / 2
        self.y2 = cy + h / 2

    def area(self) -> float:
        return max(0.0, self.x2 - self.x1) * max(0.0, self.y2 - self.y1)


def iou(a: Box, b: Box) -> float:
    """Intersection over union of two normalized boxes."""
    ix1, iy1 = max(a.x1, b.x1), max(a.y1, b.y1)
    ix2, iy2 = min(a.x2, b.x2), min(a.y2, b.y2)
    inter = max(0.0, ix2 - ix1) * max(0.0, iy2 - iy1)
    if inter <= 0.0:
        return 0.0
    union = a.area() + b.area() - inter
    return inter / union if union > 0 else 0.0


def read_classes(root: Path) -> list[str]:
    path = root / "classes.txt"
    if not path.exists():
        return []
    return [line.strip() for line in path.read_text().splitlines() if line.strip()]


def read_labels(root: Path) -> dict[str, list[Box]]:
    """Read every label file under <root>/labels, keyed by image stem."""
    labels_dir = root / "labels"
    if not labels_dir.is_dir():
        sys.exit(f"FAIL   {labels_dir} does not exist or is not a directory.")

    out: dict[str, list[Box]] = {}
    for path in sorted(labels_dir.glob("*.txt")):
        boxes: list[Box] = []
        for lineno, raw in enumerate(path.read_text().splitlines(), start=1):
            line = raw.strip()
            if not line:
                continue
            parts = line.split()
            if len(parts) != 5:
                print(f"  WARN   {path.name}:{lineno} has {len(parts)} fields, expected 5 — skipped")
                continue
            try:
                cls = int(parts[0])
                cx, cy, w, h = (float(p) for p in parts[1:])
            except ValueError:
                print(f"  WARN   {path.name}:{lineno} is not parseable — skipped")
                continue
            boxes.append(Box(cls, cx, cy, w, h))
        out[path.stem] = boxes
    return out


def match(
    gt: list[Box], pred: list[Box], threshold: float
) -> tuple[list[tuple[Box, Box, float]], list[Box], list[Box]]:
    """Greedy per-class matching by descending IoU.

    Returns (matched triples, unmatched ground truth, unmatched predictions).
    """
    candidates: list[tuple[float, int, int]] = []
    for gi, g in enumerate(gt):
        for pi, p in enumerate(pred):
            if g.cls != p.cls:
                continue
            score = iou(g, p)
            if score >= threshold:
                candidates.append((score, gi, pi))
    candidates.sort(reverse=True)

    used_gt: set[int] = set()
    used_pred: set[int] = set()
    matched: list[tuple[Box, Box, float]] = []
    for score, gi, pi in candidates:
        if gi in used_gt or pi in used_pred:
            continue
        used_gt.add(gi)
        used_pred.add(pi)
        matched.append((gt[gi], pred[pi], score))

    missed = [b for i, b in enumerate(gt) if i not in used_gt]
    spurious = [b for i, b in enumerate(pred) if i not in used_pred]
    return matched, missed, spurious


def median(values: list[float]) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    mid = len(ordered) // 2
    if len(ordered) % 2:
        return ordered[mid]
    return (ordered[mid - 1] + ordered[mid]) / 2


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Compare auto-labeled annotations against human ground truth."
    )
    parser.add_argument("predicted", type=Path, help="YOLO directory of auto-labeled annotations")
    parser.add_argument("truth", type=Path, help="YOLO directory of human ground truth")
    parser.add_argument(
        "--iou", type=float, default=DEFAULT_IOU, help=f"IoU match threshold (default {DEFAULT_IOU})"
    )
    parser.add_argument(
        "--examples",
        type=int,
        default=DEFAULT_EXAMPLES,
        help=f"Example image IDs to show per failure mode (default {DEFAULT_EXAMPLES})",
    )
    parser.add_argument(
        "--report", action="store_true", help="Emit a markdown table for the dataset card"
    )
    args = parser.parse_args()

    pred_classes = read_classes(args.predicted)
    true_classes = read_classes(args.truth)

    if pred_classes and true_classes and pred_classes != true_classes:
        print("FAIL   The two class lists differ in name or order.")
        print(f"       predicted: {pred_classes}")
        print(f"       truth:     {true_classes}")
        print("\n       YOLO labels are integer indices. Comparing across two orderings")
        print("       measures nothing. Align classes.txt before rerunning.")
        return 1

    names = true_classes or pred_classes
    predicted = read_labels(args.predicted)
    truth = read_labels(args.truth)

    shared = sorted(set(predicted) & set(truth))
    if not shared:
        print("FAIL   No image stems are common to both directories.")
        print(f"       predicted has {len(predicted)}, truth has {len(truth)}.")
        print("\n       Roboflow renames images on export. You may need to map export")
        print("       filenames back to your source stems before comparing.")
        return 1

    only_pred = sorted(set(predicted) - set(truth))
    only_true = sorted(set(truth) - set(predicted))

    print(f"Comparing {len(shared)} image(s) at IoU >= {args.iou}")
    if only_pred:
        print(f"  WARN   {len(only_pred)} image(s) only in predicted — ignored")
    if only_true:
        print(f"  WARN   {len(only_true)} image(s) only in truth — ignored")

    stats: dict[int, dict[str, float]] = defaultdict(
        lambda: {"gt": 0, "pred": 0, "tp": 0, "fn": 0, "fp": 0}
    )
    ious: dict[int, list[float]] = defaultdict(list)
    fn_examples: dict[int, list[str]] = defaultdict(list)
    fp_examples: dict[int, list[str]] = defaultdict(list)

    for stem in shared:
        gt_boxes = truth[stem]
        pred_boxes = predicted[stem]
        for b in gt_boxes:
            stats[b.cls]["gt"] += 1
        for b in pred_boxes:
            stats[b.cls]["pred"] += 1

        matched, missed, spurious = match(gt_boxes, pred_boxes, args.iou)
        for g, _p, score in matched:
            stats[g.cls]["tp"] += 1
            ious[g.cls].append(score)
        for b in missed:
            stats[b.cls]["fn"] += 1
            if len(fn_examples[b.cls]) < args.examples:
                fn_examples[b.cls].append(stem)
        for b in spurious:
            stats[b.cls]["fp"] += 1
            if len(fp_examples[b.cls]) < args.examples:
                fp_examples[b.cls].append(stem)

    def label(cls: int) -> str:
        return names[cls] if 0 <= cls < len(names) else f"class_{cls}"

    rows = []
    for cls in sorted(stats):
        s = stats[cls]
        tp, fp, fn = s["tp"], s["fp"], s["fn"]
        precision = tp / (tp + fp) if (tp + fp) else 0.0
        recall = tp / (tp + fn) if (tp + fn) else 0.0
        f1 = 2 * precision * recall / (precision + recall) if (precision + recall) else 0.0
        rows.append(
            {
                "name": label(cls),
                "gt": int(s["gt"]),
                "pred": int(s["pred"]),
                "precision": precision,
                "recall": recall,
                "f1": f1,
                "med_iou": median(ious[cls]),
                "fn_ex": fn_examples[cls],
                "fp_ex": fp_examples[cls],
            }
        )

    header = f"\n{'class':<14}{'gt':>6}{'pred':>7}{'prec':>8}{'recall':>8}{'F1':>7}{'medIoU':>8}"
    print(header)
    print("-" * len(header.strip("\n")))
    for r in rows:
        print(
            f"{r['name']:<14}{r['gt']:>6}{r['pred']:>7}"
            f"{r['precision']:>8.2f}{r['recall']:>8.2f}{r['f1']:>7.2f}{r['med_iou']:>8.2f}"
        )

    total_gt = sum(r["gt"] for r in rows)
    total_tp = sum(stats[c]["tp"] for c in stats)
    total_pred = sum(r["pred"] for r in rows)
    micro_p = total_tp / total_pred if total_pred else 0.0
    micro_r = total_tp / total_gt if total_gt else 0.0
    print("-" * len(header.strip("\n")))
    print(f"{'ALL':<14}{total_gt:>6}{total_pred:>7}{micro_p:>8.2f}{micro_r:>8.2f}")

    print("\nExamples to open in the Roboflow annotator:")
    for r in rows:
        if r["fn_ex"]:
            print(f"  {r['name']:<12} missed by the model:  {', '.join(r['fn_ex'])}")
        if r["fp_ex"]:
            print(f"  {r['name']:<12} predicted, no match:  {', '.join(r['fp_ex'])}")

    low = [r["name"] for r in rows if r["gt"] >= 10 and r["recall"] < 0.5]
    thin = [r["name"] for r in rows if r["gt"] < 10]
    print()
    if low:
        print(f"  Recall below 0.50 on: {', '.join(low)}")
        print("  A machine-labeled dataset would be missing these objects entirely,")
        print("  which teaches the model they are background.")
    if thin:
        print(f"  Too few instances to judge: {', '.join(thin)}")
        print("  Fewer than 10 ground-truth instances. These rates are noise; say so")
        print("  in the dataset card rather than quoting them.")

    print("\n  Before reading these as model quality: some disagreements are")
    print("  annotation-convention differences, not errors. Open the example images.")

    if args.report:
        print("\n\n<!-- paste into docs/dataset-card-v1.md -->\n")
        print(f"Auto Label audit — {len(shared)} images, IoU >= {args.iou}\n")
        print("| Class | GT instances | Predicted | Precision | Recall | F1 | Median IoU |")
        print("|---|---|---|---|---|---|---|")
        for r in rows:
            print(
                f"| `{r['name']}` | {r['gt']} | {r['pred']} | {r['precision']:.2f} | "
                f"{r['recall']:.2f} | {r['f1']:.2f} | {r['med_iou']:.2f} |"
            )
        print(f"| **All** | **{total_gt}** | **{total_pred}** | **{micro_p:.2f}** | **{micro_r:.2f}** | | |")

    return 0


if __name__ == "__main__":
    sys.exit(main())
