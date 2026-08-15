# Concurrency — Threads, Processes, asyncio

> The GIL: **[execution_model.md](execution_model.md)** · Generators/coroutines: **[iterators.md](iterators.md)**

---

## 1. Choosing — the only decision that matters ⭐⭐

```
Is the work CPU-bound (computing) or I/O-bound (waiting)?

 CPU-bound ──▶ multiprocessing / ProcessPoolExecutor
              (or NumPy / C extensions / PyPy / Rust)

 I/O-bound ──▶ how many concurrent operations?
              ├─ tens/low hundreds ─▶ threading / ThreadPoolExecutor
              └─ thousands+         ─▶ asyncio
```

| | **threading** | **multiprocessing** | **asyncio** |
|---|---|---|---|
| Parallel CPU | ❌ (GIL) | ✅ **real cores** | ❌ single thread |
| Best for | I/O-bound, blocking libs | **CPU-bound** | ⭐ **massive** I/O concurrency |
| Memory | shared, cheap | ⚠️ separate, ~10–50 MB/process | shared, cheapest |
| Switching | **preemptive** (OS, any bytecode) | processes | ⭐ **cooperative** (only at `await`) |
| Practical scale | ~hundreds | ~cores | ⭐ **10k+** |
| Data sharing | direct (⚠️ needs locks) | IPC: pickle, queues | direct, ⭐ few races |
| Hard part | race conditions | serialisation cost, spawn overhead | ⚠️ one blocking call stalls everything |

⭐ **Say this in an interview:** *"Threads for waiting, processes for computing, asyncio for
waiting at scale."* Then justify with the GIL: it serialises **bytecode**, but is **released
during blocking I/O and inside well-written C extensions** — so threads genuinely help
I/O-bound work and genuinely don't help pure-Python CPU work.

**Concurrency vs parallelism:** concurrency = several tasks *in progress* (structure);
parallelism = several tasks *executing at once* (hardware). asyncio and threads give
concurrency; only multiprocessing gives CPU parallelism in CPython.

---

## 2. threading

```python
import threading, requests

def download(url, results, idx):
    results[idx] = requests.get(url).text        # ⭐ GIL RELEASED while waiting

threads, results = [], [None] * len(urls)
for i, url in enumerate(urls):
    t = threading.Thread(target=download, args=(url, results, i))
    t.start(); threads.append(t)
for t in threads:
    t.join()                                     # ⭐ wait for completion
```

⭐ **Prefer `concurrent.futures` to raw threads** — it handles pooling, results, and
exceptions:

```python
from concurrent.futures import ThreadPoolExecutor, as_completed

with ThreadPoolExecutor(max_workers=10) as pool:
    futures = {pool.submit(fetch, u): u for u in urls}
    for fut in as_completed(futures):            # ⭐ results as they finish
        try:
            data = fut.result()                  # ⚠️ re-raises worker exceptions HERE
        except requests.Timeout:
            log.warning("timeout on %s", futures[fut])
```

⚠️⚠️ **An exception inside a worker is silently stored, not raised** — it surfaces only when
you call `.result()`. Code that submits work and never inspects the futures swallows every
error. (`pool.map` re-raises on iteration.)

### Race conditions & locks ⭐

```python
counter = 0
def bump():
    global counter
    for _ in range(100_000):
        counter += 1        # ⚠️ LOAD, ADD, STORE — interruptible between opcodes
# result: < 200_000 with two threads
```

⭐ **The GIL does not make you thread-safe.** It guarantees one thread runs bytecode at a
time, not that a *statement* is atomic. `+=`, check-then-act, and read-modify-write all need
a lock.

```python
lock = threading.Lock()
with lock:                          # ⭐ context manager — always released
    counter += 1

threading.RLock()      # re-entrant: same thread can acquire twice (recursive code)
threading.Semaphore(5) # limit concurrent access to N
threading.Event()      # a flag: wait() / set()
threading.local()      # ⭐ per-thread storage (how DB connections stay thread-safe)
```

⚠️ **Deadlock** — two threads each holding what the other needs. Prevention: **acquire locks
in a consistent global order**, use `timeout=` on `acquire`, and keep critical sections tiny.

⭐ `queue.Queue` is already thread-safe — a producer/consumer queue usually removes the need
for explicit locks entirely. Prefer message passing to shared state.

**Daemon threads** (`daemon=True`) are killed abruptly at interpreter exit — never use them
for work that must finish.

---

## 3. multiprocessing

```python
from concurrent.futures import ProcessPoolExecutor

def crunch(chunk):                       # ⭐ must be a TOP-LEVEL function (picklable)
    return sum(x * x for x in chunk)

if __name__ == "__main__":               # ⭐⭐ REQUIRED — see below
    with ProcessPoolExecutor() as pool:  # defaults to os.cpu_count()
        totals = list(pool.map(crunch, chunks))
```

**Lower-level API:**

```python
from multiprocessing import Process, Pool, Queue, Manager, Lock, Semaphore

with Pool(processes=4) as pool:
    results = pool.map(work, items)          # blocking, ordered
    results = pool.imap_unordered(work, items)   # ⭐ lazy, as-completed
    async_r = pool.apply_async(work, args=(x,)); async_r.get(timeout=30)
```

**IPC — processes share nothing:**

| Tool | Use |
|---|---|
| `Queue` | process-safe FIFO, many-to-many |
| `Pipe` | fast 1-to-1 channel |
| `Manager().dict()/.list()` | ⭐ shared objects — convenient, **slow** (proxied over IPC) |
| `Value` / `Array` | shared C types in real shared memory |
| `shared_memory` | ⭐ 3.8+ zero-copy buffers — for NumPy-sized data |

Synchronisation mirrors threading: `Lock`, `Event`, `Semaphore`, `Barrier`.

⚠️⚠️ **The traps that make multiprocessing slower than serial code:**

1. **Everything crosses the boundary via `pickle`.** Sending a 500 MB DataFrame to 8 workers
   serialises it 8 times. ⭐ **Chunk the work, not the data** — or use `shared_memory`.
2. **`if __name__ == "__main__":` is mandatory** on Windows/macOS. The default start method
   there is **spawn**, which re-imports your module in each child; without the guard the
   children re-execute the spawning code → fork bomb.
3. **Unpicklable objects fail** — lambdas, nested functions, open sockets, DB connections,
   file handles. Create connections *inside* the worker.
4. **Process startup is ~10–100 ms and ~10–50 MB each.** Pooling many tiny tasks loses to a
   plain loop.

**fork vs spawn:** `fork` (Linux default) is fast and copy-on-write but ⚠️ **unsafe with
threads** and inherits locks in indeterminate states; `spawn` (macOS/Windows default, and
the safer choice everywhere) starts a fresh interpreter. Set it explicitly with
`multiprocessing.set_start_method("spawn")`.

⭐ **Copy-on-write is defeated by refcounting** — a forked child that merely *reads* a large
shared object touches its refcount, dirtying the page and copying it. `gc.freeze()` before
forking mitigates this.

---

## 4. asyncio ⭐⭐

**One thread, one event loop, cooperative multitasking.** A coroutine runs until it hits
`await` on something not ready, then yields control to the loop, which runs another task.

```python
import asyncio, aiohttp

async def fetch(session, url):
    async with session.get(url) as resp:      # ⭐ suspends here, loop runs others
        return await resp.json()

async def main():
    async with aiohttp.ClientSession() as session:
        results = await asyncio.gather(*(fetch(session, u) for u in urls))
    return results

asyncio.run(main())        # ⭐ 3.7+ entry point — creates and closes the loop
```

```python
async def worker(): ...

# Structured patterns
await asyncio.gather(*tasks, return_exceptions=True)   # ⭐ all, collecting errors
async with asyncio.TaskGroup() as tg:                  # ⭐⭐ 3.11+ — preferred
    tg.create_task(worker())                           # cancels siblings on failure
await asyncio.wait_for(op(), timeout=5)                # ⭐ timeout
async with asyncio.timeout(5): ...                     # 3.11+
sem = asyncio.Semaphore(20)                            # ⭐ bound concurrency
task = asyncio.create_task(bg())                       # fire off concurrently
```

⭐ **`TaskGroup` (3.11+) over bare `gather`** — it guarantees no task is left orphaned and
cancels siblings when one fails. Un-awaited `create_task` results are a classic source of
"task exception was never retrieved" warnings and lost errors.

⚠️⚠️ **One blocking call freezes the entire loop.** `time.sleep()`, `requests.get()`, heavy
CPU work, or a synchronous DB driver blocks *every* task — the single biggest asyncio
mistake:

```python
await asyncio.sleep(1)                                    # ⭐ not time.sleep(1)
await loop.run_in_executor(None, blocking_call, arg)      # ⭐ offload to a thread
await asyncio.to_thread(blocking_call, arg)               # ⭐ 3.9+ cleaner
```

⚠️ **`async` is viral.** You can only `await` inside `async def`; adopting it usually means
async drivers all the way down (`asyncpg`, `httpx`, `aioredis`). Mixing sync ORMs into an
async view is the classic FastAPI/Django-async performance bug.

**Async iteration & context managers:**

```python
async for row in cursor: ...
async with session.begin(): ...
async def gen():
    yield x                     # async generator
```

---

## 5. Practical guidance

**Web servers:** gunicorn with **`workers = 2 × cores + 1`** processes (bypasses the GIL),
each with threads or an async worker class for I/O. Processes for CPU, threads/async inside
for concurrency.

**Task queues:** for real background work use **Celery/RQ** rather than hand-rolled threads —
you get retries, persistence, and monitoring. See
[../../SDLC/architecture.md](../../SDLC/architecture.md).

**Combining:** `ProcessPoolExecutor` inside an async app for CPU work is a legitimate and
common pattern:

```python
loop = asyncio.get_running_loop()
with ProcessPoolExecutor() as pool:
    result = await loop.run_in_executor(pool, cpu_heavy, data)
```

⭐ **Measure before choosing.** Threads on a CPU-bound task can be *slower* than serial;
processes on many small tasks lose to serialisation overhead. Time the naive version first.

---

## 6. Interview points

- **Threads vs processes vs asyncio — how do you choose?** CPU-bound → processes; I/O-bound →
  threads; very high I/O concurrency → asyncio.
- **Why don't threads speed up CPU-bound Python?** The GIL serialises bytecode; you add
  switching overhead without parallelism.
- **Then why do threads help with I/O?** The GIL is **released** during blocking syscalls, so
  other threads run while one waits.
- **Does the GIL make code thread-safe?** No — `x += 1` is three opcodes and can be
  interrupted. Use locks.
- **Concurrency vs parallelism?** Tasks in progress vs tasks executing simultaneously.
- **What is a race condition, and how do you prevent it?** Unsynchronised concurrent access
  where the result depends on timing; prevent with locks, atomic queues, or by not sharing
  state.
- **How do deadlocks happen?** Circular lock waits — avoid by acquiring in a consistent order
  and using timeouts.
- **Why is multiprocessing sometimes slower?** Pickling data, ~10–100 ms process startup, and
  memory duplication can exceed the compute saved.
- **Why does multiprocessing need `if __name__ == "__main__"`?** With `spawn`, children
  re-import the module; without the guard they re-run the spawn code recursively.
- **What breaks an asyncio app?** Any blocking call in a coroutine — it stalls the whole
  event loop. Offload with `asyncio.to_thread`.
- **`asyncio.gather` vs `TaskGroup`?** `TaskGroup` (3.11+) gives structured concurrency —
  siblings cancelled on failure, no orphaned tasks.
- **How do you limit concurrency in asyncio?** `asyncio.Semaphore`, or a bounded worker pool —
  otherwise 10,000 tasks open 10,000 sockets.
