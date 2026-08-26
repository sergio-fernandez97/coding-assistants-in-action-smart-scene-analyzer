# app/ — the Expo app

Empty on purpose. **Lesson 05 creates this**, the same way Lesson 01 creates
`docs/architecture.md` rather than shipping it.

Nothing is scaffolded here because a half-built Expo app in a course template rots
faster than anything else in the repo: SDK versions move, `npx create-expo-app`
templates change, and a student following Lesson 05 against a stale scaffold debugs
the scaffold instead of learning the lesson. That is more true now, not less — this app
carries two native ML runtimes, and a stale native dependency does not fail with a
readable error.

This directory is the product. `src/` trains and exports the models; `app/` is what
somebody holds.

## What lands here

```
app/
├── app.json                  Expo config — name, icon, permissions, plugins
├── package.json
├── metro.config.js           assetExts must include 'tflite' and 'pte'
├── App.tsx                   Capture / pick, run inference, show the result
├── assets/
│   └── models/
│       ├── yolo11n_int8.tflite       Detection. Bundled, gitignored
│       └── depth_anything_v2s.pte    Depth. Bundled, gitignored
└── src/
    ├── inference/
    │   ├── detector.ts       Loads the .tflite, decodes raw output, runs NMS
    │   └── depth.ts          Loads the .pte via ExecutorchModule
    ├── fusion/
    │   └── index.ts          PORT of src/smart_scene_analyzer/fusion.py
    ├── geometry/
    │   └── toScreen.ts       Model-input pixels → screen points. One named function
    └── components/
        └── DetectionOverlay.tsx   Boxes and relative-depth shading
```

## Three rules that predate the code

They are in `CLAUDE.md` and `.claude/agents/mobile.md` too, and they are repeated here
because this directory is where they get broken.

1. **Never print a distance.** Depth here is relative inverse depth — no unit, no scale,
   comparable only within one image. "Nearer" and "farther" are fine. "2.3 m" is a claim
   this system cannot make. `units_guard` now enforces this in `app/` as well as `src/`,
   in `.ts` and `.tsx` — because this is where the number is *computed* now, not merely
   displayed. It is still worth knowing the rule rather than relying on the hook.
2. **`src/fusion/index.ts` is a port, not an original.** It must reproduce
   `src/smart_scene_analyzer/fusion.py` on the same fixtures. Two implementations of one
   algorithm stay honest only as long as that shared fixture set does. If they disagree,
   that disagreement is the finding — do not edit the fixtures until they agree.
3. **What is in `assets/models/` is what runs.** Not what the export script would produce
   if you ran it now. `artifact_drift.py` warns when they have diverged; it cannot tell
   whether the difference matters, so it tells you instead of deciding.

## Running it

```bash
cd app && npm install
npx expo run:ios        # builds and installs to the iOS Simulator
npx expo run:android    # builds and installs to a running Android Emulator
```

**This is a development build, not Expo Go.** Both ML runtimes are native modules, so the
Expo Go sandbox cannot load them. The first build compiles native code and takes minutes;
after that, TypeScript edits hot-reload and only a native dependency change forces
another build.

**Inference runs on a bundled or picked still image, not the live camera.** The iOS
Simulator has no camera at all, so a still image is the only input that works in both
simulators — and being deterministic is what makes the device-versus-reference parity
check in Lesson 05 possible. Live camera capture is the real-device path.

Simulator latency is not device latency. Report the two separately or not at all.
