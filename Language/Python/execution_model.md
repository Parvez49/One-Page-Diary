# CPython Execution Model — Bytecode, Memory, GC

> Concurrency consequences: **[concurrency.md](concurrency.md)** · Object protocol: **[data_model.md](data_model.md)**

---

## 1. What happens when you run `python hello.py`

```python
# hello.py
print("hello world")
```

```
source .py
    │  tokenize + parse
    ▼
AST  (abstract syntax tree)          ← `ast.parse()` exposes this
    │  compile
    ▼
bytecode (code objects)              ← cached in __pycache__/*.pyc
    │
    ▼
PVM — the CPython eval loop          ← a giant switch over opcodes
    │
    ▼
C function calls / CPU
```

```python
import ast, dis
print(ast.dump(ast.parse("print('hi')")))
dis.dis("print('hi')")
```

```
  LOAD_NAME     0 (print)
  LOAD_CONST    0 ('hi')
  CALL          1
  POP_TOP
```

⭐ **Python is compiled *and* interpreted.** Source → **bytecode** (compilation) →
executed by a **virtual machine** (interpretation). Saying "Python is interpreted, not
compiled" is the answer that costs you points; the accurate phrasing is *"compiled to
bytecode, which the CPython VM interprets."*

**`.pyc` caching:** bytecode is written to `__pycache__/module.cpython-312.pyc` and reused
when the source's mtime/size is unchanged. It saves **parse+compile** time only — never
execution time. ⚠️ The top-level script itself is **never cached**, only imported modules.

**Implementations worth naming:** **CPython** (reference, C), **PyPy** (JIT — often 5×
faster on long-running pure-Python loops), **Cython**/**mypyc** (compile to C extensions),
**Jython**/**IronPython** (JVM/.NET), **MicroPython**. "The GIL" is a *CPython*
implementation detail, not a language rule — a genuinely senior distinction.

⭐ **Python 3.11+ is meaningfully faster** thanks to the "adaptive specializing interpreter"
(inline caches, quickened opcodes), 3.12 added a per-interpreter GIL, and **3.13 ships an
experimental free-threaded build (PEP 703)** that removes the GIL entirely. Knowing this
signals you follow the language, not just use it.

---

## 2. Names, objects, and references ⭐⭐

**Python has no variables in the C sense.** A name is a binding in a namespace dict pointing
at an object on the heap. Assignment **rebinds a name**; it never copies an object.

```python
a = [1, 2, 3]
b = a            # b is a SECOND NAME for the SAME object
b.append(4)
print(a)         # [1, 2, 3, 4]   ⚠️ not a copy
print(a is b)    # True — same identity
```

**Argument passing: "call by object reference"** (or *call by sharing*) — neither call by
value nor call by reference:

```python
def f(lst, num):
    lst.append(1)      # MUTATES the caller's object  → visible outside
    num += 1           # REBINDS a local name         → invisible outside
    lst = [99]         # REBINDS too                  → caller unaffected

data, n = [], 0
f(data, n)
print(data, n)         # [1] 0
```

⭐ **The rule to state:** the function receives a reference to the same object. **Mutating**
it is visible to the caller; **rebinding** the parameter is not. Whether an argument "acts
like" pass-by-value depends entirely on whether the object is mutable.

**Identity vs equality:**

```python
a = [1, 2];  b = [1, 2]
a == b       # True  → __eq__: same VALUE
a is b       # False → different objects
id(a), id(b) # distinct memory addresses
```

⚠️ **Integer/string caching makes `is` lie.** CPython interns small ints (**−5..256**) and
some strings, so `256 is 256` → `True` but `257 is 257` → `False` (in a REPL). Never use
`is` for value comparison; reserve it for `None`, `True`, `False`, and sentinels.

---

## 3. Memory management

### Reference counting — the primary mechanism

Every object carries a refcount; when it drops to **zero** the object is freed
**immediately and deterministically**.

```python
import sys
x = []
sys.getrefcount(x)      # 2 — one for x, one for getrefcount's own argument ⚠️
```

**Why refcounting:** memory is reclaimed the moment the last reference disappears — no
pauses, and `__del__`/file closing is predictable. **The cost:** every assignment touches a
counter (slow, and a **cache-line contention nightmare across threads** — this is a core
reason the GIL exists, see §4).

### The cycle collector — the backup

Refcounting alone leaks on **reference cycles**:

```python
a = {};  b = {}
a['b'] = b;  b['a'] = a       # refcount never reaches 0
del a, b                      # ⚠️ unreachable but still allocated
```

The **generational GC** finds these. Three generations (0, 1, 2); objects surviving a
collection are promoted, and older generations are scanned less often — based on the
*generational hypothesis* that most objects die young.

```python
import gc
gc.collect()              # force a full collection
gc.get_stats()
gc.freeze()               # ⭐ pre-fork: move current objects out of GC's view
gc.disable()              # only with a real measurement to justify it
```

⭐ **`gc.freeze()` before forking workers** (gunicorn/uwsgi) is a real optimisation: without
it, the GC touches refcounts on shared pages and **copy-on-write breaks**, ballooning memory
across every worker.

⚠️ The GC only handles **container** cycles. It cannot collect a cycle whose members define
`__del__` in old Pythons (fixed in 3.4+), and it never sees objects held by C extensions.

### Allocator layers

```
your object  →  pymalloc (arenas → pools → blocks, for objects ≤ 512 bytes)
             →  malloc / mmap (larger objects)
```

⚠️ **Freed memory is often not returned to the OS.** pymalloc keeps arenas for reuse, so RSS
stays high after a spike — a memory *high-water mark*, not a leak. The reliable fix for a
process that peaked is to restart the worker (`max_requests` in gunicorn).

**Interning:** small ints (−5..256) and identifier-like strings are pre-created and shared.
`sys.intern(s)` forces it — genuinely useful when you compare millions of repeated strings.

---

## 4. The GIL ⭐⭐⭐

**A single mutex that lets only one thread execute Python bytecode at a time**, per
interpreter.

**Why it exists:** it makes refcounting safe without a lock on every object, keeps the C API
simple for extension authors, and makes single-threaded code fast. Removing it naively slows
single-threaded performance by ~30% — which is why every previous attempt was rejected.

**Consequences:**

| Workload | Threads help? | Why |
|---|---|---|
| **CPU-bound** (math, parsing, compression) | ❌ **no** — often *slower* | only one thread runs bytecode; you add switching overhead |
| **I/O-bound** (HTTP, DB, disk) | ✅ **yes** | ⭐ the GIL is **released during blocking I/O** |
| **C extensions** (NumPy, `hashlib`) | ✅ often | well-written extensions release the GIL around heavy C work |

⭐ **The precise statement:** the GIL prevents Python *bytecode* from running in parallel. It
does **not** prevent parallelism inside C code or during syscalls — which is exactly why
NumPy operations and network calls scale across threads while a pure-Python loop does not.

⚠️ **The GIL does not make your code thread-safe.** `counter += 1` is
`LOAD → ADD → STORE`; a thread switch between those opcodes loses updates. You still need
`threading.Lock`. (Switches happen every ~5 ms — `sys.setswitchinterval()`.)

**Escapes:** `multiprocessing` (separate interpreters), C extensions that release it,
`asyncio` for I/O concurrency, sub-interpreters (PEP 554), and the **free-threaded 3.13+
build**. See [concurrency.md](concurrency.md).

---

## 5. Namespaces & scope — LEGB

```
Local → Enclosing → Global → Builtins
```

```python
x = "global"
def outer():
    x = "enclosing"
    def inner():
        print(x)          # "enclosing" — found in E before G
    inner()
```

```python
count = 0
def bad():
    count += 1            # ⚠️ UnboundLocalError
```

⭐ **Assignment anywhere in a function makes the name local for the whole function** — the
compiler decides scope statically, so the read on the right-hand side fails before the
assignment runs. Fix with `global count` or, better, return a value.

```python
def counter():
    n = 0
    def inc():
        nonlocal n        # ⭐ rebind in the ENCLOSING scope, not global
        n += 1
        return n
    return inc
```

Namespaces are dicts: `globals()`, `locals()`, `vars(obj)`, `obj.__dict__`.

---

## 6. Import system

```
import x  →  sys.modules cache?  →  yes: return it (⭐ modules are SINGLETONS)
                                 →  no: find via sys.path → load → EXECUTE top level
                                     → store in sys.modules → bind the name
```

⭐ **A module's top-level code runs exactly once per process.** That's the idiomatic Python
singleton (see [oop.md](oop.md)) and the reason a module-level `logging.basicConfig()` or DB
connection is created once no matter how many places import it.

```python
import sys
sys.modules.keys()
sys.path            # search order: script dir / cwd, PYTHONPATH, site-packages
```

⚠️ **Shadowing stdlib** — a local `random.py` or `queue.py` breaks imports across the whole
project, because the script's own directory comes **first** on `sys.path`.

**Circular imports** — `a` imports `b` which imports `a`, and the second import gets a
half-initialised module (`ImportError: cannot import name X`). Fixes: move the import inside
the function, import the *module* rather than the name (`import a` then `a.thing`), or
extract the shared piece into a third module. ⭐ In practice a circular import is a design
smell — two modules that want to be one.

`if __name__ == "__main__":` — `__name__` is `"__main__"` only for the entry script, and the
module's real name when imported. ⭐ On Windows/macOS `multiprocessing` **requires** this
guard: workers re-import the module, and without it they re-execute your spawn code and fork
bomb.

---

## 7. Interview points

- **Is Python compiled or interpreted?** Both — compiled to bytecode, then interpreted by
  the CPython VM. Bytecode is cached in `__pycache__`.
- **Pass by value or reference?** Neither: **call by object reference**. Mutations are
  visible to the caller, rebinding is not.
- **`is` vs `==`?** Identity vs value. Use `is` only for `None`/sentinels; small-int and
  string interning makes `is` deceptively "work" on values.
- **How does Python manage memory?** Reference counting first (immediate, deterministic),
  plus a **generational cycle collector** for reference cycles, on top of pymalloc arenas.
- **Why is memory not released back to the OS?** pymalloc retains arenas; RSS reflects the
  high-water mark. Restart workers periodically.
- **What is the GIL and why does it exist?** One mutex per interpreter around bytecode
  execution; it makes refcounting cheap and the C API simple.
- **Does the GIL make code thread-safe?** **No** — `x += 1` is three opcodes and can be
  interrupted between them.
- **When do threads still help?** I/O-bound work and C extensions, because both release the
  GIL while blocking.
- **What is `UnboundLocalError`?** You assigned to a name somewhere in the function, making
  it local everywhere in that function, then read it before assignment.
- **`global` vs `nonlocal`?** Module scope vs the nearest enclosing *function* scope.
- **Why is `if __name__ == "__main__"` required for multiprocessing?** Spawned children
  re-import the module; without the guard they re-run the spawning code recursively.
