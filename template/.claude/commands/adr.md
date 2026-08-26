---
description: Record an architectural decision as a numbered ADR in docs/decisions/
argument-hint: <short decision title>
---

Create an Architecture Decision Record for: **$ARGUMENTS**

1. Read `docs/decisions/0000-adr-template.md` for the format, and list the existing
   ADRs to determine the next number.
2. Search the repository for code, configuration, and documentation that this decision
   affects. Name those files in the Consequences section — a decision without a
   dependency list cannot be safely reversed later.
3. Write `docs/decisions/NNNN-<kebab-case-title>.md` following the template.
4. If the decision is already reflected in `CLAUDE.md` or `docs/architecture.md`,
   cross-link them.

Fill in the Context section from what you find in the repo and from what I tell you.
If you do not know why this decision was forced — what constraint made it non-obvious
— ask me rather than writing a plausible-sounding rationale. A fabricated Context is
worse than a blank one, because it will be believed.
