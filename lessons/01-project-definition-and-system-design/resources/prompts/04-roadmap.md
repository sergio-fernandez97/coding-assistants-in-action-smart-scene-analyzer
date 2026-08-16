# Prompt — Engineering Roadmap

**When:** Lesson 01, step 11. The last generation step of the session.

**Which agent:** `architecture`. Planning is design work, not documentation work —
the roadmap has to be consistent with the module boundaries.

---

```
Use the architecture agent to write docs/roadmap.md — the engineering plan for the
remaining four weeks of this project.

Read first: docs/architecture.md, docs/requirements.md, docs/decisions/, CLAUDE.md.

The phases are fixed:
  Week 2 — Dataset Engineering: dataset versions, preprocessing, augmentation
  Week 3 — Model Development: YOLO11 fine-tuning, Depth Anything V2, MLflow
  Week 4 — Export, quantization and parity: model fusion, TFLite and ExecuTorch
           export, numerical parity against the PyTorch reference, tests
  Week 5 — On-device inference and mobile delivery: Expo development build,
           two on-device runtimes, the artifact contract, device-vs-reference parity
  Week 6 — CI/CD/CT: GitHub Actions, continuous training, promotion logic

For each phase produce:
- The deliverables, named as artifacts that either exist or do not — not activities
- The owning engineering role from .claude/agents/ (note which roles do not exist
  yet and must be created)
- Entry conditions: what must be true before this phase can start
- Exit criteria: the observable test that says the phase is done
- Dependencies on earlier phases
- The specific risk most likely to derail this phase, and its early warning sign

Then add a "Blocked on decisions" section listing every open decision, which phase
it blocks, and the latest point at which it must be resolved.

Constraints:
- Exit criteria must be checkable by someone who was not present. "Model trained" is
  not checkable. "Model V1 registered in MLflow with mAP@50 recorded against the
  held-out test split of dataset version 1" is.
- Do not invent dates or durations. Order and dependencies only.
- Do not assume an open decision resolved a particular way.
```

---

## What good output looks like

- Every exit criterion names an artifact and a place it lives
- The "Blocked on decisions" section lists at least the inference target and MLflow
  hosting
- Risks are specific to this project ("depth ground truth has no storage path"), not
  generic ("scope creep")
- Roles that do not yet exist are called out as work to be done

## Reject and re-run if

- Exit criteria are activities rather than artifacts
- Dates or effort estimates appear
- The decision-blockers section is missing
