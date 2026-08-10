# Prompt — Documentation Agent

**When:** Lesson 01, step 9. After `docs/architecture.md` exists.

---

```
Write the project documentation for the Smart Scene Analyzer.

Read first: CLAUDE.md, docs/architecture.md, docs/requirements.md,
docs/decisions/, pyproject.toml, and the actual contents of src/ and tests/.

Produce two files.

README.md — replace the template placeholder entirely:
- One-paragraph description of what the service does, from a user's point of view
- Prerequisites with version numbers
- Setup: exact commands, runnable verbatim, starting from a fresh clone
- Running the service
- Running tests, lint, and type checks
- Project layout table
- A "Current status" section that states plainly which parts are implemented and
  which are stubs. Right now that is almost everything — say so.
- Links to docs/architecture.md and CONTRIBUTING.md

CONTRIBUTING.md:
- Development environment setup with uv
- Branch naming and commit message conventions
- The gates a change must pass before review (ruff, mypy, pytest) with the commands
- How to work with the .claude/agents/ roles, and which role owns which area
- What must never be committed: secrets, datasets, model weights

Constraints:
- Every command must run verbatim from a fresh clone. Placeholders in
  <angle-brackets>, and say what fills them.
- Do NOT document endpoints, metrics, or capabilities that do not exist yet. If
  something is a stub, the word "stub" appears next to it.
- Do NOT invent benchmark numbers. If a number is not in a committed report or in
  MLflow, it does not appear in the docs.
- Do not use example secret values that could be mistaken for real ones.
```

---

## Verification

The only test that matters:

```bash
rm -rf .venv
# follow your own README setup section, verbatim, without improvising
```

If you had to improvise, the README is wrong. Fix it now.

## Reject and re-run if

- The README describes an API endpoint that does not exist in `src/`
- Any performance number appears (there are no trained models yet)
- The setup section skips a step you actually had to run
- "Current status" is missing or claims more than is true
