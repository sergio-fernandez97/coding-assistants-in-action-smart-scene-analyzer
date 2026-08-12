# Lesson 05 — Deliverables checklist

## Before you start

- [ ] `docker compose up -d` serves `/analyze` and `/health` locally
- [ ] `uv run pytest` passes with no GPU and no weights on disk
- [ ] Detection runs on **local weights** — no Roboflow call on the request path
- [ ] `node --version` is 20+
- [ ] `az login` succeeded, and you can create resources in the subscription
- [ ] Expo Go installed on a phone, on the same Wi-Fi as your machine
- [ ] `docs/credit-budget.md` reconciled

## Roles

- [ ] `.claude/agents/mobile.md` read
- [ ] You can state both of its hard constraints without looking
- [ ] Nothing under `src/` was edited by the `mobile` agent

## Azure budget — before any resource exists

- [ ] `docs/azure-budget.md` copied into the project
- [ ] A subscription **budget alert** exists
- [ ] You can say why an alert is a weaker guarantee than `credit_gate.py`
- [ ] The ACR daily rate was looked up **before** the registry was created, and recorded
- [ ] You can state the one configuration that would exhaust the free grant

## Deployment

- [ ] The Dockerfile was inspected before deploying — bind address and weight strategy known
- [ ] All resources are in **one** resource group
- [ ] `--cpu 1.0 --memory 2.0Gi` set explicitly
- [ ] **`minReplicas` is `0`, confirmed from `az containerapp show` output** — not from
      the deploy command's summary
- [ ] `--max-replicas` set explicitly
- [ ] `curl $API_URL/health` returns 200 over **HTTPS**
- [ ] Cold and warm first-byte times measured and recorded separately
- [ ] Every created resource is listed in `docs/azure-budget.md` with whether it bills to exist

## The contract

- [ ] `app/openapi.json` generated from the running service
- [ ] `app/src/api/types.ts` **generated**, never hand-written
- [ ] `app/openapi.json` is gitignored
- [ ] The response type is imported from `types.ts` everywhere — no hand-declared interface
      of the response shape anywhere in `app/`
- [ ] The `contract_drift` hook was **observed firing** after a real `schemas.py` edit
- [ ] You can say why that hook warns instead of blocking, and why `units_guard` blocks

## The client

- [ ] Runs in Expo Go on a real **iOS** device
- [ ] Runs in Expo Go on a real **Android** device
- [ ] `EXPO_PUBLIC_API_BASE_URL` is the only source of the endpoint — no literal, no fallback
- [ ] **No key of any kind appears in `app/`**
- [ ] Camera permission denial is a recoverable state, not a dead screen
- [ ] All seven result states exist and are distinguishable on screen
- [ ] **Zero detections renders as a success**, not an error
- [ ] Airplane mode shows an offline state, distinct from a timeout
- [ ] An "analyzing" state is visible during the request
- [ ] `npx tsc --noEmit` passes

## Geometry

- [ ] All six real numbers printed from one real request before any transform was written
- [ ] Exactly one exported transform in `app/src/geometry/toScreen.ts`
- [ ] Both coordinate spaces named in its signature — not `number[]`
- [ ] Letterbox offset handled explicitly
- [ ] The function is pure — no React, no hooks
- [ ] Unit tests assert **hand-computed** values, not snapshots
- [ ] Boxes land on objects in portrait
- [ ] Boxes land on objects in landscape
- [ ] Boxes land at a second aspect ratio
- [ ] The overlay uses the **prepared** image dimensions, not the captured ones

## Upload preparation

- [ ] An unmodified phone photo was sent once and produced a real **413**
- [ ] Images resized so the long edge matches the server's expectation
- [ ] EXIF orientation applied **and the tag stripped**
- [ ] An upside-down photo returns correctly oriented boxes
- [ ] Before/after byte counts recorded
- [ ] The server's upload limit was **not** raised to avoid resizing
- [ ] CORS origins come from configuration as an explicit list
- [ ] **`allow_origins=["*"]` appears nowhere**

## Latency

- [ ] The round-1 prediction was written down **before** measuring
- [ ] Per-stage timings instrumented, gated behind `__DEV__`
- [ ] n ≥ 20 for each warm case
- [ ] Wi-Fi and cellular measured separately and **never averaged together**
- [ ] Measured link speed recorded for each, from an actual speed test
- [ ] Cold start reported separately with its own n
- [ ] Lesson 04's loopback number included and labelled as measuring the code
- [ ] The dominant stage identified per link
- [ ] `docs/latency-report.md` states conditions before any number
- [ ] **`docs/requirements.md` N1 is filled in and names its link** — no longer a placeholder

## Decisions

- [ ] An ADR revisits on-device vs cloud, citing step 8's measurements
- [ ] It supersedes or amends ADR 0001 rather than sitting beside it
- [ ] It states what would change the decision, in terms that could actually occur

## The units rule, where nothing enforces it

- [ ] `grep -riE 'meter|metre|\bcm\b|\bmm\b|distance|away|feet|inches' app/src/` reviewed
      hit by hit
- [ ] **No distance, unit, or raw depth number reaches the screen**
- [ ] Depth is conveyed by ordering and shading, with a "nearer / farther" legend
- [ ] You can say why this check is manual here and automatic in `src/`

## Reconciliation

- [ ] **Roboflow ledger unchanged** — Lesson 05 spends zero credits
- [ ] Azure metered cost recorded in `docs/azure-budget.md`
- [ ] `minReplicas` confirmed `0` one final time
- [ ] `git status` shows no `node_modules/`, no `.env`, no `app/openapi.json`
- [ ] `uv run ruff check . && uv run mypy src && uv run pytest` all pass
- [ ] Committed and pushed

## The check no list can make

- [ ] You took the app somewhere your dataset has never been, and looked at what happened
