# Prompt — containerize the service

**When:** Lesson 04, step 6.

**Which agent:** `devops` (from Lesson 01).

**Credits: zero.**

---

## Round 1 — the image

```
Use the devops agent.

Write a Dockerfile for the Smart Scene Analyzer API.

Requirements:
  - Multi-stage: build dependencies in one stage, copy into a slim runtime stage
  - Use uv for dependency installation, with the lockfile — not a bare `uv sync`
    resolving fresh at build time
  - Install the ml and depth extras
  - Run as a non-root user
  - HEALTHCHECK hitting /health
  - Expose 8000, run with uvicorn

Do NOT bake model weights into the image. Explain in a comment where they come from
instead. Weights are hundreds of megabytes and change on every retrain; baking them in
means rebuilding and repushing the whole image for a change that has nothing to do with
the code.

The service must start with only environment variables. No path inside the image points
anywhere outside it.
```

Two things that will each cost an hour if met the hard way:

| Trap | What happens |
|---|---|
| `opencv-python` instead of `opencv-python-headless` | Import fails looking for a display server. The error does not mention displays. The template already pins headless — keep it |
| `torch` CPU vs CUDA wheels | The default wheel may pull a multi-gigabyte CUDA runtime into an image that has no GPU. Pin the CPU index for the container build |

---

## Round 2 — compose

```
Write docker-compose.yml with two services:

  api      the Smart Scene Analyzer
           - weights mounted as a volume from ./runs, read-only
           - environment from .env
           - depends_on mlflow

  mlflow   the tracking server from Lesson 03
           - sqlite backend on a named volume so runs survive a restart
           - port 5000

The api service reads MLFLOW_TRACKING_URI pointing at the mlflow service by name, not
localhost. Inside a compose network, localhost is the container itself.

Do not put any secret in the compose file. It reads .env, which is gitignored.
```

**This finally answers Lesson 01's open MLflow-hosting decision** with a working
configuration rather than an intention. Record it if you have not already:
`/adr mlflow hosting: local sqlite in docker compose`.

Note the consequence honestly: runs live on one machine, in one volume. Lesson 05's CI
will need to read runs it did not create, and this configuration does not provide that.
Better to write that down now than to discover it inside a failing workflow.

---

## Round 3 — verify it actually serves

```bash
docker build -t smart-scene-analyzer:dev .
docker compose up -d
docker compose ps          # both services healthy

curl -sf localhost:8000/health | jq
curl -sf localhost:8000/ready | jq
curl -sF 'file=@data/v1/test/images/<sample>.jpg' localhost:8000/analyze | jq
```

**Expected:** `/health` responds immediately; `/ready` may take a few seconds while models
load; `/analyze` returns detections with relative depth.

**Do:** Check the image size and the startup log.

```bash
docker images smart-scene-analyzer:dev
docker compose logs api | head -30
```

A multi-gigabyte image usually means CUDA wheels arrived uninvited. A startup log showing
a model download on every boot means weights are being fetched rather than mounted, which
will bite in CI where the network is slower and metered differently.

---

## What good output looks like

- Multi-stage build; the runtime stage does not contain build tooling
- Lockfile used, so builds are reproducible
- Non-root user
- HEALTHCHECK present and passing
- Weights mounted, not baked in, with a comment saying why
- Compose brings up api and mlflow; the api reaches mlflow by service name
- No secret in any committed file
- Image size is explainable

## Reject and re-run if

- Weights are copied into the image
- `opencv-python` replaces the headless build
- A secret appears in `docker-compose.yml`
- The api container refers to MLflow as `localhost`
- The image is multiple gigabytes with no explanation
- `/ready` returns healthy before the models have loaded — that is the specific bug the
  health/ready split exists to prevent, and a container that lies about readiness will
  take traffic it cannot serve
