# Requirements — Smart Scene Analyzer

> Copy to your project as `docs/requirements.md` and fill in. Every `<...>` must be
> replaced with a value before you run the Architecture Agent. A requirement without a
> number does not constrain a design, and a design without constraints is arbitrary.

## Functional requirements

| ID | Requirement | Priority |
|---|---|---|
| F1 | The service accepts a single RGB image and returns detected objects | Must |
| F2 | Each detection carries a class label and a confidence score | Must |
| F3 | Each detection carries a bounding box in absolute pixels of the original image | Must |
| F4 | Each detection carries an estimated depth | Must |
| F5 | The service returns a dense depth map for the whole image | `<Must / Should / Won't>` |
| F6 | The service accepts a batch of images in one request | `<Must / Should / Won't>` |
| F7 | The service reports the model version used for each prediction | Must |
| F8 | `<add your own>` | |

### Object taxonomy

The classes the system detects. This list must match `docs/taxonomy.md` and is shared
across every dataset version — see Lesson 02.

`<list the classes, or write "pending — see Lesson 02 step 10">`

### Out of scope

State plainly what this system does **not** do. An unstated non-goal gets built.

- `<e.g. instance segmentation>`
- `<e.g. video / temporal tracking>`
- `<e.g. metric-scale absolute depth in metres>`

---

## Non-functional requirements

**These are what actually shape the architecture.** Fill in real numbers.

### Performance

| ID | Requirement | Target | How it is measured |
|---|---|---|---|
| N1 | End-to-end p95 latency, single 1280×720 image | `<___ ms>` | `<client-observed over ___ Mbit/s, at ___ KB upload / server-observed>` |
| N1a | Upload size the client sends | `<___ KB>` at `<___ px long edge>` | After on-device preparation |
| N2 | p50 latency | `<___ ms>` | Same conditions as N1 |
| N3 | Detection accuracy | mAP@50 ≥ `<___>` | Held-out test split, dataset version stated |
| N4 | Depth accuracy | `<metric, e.g. δ<1.25 ≥ ___>` | Held-out test split |
| N5 | Throughput | `<___ req/s>` at `<___ concurrency>` | Load test |
| N6 | Cold start | `<___ s>` | First request after the container scales from zero |

> **Where N1 comes from.** Work backwards from the user experience you want, not
> forwards from what you think the model can do. If the mobile client should feel
> responsive, you have roughly 400 ms; that number then tells the Architecture Agent
> whether detection and depth can run sequentially. Setting the budget from the
> model's convenience defeats the purpose.

> ⚠️ **N1 must say which side of the network it is measured on, and if it is the client's
> side, on what link.** "Client-observed p95 under 800 ms" sounds rigorous and cannot be
> passed or failed, because it does not say what the client is connected to:
>
> ```
> 250 KB upload at 5 Mbit/s  =  250 × 8 / 5000  ≈  400 ms
>                               ...before the server has seen a single byte
> ```
>
> Half the budget is gone to physics you do not control, and on a slower link the
> requirement is unachievable no matter how fast the code is. Two defensible shapes:
> client-observed **with the link pinned**, or server-observed **with transit budgeted
> separately**. Pick one now. Lesson 05 measures the real number on Wi-Fi and cellular.

> **N6 is not optional now that the service scales to zero.** A container with no replica
> running costs nothing and starts cold, and this one loads a depth model at startup. That
> trade — free idling for a slow first request — is a requirement, not an accident.

### Resource constraints

| ID | Requirement | Target |
|---|---|---|
| N7 | Max input image size accepted | `<___ MB>` / `<___ px>` |
| N8 | Serving container memory ceiling | `<___ GB>` |
| N9 | Serving image size ceiling | `<___ GB>` |
| N10 | GPU required for serving? | `<yes / no>` |

### Reliability and operations

| ID | Requirement | Target |
|---|---|---|
| N11 | Availability target | `<___%>` |
| N12 | Behaviour when a model fails to load | `<fail fast / degrade to detection-only>` |
| N13 | Behaviour on malformed or oversized input | `<HTTP code + response shape>` |
| N14 | Are request images retained? | `<yes — for active learning / no>` |
| N15 | Structured logging required | `<yes / no>` |

> N12 and N14 are easy to skip and expensive to retrofit. N12 determines whether the
> fusion layer must tolerate a missing branch. N14 is a privacy decision as much as an
> engineering one — decide it before you build the pipeline, not after.

### Development quality gates

| ID | Requirement | Target |
|---|---|---|
| N16 | Test coverage on `src/` | `<___%>` |
| N17 | Type checking | `mypy --strict` passes |
| N18 | Every PR passes CI before merge | yes |
| N19 | Reproducible training runs | Seed + dataset version + config recorded in MLflow |

---

## Open decisions blocking this document

| Decision | Blocks | Status | ADR |
|---|---|---|---|
| Inference target: cloud vs. on-device | N1, N7–N10, whole serving architecture | `<open / decided>` | `<docs/decisions/NNNN-...>` |
| MLflow hosting | N19 | `<open / decided>` | |
| N1: client- or server-observed | N1, N2, the latency budget | `<open / decided>` | |
| Object taxonomy | F-list, all of Lesson 02 | `<open / decided>` | |

> **Mobile app: real client or stub** used to be the first row of this table. It is
> **decided** — a real Expo client for iOS and Android, built in Lesson 05. The consequence
> is the row above it: a real client makes N1's link characteristics a question somebody
> has to answer.

Resolve each with `/adr <title>` and link the resulting file here.
