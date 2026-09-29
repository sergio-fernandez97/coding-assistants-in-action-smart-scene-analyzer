# Lesson 05 — retrospective

> Instructor-facing. Not linked from the student README. Written 2026-09-29, when the
> lesson was restructured from a 5–6 hour single block into before / during / after and
> gained mobile-mcp, a live camera mode, and two platform paths.

## What changed and why

| Change | Reason |
|---|---|
| Split into steps 1–4 before, 5–9 in the session, 10–14 after | The 90-minute rule. The old README had 12 steps and no session boundary |
| Steps 3 and 4 kept their numbers | Lesson 01 (`README.md` ~695–700) and `lessons/README.md` cite "Lesson 05 step 3" (build) and "step 4" (drift hook) |
| mobile-mcp added | The agent could write UI code but never see it. The screenshot and element list close that loop, and the lesson draws the line: screen yes, numbers no |
| Live mode = throttled stills through the photo pipeline | The only live design that fits 20 minutes. Frame processors and worklets were rejected as too risky for the room |
| iOS default, Android alternative | Course owner's choice. The cost is that iOS students cannot run live mode on a real camera in the session: the Simulator has no camera |
| Real-phone delivery moved to optional step 13 | Signing, Developer Mode, and USB trust are toolchain-fragile and cannot happen live |

## What has to be live

1. **Seeing the app through the agent** (step 5). This is short, but everything after it depends on it.
2. **Decoding a raw tensor** (step 6). This is where students reliably get stuck in a way that teaches.
3. **The letterbox offset** (step 8). Lesson 04's hardest bug, now visible on screen.
4. **A real camera meeting the model** (step 9). This is the payoff, and the one step never cut.

The fusion port, latency, and parity are careful solo work with clear pass/fail criteria,
so they sit after the session.

## Cut lines

1. Step 7 (depth ordering) → homework. Photo mode still shows boxes, and step 12's parity
   check covers depth ordering later.
2. Step 8's landscape check → one screenshot instead of two.
3. Step 9 is never cut.

## Watch for in the room

- **iOS students expecting a camera.** Say at minute 0 that the Simulator has none and that
  "no camera on this device" is the correct result for them in step 9.
- **The agent installing its way out.** The prompts forbid installs without approval, and
  `mobile_install_app` / `mobile_uninstall_app` are on `ask`. A student who approves one
  under time pressure has usually lost the thread.
- **Screenshots used as proof of correctness.** Redirect to step 12.

## Assets needed before this shape works

- A prebuilt development client per platform (step 3's fallback). Not built. See `TODO.md`.
- Lesson 04's pre-exported model files (prerequisite 1's fallback). Not published.
- A dry run of mobile-mcp against both simulators, confirming the tool names in
  `template/.claude/settings.json`.
