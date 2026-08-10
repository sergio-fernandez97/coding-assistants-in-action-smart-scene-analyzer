# Prompt — the response schema

**When:** Lesson 04, step 2. **Before any handler exists.**

**Which agent:** `backend`.

**Credits: zero.**

---

## Why this comes first

The response schema is the only part of this service anyone outside it will ever see.
Once a mobile client parses a field, its name and units are frozen — changing them later
is a coordinated release across two codebases, not an edit.

Designing it before the handler also forces the question the handler would let you dodge:
what, exactly, does this service claim to know?

---

## Round 1 — design, don't implement

```
Use the backend agent.

Design src/smart_scene_analyzer/schemas.py: the Pydantic v2 models for the Smart Scene
Analyzer API. Schemas only — no routes, no handlers, no inference.

Models needed:
  Detection       one detected object
  AnalyzeResponse the full response for one image
  HealthResponse  liveness and loaded model identity
  ErrorResponse   a consistent error body

Detection carries:
  - class name and class id
  - confidence
  - bounding box, xyxy in ABSOLUTE pixels (per CLAUDE.md)
  - the object's depth value

The depth field is the important one, so read this carefully before naming it.

This project runs Depth Anything V2 with NO ground truth and NO calibration. Its output
is RELATIVE INVERSE DEPTH: larger is nearer, the scale is arbitrary, it is not metres,
and values are comparable only WITHIN a single image — never across images.

Therefore:
  - The field name must not imply distance or absolute units.
  - Its Field(description=...) must state: larger = nearer, arbitrary scale, not metres,
    comparable only within one image.
  - No field name anywhere in this file may contain meter, metre, mm, cm, or distance.

Also include in AnalyzeResponse:
  - image width and height in pixels, so a client can interpret the absolute boxes
  - the model version that produced the result
  - the inference duration

Give every field a Field(description=...). Add a model_config json_schema_extra example
for each model — it becomes the OpenAPI example, which is the documentation people
actually read.

Show me the file. Do not write routes.
```

---

## The field this all turns on

```python
# Wrong — implies metres, which this project cannot provide.
depth_meters: float

# Wrong — ambiguous, which is the same failure with better manners.
depth: float

# Right.
relative_depth: float = Field(
    description=(
        "Relative inverse depth. Larger values are NEARER. Arbitrary scale — "
        "NOT metres. Comparable only between objects within this same image."
    )
)
```

The middle one is the one to watch for, because it looks fine. A consumer reading
`depth: 0.87` will assume *something*, and whatever they assume will be wrong in a way
that works during testing.

---

## Round 2 — make the constraint enforceable

```
Add a test at tests/test_schemas.py that FAILS if any field name in schemas.py contains
meter, metre, mm, cm, or distance. Walk the model fields programmatically — do not
hardcode the current field list, or the test stops protecting anything the moment
someone adds a field.

Also assert that the depth field's description mentions "not metres" and "nearer".
```

**Why a test rather than a code review note.** The constraint has to survive people who
have not read this lesson. A convention is a hope; a failing test is a fact, and it fires
at the moment someone adds `depth_meters` in six months.

---

## Round 3 — look at the generated docs

```bash
uv run uvicorn smart_scene_analyzer.api:app --reload
# then open http://localhost:8000/docs
```

Read the schema section as a client developer who has never spoken to you. Can you tell,
from the generated page alone, that the depth value is not metres?

If not, the description is not doing its job — and the OpenAPI page is exactly where that
misunderstanding would otherwise begin.

---

## What good output looks like

- Every field has a description stating its units or its meaning
- The depth field name carries "relative"; no name implies distance
- Boxes documented as `xyxy` in absolute pixels
- Image dimensions included, so absolute boxes are interpretable
- Examples present, and they render usefully in `/docs`
- The naming constraint is enforced by a test that walks fields programmatically

## Reject and re-run if

- The depth field is called `depth`, `depth_value`, or anything implying distance
- Descriptions are omitted "because the field name is obvious" — the field name is
  exactly what this lesson does not trust
- Routes or inference logic appear in `schemas.py`
- The naming test hardcodes today's field list
- Boxes are normalized without saying so, or the convention is left unstated
