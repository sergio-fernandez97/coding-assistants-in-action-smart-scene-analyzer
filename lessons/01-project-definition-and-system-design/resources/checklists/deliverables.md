# Lesson 01 — Deliverables checklist

Work top to bottom. The session is complete when every box is checked.

## Repository

- [ ] `smart-scene-analyzer` exists as its own git repository, separate from the course repo
- [ ] `uv sync` succeeds from a clean clone
- [ ] `uv run pytest` runs (passing with zero tests is fine at this stage)
- [ ] `uv run ruff check .` is clean
- [ ] Pushed to GitHub

## Harness

- [ ] `CLAUDE.md` exists and keeps the *Engineering roles*, *Conventions*, and *Constraints for assistants* sections
- [ ] `CLAUDE.md` contains nothing derivable by reading `src/` — no restated code
- [ ] `.claude/settings.json` reviewed; you can explain why each entry is in `allow` vs. `ask` vs. `deny`
- [ ] `/permissions` shows the policy loaded
- [ ] `/agents` lists all five agents
- [ ] You can state each agent's purpose in one sentence without re-reading it

## Design artifacts

- [ ] `docs/requirements.md` — every `<...>` placeholder replaced
- [ ] N1 (p95 latency) is a real number derived from the user experience, not from the model
- [ ] "Out of scope" section is non-empty
- [ ] `docs/architecture.md` — component diagram present
- [ ] Every module boundary has a data contract stating **type, units, and coordinate convention**
- [ ] The fusion strategy (box + depth map → one depth value) names a specific method and its failure mode
- [ ] Latency budget allocates N1 across stages and the numbers sum correctly
- [ ] An "Assumptions" section exists and is non-empty
- [ ] `src/smart_scene_analyzer/` has module stubs with docstrings and **no function bodies**
- [ ] `docs/roadmap.md` — Weeks 2–5, each with artifact-shaped exit criteria
- [ ] `docs/roadmap.md` has a "Blocked on decisions" section

## Decisions

- [ ] `docs/decisions/0001-*.md` records the inference target with real consequences listed
- [ ] Each ADR's "Consequences" names the files and infrastructure now depending on it
- [ ] The `TODO(Lesson 01)` markers in `CLAUDE.md` are resolved or still flagged deliberately

## Documentation

- [ ] `README.md` replaced — no template placeholder text remains
- [ ] **Setup section verified by deleting `.venv/` and following it verbatim**
- [ ] "Current status" section honestly marks stubs as stubs
- [ ] No performance numbers appear anywhere (no model has been trained)
- [ ] `CONTRIBUTING.md` exists with the quality gates and their commands

## Environment

- [ ] `docker build -t smart-scene-analyzer:dev .` succeeds
- [ ] Final image size recorded: `__________` (compare in Lesson 04)
- [ ] Runtime stage does **not** contain `torch`, `ultralytics`, or `mlflow`
- [ ] `docker compose config` validates
- [ ] `.github/workflows/ci.yml` runs lint before tests
- [ ] No credential appears in any `ENV` or `ARG`:
      `docker history --no-trunc smart-scene-analyzer:dev | grep -i -E 'api_key|secret|token'` returns nothing

## Hygiene

- [ ] `git status` shows no `.env`, no `data/`, no `.venv/`, no `*.pt`
- [ ] `.env` exists locally, is filled in, and is **not** tracked: `git check-ignore .env` prints `.env`
- [ ] `.env.example` documents every variable with no real values

## The one that isn't mechanical

- [ ] **You found at least one thing in `docs/architecture.md` you disagree with, and
      either changed it or wrote down why you kept it.**

If you skipped this box, go back. Every generated architecture contains a debatable
choice. Being unable to find it means you accepted the output rather than reviewed it
— and reviewing generated design is the entire skill this session teaches.
