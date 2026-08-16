#!/usr/bin/env python3
"""Verify a Roboflow YOLO export before it is used for training.

Checks the failures that are silent — the ones that do not raise during training but
produce a worse model:

  1. data.yaml's class list matches docs/taxonomy.md in NAME and ORDER. YOLO labels
     are integer indices, so a reordered class list mislabels the whole dataset
     without erroring anywhere.
  2. Every split directory exists and is non-empty.
  3. Every image has a label file and vice versa.
  4. Label rows are well formed: 5 fields, class id in range, coordinates normalized
     within [0, 1], positive width and height.

Usage:
    python verify_export.py data/v1
    python verify_export.py data/v1 --taxonomy docs/taxonomy.md
    python verify_export.py data/v1 --taxonomy docs/taxonomy.md --allow-empty-labels

Exit code 0 if every check passes, 1 otherwise.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

IMAGE_SUFFIXES = {".jpg", ".jpeg", ".png", ".webp", ".bmp"}
SPLITS = ("train", "valid", "test")

# Sample size for per-row label validation. Full validation on a 100k-image export is
# slow enough that people skip running it, which is worse than sampling.
DEFAULT_SAMPLE = 500


class Report:
    """Collects failures and warnings so one run surfaces every problem at once."""

    def __init__(self) -> None:
        self.errors: list[str] = []
        self.warnings: list[str] = []
        self.notes: list[str] = []

    def error(self, msg: str) -> None:
        self.errors.append(msg)

    def warn(self, msg: str) -> None:
        self.warnings.append(msg)

    def note(self, msg: str) -> None:
        self.notes.append(msg)

    def render(self) -> bool:
        for n in self.notes:
            print(f"  {n}")
        if self.warnings:
            print()
            for w in self.warnings:
                print(f"  WARN   {w}")
        if self.errors:
            print()
            for e in self.errors:
                print(f"  FAIL   {e}")
            print(f"\n{len(self.errors)} check(s) failed.")
            return False
        print(f"\nAll checks passed ({len(self.warnings)} warning(s)).")
        return True


def parse_data_yaml(path: Path) -> list[str]:
    """Return the class names from a YOLO data.yaml, in order.

    Uses PyYAML when available and falls back to a targeted parser, so the script
    runs in a bare environment. Roboflow writes `names` as either a flow list
    (``names: ['a', 'b']``) or a block list of ``- a`` items.
    """
    text = path.read_text(encoding="utf-8")

    try:
        import yaml

        data = yaml.safe_load(text)
        names = data.get("names")
        if isinstance(names, dict):  # {0: 'a', 1: 'b'} form
            return [names[k] for k in sorted(names)]
        if isinstance(names, list):
            return [str(n) for n in names]
        raise ValueError(f"`names` in {path} is neither a list nor a mapping")
    except ImportError:
        pass

    flow = re.search(r"^names:\s*\[(.*?)\]", text, re.MULTILINE | re.DOTALL)
    if flow:
        return [item.strip().strip("'\"") for item in flow.group(1).split(",") if item.strip()]

    block = re.search(r"^names:\s*$\n((?:\s*-\s*.+\n?)+)", text, re.MULTILINE)
    if block:
        return [
            line.strip().lstrip("-").strip().strip("'\"")
            for line in block.group(1).splitlines()
            if line.strip()
        ]

    raise ValueError(f"Could not find a `names` list in {path}. Install PyYAML for robust parsing.")


CLASS_LIST_HEADING = re.compile(r"^#{1,6}\s+class\s+list\b", re.IGNORECASE)
HEADING = re.compile(r"^#{1,6}\s+")
TAXONOMY_ROW = re.compile(r"^\|\s*(\d+)\s*\|\s*`?([^`|]+?)`?\s*\|")


def _class_list_section(text: str) -> list[str] | None:
    """Return the lines under a `## Class list` heading, or None if there is no such heading.

    Scoped deliberately. A filled-in taxonomy tends to grow other tables whose first two
    columns also look like ``| <int> | <name> |`` — Auto Label prompt tables are the usual
    culprit — and an unscoped scan lets the last one in the file win. That failure is
    especially nasty because it reports the class order as wrong while the class list is
    in fact correct, sending you to fix the one thing that is not broken.
    """
    lines = text.splitlines()
    for i, line in enumerate(lines):
        if not CLASS_LIST_HEADING.match(line.strip()):
            continue
        section = []
        for subsequent in lines[i + 1 :]:
            if HEADING.match(subsequent.strip()):
                break
            section.append(subsequent)
        return section
    return None


def parse_taxonomy(path: Path) -> list[str]:
    """Return the class names from the taxonomy markdown table, ordered by ID.

    Expects rows of the form ``| 0 | `chair` | notes |`` under a table whose first
    column is the integer class ID. Placeholder rows (``<...>``) are skipped.

    Reads the ``## Class list`` section when the document has one, and falls back to
    scanning the whole file when it does not — so a taxonomy written before this rule
    existed still verifies.
    """
    text = path.read_text(encoding="utf-8")

    section = _class_list_section(text)
    scoped = section is not None
    lines = section if scoped else text.splitlines()

    classes: dict[int, str] = {}
    for line in lines:
        match = TAXONOMY_ROW.match(line.strip())
        if not match:
            continue
        name = match.group(2).strip()
        if not name or name.startswith("<"):
            continue
        classes[int(match.group(1))] = name

    if not classes:
        where = "the `Class list` section of" if scoped else "anywhere in"
        raise ValueError(
            f"No class rows found in {where} {path}. "
            f"Expected markdown rows like: | 0 | `chair` | ... |"
        )

    ids = sorted(classes)
    if ids != list(range(len(ids))):
        raise ValueError(f"Taxonomy IDs are not contiguous from 0: {ids}")

    if not scoped:
        print(
            f"  NOTE   {path} has no `## Class list` heading; scanned the whole file. "
            f"Any other table with `| <int> | <name> |` rows can override the class list."
        )

    return [classes[i] for i in ids]


def check_taxonomy_match(yaml_names: list[str], taxonomy_names: list[str], rep: Report) -> None:
    if yaml_names == taxonomy_names:
        rep.note(f"Class list matches taxonomy: {len(yaml_names)} classes, order identical.")
        return

    rep.error(
        f"Class list mismatch between data.yaml and taxonomy.\n"
        f"           data.yaml: {yaml_names}\n"
        f"           taxonomy:  {taxonomy_names}"
    )

    if sorted(yaml_names) == sorted(taxonomy_names):
        rep.error(
            "Same class names in a DIFFERENT ORDER. Every label index in this export "
            "refers to the wrong class. Regenerate the version — do not train on it."
        )
        return

    missing = [n for n in taxonomy_names if n not in yaml_names]
    extra = [n for n in yaml_names if n not in taxonomy_names]
    if missing:
        rep.error(f"In taxonomy but not in export: {missing}")
    if extra:
        rep.error(f"In export but not in taxonomy: {extra}")


def split_dirs(root: Path, split: str) -> tuple[Path, Path]:
    return root / split / "images", root / split / "labels"


def check_split(
    root: Path, split: str, n_classes: int, rep: Report, sample: int, allow_empty: bool
) -> None:
    images_dir, labels_dir = split_dirs(root, split)

    if not images_dir.is_dir():
        rep.error(f"{split}: missing {images_dir}")
        return
    if not labels_dir.is_dir():
        rep.error(f"{split}: missing {labels_dir}")
        return

    images = sorted(p for p in images_dir.iterdir() if p.suffix.lower() in IMAGE_SUFFIXES)
    labels = sorted(p for p in labels_dir.glob("*.txt"))

    if not images:
        rep.error(f"{split}: no images found in {images_dir}")
        return

    image_stems = {p.stem for p in images}
    label_stems = {p.stem for p in labels}

    unlabeled = image_stems - label_stems
    orphaned = label_stems - image_stems

    if unlabeled:
        preview = sorted(unlabeled)[:5]
        rep.error(f"{split}: {len(unlabeled)} image(s) without a label file, e.g. {preview}")
    if orphaned:
        preview = sorted(orphaned)[:5]
        rep.error(f"{split}: {len(orphaned)} label file(s) without an image, e.g. {preview}")

    empty = [p.name for p in labels if p.stat().st_size == 0]
    if empty and not allow_empty:
        rep.warn(
            f"{split}: {len(empty)} empty label file(s) (background images). "
            f"Intentional? Pass --allow-empty-labels to silence. e.g. {empty[:3]}"
        )

    bad_rows = 0
    class_counts: dict[int, int] = {}
    checked = labels[:sample] if sample > 0 else labels

    for label_path in checked:
        for lineno, line in enumerate(label_path.read_text(encoding="utf-8").splitlines(), 1):
            line = line.strip()
            if not line:
                continue
            parts = line.split()
            where = f"{split}/{label_path.name}:{lineno}"

            if len(parts) != 5:
                rep.error(f"{where}: expected 5 fields, got {len(parts)}: {line!r}")
                bad_rows += 1
                continue

            try:
                cls = int(parts[0])
                cx, cy, w, h = (float(v) for v in parts[1:])
            except ValueError:
                rep.error(f"{where}: non-numeric field: {line!r}")
                bad_rows += 1
                continue

            if not 0 <= cls < n_classes:
                rep.error(f"{where}: class id {cls} outside range 0..{n_classes - 1}")
                bad_rows += 1
                continue

            class_counts[cls] = class_counts.get(cls, 0) + 1

            if not all(0.0 <= v <= 1.0 for v in (cx, cy, w, h)):
                rep.error(
                    f"{where}: coordinates not normalized to [0, 1]: {cx} {cy} {w} {h}. "
                    f"Wrong format (absolute pixels?) or a conversion bug."
                )
                bad_rows += 1
            elif w <= 0 or h <= 0:
                rep.error(f"{where}: degenerate box, w={w} h={h}")
                bad_rows += 1

        if bad_rows > 50:
            rep.error(f"{split}: stopping after 50+ bad rows — the export is systematically wrong.")
            break

    scope = (
        f"sampled {len(checked)} of {len(labels)}"
        if sample > 0 and len(labels) > sample
        else f"all {len(labels)}"
    )
    total_boxes = sum(class_counts.values())
    rep.note(f"{split}: {len(images)} images, {total_boxes} boxes in {scope} label files.")

    unseen = [c for c in range(n_classes) if c not in class_counts]
    if unseen and split == "train":
        rep.warn(f"{split}: no instances of class id(s) {unseen} in the sampled labels.")


def main() -> int:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument(
        "export_dir", type=Path, help="Roboflow YOLO export root (contains data.yaml)"
    )
    parser.add_argument(
        "--taxonomy", type=Path, help="Path to docs/taxonomy.md for class-list comparison"
    )
    parser.add_argument(
        "--sample",
        type=int,
        default=DEFAULT_SAMPLE,
        help=f"Label files to validate per split; 0 for all (default {DEFAULT_SAMPLE})",
    )
    parser.add_argument(
        "--allow-empty-labels",
        action="store_true",
        help="Treat empty label files as intentional background images",
    )
    args = parser.parse_args()

    root: Path = args.export_dir
    rep = Report()

    print(f"Verifying export: {root}")

    if not root.is_dir():
        print(f"  FAIL   {root} is not a directory")
        return 1

    data_yaml = root / "data.yaml"
    if not data_yaml.is_file():
        print(f"  FAIL   {data_yaml} not found — is this a Roboflow YOLO export?")
        return 1

    try:
        yaml_names = parse_data_yaml(data_yaml)
    except ValueError as exc:
        print(f"  FAIL   {exc}")
        return 1

    rep.note(f"data.yaml declares {len(yaml_names)} classes.")

    if args.taxonomy:
        try:
            check_taxonomy_match(yaml_names, parse_taxonomy(args.taxonomy), rep)
        except ValueError as exc:
            rep.error(str(exc))
    else:
        rep.warn(
            "No --taxonomy given; skipping the class-list comparison (the most valuable check)."
        )

    for split in SPLITS:
        if not (root / split).exists():
            rep.warn(f"{split}: split directory absent — expected for a 3-way split.")
            continue
        check_split(root, split, len(yaml_names), rep, args.sample, args.allow_empty_labels)

    return 0 if rep.render() else 1


if __name__ == "__main__":
    sys.exit(main())
