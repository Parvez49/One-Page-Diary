# Celery, Brokers & Background Work

> Event-driven design: **[../../SDLC/architecture.md](../../SDLC/architecture.md)** ·
> Transaction interaction: **[orm.md §6](orm.md)**

---

## 1. Why background tasks ⭐

An HTTP request should do one thing: change state and respond. Anything slow, unreliable, or
retriable belongs off the request path.

```python
def checkout(request):
    order = Order.objects.create(...)
    send_confirmation_email(order)      # ⚠️ 2s SMTP call blocks the worker
    generate_invoice_pdf(order)         # ⚠️ 5s CPU
    return Response(...)                # user waited 7s; a timeout loses the order
```

⭐ **The three arguments:** latency (respond in 50 ms, not 7 s), **reliability** (a failed
email shouldn't roll back a paid order), and **retries** (the queue retries; an HTTP request
can't).

**Typical work:** email/SMS, PDF and report generation, image/video processing, third-party
API calls, data exports, scheduled cleanup, cache warming, search indexing.

---

## 2. Celery

```python
# proj/celery.py
app = Celery("proj")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()

# settings.py
CELERY_BROKER_URL = env("REDIS_URL")
CELERY_RESULT_BACKEND = env("REDIS_URL")        # ⭐ only if you actually read results
CELERY_TASK_ACKS_LATE = True                    # ⭐ ack AFTER completion — survives a crash
CELERY_TASK_REJECT_ON_WORKER_LOST = True
CELERY_WORKER_PREFETCH_MULTIPLIER = 1           # ⭐ fair dispatch for long tasks
CELERY_TASK_TIME_LIMIT = 300                    # hard kill
CELERY_TASK_SOFT_TIME_LIMIT = 240               # ⭐ raises, so you can clean up
```

```python
@shared_task(
    bind=True,
    autoretry_for=(requests.RequestException,),
    retry_backoff=True, retry_jitter=True, max_retries=5,   # ⭐ exponential backoff
    acks_late=True,
)
def sync_inventory(self, product_id):
    product = Product.objects.get(id=product_id)     # ⭐ pass the ID, not the object
    ...
```

```bash
celery -A proj worker -l info -Q default,emails --concurrency=4
celery -A proj beat -l info              # scheduler
celery -A proj flower                    # ⭐ monitoring UI
```

### The rules that keep Celery working ⭐⭐

⚠️⚠️ **1. Pass IDs, never objects.** Arguments are serialised (JSON). A pickled model instance
is a stale snapshot — by the time the worker runs, the row has changed. Pass `order_id` and
re-fetch.

⚠️⚠️ **2. Wrap enqueue in `transaction.on_commit`:**

```python
with transaction.atomic():
    order = Order.objects.create(...)
    send_email.delay(order.id)                              # ⚠️ RACE — worker may run first
    transaction.on_commit(lambda: send_email.delay(order.id))   # ⭐ correct
```

The broker is faster than your commit. This produces intermittent `DoesNotExist` errors that
never reproduce locally — a very common production bug and a great thing to bring up unasked.

⭐ **3. Tasks must be idempotent.** With `acks_late`, a worker crash re-delivers the task —
**at-least-once** delivery. Charging a card twice is not acceptable, so guard with an
idempotency key or a state check (`if order.status != "pending": return`).

⚠️ **4. `ignore_result=True` unless you read the result.** Otherwise every task writes to the
result backend forever.

⚠️ **5. Never `task.get()` inside a web request** — it blocks the worker waiting on another
worker, and deadlocks when the pool is saturated. Return **202 Accepted** with a task id and
let the client poll ([drf.md §6](drf.md)).

**Routing & priority:**

```python
CELERY_TASK_ROUTES = {
    "billing.tasks.*": {"queue": "critical"},
    "reports.tasks.*": {"queue": "slow"},        # ⭐ isolate long jobs
}
```

⭐ **Separate queues by latency class.** One 20-minute report on the default queue starves
every password-reset email behind it.

**Scheduling:**

```python
app.conf.beat_schedule = {
    "cleanup": {"task": "core.tasks.cleanup", "schedule": crontab(hour=3, minute=0)},
}
```

⚠️ **Run exactly one `beat` process.** Two schedulers = every periodic task fires twice.
`django-celery-beat` moves the schedule into the database (editable, still single-instance).

**Workflows:** `chain(a.s(), b.s())` sequential · `group(...)` parallel ·
`chord(group)(callback)` fan-in.

---

## 3. Choosing a broker ⭐

| | **Redis** | **RabbitMQ** | **Kafka** |
|---|---|---|---|
| Model | in-memory data store used as a queue | ⭐ true message broker (AMQP) | ⭐ distributed **event log** |
| Delivery | at-least-once (⚠️ weaker guarantees) | ⭐ strong acks, DLQ, confirms | at-least-once, **replayable** |
| Routing | simple lists | ⭐ exchanges: direct/topic/fanout | topics + partitions |
| After consumption | deleted | deleted | ⭐ **retained** — replay from any offset |
| Persistence | optional (RDB/AOF) — ⚠️ can lose messages | durable queues | ⭐ durable log, days/weeks |
| Throughput | very high | high | ⭐ **very high, horizontally scaled** |
| Ops burden | ⭐ lowest (often already deployed) | moderate | ⚠️ highest (ZK/KRaft, partitions) |

⭐ **Decision rule:**
- **Redis** — you already run it, tasks are idempotent, and losing a rare message is
  survivable. The right default for most Django apps.
- **RabbitMQ** — you need delivery guarantees, dead-letter queues, delayed messages, or
  complex routing. Payments, order processing.
- **Kafka** — you need **replay**, high-throughput event streaming, or multiple independent
  consumers of the same events (analytics + billing + search indexing).

⚠️ **Redis-as-broker can lose messages** on failover or restart without persistence — it's a
cache pretending to be a queue. If a lost task means a lost payment, use RabbitMQ.

### Celery ≠ event-driven architecture ⭐

| | **Celery task queue** | **Event-driven (Kafka)** |
|---|---|---|
| Message | **command** — "do this" | **event** — "this happened" |
| Producer knows consumers | ✅ names the task explicitly | ❌ publishes and forgets |
| Delivery | point-to-point, **one** worker | fan-out to **N** independent consumers |
| Adding a consumer | edit the producer | ⭐ just subscribe |
| History | deleted after ack | ⭐ retained, replayable |

⭐ **The distinction to state:** Celery is *asynchronous work offloading*; EDA is
*decoupling systems*. `send_email.delay(id)` is an instruction to one known worker;
`OrderPlaced` is a fact that six services may independently care about. See
[../../SDLC/architecture.md](../../SDLC/architecture.md).

---

## 4. Reliability & operations

```python
@shared_task(bind=True, max_retries=3)
def call_api(self, order_id):
    try:
        resp = requests.post(URL, json={...}, timeout=10)   # ⭐ ALWAYS set a timeout
        resp.raise_for_status()
    except requests.Timeout as exc:
        raise self.retry(exc=exc, countdown=2 ** self.request.retries)
```

⭐ **Retry only transient failures.** Retrying a 400 five times just wastes five slots — check
the error class. And use **jittered exponential backoff**, or your retries synchronise into a
thundering herd against an already-struggling upstream.

**Dead-letter handling:** after `max_retries`, record the failure somewhere a human sees it
(`on_failure`, Sentry, a failed-jobs table) — a silently dropped task is worse than a loud one.

**Monitoring what matters:** queue **depth** (growing = under-provisioned), task **latency**
(enqueue → start), **failure rate**, and worker liveness. Flower for a UI; Prometheus for
alerts.

⚠️ **Worker memory leaks** are common with long-lived processes — `--max-tasks-per-child=100`
recycles workers ([../../Language/Python/performance.md](../../Language/Python/performance.md)).

⚠️ **Deploy ordering:** workers run *old* code until restarted. A task signature change must
be backwards compatible for one deploy, or in-flight messages fail on arrival.

---

## 5. Alternatives

| Tool | When |
|---|---|
| **Celery** | the default — mature, feature-rich, ⚠️ heavy configuration surface |
| **RQ** | ⭐ simple Redis queue; far less to learn if you don't need workflows/routing |
| **Dramatiq** | saner defaults than Celery, good middle ground |
| **django-q2** | lightweight, DB-backed |
| **`django-tasks` / DB queue** | ⭐ small apps — one less service to run |
| **Cloud** (SQS, Cloud Tasks, EventBridge) | managed, no broker to operate |
| **`asyncio` in-process** | ⚠️ not durable — lost on restart. Fire-and-forget only |

⭐ **Don't reach for Celery reflexively.** For three task types and one server, RQ or a
database-backed queue is less infrastructure and fewer failure modes.

---

## 6. Interview points

- **Why move work out of the request?** Latency, reliability (failures don't roll back the
  response), and automatic retries.
- **Why pass an ID instead of the object? ⭐** Arguments are serialised; an object is a stale
  snapshot by the time the worker runs.
- **What's the `transaction.on_commit` race? ⭐⭐** The worker can pick up the task before the
  transaction commits and fail to find the row.
- **Why must tasks be idempotent?** Delivery is at-least-once — a crash after work but before
  ack causes redelivery.
- **`acks_late` — what does it trade?** Reliability (survives worker crashes) for the risk of
  duplicate execution.
- **Redis vs RabbitMQ vs Kafka? ⭐** Simplicity vs delivery guarantees/routing vs replayable
  event streaming.
- **Is Celery event-driven architecture?** No — it's a command queue: point-to-point, producer
  names the consumer, no replay.
- **How do you stop long jobs blocking short ones?** Separate queues with dedicated workers.
- **Why never call `.get()` in a view?** It blocks a web worker on another worker and can
  deadlock; return 202 and poll.
- **How do you monitor a queue?** Depth, latency, failure rate — growing depth means
  under-provisioned workers.
- **What happens to in-flight tasks during a deploy?** Workers run old code until restarted, so
  task signatures must stay backwards compatible across one deploy.
