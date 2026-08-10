# Prompt — DevOps Agent

**When:** Lesson 01, step 10. After the README and architecture exist.

---

```
Set up the build, containerization, and CI for the Smart Scene Analyzer.

Read first: CLAUDE.md, pyproject.toml, docs/architecture.md, .env.example.

Produce:

Dockerfile
- Multi-stage: a build stage that installs dependencies with uv, and a slim runtime
  stage that copies only what is needed to serve.
- Pin the base image to a specific tag, not `latest`.
- Run as a non-root user.
- Do NOT install the training dependencies (torch, ultralytics, mlflow) in the
  runtime stage. Serving and training have different dependency sets and the
  difference is measured in gigabytes.

.dockerignore
- Must exclude: data/, datasets/, mlruns/, runs/, .venv/, .git/, notebooks/,
  *.pt, *.onnx, tests/

docker-compose.yml
- The API service, built from the Dockerfile, with the port exposed.
- An MLflow service with a named volume so runs survive a restart.
- Environment variables read from the host environment or a .env file — never
  hardcoded values.

.github/workflows/ci.yml
- Trigger on push and pull request.
- Jobs ordered cheapest-first: ruff check → ruff format --check → mypy → pytest →
  docker build. A formatting error should fail in seconds, not after a six-minute
  test run.
- Cache the uv environment.
- Do NOT push images or deploy. Build and validate only.

Then verify your own work:
  docker build -t smart-scene-analyzer:dev .
Run it, and report the actual output. If the build fails, fix it and build again.
Report the final image size.

Constraints:
- Never put a secret in a Dockerfile ENV or ARG — it is baked into the image layer
  and readable by anyone who pulls it. Secrets come from the runtime environment
  and, in CI, from GitHub Actions secrets.
- Do NOT add a cloud deployment target. That is a project decision I have not made.
- MLflow hosting is still undecided. Default to the local containerized MLflow with
  a named volume, and add a comment in docker-compose.yml saying it is a placeholder
  pending that decision.
```

---

## Verification

```bash
docker build -t smart-scene-analyzer:dev .
docker image ls smart-scene-analyzer
docker compose config          # validates compose syntax without starting anything
```

Then confirm no secret was baked in:

```bash
docker history --no-trunc smart-scene-analyzer:dev | grep -i -E 'api_key|secret|token' && echo "LEAK" || echo "clean"
```

## Reject and re-run if

- The agent reports a successful build it did not actually run
- Any `ENV` or `ARG` in the Dockerfile holds a credential
- The runtime stage contains `torch` or `ultralytics`
- CI runs tests before lint
- A cloud provider appears anywhere
