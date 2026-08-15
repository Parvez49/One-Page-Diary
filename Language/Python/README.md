# Python — Index

Domain knowledge for **senior/staff backend interviews** and production work. Assumes fluency
in the syntax — the focus is on *how CPython actually behaves*, the traps, and the answers
that separate "I write Python" from "I understand Python."

**Conventions:** ⭐ = high interview value · ⚠️ = a trap that causes real bugs ·
every file ends with an **Interview points** section.

---

## Files

| File | Covers | Interview weight |
|---|---|---|
| [execution_model.md](execution_model.md) | Bytecode & the PVM, **call by object reference**, refcounting + GC, **the GIL**, LEGB, imports | ⭐⭐⭐ |
| [data_model.md](data_model.md) | Dunder protocols, `__repr__`, **`__eq__`/`__hash__` contract**, mutability, operator overloading, **descriptors**, `__slots__` | ⭐⭐⭐ |
| [data_structures.md](data_structures.md) | **Complexity table**, list/dict/set internals, `collections`, comprehensions, strings | ⭐⭐⭐ |
| [functions.md](functions.md) | Signature grammar, **closures & late binding**, **decorators**, `functools`, EAFP | ⭐⭐⭐ |
| [oop.md](oop.md) | Classes, `@property`, **MRO & `super()`**, ABCs, mixins, **composition vs inheritance**, singleton, dataclasses | ⭐⭐⭐ |
| [iterators.md](iterators.md) | Iteration protocol, **generators & streaming**, `itertools`, **context managers** | ⭐⭐⭐ |
| [concurrency.md](concurrency.md) | **Threads vs processes vs asyncio**, locks & races, IPC costs, event-loop traps | ⭐⭐⭐ |
| [pitfalls.md](pitfalls.md) | **Mutable defaults**, late binding, `is` vs `==`, shallow copy, floats, exhausted iterators | ⭐⭐⭐ |
| [typing.md](typing.md) | Modern syntax, **variance**, generics, **Protocols**, static vs runtime validation | ⭐⭐ |
| [performance.md](performance.md) | **Profiling (`py-spy`)**, algorithmic wins, memory, **N+1 queries**, when to go native | ⭐⭐ |
| [modules.md](modules.md) | Imports, **`src/` layout**, venv & lockfiles, stdlib toolkit, `enum`, pytest | ⭐⭐ |
| [interview.md](interview.md) | **Q&A across every topic** + rapid fire | ⭐⭐⭐ |

---

## Suggested study order

1. **[execution_model.md](execution_model.md)** — the GIL and object references explain half
   the other answers. Start here.
2. **[pitfalls.md](pitfalls.md)** — the fastest ROI in the whole directory; these get asked
   verbatim.
3. **[data_structures.md](data_structures.md)** — complexity is the difference between working
   code and code that survives production data.
4. **[functions.md](functions.md)** + **[oop.md](oop.md)** — decorators, closures, MRO and
   `super()` are staple mid/senior questions.
5. **[concurrency.md](concurrency.md)** — the threads/processes/asyncio choice is the classic
   senior discriminator.
6. **[iterators.md](iterators.md)** — "process a file bigger than RAM" comes up constantly.
7. **[data_model.md](data_model.md)** — descriptors and the hash/eq contract mark the top of
   the range.
8. **[typing.md](typing.md)**, **[performance.md](performance.md)**,
   **[modules.md](modules.md)** — how you work, not just what you know.
9. **[interview.md](interview.md)** — rehearse out loud the day before.

---

## The senior answers worth memorising

| Question | Short answer |
|---|---|
| Compiled or interpreted? | **Both** — compiled to bytecode, interpreted by the CPython VM. |
| Pass by value or reference? | Neither: **call by object reference**. Mutate = visible, rebind = not. |
| What is the GIL? | One mutex per interpreter around **bytecode**; released during I/O and in C extensions. |
| Does the GIL make code thread-safe? | **No** — `x += 1` is three opcodes. |
| Threads vs processes vs asyncio | Waiting → threads · computing → processes · waiting at scale → asyncio. |
| Mutable default argument | Evaluated **once at `def` time**; use `None`. |
| `[lambda: i for i in range(3)]` | `[2,2,2]` — **late binding**; bind with `lambda i=i:`. |
| `is` vs `==` | Identity vs value; small-int interning makes `is` look right. |
| Set vs list membership | **O(1)** vs **O(n)** — the most common real speedup. |
| What does `super()` do? | Next class in the **MRO**, not necessarily the parent. |
| Defined `__eq__`, object unhashable | `__eq__` sets `__hash__ = None`; define both. |
| File bigger than RAM | **Generator pipeline** — one line at a time. |
| `__exit__` returns `True` | **Suppresses the exception** — usually a bug. |
| Are type hints enforced? | No — static checkers only; validate untrusted data at runtime. |
| App is slow | Profile (`py-spy`) → fix the **algorithm**/query count → then micro-optimise. |
| Pythonic singleton | **A module** — cached in `sys.modules`, thread-safe by construction. |

---

## Related directories

`../go/` · `../c_cpp.md` · `../JavaScript/` — other languages ·
`../../SDLC/` design patterns, SOLID, architecture · `../../Database/` SQL & ORM ·
`../../linux/` shell, processes, git · `../../Algorithm/` DSA · `../../Web/` frameworks
