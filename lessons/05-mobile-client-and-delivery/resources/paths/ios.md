# Lesson 05 — the iOS path (default)

Mac only. Where this file and the [lesson README](../../README.md) overlap, the README is
right; this file holds only what is specific to iOS.

**What you give up on iOS:** the iOS Simulator has **no camera**, so in the session live
mode replays a short clip you recorded on your phone beforehand. The live camera run is
step 13, on your own iPhone. If you want live mode on a live camera *in the room*, take the
[Android path](android.md) instead.

---

## 1. Toolchain and clip · before the session

**Do:** Confirm Xcode and an iOS 17+ simulator runtime.

```bash
xcodebuild -version
xcrun simctl list runtimes | grep iOS
```

**Expected result:** Xcode 16 or later, and at least one `iOS 17` or later runtime.
`react-native-executorch` requires iOS 17+.

**Do:** Record the clip live mode will replay in the session. On your iPhone, film 20–30
seconds of a slow pan across an indoor scene with objects from your taxonomy. Send **only
that file** to your Mac with AirDrop; in the share sheet, tap **Options** and turn
**Location** off so no GPS data travels with it. Nothing else on your phone is shared, and
the phone is not connected to anything. No iPhone? Any indoor video you own works.

**Expected result:** one `.mov` or `.mp4` on your Mac, **outside** the project folder. Never
commit it: it is large and it is your home.

---

## 2. Build and run the development build · README step 3

**Do:** Boot a simulator, then build to it from `app/`.

```bash
open -a Simulator
npx expo run:ios
```

**Expected result:** the app opens in the Simulator. Change a text string in `App.tsx` and
it reloads without a rebuild.

**Do:** Put the lesson's test photos and your clip in the Simulator's photo library, so the
picker has something to pick. This is the Simulator's library, not your phone's.

```bash
xcrun simctl addmedia booted <path-to-image>
xcrun simctl addmedia booted <path-to-clip>
```

`<path-to-image>` is each bundled test image — at least one portrait and one landscape.
`<path-to-clip>` is the video from §1.

**Expected result:** the images and the clip appear in the Simulator's Photos app.

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
change. Third-party virtual cameras exist but add native code or paid tooling; this course
does not support them. Your phone's camera reaches the session as the clip from §1.

**Do:** Run live mode against the recorded-clip source from
[`06-live-mode.md`](../prompts/06-live-mode.md) Round 4. It picks your clip, grabs one
frame per interval with `expo-video`, saves it to a file with `expo-image-manipulator`, and
hands that URI to the same function photo mode calls.

**Expected result:** the Live tab shows **"no camera on this device"** with the real
source, and boxes over successive frames of your own clip with the counter advancing. Both
are correct. No clip? Use the bundled-photos test double from the same round.

Sources, checked 2026-09-30:
[Expo Video — `generateThumbnailsAsync`](https://docs.expo.dev/versions/latest/sdk/video/),
[Expo ImageManipulator — `SharedRef` source](https://docs.expo.dev/versions/latest/sdk/imagemanipulator/).
SDK 57. ⚠️ Not yet run in the Simulator — see the README's Open items.

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
