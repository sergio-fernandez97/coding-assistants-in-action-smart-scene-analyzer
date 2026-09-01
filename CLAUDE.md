# CLAUDE.md

Guidance for assistants working **on this course repository**.

This repo holds course materials, not application code. The Smart Scene Analyzer
itself is built by students in their own repo, scaffolded from `template/`.

## What lives where

| Path | Purpose |
|---|---|
| `lessons/<NN>-<slug>/README.md` | The step-by-step for one session. The primary artifact. |
| `lessons/<NN>-<slug>/resources/prompts/` | Copy-paste prompts, one file per agent handoff |
| `lessons/<NN>-<slug>/resources/templates/` | Files students copy into their own project |
| `lessons/<NN>-<slug>/resources/checklists/` | Deliverables and verification checklists |
| `lessons/<NN>-<slug>/resources/scripts/` | Verification helpers only — never solution code |
| `template/` | The starter scaffold copied in Lesson 01 |
| `template/.claude/skills/` | The project's own procedures — the repeatable half of the prompts |
| `template/.claude/hooks/` | Enforcement scripts. Two of them block; see the Hard rules |
| `computer-vision-skills/` | Read-only local clone of the upstream Roboflow repo |

## Hard rules

- **Never commit `computer-vision-skills/`.** It is a separate git clone with its own
  `.git` directory; committing it nests a repository. It is gitignored. Read from it
  freely; do not modify or stage it.
- **Never commit API keys, `.env` files, or dataset/model artifacts.**
- **Never invent a step.** If a lesson step depends on an unresolved decision, mark it
  `⚠️ OPEN`, present the real branches with their trade-offs, and add a matching line
  to `TODO.md`. A confidently wrong instruction costs a student an hour; a flagged one
  costs nothing.
- **Verify Roboflow facts against `computer-vision-skills/skills/`** before writing
  them into a lesson. Model IDs, credit rates, RoboQL syntax, and MCP tool names change
  upstream. Do not write them from memory.
- **Verify Azure, Expo, and Claude Code facts against their live documentation**, and cite
  the URL and the date checked in the lesson. Free-grant figures, `az` flags, Expo SDK
  bundling, and hook JSON shapes all move. The same rule as the Roboflow one, applied to
  everything Lesson 05 and the harness depend on.
- **Do not weaken a hook to make a lesson step easier.** `credit_gate.py` and
  `units_guard.py` block by design, and the moment a step feels obstructed by one is
  usually the moment the hook is doing its job. If a hook is genuinely wrong, fix the hook
  deliberately and update every lesson that demonstrates it.

## Lesson README contract

Every lesson README uses this section order. Do not reorder or omit:

1. `## Session goal`
2. `## Prerequisites`
3. `## Deliverables`
4. `## Step-by-step`
5. `## Verification`
6. `## Open items`
7. `## Further reading`

Each numbered step is written as **Do → Command/Prompt → Expected result**. A student
who cannot tell whether a step succeeded is looking at an incomplete step.

Prompts belong in `resources/prompts/` as their own files, referenced from the README
by relative link — not pasted inline. Students copy files; they mis-copy fenced blocks
buried in prose.

## Session length

**Every live session is 90 minutes. This is a hard constraint, not a target.** A lesson
that does not fit is not a long lesson — it is a lesson that has not decided what belongs
in the room.

Three buckets, and every step goes in exactly one:

| Bucket | What belongs there |
|---|---|
| **Pre-session homework** | Reading, writing, environment setup, and anything long-running or toolchain-fragile that a student can retry alone |
| **The 90 minutes** | The steps where a student reliably gets stuck in a way that teaches them something, and the moments a finding is revealed |
| **Post-session homework** | Documentation, ADRs, ledger reconciliation, finishing a test suite, committing |

Rules that follow from it:

- **The README's `## Step-by-step` still teaches the whole lesson.** Session length is a
  delivery concern; do not delete content to fit the clock. Where a lesson needs a split,
  record it in that lesson's `RETROSPECTIVE.md` — instructor-facing, not linked from the
  student README.
- **State a time estimate on every step**, and make the in-session ones add to 90 or less
  with a gap. A step-by-step whose estimates sum to four hours is telling you something.
- **Name the cut lines, in order.** Every session runs behind. Which step gets shortened
  first, and which one is never cut, is a decision worth writing down before the session
  rather than making at minute 70.
- **Nothing toolchain-fragile happens live.** If a step depends on a large or
  platform-sensitive dependency tree, it is pre-session homework **and it ships with a
  fallback artifact**, so a student who fails it still arrives with something to work on.
  A blocked student costs the room, not just their evening.
- **Order-dependent homework must say so.** "Write the contract, then export" only teaches
  anything in that order; if the README does not make the dependency explicit, half a
  cohort will invert it.

## Style

- Address the student directly ("you"), imperative voice for actions.
- Treat every lesson README as student-facing: do not link to or include instructor-only
  preparation, delivery notes, or retrospective material. Put those notes in an unlinked
  `RETROSPECTIVE.md`; describe live demonstrations through what the student observes,
  verifies, and records.
- Every command must be runnable verbatim. Use placeholders in `<angle-brackets>` and
  say what fills them.
- Explain *why* a harness element exists before showing the config. `CLAUDE.md`,
  subagents, and permission allowlists are the pedagogy — not boilerplate.
- Prefer tables for option comparisons, prose for reasoning.
