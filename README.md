# Coding Assistants in Action: Build a Computer Vision Smart Scene Analyzer

Course materials for building a production-grade computer vision system using AI
coding assistants as a coordinated engineering workforce — the **Harness Engineering**
approach.

Source of truth for curriculum design: the
[Notion course page](https://app.notion.com/p/3b50d1de1f52808080c2f87b89c5766b).
This repository is the executable half: the exact commands, configuration files, and
prompts a student runs.

## What students build

The **Smart Scene Analyzer** — a mobile perception system that runs entirely on the phone:

- an **Expo app** for iOS and Android that captures an image and draws the result
- **YOLO11** for indoor object detection and **Depth Anything V2** for monocular depth,
  both trained in Python, both **exported and executed on the handset** — TFLite for
  detection, ExecuTorch for depth
- fused on-device into one scene result, with **no network call on the inference path**,
  and improved continuously through CI/CD/CT

The point is not the model. The point is that students learn to decompose engineering
work into specialized roles — Dataset Engineer, ML Engineer, DevOps Engineer, QA
Engineer, Integration Engineer, Mobile Engineer — and drive an AI assistant inside a
*harness* that constrains, guides, and validates each role's output.

## Lessons

| Lesson | Notion week | Focus | Status |
|---|---|---|---|
| [01 — Project Definition & System Design](lessons/01-project-definition-and-system-design/) | Week 1 | Repo, the four-layer harness, architecture, roadmap | Ready |
| [02 — Dataset Engineering](lessons/02-dataset-engineering/) | Week 2 | Roboflow MCP, annotation conversion, dataset versions, the credit harness | Ready |
| [03 — Model Development](lessons/03-model-development/) | Week 3 | YOLO11 fine-tuning, MLflow, error analysis, depth inference | Ready |
| [04 — Export, Quantization & Numerical Parity](lessons/04-backend-engineering/) | Week 4 | Detection–depth fusion, model export, int8 quantization, parity against the reference | Rewriting |
| [05 — On-Device Inference & Mobile Delivery](lessons/05-mobile-client-and-delivery/) | Week 5 | Expo dev build on both simulators, two on-device runtimes, the artifact contract, device-vs-reference parity | Rewriting |
| 06 — CI / CD / CT | Week 6 | GitHub Actions, continuous training, promotion logic | Not written |

See [`lessons/README.md`](lessons/README.md) for the lesson format contract and the
inventory of reusable material already available for Lesson 06.

## The harness has four layers

Every lesson adds to the same structure, and the distinction between the layers is the
curriculum rather than a detail of it:

| Layer | Where | How it constrains | Introduced |
|---|---|---|---|
| **Rules** | `CLAUDE.md` | By being **read**. Loaded into every session | 01 |
| **Roles** | `.claude/agents/` | By **scope**. Own context, restricted tools, one responsibility each | 01 |
| **Procedures** | `.claude/skills/` | By being **invoked**. A repeatable method with its own acceptance criteria | 01, authored in 02 |
| **Enforcement** | `.claude/hooks/` | By **blocking**. Runs on the tool call, whether or not anyone read anything | 01, load-bearing in 02 |

The first three depend on cooperation, and for most work that is enough. The fourth does
not, which is why the credit budget lives there: a `PreToolUse` hook exiting with status 2
means a billed call does not happen, and no amount of plausible reasoning gets past it.
Students see the same rule expressed at every layer in Lesson 02 step 4 and can feel the
difference.

## The credit budget

Students work on Roboflow's free Public plan under a hard cap of **20 credits for the
entire course**. That constraint is not an inconvenience the course works around — it is
a substantial part of the curriculum.

Most of what a dataset engineer does is nearly free: uploading 10,000 images costs one
credit. Compute is not: *labeling* 10,000 images costs a hundred, and GPU training bills
two credits an hour. That asymmetry decides the architecture of Lesson 02, and the
budget is enforced in three places rather than described in one:

| Where | What it does |
|---|---|
| `template/CLAUDE.md` | States the cap, the rates, and the forbidden operations with reasons |
| `template/.claude/settings.json` | `ask` on billed MCP tools, `deny` on the uptime-billed ones |
| `template/.claude/skills/credit-ledger/` | The estimate → record → approve → reconcile procedure |
| `template/.claude/hooks/credit_gate.py` | **Blocks** a billed call unless the ledger already holds an estimate that fits |
| `docs/credit-budget.md` | The ledger students keep and reconcile against the usage page |

The fourth row is the one that changed the design. The first three all *ask* an assistant
to estimate before spending, and the permission prompt then offers a button that says
yes — at the twentieth prompt of a session, to someone who has been clicking yes all
afternoon. The hook does not ask. It reads the ledger and refuses. Students prove it in
Lesson 02 by attempting a version generation with an empty ledger and watching the call
fail rather than prompt.

Lesson 05 adds a **second budget**, and it deliberately does not work the same way.
Roboflow credits are prepaid: they run out, and a hook can refuse the call that would
spend them. The artifact budget — model file sizes, bundled asset total, install size,
peak memory with two runtimes loaded — has no currency at all. It cannot be overspent,
only exceeded, and exceeding it does not produce a bill or an alert. It produces a build
that fails, or an app that installs everywhere except on the devices you did not test.

There is no hook to write, because there is no tool call to intercept: the constraint is
enforced by a store, a device's memory, and someone's patience with a download. Learning
that some budgets cannot be harnessed — only measured, early, and written down — is the
point of putting it last.

The sharpest lesson in it: Roboflow's own `training-and-evaluation` skill recommends
**RF-DETR NAS** as its default first choice. It is good advice in general and would
consume this entire budget several times over. Lesson 03 makes students override a
vendor's default deliberately, which is what a project constraint layer is for.

## Repository layout

```
lessons/          One directory per session. Everything needed to run it lives inside.
template/         The starter scaffold students copy in Lesson 01.
TODO.md           Open course decisions. Every ⚠️ OPEN marker in a lesson maps here.
computer-vision-skills/   Local clone of roboflow/computer-vision-skills (gitignored).
```

`computer-vision-skills/` is **reference only** and is not committed. Lesson 02
installs it as a Claude Code plugin straight from GitHub, so students always get the
current upstream skills.

## Global prerequisites

Verify these before Lesson 01. Per-lesson prerequisites are listed in each README.

| Requirement | Check | Notes |
|---|---|---|
| Git | `git --version` | |
| Claude Code | `claude --version` | [Install guide](https://docs.claude.com/en/docs/claude-code/overview) |
| `uv` | `uv --version` | Python toolchain manager; installs the interpreter too |
| Python 3.11+ | `uv python install 3.11` | macOS system Python (3.9) is too old |
| Docker | `docker --version` | **Optional.** No lesson requires it. Only needed if you resolve the open MLflow-hosting decision toward a containerized tracker; Lesson 03 uses `uv run mlflow server` |
| GitHub account | | Students push their own project repo |
| Roboflow account | | Free tier is enough; **note it makes data and models public** |
| ~20 GB free disk | | Raw dataset downloads in Lesson 02; more once native builds land |
| Node.js 20+ | `node --version` | Lessons 04–05 |
| **Android Studio** + an API 33+ emulator | `adb --version` | Lesson 05. The free path — the emulator's camera works |
| **Xcode 16+** with an iOS 17+ runtime | `xcodebuild -version` | Lesson 05, iOS only. **Requires a Mac** |

> ⚠️ **This is an accessibility regression, and it is deliberate.** Earlier versions of
> this course ran the client in Expo Go specifically so that no student needed a Mac or a
> paid Apple Developer account. On-device inference makes that impossible: both ML
> runtimes are native modules, which Expo Go cannot load, so a development build is
> mandatory. Android-only is a viable path for students without a Mac and costs nothing,
> but "both platforms from one codebase" is no longer free. Tracked in `TODO.md`; a
> supported fallback has not yet been designed.

## How a lesson works

Every lesson README follows the same section order, so students always know where to
look:

1. **Session goal** — one paragraph
2. **Prerequisites** — what must already be true
3. **Deliverables** — the artifacts that exist when the session ends
4. **Step-by-step** — numbered. Each step states *what you do*, *the exact command or
   prompt*, and *the expected result*
5. **Verification** — how to prove the session succeeded
6. **Open items** — anything unresolved, marked `⚠️ OPEN`
7. **Further reading**

### The ⚠️ OPEN convention

Where a step depends on a decision that has not been made, the lesson says so
explicitly and presents the real branches. It never invents an answer. Every `⚠️ OPEN`
marker has a matching entry in [`TODO.md`](TODO.md).

## Course-wide conventions

- **Students work in their own repo.** Lesson 01 creates `smart-scene-analyzer` from
  `template/`. This course repo is the instructor source; students read from it and
  write to theirs.
- **Never commit secrets.** API keys live in the shell environment and in a gitignored
  `.env`. Both this repo and `template/` ignore `.env`.
- **Never commit datasets or weights.** Datasets are versioned in Roboflow; models and
  metrics in MLflow.
- **Permissions stay on.** The course does not use
  `--dangerously-skip-permissions`. Reviewing what an assistant is about to do is part
  of the harness, not friction to be removed. From Lesson 02 onward some of those
  prompts guard operations that cost real money, which is the point at which the habit
  stops being theoretical.
- **Estimate before spending.** Every billed operation gets an estimate, an approval,
  and a ledger entry — with the actual cost recorded afterwards. A gap between the two
  is a finding worth chasing, not an error to hide.
