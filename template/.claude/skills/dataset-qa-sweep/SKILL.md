---
name: dataset-qa-sweep
description: Use after uploading images to Roboflow, after any annotation change, and before generating a dataset version. Runs a read-only RoboQL sweep for unannotated images, sparse annotations, class distribution, and outliers, then separates converter bugs from genuine data quality issues. Invoke whenever asked to check dataset quality, review annotations, or investigate a suspicious class count.
---

# Dataset QA sweep

Run this with the `dataset-engineer` role, after every upload and before every version
generation. **Credits: zero** — RoboQL queries and `images_search` are free.

Consult `roboflow:data-management` for current RoboQL syntax before starting. The syntax
changes upstream; this file does not.

## This sweep is read-only

**Do not delete, modify, or re-annotate anything.** Report and stop.

That constraint is not boilerplate. Roboflow bulk operations are not undoable, and an
agent that helpfully removes images it judges "empty" has destroyed the evidence you
would have used to diagnose the converter. Review and mutation stay separate operations
with a human decision between them.

## The queries

Run each with `images_search`; report the count plus up to five example image IDs.

| # | Query | Looking for |
|---|---|---|
| 1 | `max-annotations:0` | Unannotated images |
| 2 | `max-annotations:1` | A single annotation — suspicious for an indoor scene |
| 3 | `class:<name>` for each class in `docs/taxonomy.md` | Instance distribution |
| 4 | `min-width:2000 OR min-height:2000` | Unusually large images |
| 5 | `tag:<source-tag>` | Confirm the tag count matches what was uploaded |

## The report

- Total image count, and how it compares to the expected count
- The class distribution, sorted, with any class under 50 instances called out
- **Which findings suggest a converter bug rather than a data quality issue, and why**

That last judgment is the one worth practising, because the two look identical in a class
distribution and have completely different responses. A dataset that genuinely contains
few lamps is a modelling problem you handle with class weighting. A converter that
dropped the lamps is a bug you fix.

| Finding | Likely cause |
|---|---|
| Many `max-annotations:0` | Converter dropped annotations, or images uploaded that had none |
| Spike in `max-annotations:1` | Converter kept only the first object per record |
| One class with implausibly high count | Taxonomy mapping collapsed several source labels into one |
| Class in the taxonomy with zero instances | Mapping name mismatch — a typo in `docs/taxonomy.md` |
| Total count well below source | Silent skips in conversion; go back to the converter's report |

## What good output looks like

- Every query run, with counts and example IDs
- Class distribution sorted, sparse classes named
- Each anomaly attributed to *converter bug* or *data quality*, with the reasoning
- Expected versus actual totals compared explicitly
- Nothing mutated

## Reject and re-run if

- Anything was deleted, re-annotated, or modified
- Counts are reported without comparison to an expected figure
- Anomalies are listed without the bug-versus-quality judgment
- A class missing from the results is not investigated — a zero is a finding, not an
  absence of one
