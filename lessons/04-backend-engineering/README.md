# Lesson 04 — Backend Engineering & Production APIs

> Notion Week 4. Estimated time: 4–5 hours.

## Session goal

Turn two models and a depth estimator into one service that returns a single, coherent
answer — and prove the cost model of the alternative rather than assuming it.

Three new roles arrive: `backend` owns the HTTP surface, `integration` owns the fusion
between detection and depth, `qa` owns the proof that any of it works. The split matters
because the hardest bug in this lesson lives in exactly one of those seams. Two models,
two coordinate spaces, two resolutions, and one silent mismatch that produces numbers
that look completely reasonable.

The other thread is deployment economics. You will build a service that runs your own
weights in-process for zero credits, then spend about one credit measuring it against
Roboflow's hosted API — and discover that the "obviously free" middle option is not free
either. A deployment table with real numbers in it is worth more than any amount of
architectural opinion.

## Prerequisites

- [ ] Lesson 03 complete: model V1 (and V2) trained, weights under `runs/`
- [ ] `src/smart_scene_analyzer/depth.py` passing `check_depth_ordering.py`
- [ ] `docs/credit-budget.md` reconciled, with **at least 2 credits remaining**
- [ ] Docker running: `docker --version`
- [ ] `uv sync --extra ml --extra depth` runs cleanly

> **The hosted comparison in step 7 is the only billed step, and it is optional.** If you
> are short on credits, skip it and record the reason. Steps 1–6 and 8–9 produce a
> working service and every other deliverable.

## Deliverables

- [ ] `.claude/agents/backend.md`, `qa.md`, and `integration.md` in use
- [ ] `src/smart_scene_analyzer/fusion.py` — per-object depth, units stated, pure
- [ ] `src/smart_scene_analyzer/schemas.py` — Pydantic request/response contracts
- [ ] `src/smart_scene_analyzer/api.py` — FastAPI app, models loaded at startup
- [ ] A test suite passing with **no GPU, no network, no weights on disk**
- [ ] `Dockerfile` and `docker-compose.yml` with the service and MLflow
- [ ] `docs/deployment-comparison.md` — three options, measured, with cost per 1,000 images
- [ ] An ADR for the inference target, closing the Lesson 01 open decision
- [ ] The ledger updated and reconciled

Verify with [`resources/checklists/deliverables.md`](resources/checklists/deliverables.md).

---

## Step-by-step

### 1. Meet the three new roles

**Do:** Read all three definitions.

```bash
$EDITOR .claude/agents/backend.md .claude/agents/qa.md .claude/agents/integration.md
```

They have identical tool lists. The boundary between them is not capability — it is
**responsibility**, and it is drawn where the failure modes differ:

| Role | Owns | Characteristic failure |
|---|---|---|
| `backend` | HTTP surface, schemas, model lifecycle | A schema that lies about units; a model loaded per request |
| `integration` | Fusing boxes with depth | A coordinate-space mismatch that produces plausible numbers |
| `qa` | Proving it works | A test that passes on the bug it was written to catch |

**Expected result:** you can say which agent owns "the response returns `depth` as a bare
float" (`backend` — it is a schema contract) and which owns "the depth value is sampled
from the wrong region" (`integration`).

> Lesson 03 split `ml-engineer` from `evaluation` because one agent should not both build
> and grade. The same principle applies here, one layer down: `qa` writes the tests, and
> `qa` did not write the code under test.

---

### 2. Design the response schema first

**Do:** Before any handler exists, use
[`resources/prompts/01-response-schema.md`](resources/prompts/01-response-schema.md) to
have the `backend` agent design `src/smart_scene_analyzer/schemas.py`.

The response is the only part of this service anyone else will ever see. Once a mobile
client parses a field, its name and its units are frozen — changing them later is a
coordinated release, not an edit.

**That stops being hypothetical next week.** In Lesson 05 an Expo client generates its
TypeScript types from this schema's OpenAPI document, and ships to phones on its own
release cycle. Two consequences worth designing for now rather than discovering then:

- **The response must carry the dimensions of the image it processed.** Boxes are absolute
  pixels, and a client that downscales before uploading cannot place them without knowing
  which frame they are in. This is already on the deliverables checklist; Lesson 05 is why.
- **Every `description` you write becomes a comment in the generated client.** The
  sentence explaining that depth is not metres travels, automatically, into the codebase
  of the person most likely to display it as a distance.

**The field that decides this lesson:**

```python
# Wrong. Implies metres, which this project cannot provide.
depth_meters: float

# Wrong. Ambiguous, which is the same failure with better manners.
depth: float

# Right.
relative_depth: float = Field(
    description="Relative inverse depth. Larger is nearer. "
                "Arbitrary scale — NOT metres. Comparable only within one image."
)
```

`CLAUDE.md` has required this since Lesson 01: *"Ambiguity about whether a depth value is
metres or normalized disparity is a real source of bugs in this project — say which."*
Lesson 02 scoped depth to inference-only, Lesson 03 built a module that says so in every
signature, and this is where the chain either holds or breaks. A consumer who divides by
this number to get distance has been misled by the schema, and the schema is the last
place that could have stopped them.

**Expected result:** `schemas.py` with a `Detection` model (class, confidence, `xyxy`
box in absolute pixels, relative depth) and an `AnalyzeResponse`, every field carrying a
description that states units.

---

### 3. Build the fusion layer

**Do:** Use [`resources/prompts/02-fusion-layer.md`](resources/prompts/02-fusion-layer.md)
with the `integration` agent to write `src/smart_scene_analyzer/fusion.py`.

**This is where the real bugs live.** YOLO11 runs at 640×640. Depth Anything V2 has its
own input size. The uploaded image has a third. Three coordinate spaces, and a box indexed
into the wrong one returns a number — the wrong number, in range, for the wrong region.

Non-negotiables, all of which the prompt enforces:

- **Reconcile resolutions explicitly.** Never index a depth map with box coordinates
  without having proven they share a space. If the depth map is returned at input
  resolution (as Lesson 03 required), say so and assert it.
- **Median, not mean**, for reducing a box region — an occluder in front of the object
  skews the mean, and box corners routinely contain background.
- **Every degenerate case has a defined result**: zero-area box, box partly outside the
  image, box entirely outside, empty region after clipping. `NaN` reaching a JSON response
  is not a defined result.
- **Keep it pure.** Arrays and boxes in, structure out. No model loading, no file reads,
  no HTTP. That is what lets `qa` test it exhaustively without a GPU.

**Expected result:** `fusion.py` with a function taking detections and a depth map and
returning fused results, tested on a real image where you can see that the foreground
object reads as nearer.

---

### 4. Build the service

**Do:** Use [`resources/prompts/03-fastapi-service.md`](resources/prompts/03-fastapi-service.md).

```
POST /analyze      multipart image upload → detections with relative depth
GET  /health       liveness, plus which model version is loaded
GET  /ready        readiness — are the models actually loaded?
```

Three requirements that separate a service from a script:

1. **Load models once, at startup**, through the FastAPI lifespan handler and dependency
   injection. A model loaded inside a request handler is a service that times out under
   any real load, and it will pass every test you write.
2. **Configuration from the environment**, via `pydantic-settings`. Weights path,
   confidence threshold, max upload size. The service must start in a container with
   nothing but environment variables.
3. **Correct status codes.** 413 over the size limit — mirroring Roboflow's own 20 MB
   limit is a defensible choice worth stating. 415 for an undecodable format. 422 for a
   malformed request. Returning 500 for a 30 MB upload is a bug report the client cannot
   act on.

**Do:** Run it and look at a real response.

```bash
uv run uvicorn smart_scene_analyzer.api:app --reload
curl -F 'file=@data/v1/test/images/<sample>.jpg' localhost:8000/analyze | jq
```

**Expected result:** JSON with detections, boxes, confidences, and a relative depth per
object — where the object you can see is closest has the largest value.

---

### 5. Test it properly

**Do:** Hand off to `qa` with
[`resources/prompts/04-test-suite.md`](resources/prompts/04-test-suite.md).

**The suite must run with no GPU, no network, and no weights on disk**, in seconds.
Inference is mocked; fixtures return canned detections and depth maps. This is not a
purity exercise — a suite that needs a GPU is a suite that does not run in CI, and
Lesson 06 is CI.

What actually needs testing, in order of what breaks:

| Test | Why |
|---|---|
| Fusion on synthetic depth with known ordering | The core logic, testable exactly |
| All four degenerate box cases | Where `NaN` gets in |
| Coordinate-space handling at three different resolutions | The bug this lesson exists to prevent |
| Oversized upload → 413 | Boundary behaviour clients depend on |
| Corrupt / grayscale / one-pixel image | The failures that reach production |
| Zero detections | Empty list, not an error |
| Response schema field names and units | The contract |

**One test earns its place above all the others:** assert that the fused output changes
when the depth map changes. A fusion function that ignores its depth argument passes every
schema test, every status-code test, and every smoke test — and returns confident garbage.

> **Do not weaken an assertion to make a test pass.** If a test fails, either the code is
> wrong or the test encoded the wrong expectation. Decide which, and say which. Loosening
> a threshold until it goes green destroys the only signal the suite carries.

**Expected result:** `uv run pytest` passes offline in seconds, and integration tests
carry the `integration` marker.

---

### 6. Containerize

**Do:** Use the `devops` agent from Lesson 01 with
[`resources/prompts/05-containerize.md`](resources/prompts/05-containerize.md).

```bash
docker build -t smart-scene-analyzer:dev .
docker compose up -d
curl localhost:8000/health
```

`docker-compose.yml` runs the service alongside MLflow, finally answering Lesson 01's
open question about MLflow hosting with a working configuration rather than an intention.

**Expected result:** the containerized service answers `/health` and `/analyze`.

Two things that will cost you an hour otherwise:

- **Weights are not in the image.** Mount them, or fetch them at startup from MLflow.
  A multi-hundred-megabyte layer that changes every retrain defeats the point of layers.
- **`opencv-python-headless`, not `opencv-python`.** The template already specifies it.
  The non-headless build wants a display server that a container does not have, and the
  error it produces does not mention displays.

---

### 7. ⚠️ Measure the alternatives — about 1 credit

**Optional.** Skip if you have fewer than 2 credits, and record why.

You have a service running local weights for zero credits. The question this step answers
is what the other options actually cost — not what they seem like they should cost.

**Do:** Copy the template, then work through
[`resources/prompts/06-deployment-comparison.md`](resources/prompts/06-deployment-comparison.md).

```bash
cp <path-to-course-repo>/lessons/04-backend-engineering/resources/templates/deployment-comparison.md docs/
```

Send a fixed 200-image benchmark set through each available path, measure latency, and
compute cost per 1,000 images from the published rates.

| Option | Rate | Cost per 1,000 images | Notes |
|---|---|---|---|
| **Local in-process** | — | **0** | What you built. No network, no per-image cost |
| **Self-hosted inference server** | 1 credit / 3,000 images | **~0.33** | `localhost:9001`, Docker |
| **Hosted serverless (v2)** | 1 credit / 500 **seconds** | **~1** at 0.5 s/image | `serverless.roboflow.com` |
| **Dedicated (GPU)** | 1 credit / hour of **uptime** | Depends entirely on utilization | ⛔ Not in this course |
| **Local in-process, on Azure Container Apps** | Azure meter, free grant | **0 Roboflow credits** | Lesson 05's target. Cost moves currency, not away |

> **The last row is where this is going.** Lesson 05 puts your container on Azure and
> points a phone at it. Note what that changes and what it does not: the Roboflow cost per
> image stays zero because the weights are yours, and the compute cost becomes Azure's
> meter instead — a *different* budget with a *different* failure mode, which is its own
> lesson. What matters here is the row you would be on if you had chosen hosted detection:
> **1 credit per 1,000 images, paid every time somebody taps the shutter.** A `curl` loop
> never made that visible. A camera app would.

> **The correction this step exists to deliver:** the self-hosted inference server on
> `localhost:9001` is **metered**. It runs on your hardware and it still bills, at 1 credit
> per 3,000 images. "Run it yourself and it's free" is the intuition almost everyone has,
> and it is wrong — `inference/workflows.md` describes the local cost model as *"metered
> credits + your hardware"*. Carry the correct version into Lesson 06, where an automated
> pipeline will be making these calls without a human watching.

**Do:** Budget before you measure. 200 images at roughly 0.5 s each is ~100 seconds of
hosted execution, so about **0.2 credits** — but the agent must state the estimate and
your remaining balance before calling anything, and your `models_infer` permission rule
will fire.

⛔ **Dedicated deployments are denied in this project.** They bill uptime rather than
usage: one deployment left running is 24 credits a day, more than the entire course
budget. Include the row in the table with that reasoning; do not create one.

**Expected result:** `docs/deployment-comparison.md` with measured latencies, computed
cost per 1,000 images, and a recommendation tied to a traffic assumption — because the
right answer genuinely changes with volume, and a recommendation without a stated
assumption is just a preference.

---

### 8. Close the Lesson 01 open decision

Lesson 01 recorded ⚠️ OPEN: **cloud FastAPI vs. on-device ONNX / Core ML / TFLite.** You
now have the evidence to close it.

**Do:**

```
/adr inference target: containerized FastAPI with local weights
```

The ADR must state what you learned rather than what you assumed:

- Local in-process inference costs nothing per image; hosted and self-hosted both meter
- On the free plan you cannot download hosted-trained weights, so a hosted-trained model
  is not portable into your own service
- The measured latency of each path, from step 7
- What would change the decision — a traffic level, a plan upgrade, a latency requirement

**Write the *Revisit when* clause carefully.** Lesson 05 builds a real client, deploys to
Azure, and measures latency over cellular — so at least one of your trigger conditions is
about to fire on schedule. An ADR whose revisit condition occurs and is never revisited
has stopped being a decision and become a piece of history.

Note also what your latency numbers from step 7 are and are not. They were measured on
loopback, which means they measure how fast your code is. Lesson 05 measures how fast the
product is, and the gap between those two is the entire network. Say in the ADR which one
you have.

**Expected result:** an ADR whose Context section contains numbers you measured.

> The `/adr` command tells the agent: *"If you do not know why this decision was forced,
> ask me rather than writing a plausible-sounding rationale. A fabricated Context is worse
> than a blank one, because it will be believed."* This is the ADR where that instruction
> pays off — you have real measurements, and the temptation is to write the general
> argument instead of your specific one.

---

### 9. Reconcile and commit

**Do:**

1. Open `app.roboflow.com/<workspace>/settings/usage`
2. Compare against `docs/credit-budget.md`
3. Update **Remaining** and **Last reconciled**

**Expected result:** Lesson 04 spend is **0** or about **0.5**. Running total across
Lessons 02–04 at or under **7**, leaving **13 or more** for Lessons 05–06. Lesson 05
spends nothing on Roboflow; Lesson 06 is allocated 4.

```bash
uv run ruff check . && uv run mypy src && uv run pytest
git add -A
git status          # confirm: no .pt, no data/, no .env
git commit -m "Lesson 04: FastAPI service, depth fusion, tests, deployment comparison"
git push
```

---

## Verification

Work through
[`resources/checklists/deliverables.md`](resources/checklists/deliverables.md).

```bash
# Offline, no GPU, seconds
uv run pytest

# Quality gates
uv run ruff check . && uv run mypy src

# The container actually serves
docker compose up -d
curl -sf localhost:8000/health | jq
curl -sF 'file=@data/v1/test/images/<sample>.jpg' localhost:8000/analyze | jq

# Nothing leaked
git status --porcelain | grep -E '\.pt$|^\?\? data/|\.env$' && echo "LEAK" || echo "clean"
```

The check that matters most, and which no command performs:

```bash
grep -riE 'depth_m|meter|metre|distance' src/ | grep -v 'NOT metres'
```

**This must return nothing.** Any identifier implying absolute distance is a bug, because
the project cannot produce one. Lesson 02 decided it, Lesson 03 built it, and this is
where it would leak into a client contract.

Then read:

- Every response field's description states its units
- Boxes are documented as `xyxy` in absolute pixels
- The fusion layer has no model loading, file reads, or HTTP calls
- `docs/deployment-comparison.md` shows self-hosted as **metered, not free**
- The inference-target ADR cites measurements, not general arguments

The qualitative check: **upload a photo of a real room from your phone and look at the
response.** Your test images come from one dataset with one sensor. The first genuinely
out-of-distribution image usually tells you more about the system than the whole test
suite — and it is the last cheap opportunity to find that out before a real phone starts
sending you images your dataset has never seen.

---

## Open items

- ⚠️ **Self-hosted inference metering** (step 7) — the rate is documented as 1 credit per
  3,000 images, but whether a locally hosted server meters *every* call or only
  authenticated cloud-model calls is not spelled out in the skills. Measure it against the
  usage page if you run this path.
- ⚠️ **MLflow in CI** — `docker-compose.yml` gives one machine a tracking server. Lesson 06
  needs CI to read runs it did not create. Carried from Lesson 03.
- ⚠️ **Free-plan credit allowance unconfirmed** — carried from Lesson 02.

> **Resolved since this lesson was written:** *mobile app scope*. It is a real client —
> an Expo app for iOS and Android, built in Lesson 05 against the schema you designed in
> step 2. Which is why that step now asks you to include the processed image dimensions in
> the response: a client that downscales before uploading cannot place an absolute box
> without them.

All tracked in the course [`TODO.md`](../../TODO.md).

---

## Further reading

Local skill sources, in `computer-vision-skills/skills/`:

- `inference/SKILL.md` — deployment option comparison with latency and cost columns
- `inference/local-tooling.md` — the self-hosted inference server on `localhost:9001`
- `api-reference/inference.md` — URL patterns, auth, request/response shapes, error codes.
  Note: **"V2 is credit-billed by execution time (seconds)"**
- `api-reference/rest-api.md` — the wider REST surface
- `plans-and-pricing/SKILL.md` — the rates behind step 7's table

External:

- [FastAPI — lifespan events](https://fastapi.tiangolo.com/advanced/events/)
- [Pydantic — field descriptions](https://docs.pydantic.dev/latest/concepts/fields/)
- [Roboflow Inference](https://inference.roboflow.com/)

**Previous:** [Lesson 03](../03-model-development/) ·
**Next:** [Lesson 05 — Mobile Client & Cloud Delivery](../05-mobile-client-and-delivery/)
