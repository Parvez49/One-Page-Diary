# Software Architecture

> Architecture = the decisions that are **expensive to change later**: service boundaries,
> data ownership, communication style, deployment unit. Everything else is design.

---

## 1. Monolithic Architecture

A **single unified codebase** where all components (UI, business logic, data access, background
tasks) are tightly integrated into **one deployable unit**.

```
┌──────────────────────────────────────┐
│           MONOLITH (1 deploy)        │
│  ┌────────────────────────────────┐  │
│  │ Presentation Layer (React/Next)│  │
│  ├────────────────────────────────┤  │
│  │ Business Logic Layer           │  │
│  ├────────────────────────────────┤  │
│  │ Data Access Layer (ORM)        │  │
│  └────────────────────────────────┘  │
└─────────────────┬────────────────────┘
                  ▼
         ┌──────────────────┐
         │ Single Database  │
         └──────────────────┘
```

| Layer | Contains |
|---|---|
| **Presentation (UI)** | Frontend — React, Next.js, Django templates |
| **Business Logic** | Application logic, service functions, validation |
| **Data Access** | ORM, queries, repositories |
| **Database** | One centralised DB |

**✅ Advantages**
- **Simple to develop, test, deploy** — one repo, one build, one artifact.
- **No network calls between modules** → low latency, no serialisation overhead.
- **ACID transactions across the whole domain** — a single `BEGIN…COMMIT` covers everything.
- Easy debugging: one stack trace, one log file.
- **Cheapest for small teams** — no infra overhead (no service mesh, no distributed tracing).

**❌ Drawbacks**
- **Scaling is all-or-nothing** — if only image processing is hot, you still scale the whole app.
- One bug (memory leak, infinite loop) can take down **everything**.
- **Slow builds & test suites** as it grows; long CI feedback loops.
- **Tight coupling** creeps in — the "big ball of mud" — because nothing physically stops a
  module reaching into another's internals.
- **Technology lock-in**: stuck with one language/framework/version for the whole system.
- Deploy of a one-line fix requires redeploying the entire application → risky, infrequent releases.
- Large teams step on each other in the same codebase.

> 💡 **Modular Monolith** — the sweet spot most companies should start at: one deployable unit,
> but with **strictly enforced internal module boundaries** (each module owns its tables and
> exposes only a public interface). You get monolith simplicity now, and clean seams to extract
> services later *if* you ever need to.

---

## 2. Microservices Architecture ⭐

The application is split into **small, independently deployable services**, each owning a
**business capability** and its **own database**.

```
        ┌─────────────┐
        │ API Gateway │
        └──┬───┬───┬──┘
     ┌─────┘   │   └─────┐
     ▼         ▼         ▼
┌────────┐┌────────┐┌─────────┐
│ Users  ││ Orders ││ Payments│   ← independently deployable
│  svc   ││  svc   ││   svc   │
└───┬────┘└───┬────┘└────┬────┘
    ▼         ▼          ▼
 ┌─────┐   ┌─────┐    ┌─────┐    ← database PER SERVICE
 │ DB  │   │ DB  │    │ DB  │
 └─────┘   └─────┘    └─────┘
```

**Key rules (violating these gives you a distributed monolith):**
- **Database per service** — no service reads another's tables directly.
- Communicate only via **APIs (REST/gRPC)** or **events**.
- Each service is **independently deployable** and owned by one team.

**✅ Advantages**
- **Independent scaling** — scale only the Payments service on Black Friday.
- **Independent deployment** — ship 50×/day without coordinating releases.
- **Fault isolation** — Recommendations dying doesn't stop checkout (*if* you use circuit breakers).
- **Technology freedom** — Python for ML, Go for high-throughput, Node for realtime.
- **Team autonomy** — small teams own services end-to-end; scales the *organisation*, not just the software.

**❌ Drawbacks (interviewers care more about these)**
- ⚠️ **Distributed systems complexity** — network is unreliable, latency is real, partial failures are the norm.
- ⚠️ **No cross-service ACID transactions** → need **Saga** pattern & eventual consistency. This
  is the single biggest source of pain.
- **Operational overhead**: service discovery, centralised logging, distributed tracing, CI/CD
  per service, container orchestration (K8s). You need a real DevOps capability.
- **Hard to debug** — one user request spans 8 services; you need correlation IDs and tracing (Jaeger/Zipkin).
- **Data duplication & sync** — reporting across services requires aggregation or a data warehouse.
- **Testing is harder** — integration/end-to-end tests need many services running (→ contract testing).
- **Higher cost**: more infra, more monitoring, more people.
- **Wrong boundaries are brutal** to fix — worse than a monolith, because now the mistake is
  across a network *and* across teams.

> ⚠️ **Distributed Monolith** — the worst outcome: services that must be deployed together,
> share a database, or call each other synchronously in long chains. You pay all of the
> microservices costs and get none of the benefits.

---

## 3. Monolith vs Microservices ⭐⭐ *top interview question*

| Aspect | **Monolith** | **Microservices** |
|---|---|---|
| Deployment | One unit | Many independent units |
| Database | Shared, single | One per service |
| Scaling | Whole app together | Per service |
| Transactions | **ACID**, easy | Saga / eventual consistency, hard |
| Communication | In-process function calls | Network (REST/gRPC/events) |
| Failure impact | Whole app | Isolated (with circuit breakers) |
| Tech stack | One | Polyglot |
| Debugging | Single stack trace | Distributed tracing required |
| Team fit | Small teams (< 10–15) | Many autonomous teams |
| Infra cost | Low | High |
| Initial velocity | **Fast** | Slow (infra first) |
| Long-term velocity at scale | Degrades | Sustained |

> 🗣️ **Best answer:** *"Start with a **modular monolith**. Microservices solve an
> **organisational** scaling problem more than a technical one — they're worth it when multiple
> teams are blocked by a shared deployment pipeline. Adopting them on day one with a 5-person
> team means paying enormous operational cost to solve a problem you don't have yet."*
>
> **Martin Fowler's "Monolith First":** you can't design good service boundaries before you
> understand the domain — and you only understand the domain by building it.

---

## 4. Event-Driven Architecture (EDA)

Components communicate through **events** instead of direct requests. Events are captured and
processed **asynchronously**, enabling loose coupling, scalability and real-time responsiveness.

```
┌───────────┐   event   ┌──────────────┐  event  ┌───────────┐
│ Producer  │ ────────▶ │    Broker    │ ──────▶ │ Consumer  │
│(Publisher)│           │ Kafka/Rabbit │         │(Subscriber)│
└───────────┘           │ Redis Streams│         └───────────┘
                        └──────────────┘   └───▶ ┌───────────┐
   "OrderPlaced"                                 │ Consumer 2│
   producer doesn't know or care who listens     └───────────┘
```

**The 3 building blocks**
- **Event Producers (Publishers)** — detect a change (state change, user action, sensor data) and emit an event.
- **Event Broker (Message Queue / Stream)** — Kafka, RabbitMQ, Redis Streams, AWS SQS/SNS.
- **Event Consumers (Subscribers)** — listen for specific events and act.

**Example:** `OrderPlaced` → *inventory* reserves stock, *email* sends confirmation,
*analytics* records the sale — all independently, none known to the producer.
**Django + Celery** is a practical example of this style.

#### ⚠️ Is Django + Redis + Celery "event-driven"? (only partly)

It maps onto the 3 blocks — Django view calling `task.delay()` = producer, Redis/RabbitMQ =
broker, Celery worker = consumer — and gives the same wins (request returns instantly, slow
work offloaded, workers scale separately). But it is a **task queue**, not an event backbone:

| | **Celery task queue** | **True EDA** |
|---|---|---|
| Message meaning | **Command** — `send_email.delay(id)` ("do this") | **Event** — `OrderPlaced` (a past-tense fact) |
| Producer knowledge | Knows exactly which task/worker runs | Knows nothing about listeners |
| Delivery | Point-to-point: **one** worker per task | Fan-out: **N** independent consumers |
| Adding a listener | Producer code must call the new task | Just subscribe — producer untouched |
| History | Message deleted after ack → **no replay** | Log retained (Kafka) → replay, event sourcing |
| Coupling | Same app: workers import your models & DB | Separate services sharing only an event schema |
| Purpose | Offload work (async) | Decouple systems (notification) |

**Rule of thumb:** Celery = *async task queue*. EDA = *notification backbone*.
Swap `task.delay()` for publishing `user.registered` to Redis Streams/Kafka, consumed by three
services that Django never heard of — **that** is when you've crossed into event-driven.

### Message Queue vs Pub/Sub vs Event Streaming ⭐

| | **Queue** (RabbitMQ, SQS) | **Pub/Sub** (SNS, Redis) | **Event Stream** (Kafka) |
|---|---|---|---|
| Delivery | **One** consumer per message | **All** subscribers get a copy | All consumer groups, **replayable** |
| Message after read | Deleted | Gone (fire & forget) | **Retained** (by time/size) |
| Ordering | Per queue | Not guaranteed | Guaranteed **per partition** |
| Use case | Task distribution (send 10k emails) | Fan-out notifications | Event sourcing, analytics, replay |

### 🌍 Real-world example — food delivery (Uber Eats / Foodpanda style)

You tap **"Place Order"**. The API does *one* thing: save the order and publish
`OrderPlaced {order_id, user_id, restaurant_id, items, total}` to Kafka. It returns `201` in
~50 ms — it does **not** wait for payment, the restaurant, or the driver.

```
                                    ┌──────────────────┐
                                    │ Payment Service  │ → charges card → PaymentCaptured
                                    ├──────────────────┤
  [Order API] ──OrderPlaced──▶ Kafka│ Restaurant App   │ → prints ticket, chef starts cooking
   (returns                   topic ├──────────────────┤
    instantly)                      │ Dispatch Service │ → finds nearby riders
                                    ├──────────────────┤
                                    │ Notification Svc │ → push "Order confirmed 🎉"
                                    ├──────────────────┤
                                    │ Analytics/ML     │ → sales dashboard, demand forecast
                                    ├──────────────────┤
                                    │ Fraud Service    │ → risk-scores the order
                                    └──────────────────┘
```

**The chain continues** — each consumer is also a producer:

| Event | Emitted by | Who reacts |
|---|---|---|
| `OrderPlaced` | Order API | payment, restaurant, dispatch, notify, analytics, fraud |
| `PaymentCaptured` | Payment | order (→ `CONFIRMED`), accounting, notify |
| `PaymentFailed` | Payment | order (→ cancel), notify ("card declined"), restaurant (stop cooking) |
| `FoodReady` | Restaurant tablet | dispatch (assign rider), notify ("picked up soon") |
| `RiderLocationChanged` | Rider app (every 4s) | live-tracking map, ETA service |
| `OrderDelivered` | Rider app | payout to restaurant, loyalty points, review request, analytics |

**Why EDA and not direct API calls**
- The **notification service can be down** for 5 minutes — Kafka holds the events, it catches up.
  A synchronous `requests.post()` chain would have failed the whole checkout.
- **Marketing wants "3rd order → send a coupon."** New consumer on `OrderDelivered`.
  **Zero changes** to the Order API. That's loose coupling paying off.
- **Friday 8 PM spike**: 50× orders. The broker buffers; you scale only the dispatch consumers.
- **Replay**: the ML team ships a better ETA model → re-consume 6 months of
  `RiderLocationChanged` from the Kafka log to backtest it. Impossible with a plain queue.

**And the pain is real too** ⚠️
- The app shows *"Payment processing…"* for 2 s — **eventual consistency** leaking into the UI.
- Payment webhook fires twice → must **dedupe by `payment_id`** (idempotency) or the user is
  charged double.
- Order stuck in `PENDING`: was it payment, dispatch, or the restaurant? You need a
  **correlation ID** (`order_id`) stitched across all service logs to find out.
- A malformed event that crashes the payment consumer would block the partition → it goes to a
  **dead-letter queue** and a human inspects it.

> **Smaller everyday examples:** GitHub webhooks (push → CI, Slack, deploy),
> Stripe webhooks (`payment_intent.succeeded` → your app), IoT sensors → Kafka → alerting,
> and the classic `UserRegistered` → welcome email + CRM sync + free-trial provisioning.

**✅ Advantages of EDA**
- **Loose coupling** — add a consumer without touching the producer.
- **Async & non-blocking** → producer responds immediately; better perceived performance.
- **Natural scalability** — add consumer instances to drain a backlog.
- **Resilience & buffering** — the broker absorbs traffic spikes; if a consumer is down, messages wait.

**❌ Drawbacks**
- ⚠️ **Eventual consistency** — data is briefly out of sync; the UI must handle "processing…" states.
- **Debugging is hard** — no single call stack; you need correlation IDs and tracing.
- **Ordering & duplicates** — most brokers guarantee *at-least-once*, so consumers **must be
  idempotent** (dedupe by event ID).
- **The broker becomes critical infra** — a new SPOF that needs its own HA setup.
- **Schema evolution** — changing an event's shape can break unknown downstream consumers → needs a schema registry.
- **Poison messages** — a permanently failing message can block a partition; needs **dead-letter queues**.

### Related patterns
- **CQRS (Command Query Responsibility Segregation)** — separate write model from read model
  (optimised read replicas/projections). *Pro:* each side scales & is modelled independently.
  *Con:* two models to keep in sync, eventual consistency, significant complexity.
- **Event Sourcing** — store the **sequence of events** as the source of truth, not the current
  state. *Pro:* full audit trail, time-travel debugging, rebuild any past state. *Con:* very
  hard to query, schema migration of old events is painful, steep learning curve.
- **Saga** — manage a transaction spanning services via a chain of local transactions plus
  **compensating actions** (e.g. payment fails → *release* reserved stock). *Choreography*
  (services react to events, no coordinator) vs *Orchestration* (a central saga coordinator).

---

## 5. Other Architectural Styles

### Layered / N-Tier
The default. `Presentation → Business → Data Access → Database`, each layer calling only downward.
- **✅** Simple, familiar, clear separation, easy to staff for.
- **❌** "**Sinkhole anti-pattern**" — simple requests pass through every layer doing nothing;
  tends toward a monolithic deployment; changes ripple through all layers.

### Client-Server
Clients request, a central server responds. Foundation of the web.
- **✅** Centralised control, data, and security.
- **❌** Server is a bottleneck and a SPOF.

### Service-Oriented Architecture (SOA)
Microservices' predecessor: coarser-grained services communicating over an **ESB (Enterprise
Service Bus)**, often sharing a database.
- **Difference from microservices:** SOA = *share as much as possible* (smart pipes, shared DB);
  microservices = *share as little as possible* (dumb pipes, smart endpoints, DB per service).

### Serverless (FaaS)
Functions run on demand; the cloud manages the servers (AWS Lambda, Cloud Functions).
- **✅** No server management, **scale to zero** (pay per invocation), auto-scaling, fast to ship.
- **❌** ⚠️ **Cold starts** (latency spikes), execution time limits (~15 min), **vendor lock-in**,
  hard local testing/debugging, expensive at sustained high volume, statelessness forces
  external state (Redis/DynamoDB).

### Peer-to-Peer (P2P)
No central server; nodes are both client and server (BitTorrent, blockchain).
- **✅** No SPOF, scales with participants. **❌** Hard to secure, coordinate, and guarantee consistency.

### Hexagonal (Ports & Adapters) / Clean Architecture
Domain logic sits in the centre, entirely free of framework/DB/HTTP concerns. Everything
external plugs in through **ports** (interfaces) implemented by **adapters**.
- **✅** Domain is testable in isolation and outlives the framework; swap DB or delivery mechanism.
- **❌** Lots of boilerplate & mapping; overkill for CRUD apps.

---

## 6. Choosing an Architecture

| If you have… | Choose |
|---|---|
| Small team, new product, unclear domain | **Modular Monolith** |
| Many teams blocked by one deploy pipeline | **Microservices** |
| Async workflows, fan-out reactions, high write throughput | **Event-Driven** |
| Spiky/unpredictable traffic, glue code, cron jobs | **Serverless** |
| Read-heavy with very different read/write shapes | **CQRS** |
| Strict audit/compliance history requirements | **Event Sourcing** |
| Complex, long-lived business domain | **Hexagonal + DDD** |

**Trade-offs are the whole point.** In an interview, never answer "microservices" without
naming what you're paying for it.

---

## 7. Common Interview Questions

- **Q: How would you break a monolith into microservices?**
  → Never big-bang it. Use the **Strangler Fig pattern**: put a facade/gateway in front,
  extract one bounded context at a time (start with something loosely coupled and separately
  scalable, like notifications or search), route that traffic to the new service, and repeat.
  Split the database *last* and *deliberately* — that's the hard part.

- **Q: How do you decide service boundaries?**
  → By **business capability / DDD bounded context**, not by technical layer. A "Database
  service" or "Validation service" is an anti-pattern. Good test: can this team ship a feature
  without changing another service? Data that changes together belongs together.

- **Q: How do services handle a failing dependency?**
  → **Circuit breaker** (stop calling after N failures, fail fast, probe for recovery),
  **retry with exponential backoff + jitter**, **timeouts** on every call, **bulkheads** (isolated
  connection pools), and graceful degradation (serve cached/default data).

---

**Related:** [system_design.md](system_design.md) · [design_patterns.md](design_patterns.md) · [principles.md](principles.md) · `../Deploy/` · `../CICD/`
