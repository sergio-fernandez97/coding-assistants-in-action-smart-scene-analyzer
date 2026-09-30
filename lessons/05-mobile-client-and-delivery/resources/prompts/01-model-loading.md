# Prompt — bundle and load two models on-device

**When:** Lesson 05, step 4 — before the session.

**Which agent:** `mobile`.

**Credits: zero.**

---

Two runtimes, two artifacts, two loading APIs. They fail differently and it is worth
meeting both failures deliberately rather than in the middle of debugging a decoder.

---

## Round 1 — read the contract before loading anything

```
Use the mobile agent.

Open docs/model-card-<name>.md and read the "Exported artifact" table. Report back, for
each of the two models:

  - The artifact filename and its size on disk
  - The input tensor shape, dtype, and layout (NCHW or NHWC)
  - The normalization mean and std
  - The number of output tensors and what each one is
  - The label order, and where the source of truth for it lives

Do not write loading code yet. If any of these is missing from the model card, say which
— do not infer it.
```

Every one of those values is assumed by the app and validated by nothing. A missing row is
a question for the ML Engineer, not a gap to fill with a plausible default.

---

## Round 2 — bundle them

```
Configure bundling:

  - app/metro.config.js: resolver.assetExts must include 'tflite' and 'pte'
  - Place both artifacts in app/assets/models/
  - Confirm .gitignore excludes *.tflite and *.pte — they are build outputs

Then verify the bundler actually picked them up, rather than assuming it did.
```

**The failure mode here is silence.** Without the `assetExts` entry Metro does not warn —
it simply does not bundle the file, and the app fails at load with an error naming a path
that looks correct.

---

## Round 3 — load each one, separately

```
Write app/src/inference/detector.ts and app/src/inference/depth.ts.

Detection — react-native-fast-tflite:
  - loadTensorflowModel with the bundled require(...)
  - Report the model's actual input and output tensor shapes at load time
  - Compare them against what the model card claimed and report any disagreement

Depth — react-native-executorch:
  - The 0.10 core API: loadModel(path) on the bundled .pte, resolved to a local path
    with expo-asset. No initExecutorch, no resource fetcher (both are /legacy)
  - setTelemetryEnabled(false): nothing leaves the device
  - Report the shapes the same way

Both:
  - Load once and cache. Per-inference loading is a bug, not a slow path.
  - Expose an explicit "not loaded yet" state — loading takes seconds and the UI must
    say so rather than appearing frozen.
  - Time the load and log it.
```

**Report the shapes rather than trusting them.** This is the cheapest possible moment to
discover that the export produced something other than what the model card says, and the
most expensive moment to discover it is after writing a decoder against the wrong one.

---

## Round 4 — make the drift hook fire

```
Touch scripts/export.py and show me what the artifact_drift hook printed.

Then explain, in two sentences, why it warns rather than blocks — and why units_guard
does the opposite.
```

---

## What good output looks like

- Round 1 reported all five contract values per model, from the model card
- Loaded shapes were compared against the card and any disagreement reported
- Both models load once, cached, with an explicit loading state
- Cold load time logged for each
- `artifact_drift` observed warning
- The student can state why one hook warns and the other blocks

## Reject and re-run if

- A model is loaded inside a per-image code path
- Tensor shapes were assumed from the model card without checking the loaded model
- Missing model-card values were filled in with plausible defaults
- `assetExts` was not configured and the failure was worked around another way
- The loading state is invisible to the user
