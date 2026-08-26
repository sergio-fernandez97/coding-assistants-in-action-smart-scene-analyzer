---
name: credit-ledger
description: Use before and after ANY operation that spends Roboflow credits — training runs, hosted or self-hosted inference, Auto Label, version generation, workflow runs, batch jobs. Produces the cost estimate with arithmetic, records it in docs/credit-budget.md, and reconciles the actual afterwards. Invoke this whenever a tool call might bill, when asked "can we afford this", or when the credit gate hook has blocked a call.
---

# The credit ledger

This project has a hard cap of **20 Roboflow credits for its entire lifetime**, across
Lessons 01–06, with no top-up. `docs/credit-budget.md` is the ledger and the only source
of truth for what has been spent.

The ritual below is not paperwork. It exists because the failure mode it prevents —
spending the budget discovering what something costs — is unrecoverable. There is no
Lesson 06 for a project that ran out in Lesson 03.

## Before the call

Do these in order. Do not call the billed tool until all four are done.

1. **Find the rate.** Read it from `roboflow:plans-and-pricing`, not from memory and not
   from the summary table in `CLAUDE.md`. Upstream rates change; the skill is re-read
   from disk every session, the table is not. Quote the rate you found.

2. **Show the arithmetic.** Not "roughly 2 credits" — the multiplication.

   ```
   Auto Label, 100 images
     rate: 1 credit / 100 images
     100 / 100 = 1.0 credits
   ```

   An estimate you cannot subtract from a balance is not an estimate. If the operation
   bills on time rather than count (training at 1 credit / 30 min, hosted inference at
   1 credit / 500 execution-seconds), state the assumed duration and where it came from.

3. **Read the remaining balance** from `docs/credit-budget.md`. Compare it to the
   estimate.

   **If the estimate exceeds the balance, stop and report.** Do not run a smaller version
   of the operation to fit. Say what the full operation would cost and let the user decide
   what to cut — shrinking it silently converts a budget decision into a technical one.

4. **Append the ledger row**, with `Actual` left blank:

   ```
   | 2026-08-11 | 03 | Hosted training, yolov11s, 100 epochs | 1cr/30min | 2.0 |  | 2.0 | 18.0 |
   ```

   The `PreToolUse` credit gate reads this file and blocks billed MCP tools until a row
   with an estimate and no actual exists. If a call was blocked, this step is what was
   missing.

Then ask for approval and make the call.

## After the call

5. **Record the actual cost** in the same row, and update `Remaining` and
   `Last reconciled` in the header table.

   Get the actual from `app.roboflow.com/<workspace>/settings/usage`, not from your own
   estimate. Copying the estimate into the actual column defeats the entire mechanism.

6. **If estimate and actual differ, write a Notes row saying why.** A gap is a finding,
   not an error to hide — it means an operation bills for something the rate table does
   not model, and that note is worth more than the credit it cost.

## Operations that are forbidden, not merely expensive

Refuse these and explain why; do not price them and ask.

| Operation | Why |
|---|---|
| RF-DETR **NAS** (`rfdetr-nas-*-parent`) | Roboflow's own skill recommends it by default. Dozens of child models at 2 credits/hour, and it fails outright on non-Core plans |
| Dedicated deployments | Bills **uptime**, not usage — 24 credits/day, more than the whole budget |
| Batch processing on GPU | 4 credits/hour, the worst rate on the platform |
| Auto Label beyond the agreed 100-image audit | Linear at 0.01 credits/image |
| `datasource_trigger`, `connect_cloud_storage` | Mirror runs bill, and `trigger` defaults to **true** |
| Video streams and WebRTC, hosted or local | Self-hosted video alone caps at 20 credits/month |

## Free — take these paths first, and say that you did

Auto Label's 4-image "Generate Test Results" preview · Roboflow Instant training ·
Universe search and browsing · RoboQL queries · tags and splits · workflow authoring,
block listing, and spec validation (only *running* a workflow bills) · cancelling a
training run early.

Recording a free operation in the ledger is worth doing anyway: it documents that the
cheap path was chosen deliberately rather than missed.

## What good output looks like

- The rate is quoted from `roboflow:plans-and-pricing` with the operation it applies to
- The arithmetic is shown, not summarized
- The remaining balance is read from the ledger, not recalled
- A ledger row exists before the call and is completed after it
- Estimate/actual divergence is explained in Notes rather than smoothed over

## Reject and re-run if

- A billed call happened before a ledger row existed
- The estimate is a range or an adjective ("small", "a couple") rather than a number
- The rate came from `CLAUDE.md`'s summary table instead of the skill
- The operation was quietly resized to fit the remaining balance
- `Actual` was filled in with the estimated figure rather than the platform's usage page
- The ledger's `Remaining` was not updated after reconciliation
