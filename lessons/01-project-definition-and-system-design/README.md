# Lesson 01 — Project Definition & System Design

> Notion Week 1. Estimated time: 2.5–3 hours.

## Session goal

Build the **harness** before building the system. By the end of this session you will
have a repository whose structure, rules, and specialized roles are defined well
enough that an AI assistant working inside it produces consistent, reviewable output —
and you will have used that harness to generate the Smart Scene Analyzer's
architecture, documentation, and development environment.

The distinction that matters all course: a prompt is a request, a harness is a
constraint. A prompt shapes one response. A harness shapes every response, in every
future session, including the ones you are not present for. This session builds the
harness.

## Prerequisites

Run each check. Every one must pass before you continue.

| Requirement | Check | If it fails |
|---|---|---|
| Git | `git --version` | [git-scm.com](https://git-scm.com/downloads) |
| Claude Code | `claude --version` | [Install guide](https://docs.claude.com/en/docs/claude-code/overview) |
| `uv` | `uv --version` | `curl -LsSf https://astral.sh/uv/install.sh \| sh` |
| Python 3.11+ | `uv python install 3.11` | — |
| Docker running | `docker info` | Start Docker Desktop |
| GitHub account | `gh auth status` (optional) | Create one; you push your project at the end |

> **macOS note.** The system Python is 3.9 and is too old for this project. `uv` installs
> and manages 3.11 for you — do not modify the system interpreter.

## Deliverables

When this session ends, your `smart-scene-analyzer` repository contains:

- [ ] A git repository with an initial commit, pushed to GitHub
- [ ] `CLAUDE.md` — project rules loaded into every assistant session
- [ ] `.claude/settings.json` — a reviewed permission policy
- [ ] `.claude/agents/` — three role definitions (architecture, documentation, devops)
- [ ] `docs/requirements.md` — functional and non-functional requirements with numbers
- [ ] `docs/architecture.md` — components, data contracts, pipeline stages
- [ ] `docs/decisions/` — at least one ADR recording the inference-target decision
- [ ] `docs/roadmap.md` — the engineering plan for Weeks 2–5
- [ ] `README.md` and `CONTRIBUTING.md`
- [ ] `Dockerfile`, `docker-compose.yml`, `.github/workflows/ci.yml`

Verify with [`resources/checklists/deliverables.md`](resources/checklists/deliverables.md).

---

## Step-by-step

### 1. Create your project repository

**Do:** Create your own repo from the course template. Your project is separate from
this course repo — you read from the course, you write to yours.

```bash
# From the directory where you keep projects (NOT inside the course repo)
mkdir smart-scene-analyzer && cd smart-scene-analyzer
git init

# Copy the scaffold. Adjust the path to wherever you cloned the course.
cp -R <path-to-course-repo>/template/. .

ls -a
```

**Expected result:** the directory contains `CLAUDE.md`, `README.md`, `pyproject.toml`,
`.env.example`, `.gitignore`, `.mcp.json`, and the directories `.claude/`, `src/`,
`tests/`, `docs/`, `data/`, `notebooks/`.

> `cp -R template/. .` — the trailing `/.` copies hidden files too. Without it you
> silently lose `.claude/`, and nothing later in this lesson works.

---

### 2. Install dependencies and confirm the environment

**Do:**

```bash
uv sync
uv run python -c "import fastapi, cv2, numpy; print('ok')"
```

**Expected result:** `ok`. A `.venv/` directory now exists and is gitignored.

---

### 3. Read the harness before you run it

**Do:** Open `CLAUDE.md` and read it end to end. Then open the three files in
`.claude/agents/`.

This is not a formality. `CLAUDE.md` is loaded into the context of *every* Claude Code
session in this repository — it is where a rule goes when you want it to survive the
session you are in. Rules that live only in a prompt are gone in an hour.

Notice what the file does and does not contain:

| It contains | It does not contain |
|---|---|
| Layout, and what each directory is for | Implementation detail |
| Commands to run tests, lint, types | Anything reachable by reading the code |
| Conventions an assistant cannot infer (bbox is `xyxy` absolute pixels) | Restatements of the code |
| Constraints (ask before adding a dependency) | Aspirations |

The last row is the one students get wrong. `CLAUDE.md` earns its place by carrying
what is *not* derivable from the repository. Anything an assistant could learn by
reading `src/` is noise that costs context on every single request.

**Expected result:** you can say in one sentence what each of the three agents is for.

---

### 4. Bootstrap and refine `CLAUDE.md`

**Do:** Start Claude Code and generate a baseline, then compare it to the template
version.

```bash
claude
```

```
/init
```

`/init` scans the repository and writes a `CLAUDE.md` describing what it finds. It will
overwrite or extend the template file — that is intentional. Your job is to review its
output and keep the parts that are true, then restore the template's constraint
sections, which `/init` cannot know about.

**Expected result:** a `CLAUDE.md` that keeps the template's *Engineering roles*,
*Conventions*, and *Constraints for assistants* sections, plus anything accurate that
`/init` discovered. Two `TODO(Lesson 01)` markers remain at the bottom — you resolve
them in step 7.

> **Why not just accept `/init`'s output?** Because `/init` documents what exists. The
> value of `CLAUDE.md` is mostly in what *must be true* — the constraints. An assistant
> can read your directory tree. It cannot read your intent.

---

### 5. Review the permission policy

**Do:** Open `.claude/settings.json` and read the three lists.

```jsonc
"allow":  // runs without asking
"ask":    // prompts every time
"deny":   // refused outright
```

Walk the reasoning:

- `git status`, `git diff`, `uv run` are in `allow` — read-only or trivially
  reversible, and prompting on them trains you to click *yes* without reading.
- `git push`, `git commit`, `uv add`, `docker run` are in `ask` — each has a cost
  outside your working tree, or changes the dependency surface.
- `.env` and `*.pem` are in `deny` — an assistant never needs to read a secret to do
  its job, and content it reads can end up in output.

**Do:** Verify the policy is loaded:

```
/permissions
```

**Expected result:** the rules from `settings.json` are listed.

> **The course never uses `--dangerously-skip-permissions`.** Reviewing what an
> assistant is about to do is not friction to be removed — it is the part of the
> harness that catches the confident mistake. Skip it and you have a code generator
> again.

---

### 6. Understand the subagent definitions

**Do:** Open `.claude/agents/architecture.md` and look at the frontmatter.

```yaml
---
name: architecture
description: Use for system design work — ...
tools: Read, Grep, Glob, Write, Edit, WebFetch
model: opus
---
```

| Field | What it does |
|---|---|
| `name` | How you invoke it |
| `description` | **How the main assistant decides to delegate.** Written for a dispatcher, not a human. This is the field students under-invest in. |
| `tools` | The agent's capability boundary. Architecture has no `Bash` — it designs, it does not run things. |
| `model` | Design work gets `opus`; mechanical work gets `sonnet` |

A subagent also gets its **own context window**. That is the real reason to use one:
the Architecture Agent can read forty files to produce one design document, and none of
that reading pollutes your main session.

**Do:** Confirm they are registered:

```
/agents
```

**Expected result:** `architecture`, `documentation`, `devops`, `dataset-engineer`, and
`data-pipeline` are listed. (The last two are used in Lesson 02.)

---

### 7. Define requirements — including the numbers

**Do:** Fill in
[`resources/templates/requirements-worksheet.md`](resources/templates/requirements-worksheet.md).
Copy it to your project as `docs/requirements.md` and complete it.

```bash
cp <path-to-course-repo>/lessons/01-project-definition-and-system-design/resources/templates/requirements-worksheet.md docs/requirements.md
```

The non-functional section is the one that changes the architecture. "Fast" is not a
requirement. "p95 end-to-end latency under 400 ms for a 1280×720 image" is — it
determines model size, whether depth and detection run in parallel, and whether you can
afford a network hop per request.

⚠️ **OPEN — resolve this before step 8.** The single biggest architectural fork is the
**inference target**, and it is not yet decided for this course:

| Option | Consequence |
|---|---|
| **Cloud** — FastAPI serves both models | Simpler pipeline, single codebase, network round-trip per frame, server GPU cost |
| **On-device** — ONNX / Core ML / TFLite | No round-trip, works offline, but forces export/quantization work and splits the codebase |

Pick one, then record it:

```
/adr inference target: cloud vs on-device
```

**Expected result:** `docs/requirements.md` with numeric targets, and
`docs/decisions/0001-inference-target.md`. Update the first `TODO(Lesson 01)` marker in
`CLAUDE.md`.

---

### 8. Run the Architecture Agent

**Do:** Use the prompt in
[`resources/prompts/01-architecture-agent.md`](resources/prompts/01-architecture-agent.md).

**Expected result:** `docs/architecture.md` containing a component diagram, one named
data contract per module boundary (with units and coordinate conventions), a latency
budget allocated across stages, and a rationale per major choice. Plus module stubs
under `src/smart_scene_analyzer/` with docstrings and no function bodies.

**Review it against the template scaffold.** The directory shape the agent produces
should be close to `template/`'s. Where it differs, decide which is better — do not
assume either is right. Being able to judge an assistant's architectural output is the
skill this session is actually teaching.

**Red flags to reject and re-run:**

- A data contract that says "detections" without stating the type, units, and frame
- Implementation bodies (you asked for design)
- A latency budget that does not sum to your requirement
- Silent resolution of a decision you marked open

---

### 9. Run the Documentation Agent

**Do:** Use [`resources/prompts/02-documentation-agent.md`](resources/prompts/02-documentation-agent.md).

**Expected result:** a rewritten `README.md` (replacing the template placeholder) and a
new `CONTRIBUTING.md`.

**Verify by the harshest available test:** delete your `.venv/`, follow your own README
setup section verbatim, and see whether it works.

```bash
rm -rf .venv && uv sync && uv run pytest
```

If a step is missing or wrong, that is a documentation bug — fix it now, while you
still remember what the correct step was.

---

### 10. Run the DevOps Agent

**Do:** Use [`resources/prompts/03-devops-agent.md`](resources/prompts/03-devops-agent.md).

**Expected result:** `Dockerfile` (multi-stage, non-root, pinned base), `.dockerignore`,
`docker-compose.yml`, and `.github/workflows/ci.yml`.

**Do:** Prove the image builds. Do not take the agent's word for it.

```bash
docker build -t smart-scene-analyzer:dev .
docker image ls smart-scene-analyzer
```

**Expected result:** a successful build. Note the image size — you will compare against
it in Lesson 04 once the model dependencies land.

⚠️ **OPEN — MLflow hosting.** `docker-compose.yml` needs an MLflow service, and where
MLflow runs (local Docker / self-hosted server / managed) is undecided. The DevOps
Agent defaults to local MLflow with a named volume and labels it a placeholder. Record
the choice when it is made:

```
/adr mlflow hosting strategy
```

---

### 11. Generate the engineering roadmap

**Do:** Use [`resources/prompts/04-roadmap.md`](resources/prompts/04-roadmap.md).

**Expected result:** `docs/roadmap.md` covering Weeks 2–5, where each milestone names
its deliverable, its owning role, and its entry condition — not just a list of tasks.

---

### 12. Commit and push

**Do:**

```bash
git add -A
git status          # read this. Confirm no .env, no data/, no .venv/
git commit -m "Lesson 01: project scaffold, harness configuration, and system design"
gh repo create smart-scene-analyzer --private --source=. --push
```

**Expected result:** a pushed repository. `git status` before committing must show no
`.env`, no `data/`, no `.venv/`, and no model weights.

---

## Verification

Work through
[`resources/checklists/deliverables.md`](resources/checklists/deliverables.md). The
session is complete when every box is checked.

Fast automated pass:

```bash
uv run ruff check .
uv run pytest
docker build -t smart-scene-analyzer:dev .
git status --porcelain | grep -E '\.env$|^\?\? data/' && echo "LEAK — fix .gitignore" || echo "clean"
```

The real check is qualitative: **open `docs/architecture.md` and find one thing you
disagree with.** If you cannot, you have not read it critically enough. Every generated
architecture contains at least one choice worth arguing about — finding it is the
skill.

---

## Open items

- ⚠️ **Inference target** — cloud FastAPI vs. on-device ONNX/Core ML/TFLite (step 7).
  Notion Open Decision #2. Blocks a final architecture.
- ⚠️ **MLflow hosting** — local Docker, self-hosted, or managed (step 10). Notion Open
  Decision #4. Determines `docker-compose.yml` and Lesson 03's tracking setup.
- ⚠️ **Mobile app scope** — a real client application, or a stub that exercises the
  API? The architecture's outermost layer depends on this, and it is not yet decided.
- ⚠️ **Codex** — the course lists OpenAI Codex alongside Claude Code. This lesson is
  Claude Code only; the `AGENTS.md` and `codex plugin` equivalents are not yet written.

All four are tracked in the course [`TODO.md`](../../TODO.md).

---

## Further reading

- [Claude Code — memory and `CLAUDE.md`](https://docs.claude.com/en/docs/claude-code/memory)
- [Claude Code — subagents](https://docs.claude.com/en/docs/claude-code/sub-agents)
- [Claude Code — settings and permissions](https://docs.claude.com/en/docs/claude-code/settings)
- [Claude Code — slash commands](https://docs.claude.com/en/docs/claude-code/slash-commands)
- [Architecture Decision Records](https://adr.github.io/)

**Next:** [Lesson 02 — Dataset Engineering](../02-dataset-engineering/)
