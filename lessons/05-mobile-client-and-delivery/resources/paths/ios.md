# Lesson 05 — the iOS path (default)

Mac only. Where this file and the [lesson README](../../README.md) overlap, the README is
right; this file holds only what is specific to iOS.

**What you give up on iOS:** the iOS Simulator has **no camera**, so in the session live
mode runs against a test double. The real camera run is step 13, on your own iPhone. If you
want live mode on a real camera *in the room*, take the [Android path](android.md) instead.

---

## 1. Toolchain · before the session

**Do:** Confirm Xcode and an iOS 17+ simulator runtime.

```bash
xcodebuild -version
xcrun simctl list runtimes | grep iOS
```

**Expected result:** Xcode 16 or later, and at least one `iOS 17` or later runtime.
`react-native-executorch` requires iOS 17+.

---

## 2. Build and run the development build · README step 3

**Do:** Boot a simulator, then build to it from `app/`.

```bash
open -a Simulator
npx expo run:ios
```

**Expected result:** the app opens in the Simulator. Change a text string in `App.tsx` and
it reloads without a rebuild.

**Do:** Put the lesson's test photos in the Simulator's photo library, so the picker has
something to pick.

```bash
xcrun simctl addmedia booted <path-to-image>
```

`<path-to-image>` is each bundled test image — at least one portrait and one landscape.

**Expected result:** the images appear in the Simulator's Photos app.

---

## 3. mobile-mcp sees the Simulator · README prerequisite 6

**Do:** With the Simulator booted, ask Claude Code: *"Use mobile-mcp to list available
devices."*

**Expected result:** your booted simulator is listed by name and iOS version. mobile-mcp
drives simulators through the Xcode command-line tools.

If every UI call then fails with `Agent is not installed on the device`, install its
on-device agent once: `npx mobilecli agent install --device <udid>`, where `<udid>` is the
simulator id from `xcrun simctl list devices booted`. To open the development client's
deep link, use `xcrun simctl openurl booted <url>`: `mobile_open_url` refuses custom
schemes.

---

## 4. Camera in the session · README step 9

There is none. The iOS Simulator has no camera device, and it is not a setting you can
change. Third-party virtual cameras exist but need a developer account and a macOS system
extension; this course does not support them.

**Do:** Run live mode against the test double from
[`06-live-mode.md`](../prompts/06-live-mode.md) Round 4 — it cycles the bundled test
images through the real pipeline.

**Expected result:** the Live tab shows **"no camera on this device"** with the real
source, and advancing frames with the test double. Both are correct.

---

## 5. Extra — deliver to your iPhone · README step 13

Everything so far ran on your Mac's CPU. This is the first time the models run on the
hardware they were exported for, and the first time live mode sees a real scene.

**Do:**

1. Set a unique `ios.bundleIdentifier` in `app/app.json` (for example
   `com.<your-name>.smartscene`). Xcode generates the provisioning profile from it.
2. In Xcode → **Settings → Accounts**, sign in with your Apple ID. A free account works
   for your own phone.
3. Connect the iPhone by cable, unlock it, and tap **Trust**.
4. On the iPhone: **Settings → Privacy & Security → Developer Mode**, turn it on, restart,
   and confirm **Turn On** after the restart.
5. From `app/`:

```bash
npx expo run:ios --device
```

Pick your iPhone from the list.

**Expected result:** the app installs and opens on your phone. The Live tab asks for camera
permission, then analyses what the camera sees.

**Then:**

- Re-run step 11's latency measurement and put the numbers in a **separate table** marked
  as the device. Simulator and device figures never share a table.
- Turn on airplane mode and use both modes. Nothing should change.

> If the app refuses to open with an untrusted-developer message, go to **Settings →
> General → VPN & Device Management** and trust your Apple ID. With a free Apple ID the
> signature expires after a few days; run the command again to reinstall.
> ⚠️ Both details are from Apple's signing behaviour, not the Expo docs, and were not
> re-verified on a clean device for this lesson — see the README's Open items.

Sources, checked 2026-09-29:
[Expo — local app development](https://docs.expo.dev/guides/local-app-development/),
[Expo — set up an iOS device](https://docs.expo.dev/get-started/set-up-your-environment/?platform=ios&device=physical&mode=development-build&buildEnv=local).
