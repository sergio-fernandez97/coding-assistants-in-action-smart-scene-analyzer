# Lesson 05 — Mobile Client & Cloud Delivery

> Notion Week 5. Estimated time: 4–5 hours.

## Session goal

Put the system in someone's hand. The service you built in Lesson 04 answers `curl`; by
the end of this session it answers a phone, over the public internet, from an app you
built for both iOS and Android.

The real subject is not the app. It is the **contract**. For four lessons the response
schema has been a Pydantic class that one codebase produced and the same codebase
consumed — which is not a contract, it is a convention. This is the session where a second
codebase starts depending on it, written in a different language, shipped separately, and
unable to be fixed by editing the file next to it. Every naming decision you made in
Lesson 04 either holds up here or shows itself.

Two things surface that no amount of local testing produces. The first is **the network**:
Lesson 04 measured latency on loopback, which is a measurement of your CPU, not of your
system. The second is **real photographs** — sideways, eight megabytes, taken in a room
your dataset has never seen.

## Prerequisites

- [ ] Lesson 04 complete: `docker compose up -d` serves `POST /analyze` and `GET /health`
- [ ] `uv run pytest` passes with no GPU and no weights on disk
- [ ] `docs/deployment-comparison.md` exists, with local in-process at **0 credits/image**
- [ ] Node.js 20+ — `node --version`
- [ ] Azure CLI — `az --version`, then `az login`
- [ ] An Azure subscription you are allowed to create resources in
- [ ] A phone with **Expo Go** installed (iOS App Store or Google Play), on the same
      Wi-Fi as your machine
- [ ] `docs/credit-budget.md` reconciled

> **Roboflow credits needed: zero.** Detection runs on your own weights inside the
> container, so no request from the phone touches a metered endpoint. If your service
> still calls Roboflow's hosted API on the request path, stop and fix that first — a
> camera app makes requests at a rate a `curl` loop never did, and at 1 credit per 500
> execution-seconds a demo afternoon is a meaningful fraction of the budget.

> **You do not need a Mac, an Apple Developer account, or an Android build.** Expo Go runs
> the app on both platforms from the same development server. Standalone builds are
> step 10 and they are optional.

## Deliverables

- [ ] `.claude/agents/mobile.md` in use
- [ ] `docs/azure-budget.md` filled in, with a subscription budget alert configured
- [ ] The service running on Azure Container Apps at a public HTTPS URL, `--min-replicas 0`
- [ ] `app/` — an Expo client running on a real iOS **and** a real Android device
- [ ] `app/src/api/types.ts` **generated** from the service's OpenAPI document
- [ ] `app/src/geometry/toScreen.ts` — one named function, both coordinate spaces in its
      signature, with tests
- [ ] `docs/latency-report.md` — client-observed p95 on Wi-Fi and on cellular, with the
      link characteristics stated
- [ ] `docs/requirements.md` N1 filled in, no longer a placeholder
- [ ] An ADR revisiting on-device versus cloud, now that a real client exists
- [ ] Both ledgers reconciled

Verify with [`resources/checklists/deliverables.md`](resources/checklists/deliverables.md).

---

## Step-by-step

### 1. Meet the Mobile Engineer

**Do:** Read the role definition.

```bash
$EDITOR .claude/agents/mobile.md
```

**Expected result:** you can state its two hard constraints without looking.

They are worth pausing on, because both are about authority rather than capability:

| Constraint | Why it is drawn there |
|---|---|
| **Does not edit `src/`** | The client adapts to the contract. A mobile engineer who can edit the server fixes a naming disagreement by renaming the server field, and the disagreement — which was information — disappears |
| **Never prints a distance** | The `units_guard` hook enforces this in `src/`. It does not watch `app/`. The rule is the same; the enforcement is not |

That second row is the more interesting one. Every previous lesson had the harness behind
the rule. Here you cross a boundary the hooks do not reach, and the rule has to survive on
its own. Notice whether it does.

---

### 2. Set the Azure budget before creating anything

**This step comes before any resource, and the ordering is the same lesson as Lesson 02
step 4.** But the mechanism is different, and the difference is the point.

**Do:** Copy the Azure ledger into your project and read it.

```bash
cp <path-to-course-repo>/template/docs/azure-budget.md docs/azure-budget.md
$EDITOR docs/azure-budget.md
```

| | Roboflow | Azure |
|---|---|---|
| Model | Prepaid credits | Postpaid meter with a monthly free grant |
| Exceeding it | Operations **fail** | Operations **succeed, and you are invoiced** |
| You find out | Immediately | At the end of the month |

A hard cap is a harness that costs nothing to build — it enforces itself. A meter is not.
Nothing in Azure will stop you the way `credit_gate.py` stops a Roboflow call, and there
is no hook to write because the spend happens on Microsoft's side of the wire, not on a
tool call you can intercept.

The closest available substitute is a budget alert. It does not block anything; it emails
you. Set one anyway, and notice that you are accepting a weaker guarantee than you have
had for three lessons.

**Do:** Create a subscription budget with an alert in the portal under
**Cost Management → Budgets**, or read the current CLI syntax with `az consumption budget create --help`.

**The free grant** — verified against
[learn.microsoft.com/azure/container-apps/billing](https://learn.microsoft.com/en-us/azure/container-apps/billing)
on 2026-08-11. Re-check it; Azure revises these:

| Meter | Free per subscription per calendar month |
|---|---|
| vCPU | 180,000 vCPU-seconds |
| Memory | 360,000 GiB-seconds |
| HTTP requests | 2,000,000 |

At the container size this service needs, 1.0 vCPU and 2.0 GiB, both compute meters bind
at the same place:

```
180,000 vCPU-s ÷ 1.0 vCPU = 180,000 s = 50 hours
360,000 GiB-s  ÷ 2.0 GiB  = 180,000 s = 50 hours

50 hours of replica runtime per month, free.
```

Fifty hours is not tight — a replica runs while a request is in flight and for the
cool-down after it, not while your phone is in your pocket. It becomes tight in exactly
one way, and it is the thing to watch for the rest of this lesson:

> ⛔ **A revision left at `--min-replicas 1` runs continuously and spends fifty hours in
> just over two days.** This is the Roboflow dedicated-deployment mistake wearing a
> different costume: billing for existing rather than for working. You denied that one in
> `settings.json`. You cannot deny this one — you can only check it.

**Expected result:** `docs/azure-budget.md` has your subscription, a budget alert exists,
and you can state what the app must never be configured with.

---

### 3. Deploy the service to Azure

**Do:** Use [`resources/prompts/01-azure-deploy.md`](resources/prompts/01-azure-deploy.md)
with the `devops` agent.

The Dockerfile from Lesson 04 is the deliverable being deployed. Nothing about the service
changes in this step — if you find yourself editing `src/`, the deployment is telling you
something about Lesson 04's containerization that is worth stopping to hear.

```bash
az login
az upgrade
az extension add --name containerapp --upgrade --allow-preview true
az provider register --namespace Microsoft.App
az provider register --namespace Microsoft.OperationalInsights
```

```bash
export RESOURCE_GROUP="rg-smart-scene-analyzer"
export LOCATION="<your-region>"          # e.g. westeurope, eastus
export ENVIRONMENT="env-smart-scene-analyzer"
export APP_NAME="smart-scene-analyzer"

az group create --name $RESOURCE_GROUP --location $LOCATION

az containerapp up \
  --name $APP_NAME \
  --resource-group $RESOURCE_GROUP \
  --location $LOCATION \
  --environment $ENVIRONMENT \
  --source .
```

`az containerapp up --source .` builds the image in Azure from your Dockerfile, pushes it
to a registry it creates, makes the environment, and deploys — one command covering what
would otherwise be five. The `EXPOSE` line in your Dockerfile sets the ingress target
port. If it is not picked up, add `--target-port 8000 --ingress external`.

**Then size it and pin the scale floor**, which `up` does not do for you:

```bash
az containerapp update \
  --name $APP_NAME --resource-group $RESOURCE_GROUP \
  --cpu 1.0 --memory 2.0Gi \
  --min-replicas 0 --max-replicas 1
```

**Do:** Verify both, rather than assuming.

```bash
az containerapp show -n $APP_NAME -g $RESOURCE_GROUP \
  --query "properties.template.scale" -o json

export API_URL="https://$(az containerapp show -n $APP_NAME -g $RESOURCE_GROUP \
  --query properties.configuration.ingress.fqdn -o tsv)"
echo $API_URL

curl -sf $API_URL/health | jq
```

**Expected result:** `minReplicas` is `0`, `/health` returns 200 over HTTPS, and the
registry is recorded in `docs/azure-budget.md`.

> **The first request after an idle period is slow** — the replica is cold, and this
> container loads a depth model at startup. That is not a bug and it is not the latency
> you will report in step 8; it is the cost of paying nothing to sit idle. Measure it once
> so you know what it is, and say so in the report.

---

### 4. Generate the client's types from the service

**Do:** Export the OpenAPI document and generate TypeScript from it.

```bash
mkdir -p app
uv run python -c "import json; from smart_scene_analyzer.api import app; print(json.dumps(app.openapi()))" > app/openapi.json

cd app && npx openapi-typescript openapi.json -o src/api/types.ts
```

**Expected result:** `app/src/api/types.ts` exists and contains a type for the analyze
response, including `relative_depth` and the box field, with the descriptions you wrote in
Lesson 04 carried through as comments.

**This is the most important step in the lesson and it takes thirty seconds.** Read the
generated file before moving on.

The alternative — a mobile engineer reading the API docs and writing a matching interface
by hand — produces a client that is correct on the day it is written and silently wrong
afterwards. Rename a field on the server and the hand-written client still compiles, still
typechecks, still passes its tests, and is now wrong about every response it receives.
Nothing fails. That is the whole problem: the failure is invisible on both sides.

Your generated file is not immune, only cheaper to fix. The `contract_drift` hook
(`.claude/hooks/contract_drift.py`) fires after any edit to `schemas.py` and tells you the
types are stale. It does not regenerate them — a hook that rewrites your files mid-edit is
worse than one that tells you.

**Do:** Prove the hook works. Ask an agent to change a field description in
`src/smart_scene_analyzer/schemas.py`, and watch for the drift warning.

```
Add a sentence to the relative_depth field description in schemas.py noting that
values are comparable only within a single response.
```

**Expected result:** the edit succeeds and the hook reports `CONTRACT DRIFT`. Regenerate,
and confirm the diff in `types.ts` is exactly the comment you changed.

> Note what the hook did **not** do. It did not block — editing a schema is legitimate
> work. Compare that against `units_guard.py`, which does block. The difference is whether
> the action is wrong or merely has a consequence, and choosing correctly between the two
> is most of hook design.

---

### 5. Build the client

**Do:** Use [`resources/prompts/02-client-scaffold.md`](resources/prompts/02-client-scaffold.md)
with the `mobile` agent.

```bash
cd app
npx create-expo-app@latest . --template blank-typescript
npx expo install expo-camera expo-image-manipulator
```

Point the client at the deployed service. During development you may prefer your local
container, in which case use your machine's **LAN address** — on a phone, `localhost` is
the phone.

```bash
echo "EXPO_PUBLIC_API_BASE_URL=$API_URL" >> .env
npx expo start
```

Scan the QR code with Expo Go on your phone.

**Expected result:** the app runs on a real device, asks for camera permission, takes a
photo, uploads it, and displays the raw JSON response. Boxes come in step 6 — get the
round trip working first, because a failure now is a networking failure and a failure
later is a geometry failure, and you want to have already ruled one out.

> **Anything prefixed `EXPO_PUBLIC_` is compiled into the app bundle** and readable by
> anyone who installs it. An endpoint belongs there. A key never does. This is the same
> rule as `.env` never being committed, applied to a distribution channel that did not
> exist until this lesson.

---

### 6. Draw the boxes — the fourth coordinate space

**Do:** Use [`resources/prompts/03-overlay-geometry.md`](resources/prompts/03-overlay-geometry.md).

Lesson 04's fusion layer reconciled three coordinate spaces: the client image, YOLO's
640×640 letterboxed input, and the depth model's own resolution. That was the lesson's
hardest bug, and the fix was to name every space explicitly.

Here is the fourth, and it has a property none of the others had:

| Space | Units | Notes |
|---|---|---|
| Camera sensor | pixels | Whatever the device produces |
| **Uploaded image** | pixels | What the server sees — **already downscaled by step 7** |
| Server response | pixels, `xyxy`, absolute | Relative to the *uploaded* image |
| **Device screen** | density-independent points | Not pixels. Varies per device |

The trap is that both of the last two are numbers in the low hundreds, so a wrong
conversion produces boxes that are plausibly placed and consistently wrong. Exactly the
Lesson 04 failure mode, one process boundary later.

**Do:** Write the transform as **one named function** in `app/src/geometry/toScreen.ts`,
with both spaces in its signature, and unit-test it against hand-computed values.

```ts
export function imagePixelsToScreenPoints(
  box: BoxXYXYImagePixels,
  uploadedImageSize: { width: number; height: number },
  screenViewSize: { width: number; height: number },
): BoxXYXYScreenPoints
```

**Expected result:** boxes land on the objects, at more than one aspect ratio. Test in
portrait and landscape — a transform that assumes one of them works perfectly until it
is rotated.

---

### 7. Prepare the image before uploading it

**Do:** Use [`resources/prompts/04-upload-preparation.md`](resources/prompts/04-upload-preparation.md).

Four things go wrong here, and all four are invisible until a real camera is involved:

| Problem | Symptom | Fix |
|---|---|---|
| **Photo size** | Your Lesson 04 413 fires immediately | Resize to the server's expected long edge before upload |
| **EXIF orientation** | Detections are confidently sideways | Apply the orientation, then strip the tag |
| **CORS** | Works in Expo Go, fails in a browser | Add explicit origins to the FastAPI middleware — never `*` |
| **Upload time** | Latency far worse than Lesson 04 measured | See step 8 |

The size one is the one to think about rather than just fix. A phone photo is several
megabytes; the model receives 640×640. Every byte above what the model consumes is time
the user waits for nothing. Resizing on device is not an optimization, it is removing work
that was never needed — and it is the single largest latency win available in this lesson.

**Expected result:** a full-resolution photo from your phone's camera returns a correct
response, in the same time as a small one, in both orientations.

---

### 8. Measure latency with the network in it

**Do:** Use [`resources/prompts/05-latency-measurement.md`](resources/prompts/05-latency-measurement.md),
and copy the template.

```bash
cp <path-to-course-repo>/lessons/05-mobile-client-and-delivery/resources/templates/latency-report.md docs/latency-report.md
```

`docs/requirements.md` N1 has been a placeholder since Lesson 01, and
`docs/roadmap.md` flags exactly why: it is written as *client-observed* with **no link
characteristics specified**. That is not a requirement anyone can pass or fail. You now
have the only instrument that can settle it.

**Measure capture → rendered**, on the device, over each link. Report p50 and p95 across at
least 20 requests, with the stage breakdown: on-device preparation, upload, server
processing (from the response), download, render.

Do the arithmetic before you look at the numbers, so you know what to expect:

```
A 250 KB upload at 5 Mbit/s  =  250 × 8 / 5000  ≈  400 ms
                                 ...before the server has seen a single byte
```

**Expected result:** `docs/latency-report.md` with p50/p95 on Wi-Fi and on cellular,
each stating the measured link speed, plus the cold-start figure reported separately.
Then rewrite N1 in `docs/requirements.md` to name its link — or restate it as
server-observed and give transit its own budget. Either is defensible. Leaving it
ambiguous is not.

> Compare against Lesson 04's loopback number. That measurement was not wrong; it was
> answering a different question — how fast the code is, not how fast the product is.
> Both belong in the report, labelled.

---

### 9. Revisit the on-device decision

**Do:**

```
/adr on-device inference, revisited with a real client
```

ADR 0001 chose cloud inference, and its own *Revisit when* clause named this moment:
**a real mobile client and a named target device.** Both now exist. This is not a
formality — an ADR with a trigger condition that fires and is never revisited is a decision
nobody is making any more.

The honest answer is very likely still cloud. Write it anyway, and write it with what you
now know instead of what you assumed:

- The measured client-observed latency, and how much of it is transit rather than compute
- The cold-start cost of scale-to-zero, and what `--min-replicas 1` would cost to remove it
- That a model update is currently a deploy, and on-device would make it an app-store
  release
- What would actually change the decision — an offline requirement, a privacy requirement
  that image bytes never leave the device, a latency target transit alone cannot meet

**Expected result:** an ADR whose Context contains measurements from step 8, superseding
or amending ADR 0001 rather than sitting beside it.

---

### 10. Optional — a standalone build

Expo Go is enough for this course and for the deliverables above. If you want an installable
app:

```bash
npm install -g eas-cli
eas login
eas build --platform android --profile preview
```

Android produces an installable `.apk` from EAS's free tier. **iOS is different** — a
device build requires an Apple Developer Program membership (paid, annual) and
distribution goes through TestFlight or the App Store. That is a real cost and a real
review queue, and it is why this course runs on Expo Go.

Record what you did or did not do and why. "We did not build for iOS because it requires a
paid developer account" is a project constraint worth writing down, not a gap.

---

### 11. Reconcile and commit

**Do:**

1. **Roboflow:** the ledger should be unchanged. Lesson 05 spends nothing. If it moved,
   something on the request path is calling a metered endpoint — find it.
2. **Azure:** Cost Management → Cost analysis. Record the metered cost in
   `docs/azure-budget.md`.
3. **Confirm the scale floor one more time.** This is the check worth repeating because
   it is the only one whose failure is silent and cumulative:

```bash
az containerapp show -n $APP_NAME -g $RESOURCE_GROUP \
  --query "properties.template.scale.minReplicas"
```

```bash
uv run ruff check . && uv run mypy src && uv run pytest
cd app && npm run lint 2>/dev/null; npx tsc --noEmit; cd ..

git status          # confirm: no node_modules/, no .env, no app/openapi.json
git add -A
git commit -m "Lesson 05: Expo client, Azure deployment, client-observed latency"
git push
```

---

## Verification

Work through
[`resources/checklists/deliverables.md`](resources/checklists/deliverables.md).

```bash
# The service is reachable and cheap
curl -sf $API_URL/health | jq
az containerapp show -n $APP_NAME -g $RESOURCE_GROUP \
  --query "properties.template.scale.minReplicas"        # must be 0

# The client typechecks against the generated contract
cd app && npx tsc --noEmit

# The types are not stale
cd .. && uv run python -c "import json; from smart_scene_analyzer.api import app; print(json.dumps(app.openapi()))" > /tmp/openapi-check.json
diff <(jq -S . app/openapi.json) <(jq -S . /tmp/openapi-check.json) && echo "contract in sync"

# Nothing leaked
git status --porcelain | grep -E 'node_modules|\.env$|openapi\.json' && echo "LEAK" || echo "clean"
```

The check that matters most, and which no command performs — the `units_guard` hook covers
`src/` and does not reach here:

```bash
grep -riE 'meter|metre|\bcm\b|\bmm\b|distance|away|feet|inches' app/src/ | grep -v types.ts
```

**Read every hit.** A comment is fine. A variable name is a smell. A string that reaches
the screen is a bug — the system cannot produce a distance, and an interface that displays
one is making a claim about the physical world on the strength of a number that has no
scale. Four lessons of discipline about this end at the one place a user can actually read
it.

Then, on a real device:

- Boxes land on objects in portrait **and** landscape
- Nearer objects are shaded or ordered as nearer, and nothing shows a unit
- A photo with no recognizable objects shows an empty result, not an error
- Airplane mode shows a network error, distinct from a timeout, distinct from empty results
- The first request after an idle hour is slow, and the app says something rather than
  appearing frozen

The qualitative check, and the one worth the most: **take the app somewhere your dataset
has never been.** SUN RGB-D and NYU are indoor scenes captured with particular sensors in
particular rooms. Your kitchen at night is out of distribution, and thirty seconds of that
tells you more about what you have built than the entire test suite.

---

## Open items

- ⚠️ **Azure account per student** — free trial, Azure for Students, or a shared instructor
  subscription, and who pays on overrun. The free grant is **per subscription**, so a
  shared subscription shares one grant across the whole cohort, which is a materially
  different design.
- ⚠️ **Azure Container Registry is not covered by the Container Apps free grant.** Basic
  tier bills a fixed daily rate whether or not you push. Read the current figure from the
  ACR pricing page and record it in `docs/azure-budget.md` before creating the registry.
- ⚠️ **iOS standalone distribution** (step 10) requires a paid Apple Developer Program
  membership. The course runs on Expo Go for this reason. Confirm current Expo Go SDK
  support before a cohort.
- ⚠️ **N1's link characteristics** — this lesson provides the measurement, but which form
  N1 finally takes (client-observed with a pinned link, or server-observed with a separate
  transit budget) is a requirements decision, not a measurement.
- ⚠️ **MLflow in CI** — carried from Lessons 03 and 04, resolved in Lesson 06.

All tracked in the course [`TODO.md`](../../TODO.md).

---

## Further reading

- [Azure Container Apps — billing](https://learn.microsoft.com/en-us/azure/container-apps/billing) —
  the free grant, and why scale-to-zero is the whole design
- [Azure Container Apps — `az containerapp up`](https://learn.microsoft.com/en-us/azure/container-apps/quickstart-code-to-cloud)
- [Azure Container Apps — scaling](https://learn.microsoft.com/en-us/azure/container-apps/scale-app)
- [Expo — camera](https://docs.expo.dev/versions/latest/sdk/camera/)
- [Expo — environment variables and `EXPO_PUBLIC_`](https://docs.expo.dev/guides/environment-variables/)
- [openapi-typescript](https://openapi-ts.dev/)
- [FastAPI — CORS middleware](https://fastapi.tiangolo.com/tutorial/cors/)

**Previous:** [Lesson 04](../04-backend-engineering/) ·
**Next:** Lesson 06 — CI / CD / CT
