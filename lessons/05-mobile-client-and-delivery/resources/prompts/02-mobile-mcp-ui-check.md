# Prompt — let the agent see the app

**When:** Lesson 05, step 5 — in the session. Reused in step 8 for the orientation check.

**Which agent:** `mobile`.

**Credits: zero.**

---

Until now the agent wrote app code blind: it could compile the code, but it could not see
the result. mobile-mcp gives it a screenshot, the accessibility tree, and a finger. That
closes the loop for **what is on screen** — and for nothing else. A screenshot of a box on
a lamp does not tell you the box's numbers are right. That is what parity (step 12) is for.

---

## Round 1 — find the device, look at the app

```
Use the mobile agent.

With mobile-mcp:
  1. List the available devices. Name the one you will use and its platform.
  2. Launch the app by its bundle identifier from app/app.json.
  3. Take a screenshot and list the elements on screen.

Report what the app is showing, in one sentence, from the element list — not from the
screenshot alone. If the app is not running, say so and stop; do not start a build.
```

**Why the element list, not only the screenshot.** The accessibility tree is text: labels,
roles, and positions the agent can act on exactly. A screenshot is pixels the agent has to
interpret. When the two disagree, the tree is usually right about *what* is there and the
screenshot about *how it looks*.

---

## Round 2 — drive one flow end to end

```
Using taps only, go from the home screen to the photo picker and back. After each tap,
take a screenshot and state which of these the app is in:

  - loading models
  - ready, nothing analysed
  - picker open
  - error

If a state has no visible text that says which state it is, report that as a bug in the
app, not as ambiguity in your reading.
```

**Expected result:** four states that you can tell apart on screen. A state the agent
cannot name from the screen is a state a user cannot name either.

---

## Round 3 — step 8 only: rotate and compare

```
Load the same test photo. Take a screenshot in portrait. Set the orientation to landscape
and take another. For each, report whether every box sits on its object.

Save both screenshots under docs/screenshots/ with the orientation in the filename.
```

---

## What good output looks like

- The device was named, with its platform, before anything else happened
- The app's state was read from the element list, not guessed from pixels
- Every state has on-screen text that names it
- Portrait and landscape screenshots saved, each with a verdict

## Reject and re-run if

- The agent started a native build or installed an app to "fix" a missing launch
- A numeric claim ("the box is correct", "depth is right") was made from a screenshot
- An unlabelled state was described as fine
