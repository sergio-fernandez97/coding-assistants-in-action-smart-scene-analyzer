# Prompt — live mode: throttled snapshots through the photo pipeline

**When:** Lesson 05, step 9 — in the session.

**Which agent:** `mobile`.

**Credits: zero.**

---

Live mode is **not** a second pipeline. It is a camera that hands the photo pipeline a new
image about once a second. Everything you built in steps 6–8 — the decoder, depth, the
letterbox transform — runs unchanged. If live mode needs its own decoder, something went
wrong earlier.

What is new is **time**. A frame can arrive while the last one is still in inference.

---

## Round 1 — choose the camera library, and ask first

```
Use the mobile agent.

Live mode needs a camera preview and a way to capture a still from it. Compare
expo-camera (CameraView + takePictureAsync) and react-native-vision-camera for this one
job: one still roughly every second, handed to the existing photo pipeline.

For each: native code added, install-size cost, and whether it needs a config plugin for
the camera permission. Check docs/artifact-budget.md first.

Recommend one. Do not install anything yet — the mobile role asks before adding a
dependency.

iOS Simulator only: live mode will also replay a recorded clip, which needs expo-video.
List it with its native and install-size cost so I approve both together.
```

**Expected result:** a recommendation you approve or reject before any install. Frame
processors and worklets are out of scope: this lesson grabs stills, it does not process a
stream.

---

## Round 2 — permissions, all three states

```
Install the approved library and configure the camera permission through its config plugin
in app/app.json (the iOS usage string and the Android CAMERA permission).

The screen must distinguish three states, each with visible text:
  - permission not yet asked
  - permission denied — with a way to open settings
  - no camera on this device

On the iOS path, also install expo-video now (npx expo install expo-video).

Rebuild the development build once — a new native module requires it.
```

**Why "no camera" is its own state.** On the iOS Simulator the camera does not exist. That
is not a denied permission and must not look like one.

---

## Round 3 — the throttle, and the in-flight rule

```
Add a Live tab. While it is visible:

  - Capture a still every <interval> ms and pass it to the same function photo mode calls.
  - If an inference is still running when the next capture is due, SKIP the capture. Never
    queue frames.
  - Show a frame counter and the number of skipped frames.
  - Stop capturing when the tab is hidden or the app is backgrounded.
  - Draw the overlay against the still that produced it, not against the live preview.

Keep the capture source behind one small interface, so a test double can replace it.
```

`<interval>` is your choice — start at 1000. Your latency numbers from step 11 will tell you
what it should be.

**Why skip rather than queue.** Depth is a ViT and may take longer than the interval. A
queue grows without limit and the overlay drifts further behind reality every second. A
skipped frame costs nothing.

**Why the overlay goes on the still.** The preview keeps moving while inference runs. A box
computed on frame N drawn over frame N+3 is off target on the screen, and nothing tells you why.

---

## Round 4 — make it run where you are

```
Android emulator: confirm the back camera is Webcam0 (see your path file), open the Live
tab, and point the laptop camera at something in the taxonomy. Screenshot with mobile-mcp.

iOS Simulator: there is no camera. Add a second capture source behind the same interface,
a recorded clip:
  - Let me pick a video with expo-image-picker (mediaTypes: videos).
  - Load it with expo-video's createVideoPlayer. No VideoView is needed.
  - On each capture, call player.generateThumbnailsAsync(t), pass the thumbnail to
    ImageManipulator.manipulate(...).renderAsync(), then saveAsync() to get a file URI.
  - Hand that URI to the same function photo mode calls. Do not decode pixels here.
  - Advance t by one interval per capture; wrap to 0 at the clip's duration.
Keep a bundled-photos test double too, for the fake-timer test and as a fallback.
Confirm the Live tab runs the same pipeline on my clip. Screenshot with mobile-mcp.
```

**Expected result:** the frame counter advances and boxes appear over your scene. On iOS,
the live camera run is step 13.

**The skip counter will probably stay at 0, and that is a finding, not a pass.** Decode,
preprocess, fusion, and the ExecuTorch call all run synchronously on the JS thread, so the
timer cannot fire while a frame is in flight: frames are throttled by a *blocked thread*,
and the UI freezes during analysis. Prove the skip rule with a fake-timer unit test
(a slow `analyze` stub, advance the clock past two intervals, assert one skip and no
queue). The on-screen counter only moves once inference runs off the JS thread.

---

## What good output looks like

- One pipeline: live mode calls the photo-mode function, and no decoding code is duplicated
- Frames are skipped, never queued, while inference is in flight, proven by a fake-timer test
- Three permission/availability states, each with its own visible text
- The overlay is drawn on the still that produced it
- Capture stops when the tab is hidden
- The capture source can be swapped for a test double

## Reject and re-run if

- A dependency was installed before you approved it
- Live mode has its own decoder, letterbox, or depth call — including a clip source that
  decodes pixels instead of handing a URI to the photo-mode function
- A queue or array of pending frames exists anywhere
- "No camera" and "permission denied" render the same
- A distance, unit, or raw depth number appears on the Live tab
