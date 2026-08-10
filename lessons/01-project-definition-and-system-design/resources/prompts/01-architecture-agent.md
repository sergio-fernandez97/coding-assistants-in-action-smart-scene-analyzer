# Prompt — Architecture Agent

**When:** Lesson 01, step 8. After `docs/requirements.md` is filled in and the
inference-target ADR exists.

**How:** Paste into Claude Code. The `description` field on the `architecture` agent
should cause automatic delegation; if it does not, prefix with
`Use the architecture agent to:`.

---

```
Design the system architecture for the Smart Scene Analyzer.

Read first, in this order:
- CLAUDE.md
- docs/requirements.md
- docs/decisions/ (every ADR — the inference-target decision constrains this design)

Produce docs/architecture.md containing:

1. A component diagram of the pipeline: capture → preprocessing → parallel
   inference (YOLO11 detection, Depth Anything V2 depth) → scene understanding
   layer → FastAPI → client.

2. A data contract for EVERY boundary between components. Each contract states the
   type, the units, and the coordinate convention. For example, do not write
   "detections pass to the fusion layer" — write "list[Detection], where bbox is
   xyxy in absolute pixels in the ORIGINAL image frame, not the resized model input
   frame." Boundaries where resizing happens are where this project will lose an
   afternoon if the contract is vague.

3. The scene understanding layer's fusion strategy: given a bounding box and a dense
   depth map, how is a single depth value derived per object? Name the method
   (median over the box? over an eroded box? masked region?) and say what it does
   when the box contains a background gap.

4. A latency budget allocating my p95 target from docs/requirements.md across the
   pipeline stages. The allocations must sum to the target. If they cannot, say so
   and tell me which requirement is unachievable.

5. Module boundaries designed to be mockable: unit tests must run with no GPU and no
   network.

6. A short rationale for each major choice, and an explicit list of the assumptions
   you had to make.

Then scaffold src/smart_scene_analyzer/ to match: packages, __init__.py files, and
module docstrings stating each module's single responsibility.

Constraints:
- Do NOT write function bodies. Stubs and docstrings only.
- Do NOT resolve a decision that is still open in docs/decisions/ or the course
  TODO. If the design depends on one, stop and tell me the branches with their
  architectural consequences.
- If docs/requirements.md is silent on something the design forces you to choose,
  flag it explicitly rather than picking quietly.
```

---

## What good output looks like

- Every arrow in the diagram has a named type and units next to it
- The latency budget arithmetic is shown and sums correctly
- The fusion strategy names a specific method and its failure mode
- An "Assumptions" section exists and is non-empty
- `src/` contains docstrings and no logic

## Reject and re-run if

- Any contract is described in prose without a type
- Function bodies appear
- The budget does not sum, or is omitted
- An open decision was resolved silently
- The "Assumptions" section is missing — it is never legitimately empty at this stage
