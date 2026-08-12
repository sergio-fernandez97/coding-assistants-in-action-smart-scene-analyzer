# Prompt — the Expo client

**When:** Lesson 05, step 5.

**Which agent:** `mobile`.

**Credits: zero.**

---

## Before you start

The types must exist first. Step 4 generates `app/src/api/types.ts` from the service's
OpenAPI document, and this prompt assumes it is there. If you scaffold the client before
generating the types, the agent will write its own interfaces from what it thinks the API
returns — and that is precisely the thing this lesson exists to prevent.

---

## Round 1 — the API client, typed from the contract

```
Use the mobile agent.

Write app/src/api/client.ts.

  - Import the response type from ./types.ts. Do NOT declare your own interface for
    the response shape. If types.ts does not have what you need, stop and tell me —
    that is a server change, not a client one.
  - POST multipart/form-data to `${process.env.EXPO_PUBLIC_API_BASE_URL}/analyze`.
    The base URL is configuration. Never a literal, never committed.
  - A 20-second timeout. The first request after idle hits a cold container.
  - Return a discriminated union, not a nullable result:
      { kind: 'ok', scene }
      { kind: 'empty' }              200 with zero detections — a SUCCESS
      { kind: 'tooLarge' }           413
      { kind: 'badImage' }           415
      { kind: 'timeout' }
      { kind: 'offline' }
      { kind: 'serverError', status }

Do not add a state-management library, a networking library, or a UI kit.
fetch and useState are enough for this and I want the failure modes visible.
```

**Why the union, and why `empty` is separate.** These six states look alike in a
`try/catch` and mean entirely different things to whoever is holding the phone. "No
objects found" is a working system. "Timed out" is a system that might work if you try
again. "Offline" is not the server's fault at all. Collapsing them into `error` produces
the interface everyone has used and nobody likes — a spinner, then *Something went wrong*.

Making them distinct types means the compiler asks you to handle each one when you render.

---

## Round 2 — capture and round trip

```
Write App.tsx:

  - Request camera permission with expo-camera. Handle denial as a real state with
    a way to recover, not an alert and a dead screen.
  - Take a photo, call the API client, and render the RAW JSON response.
  - Show which of the seven result states you are in.
  - A visible "analyzing" state — the cold path takes seconds and a frozen screen
    reads as a crash.

No overlays and no boxes yet. I want the round trip proven on its own.
```

**Get the round trip working before the geometry.** A failure now is a networking failure;
a failure after step 6 is a geometry failure. Ruling one out first turns a confusing bug
into an obvious one — and the most common cause at this point is pointing the client at
`localhost`, which on a phone is the phone.

---

## What good output looks like

- The response type is imported from `types.ts`, not redeclared
- The base URL comes from `EXPO_PUBLIC_API_BASE_URL`
- All seven result states exist, and `empty` is rendered as a success
- Permission denial is a recoverable state
- Runs in Expo Go on a real device without a custom native build
- `npx tsc --noEmit` passes

## Reject and re-run if

- Any interface describing the response is hand-written in the client
- The API URL appears as a literal anywhere, including in a fallback default
- A key of any kind appears in `app/`
- Zero detections is rendered as an error
- Dependencies were added beyond `expo-camera` and `expo-image-manipulator` without
  being raised first
- The agent edited `src/` — it does not own the server, and a schema that needs changing
  is a conversation, not a commit
