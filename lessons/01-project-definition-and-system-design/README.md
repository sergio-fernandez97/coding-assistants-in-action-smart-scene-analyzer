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
- [ ] `.claude/settings.json` — a reviewed permission policy **and a hooks block**
- [ ] `.claude/agents/` — three role definitions (architecture, documentation, devops)
- [ ] `.claude/skills/` — this project's own procedures, read but not yet used
- [ ] `.claude/hooks/` — enforcement scripts, with two of them observed running
- [ ] `docs/requirements.md` — functional and non-functional requirements with numbers
- [ ] `docs/architecture.md` — components, data contracts, pipeline stages
- [ ] `docs/decisions/` — at least one ADR recording the inference-target decision
- [ ] `docs/roadmap.md` — the engineering plan for Weeks 2–6
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

**The harness has four layers, and they are not interchangeable.** You will meet all four
in this session; the distinction between the last two is the one worth carrying:

| Layer | Where | How it constrains |
|---|---|---|
| **Rules** | `CLAUDE.md` | By being **read**. Loaded into every session |
| **Roles** | `.claude/agents/` | By **scope**. Separate context, restricted tools, one responsibility |
| **Procedures** | `.claude/skills/` | By being **invoked**. A repeatable method with its own acceptance criteria |
| **Enforcement** | `.claude/hooks/` | By **blocking**. Runs on the tool call, whether or not anyone read anything |

The first three all depend on cooperation. An assistant that has read a rule can still
decide, plausibly and in good faith, that this particular case is different. That is not
usually a problem — until the case that is different costs money or ships a lie to a user.
Which is exactly what the fourth layer is for, and why Lesson 02 puts the credit budget
there rather than leaving it in prose.

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

#### What a permission rule cannot do

Scroll further down `settings.json` to the `hooks` block, and open the scripts it points
at in `.claude/hooks/`.

A permission rule pauses and asks **you**. That works exactly as well as your attention
does — and the twentieth prompt in a session gets the same click as the first. A hook does
not ask. It runs a script before or after the tool call, and a `PreToolUse` hook exiting
with status 2 means the call does not happen.

Five ship with the scaffold. Two of them block:

| Hook | Fires on | Effect |
|---|---|---|
| `session_balance.py` | Session start | Prints the remaining credit balance into context |
| `format_python.py` | After `Write`/`Edit` | `ruff format` + `ruff check --fix`. Never blocks |
| `credit_gate.py` | Before billed Roboflow tools | **Blocks** unless the ledger has a pending estimate that fits the balance |
| `units_guard.py` | Before `Write`/`Edit` to `src/` | **Blocks** any metric-depth identifier |
| `contract_drift.py` | After editing `schemas.py` | Warns that the client's generated types are stale |

**Do:** Watch the harmless one work. Ask for a deliberately badly formatted file.

```
Create src/smart_scene_analyzer/scratch.py containing:
x=1
def  f( a,b ):
     return a+b
```

**Expected result:** the file is written, and when you read it back it is formatted. You
did not ask for that, and nothing in `CLAUDE.md` requested it. Delete the file.

**Do:** Now watch one that blocks.

```
In src/smart_scene_analyzer/__init__.py, add a comment reading
"# depth values are returned in meters"
```

**Expected result:** the edit is **refused**, with a message explaining that this project
returns relative inverse depth and no identifier or comment in `src/` may imply metres.
The assistant cannot proceed by rewording, retrying, or writing the file another way.

> Sit with the difference. `CLAUDE.md` already said depth is not metres — that rule has
> been loaded into context this entire session. It is a good rule, correctly stated, and
> a sufficiently confident model at eleven at night will write `depth_meters` anyway
> because in that moment it seems obviously right. The hook does not care what seemed
> right. **That is the entire distinction between a rule and a constraint**, and Lesson 02
> puts your Roboflow budget on the far side of it.
>
> One consequence worth naming now: if a hook blocks you, the fix is to satisfy it. Not to
> edit the hook, and not to route around it. A hook you can talk your way past is a
> comment.

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

**Expected result:** `architecture`, `documentation`, `devops`, `dataset-engineer`,
`data-pipeline`, and the rest of the ten — through `mobile`, which Lesson 05 uses — are
listed. Only the first three matter today.

**Do:** Finally, look at the layer between roles and enforcement.

```
/skills
```

**Expected result:** five project skills are listed — `credit-ledger`, `error-triage`,
`annotation-conversion`, `dataset-qa-sweep`, `offline-suite`.

Open `.claude/skills/credit-ledger/SKILL.md` and read the `description` in its
frontmatter. It is written the same way an agent's `description` is: for a dispatcher
deciding whether this is the right thing to reach for, not for a human browsing a menu.

You will not invoke any of them today — Lesson 01 spends nothing, trains nothing, and
tests nothing. They are here so that when you meet the vendor's `roboflow:*` skills in
Lesson 02, the distinction is already concrete: those encode Roboflow's knowledge, these
encode your project's, and when the two disagree yours wins because it is the one that
knows your budget.

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

**The client is a real application, and that is now settled.** Lesson 05 builds an Expo
app for iOS and Android against this API. Write your requirements for a user holding a
phone, not for a `curl` command — it changes which non-functional numbers matter.

In particular, **N1 must state its link.** "p95 client-observed latency under 800 ms" is
not a requirement anyone can pass or fail, because a 250 KB upload alone is roughly 400 ms
at 5 Mbit/s. Either pin the link characteristics in the requirement, or state it as
server-observed and give transit a separate budget. Lesson 05 supplies the measurement;
this is where you decide which shape the requirement takes.

⚠️ **OPEN — resolve this before step 8.** The single biggest architectural fork is the
**inference target**, and it is not yet decided for this course:

| Option | Consequence |
|---|---|
| **Cloud, self-hosted** — your container serves both models | Simpler pipeline, one codebase, a network round-trip per frame. Zero per-image platform cost, since the weights are yours |
| **Cloud, hosted API** — detection served by Roboflow | No weights in your image, but **bills per request** — and a camera app makes far more requests than a `curl` loop |
| **On-device** — ONNX / Core ML / TFLite | No round-trip, works offline, best privacy posture. Forces per-platform export, quantization, and numerical validation of two models, and a model update becomes an app-store release |

Pick one, then record it:

```
/adr inference target: cloud vs on-device
```

> The middle row is the one to think hardest about now that a real client exists. It looks
> like the cheap option — no weights to ship, no GPU to size — and it is the only one whose
> cost scales with how much anyone uses your app. Lesson 04 measures all three; Lesson 05
> is where the difference would actually be spent.

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

**Expected result:** `docs/roadmap.md` covering Weeks 2–6, where each milestone names
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

- ⚠️ **Inference target** — self-hosted cloud, hosted API, or on-device (step 7).
  Notion Open Decision #2. Blocks a final architecture. Lesson 04 measures all three;
  Lesson 05 revisits the on-device branch once a real client exists.
- ⚠️ **MLflow hosting** — local Docker, self-hosted, or managed (step 10). Notion Open
  Decision #4. Determines `docker-compose.yml` and Lesson 03's tracking setup.
- ⚠️ **N1's shape** — client-observed with a pinned link, or server-observed with a
  separate transit budget (step 7). You choose the shape now; Lesson 05 supplies the
  number that fills it.
- ⚠️ **Codex** — the course lists OpenAI Codex alongside Claude Code. This lesson is
  Claude Code only; the `AGENTS.md` and `codex plugin` equivalents are not yet written.
  Note that **Codex does not run the hooks you met in step 5** — those two constraints
  become yours to keep there.

All four are tracked in the course [`TODO.md`](../../TODO.md).

> **Resolved since this lesson was first written:** *mobile app scope*. It is a real
> client application — an Expo app for iOS and Android, built in Lesson 05. The
> architecture's outermost layer is a component with a contract, not a placeholder.

---

## Further reading

- [Claude Code — memory and `CLAUDE.md`](https://docs.claude.com/en/docs/claude-code/memory)
- [Claude Code — subagents](https://docs.claude.com/en/docs/claude-code/sub-agents)
- [Claude Code — settings and permissions](https://docs.claude.com/en/docs/claude-code/settings)
- [Claude Code — slash commands](https://docs.claude.com/en/docs/claude-code/slash-commands)
- [Claude Code — hooks](https://code.claude.com/docs/en/hooks) — the reference for step 5's
  `hooks` block, including the exit codes and the `PreToolUse` decision fields
- [Claude Code — skills](https://code.claude.com/docs/en/skills)
- [Architecture Decision Records](https://adr.github.io/)

**Next:** [Lesson 02 — Dataset Engineering](../02-dataset-engineering/)
