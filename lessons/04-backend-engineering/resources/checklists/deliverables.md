# Lesson 04 — Deliverables checklist

## Before you start

- [ ] Model V1 weights exist under `runs/`
- [ ] `check_depth_ordering.py` passes on five scenes
- [ ] `docs/credit-budget.md` reconciled, at least 2 credits remaining
- [ ] Docker running

## Roles

- [ ] `backend.md`, `qa.md`, `integration.md` all read
- [ ] You can say which agent owns a schema bug and which owns a coordinate-space bug
- [ ] The tests were written by `qa`, not by the agent that wrote the code

## Schema — designed before the handler

- [ ] `src/smart_scene_analyzer/schemas.py` exists
- [ ] Every field has a `Field(description=...)` stating units or meaning
- [ ] The depth field name carries "relative"
- [ ] **No field name contains** `meter`, `metre`, `mm`, `cm`, or `distance`
- [ ] The depth description says "not metres", "larger is nearer", and "within one image"
- [ ] Boxes documented as `xyxy` in **absolute pixels**
- [ ] Image dimensions included in the response, so absolute boxes are interpretable
- [ ] The naming constraint is enforced by a test that walks fields programmatically
- [ ] `/docs` renders the descriptions, and a stranger could tell depth is not metres

## Fusion layer

- [ ] Coordinate spaces established from **real printed output**, on a non-square image
- [ ] `src/smart_scene_analyzer/fusion.py` exists
- [ ] A mismatched depth-map shape **raises** rather than being silently resized
- [ ] Region reduction uses the **median**, justified in the docstring
- [ ] All four degenerate cases defined and documented: zero-area, partly outside,
      entirely outside, empty after clipping
- [ ] No `NaN` can reach a JSON response
- [ ] The module is **pure** — no model loading, no file reads, no HTTP, no Roboflow
- [ ] Verified on a real scene: the visibly nearest object has the largest value
- [ ] Ordering is stable when the same scene is given at a different aspect ratio

## Service

- [ ] `config.py` reads everything from the environment, with container-safe defaults
- [ ] Models load **once**, in the lifespan handler, injected as dependencies
- [ ] `POST /analyze`, `GET /health`, `GET /ready` all present
- [ ] `/health` and `/ready` mean **different things**
- [ ] Oversized upload → **413**, decided before decoding
- [ ] Undecodable bytes → **415**
- [ ] Missing file field → **422**
- [ ] Zero detections → **200 with an empty list**
- [ ] Route bodies are short; inference logic is importable without an HTTP client
- [ ] Logs carry request id, dimensions, duration, detection count — and no image bytes, no key

## Tests

- [ ] `uv run pytest` passes in **seconds**
- [ ] Verified offline by actually hiding the weights, not by reading the code
- [ ] Image fixtures generated in code; **no committed binaries**
- [ ] A known-gradient depth fixture makes fusion assertions exact
- [ ] **The "fusion actually uses the depth map" test exists**
- [ ] All four degenerate box cases covered
- [ ] Boundary tests: 413, 415, 422, empty results, grayscale, 1×1
- [ ] Integration tests carry the `integration` marker and are excluded by default
- [ ] No assertion was loosened to make a test pass

## Container

- [ ] Multi-stage build; runtime stage has no build tooling
- [ ] Lockfile used
- [ ] Runs as non-root
- [ ] `HEALTHCHECK` present and passing
- [ ] **Weights mounted, not baked in**, with a comment saying why
- [ ] `opencv-python-headless`, not `opencv-python`
- [ ] Image size is explainable — no uninvited CUDA wheels
- [ ] `docker compose up -d` brings up api and mlflow
- [ ] The api reaches mlflow **by service name**, not `localhost`
- [ ] No secret in any committed file

## Deployment comparison — optional, ~1 credit

Skip entirely if you were short on credits. Record that you skipped it and why.

- [ ] Rates quoted from the skills with arithmetic, not recalled
- [ ] **Self-hosted correctly identified as metered, not free** (1 credit / 3,000 images)
- [ ] Hosted v2 identified as billed by **execution seconds**, not per image
- [ ] Benchmark discards warmup requests
- [ ] Estimate recorded in the ledger **before** the hosted run
- [ ] Actual cost reconciled against the estimate
- [ ] **No dedicated deployment was created** — it appears as a row with reasoning
- [ ] `docs/deployment-comparison.md` has measured latencies and cost per 1,000 images
- [ ] The recommendation names a traffic assumption and a crossover point
- [ ] The benchmark's limitations are stated

## Decisions

- [ ] `/adr inference target: ...` — closes the Lesson 01 open decision
- [ ] The ADR's Context contains **numbers you measured**, not a general argument
- [ ] It records that hosted-trained weights are not downloadable on the free plan
- [ ] It states what would change the decision

## Ledger

- [ ] Lesson 04 spend is 0 or about 0.5
- [ ] Running total across Lessons 02–04 at or under 7
- [ ] Reconciled against the Roboflow usage page

## Hygiene

- [ ] `uv run ruff check .` passes
- [ ] `uv run mypy src` passes
- [ ] `git status` shows no `.pt`, no `data/`, no `.env`
- [ ] This returns **nothing**:
      `grep -riE 'depth_m|meter|metre|distance' src/ | grep -v 'NOT metres'`

## The one that isn't mechanical

- [ ] **You photographed a real room with your phone, sent it to the service, and looked
      at the response.**

Every test image so far came from one dataset, one sensor, one set of rooms. The first
genuinely out-of-distribution image tells you more about the system than the entire test
suite — and this is the last cheap chance to learn it before Lesson 05 automates the whole
pipeline.
