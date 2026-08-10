# Prompt — the FastAPI service

**When:** Lesson 04, step 4.

**Which agent:** `backend`.

**Credits: zero.** The service runs your own weights in-process.

---

## Round 1 — settings and lifecycle

```
Use the backend agent.

Write src/smart_scene_analyzer/config.py using pydantic-settings.

Settings, all from the environment with sensible defaults:
  detector_weights_path    path to the YOLO11 .pt
  depth_model_id           the Depth Anything V2 HF identifier
  confidence_threshold     default 0.25
  max_upload_bytes         default 20 MB, matching Roboflow's own limit
  device                   auto-detect, overridable
  model_version            a string recorded in every response

The service must start in a container with nothing but environment variables. No path is
hardcoded, and no default points at anything outside the container.

Then write the model lifecycle in src/smart_scene_analyzer/models.py:
  - Load the detector and the depth model ONCE, in the FastAPI lifespan handler
  - Expose them through dependency injection
  - Loading inside a request handler is a bug. It will pass every test I write and time
    out under any real load.

Do not write routes yet.
```

**Why `model_version` is a setting rather than derived.** In Lesson 05, CI will deploy a
container and need to know which model is inside it. A version read from the environment
is a deployment fact; a version parsed from a weights filename is a guess.

---

## Round 2 — the routes

```
Now write src/smart_scene_analyzer/api.py.

  POST /analyze   multipart image upload -> AnalyzeResponse
  GET  /health    liveness + loaded model version
  GET  /ready     readiness — are the models actually loaded and usable?

/analyze must:
  1. Enforce max_upload_bytes and return 413 with a useful body if exceeded. Check the
     size before decoding — reading a 500 MB upload into memory to discover it is too
     large is the failure mode this limit exists to prevent.
  2. Return 415 if the bytes cannot be decoded as an image.
  3. Run detection, run depth, and fuse them via fusion.py.
  4. Return AnalyzeResponse, including image dimensions, model version, and inference
     duration.
  5. Return an empty detections list — with 200 — when nothing is found. Zero detections
     is a valid result, not an error.

Routes validate, delegate, and serialize. All inference logic lives in importable modules
that work without an HTTP client. If a route body is longer than about fifteen lines,
something belongs elsewhere.

/health and /ready are different: health means the process is up, ready means the models
are loaded. Lesson 05's deployment will use both, and conflating them makes a container
report itself available while it is still loading a model.

Structured logging: request id, image dimensions, inference duration, detection count.
Never log the image bytes or the API key.
```

---

## Round 3 — see a real response

```bash
uv run uvicorn smart_scene_analyzer.api:app --reload
curl -F 'file=@data/v1/test/images/<sample>.jpg' localhost:8000/analyze | jq
```

Check, by eye:

- The object you can see is closest has the **largest** `relative_depth`
- Boxes are in absolute pixels and land within the reported image dimensions
- `model_version` is populated
- `/docs` renders the schema descriptions, including the depth units

Then test the boundaries by hand, because these are what clients actually hit:

```bash
# Oversized -> 413
dd if=/dev/zero of=/tmp/big.jpg bs=1m count=25 2>/dev/null
curl -s -o /dev/null -w '%{http_code}\n' -F 'file=@/tmp/big.jpg' localhost:8000/analyze

# Not an image -> 415
echo "not an image" > /tmp/bad.jpg
curl -s -o /dev/null -w '%{http_code}\n' -F 'file=@/tmp/bad.jpg' localhost:8000/analyze
```

**Expected:** `413` and `415`. If either returns `500`, the service is telling the client
"something went wrong on my end" about a problem entirely on theirs.

---

## What good output looks like

- Models load once, in the lifespan handler, injected as dependencies
- Every setting comes from the environment with a container-safe default
- 413 is decided from the size before the image is decoded
- 415, 422, and 200-with-empty-list all behave as specified
- Route bodies are short; inference logic is importable and testable without HTTP
- `/health` and `/ready` mean different things
- Logs carry request id, dimensions, duration, and detection count — and no image bytes

## Reject and re-run if

- A model is loaded inside a request handler
- Any path, threshold, or model id is hardcoded
- Oversized or undecodable uploads produce 500
- Zero detections produces an error instead of an empty list
- Inference logic lives in the route body, making it untestable without an HTTP client
- `/health` and `/ready` are aliases for the same check
