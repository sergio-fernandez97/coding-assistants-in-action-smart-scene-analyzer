# Prompt — preparing the image for upload

**When:** Lesson 05, step 7.

**Which agent:** `mobile` for rounds 1–3; `backend` for round 4.

**Credits: zero.**

---

## Round 1 — find out what your camera actually produces

```
Use the mobile agent.

Take one photo and report, before changing anything:

  - The file size in bytes
  - The pixel dimensions
  - The EXIF Orientation tag value
  - Whether that size exceeds the server's upload limit from Lesson 04

Then send it to /analyze unmodified and show me the status code.
```

**Expect a 413**, and let it happen. A modern phone photo is several megabytes and the
Lesson 04 limit was set for dataset images. Seeing the boundary fire is worth more than
being told about it — it is your own requirement rejecting your own client.

---

## Round 2 — resize, and orient

```
Write app/src/imaging/prepare.ts using expo-image-manipulator:

  - Resize so the long edge is <server long edge>, preserving aspect ratio
  - Apply the EXIF orientation so the pixels are upright, then strip the tag
  - Re-encode as JPEG at a stated quality
  - Return the prepared URI AND its dimensions — the overlay transform needs the
    uploaded size, not the captured size

Report before/after bytes and dimensions for one photo.
```

**Both halves matter and only one is obvious.**

The resize is the largest single latency win in this lesson, and it is not an
optimization — the model receives 640×640, so every byte above that is time the user
spends uploading data that is discarded on arrival.

The orientation is the subtler one. Phones record the sensor's raw pixels and an EXIF tag
saying which way is up. Decoders that honour the tag and decoders that ignore it both
exist, and yours and the server's may disagree. When they do, detections come back
confidently sideways — the model works perfectly on a rotated image and gives you rotated
boxes. Normalize on the device, where the tag is still available, and then strip it so
nothing downstream can apply it twice.

---

## Round 3 — check the failure modes you just moved

```
Verify after preparation:
  - A 4:3 portrait photo returns correctly oriented boxes
  - A 16:9 landscape photo returns correctly oriented boxes
  - A photo taken upside down returns correctly oriented boxes
  - The prepared size is well under the server limit
  - The overlay uses the PREPARED dimensions, not the captured ones

That last one: if the overlay still uses the camera's dimensions, boxes will be
proportionally offset and it will look like a model problem.
```

---

## Round 4 — CORS, on the server side

```
Use the backend agent.

Add CORS middleware to the FastAPI app, configured from settings:

  - Allowed origins come from an environment variable, as an explicit list
  - Do NOT use allow_origins=["*"]
  - Only the methods and headers actually needed

Then explain in one sentence why Expo Go worked without this and a browser would not.
```

**Expo Go is not a browser and does not enforce the same-origin policy**, so a native
client reaches the API with no CORS configuration at all. It will keep working. Anything
served from a web origin — a debug build in a browser tab, a future web target, a demo
page — will not, and the error arrives in a console nobody was watching.

`allow_origins=["*"]` makes the symptom disappear and is the wrong fix. This API is
public and unauthenticated already; a wildcard does not make that worse today, but it
removes the one place a future decision about who may call this would have been recorded.

---

## What good output looks like

- Round 1 shows a real 413 from a real photo
- Prepared images are well under the limit and upright in all orientations
- The prepared dimensions are what the overlay transform receives
- CORS origins come from configuration as an explicit list
- Before/after byte counts are reported

## Reject and re-run if

- The server's upload limit was raised instead of the client resizing. That fixes the
  status code and keeps the latency, which is the wrong half of the problem
- EXIF orientation is applied but the tag is not stripped, so it can be applied twice
- The overlay still uses the captured dimensions
- `allow_origins=["*"]` appears
- The agent claims orientation is handled without testing an upside-down photo
