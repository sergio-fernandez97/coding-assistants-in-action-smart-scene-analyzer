# Prompt — Annotation quality review

**When:** Lesson 02, Part 2 — E1 (optional). Before generating any version.

**Which agent:** `dataset-engineer`.

**Which skill:** `dataset-qa-sweep`. It carries the queries, the read-only constraint, and
the converter-bug-versus-data-quality table. Run it after *every* upload from here on, not
only at this step — that is why it is a skill and not a one-off prompt.

---

```
Use the dataset-engineer agent.

Review annotation quality in the smart-scene-analyzer project. Consult the
roboflow:data-management skill for RoboQL syntax before you start.

Run these searches with images_search and report the count plus up to 5 example
image IDs for each:

1. max-annotations:0        — unannotated images
2. max-annotations:1        — a single annotation; suspicious for an indoor scene
3. For each class in docs/taxonomy.md: class:<name>   — instance distribution
4. min-width:2000 OR min-height:2000    — unusually large
5. tag:<source-tag>         — confirm the tag count matches what I uploaded

Then report:
- Total image count, and how it compares to my expected count
- The class distribution, sorted, with any class under 50 instances called out
- Which of the above queries suggests a conversion bug rather than a data quality
  issue, and why

Do NOT delete, modify, or re-annotate anything. This is a read-only review. I will
decide what to act on.
```

---

## Reading the results

| Finding | Likely cause |
|---|---|
| Many `max-annotations:0` | Converter dropped annotations, or uploaded images that had none |
| Spike in `max-annotations:1` | Converter kept only the first object per record |
| One class with implausibly high count | Taxonomy mapping collapsed several source labels into one |
| Class present in taxonomy, zero instances | Mapping name mismatch — a typo in `docs/taxonomy.md` |
| Total count well below source | Silent skips in conversion; go back to the converter's report |

The distinction the prompt asks for — conversion bug vs. data quality issue — is the
judgment worth practising. A dataset that genuinely contains few lamps is a modelling
problem you handle with class weighting. A converter that dropped the lamps is a bug
you fix. They look identical in the class distribution and have completely different
responses.

## Note on the read-only constraint

`Do NOT delete, modify, or re-annotate anything` is not boilerplate. Roboflow bulk
operations are not undoable, and an agent that helpfully removes images it judges
"empty" has destroyed the evidence you would use to diagnose the converter. Review and
mutation stay separate operations, with a human decision between them.
