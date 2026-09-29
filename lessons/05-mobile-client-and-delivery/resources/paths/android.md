# Lesson 05 — the Android path

Works on macOS, Windows, and Linux. Where this file and the
[lesson README](../../README.md) overlap, the README is right; this file holds only what is
specific to Android.

**What you get on Android:** the emulator can use your laptop's webcam, so live mode runs
on a real camera **in the session**.

---

## 1. Toolchain · before the session

**Do:** Confirm Android Studio's platform tools and an API 33+ emulator.

```bash
adb --version
emulator -list-avds
```

**Expected result:** `adb` prints a version, and at least one AVD is listed with API 33
(Android 13) or later. `react-native-executorch` requires Android 13+. If `emulator` is not
found, add `$ANDROID_HOME/emulator` to your `PATH`.

---

## 2. Point the emulator camera at your webcam · before the session

**Do:** In Android Studio → **Device Manager**, edit your AVD → **Show Advanced Settings**
→ **Camera**, and set **Back** to `Webcam0`. Save, then cold-boot the emulator.

**Expected result:** the emulator's built-in Camera app shows your laptop's webcam feed.
The default setting, `VirtualScene`, shows a rendered room instead. That is fine for
testing the camera, but your model has nothing to find in it.

> Only the host's webcams can be used. The emulator cannot use the camera of a phone
> plugged into your laptop directly. ⚠️ **OPEN:** on a Mac, Continuity Camera can present
> an iPhone as a Mac webcam, which should then appear as another `Webcam` option here.
> This has not been verified — see the README's Open items.

Source: [Android — emulator camera](https://developer.android.com/studio/run/emulator-use-camera),
checked 2026-09-29.

---

## 3. Build and run the development build · README step 3

**Do:** Start the emulator, then build to it from `app/`.

```bash
npx expo run:android
```

**Expected result:** the app opens in the emulator. Change a text string in `App.tsx` and
it reloads without a rebuild.

**Do:** Put the lesson's test photos where the picker can find them.

```bash
adb push <path-to-image> /sdcard/Pictures/
```

`<path-to-image>` is each bundled test image, at least one portrait and one landscape. If
the picker does not show them yet, drag the same files onto the emulator window instead.

**Expected result:** the images appear in the emulator's photo picker.

---

## 4. mobile-mcp sees the emulator · README prerequisite 6

**Do:** With the emulator running, ask Claude Code: *"Use mobile-mcp to list available
devices."*

**Expected result:** your emulator is listed. mobile-mcp reaches it through `adb`; if it
is missing here, `adb devices` will be missing it too.

---

## 5. Camera in the session · README step 9

**Do:** Open the Live tab and point your laptop camera at something in your taxonomy.

**Expected result:** boxes appear, the frame counter advances, and the skipped-frame counter
goes above zero at least once. Emulator latency is your laptop's latency, not a phone's.

---

## 6. Extra — deliver to your Android phone · README step 13

**Do:**

1. On the phone, enable **Developer options** (tap **Build number** seven times in
   **Settings → About phone**), then turn on **USB debugging**.
2. Connect it by cable and accept the debugging prompt on the phone.
3. Confirm it is visible, then build to it from `app/`:

```bash
adb devices
npx expo run:android --device
```

Pick your phone from the list.

**Expected result:** `adb devices` lists your phone as `device`, not `unauthorized`, and
the app installs and opens on it. The Live tab asks for camera permission, then analyses
the scene.

**Then:**

- Re-run step 11's latency measurement and put the numbers in a **separate table** marked
  as the device.
- Turn on airplane mode and use both modes. Nothing should change.

Sources, checked 2026-09-29:
[Expo — local app development](https://docs.expo.dev/guides/local-app-development/),
[Expo — set up an Android device](https://docs.expo.dev/get-started/set-up-your-environment/?platform=android&device=physical&mode=development-build&buildEnv=local).
