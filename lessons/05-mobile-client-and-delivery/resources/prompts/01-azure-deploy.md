# Prompt — deploy the service to Azure Container Apps

**When:** Lesson 05, step 3.

**Which agent:** `devops`. This is delivery, not application work.

**Credits: zero Roboflow.** Azure cost is the free grant, provided round 2 lands.

---

## Round 1 — read the image before shipping it

```
Use the devops agent.

Before deploying anything, tell me what my current Dockerfile actually produces:

  - The final image size, from `docker images`
  - Whether the weights are baked into the image or mounted at runtime
  - What the container needs at startup that is not in the image — env vars,
    mounted paths, network access
  - The EXPOSE port, and whether the app binds 0.0.0.0 or 127.0.0.1
  - How long `docker run` takes from start to the first successful /health

Do not change the Dockerfile. Report what is there.
```

**Why this round exists.** Two of those answers decide whether the deployment can work at
all, and both are easy to get wrong locally without noticing.

An app bound to `127.0.0.1` serves fine under `docker run -p` on your machine and is
unreachable behind Container Apps ingress. And weights **mounted** from your filesystem —
which Lesson 04 recommended, to keep the image small — do not exist in a cloud container.
If round 1 reports a mount, that is the finding, and the fix is a deliberate choice
between baking the weights in and pulling them at startup. Decide it here, not from a
confusing 503 twenty minutes later.

---

## Round 2 — deploy, and pin the scale floor

```
Deploy the service to Azure Container Apps using `az containerapp up --source .`
against the existing Dockerfile.

Requirements:
  - Ingress external, target port matching EXPOSE
  - --cpu 1.0 --memory 2.0Gi
  - --min-replicas 0 --max-replicas 1
  - Everything in one resource group so teardown is a single command

Then VERIFY, do not assert:
  - `az containerapp show --query "properties.template.scale"` shows minReplicas 0
  - curl the FQDN's /health and show me the response
  - report the FQDN

Record the resource group, registry, environment, and app name in docs/azure-budget.md,
including which of them cost money to merely exist.
```

**`--min-replicas 0` is the whole cost model.** A revision scaled to zero incurs no
resource-consumption charges; a revision pinned at one replica runs continuously and
exhausts a 50-hour monthly grant in just over two days. It is the same failure as a
Roboflow dedicated deployment left running — billing for existing rather than for working
— and neither a permission rule nor a hook can catch this one, because the spend happens
on Microsoft's side of a wire you do not control.

Ask for the verification command's output, not the agent's summary of it. "Configured with
min-replicas 0" and "the API reports minReplicas 0" are different claims.

---

## Round 3 — cold start, measured once

```
Scale the app to zero by leaving it idle, then measure:
  - Time to first byte on the FIRST request after idle
  - Time to first byte on the second request immediately after

Report both. Do not tune anything yet.
```

This container loads a depth model at startup, so the first request after an idle period
is slow. That is not a bug — it is the price of paying nothing to sit idle, and it is a
number the latency report in step 8 has to keep separate from steady-state.

---

## What good output looks like

- Round 1 reports the actual bind address and weight-loading strategy from the real image
- Ingress is external, HTTPS, and `/health` returns 200 over the public FQDN
- `minReplicas` is confirmed **from the platform's own output**, not from the deploy command
- Every resource is in one resource group
- `docs/azure-budget.md` names each resource and whether it bills to exist
- Cold and warm start times are reported as separate numbers

## Reject and re-run if

- The Dockerfile or anything in `src/` was modified to make the deployment work, without
  that being raised as a decision first
- `--min-replicas` was left at its default rather than set explicitly
- The agent reports success without showing the `curl` output
- Resources were created across multiple resource groups, making teardown multi-step
- A registry was created before its cost was looked up
- The agent proposes `--min-replicas 1` to fix cold starts. That is a real trade-off, but
  it is a budget decision, and at this budget the answer is no
