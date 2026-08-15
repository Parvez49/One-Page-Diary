# Modules, Packaging & Stdlib Toolkit

> Import machinery: **[execution_model.md](execution_model.md)** · Type checking config: **[typing.md](typing.md)**

---

## 1. Modules & packages

- **Module** — one `.py` file.
- **Package** — a directory of modules (with `__init__.py`; without it, it's a *namespace
  package*, which works but silently breaks tooling assumptions).

```python
import json                       # module object
from pathlib import Path          # a name from a module
from . import sibling             # ⭐ explicit relative (inside a package only)
from ..core import utils
import numpy as np                # alias
```

⚠️ **Never `from module import *`** — it pollutes the namespace, shadows builtins
unpredictably, and makes it impossible to tell where a name came from. `__all__` limits what
`*` exports if you're forced to support it.

**Import order (PEP 8), what `ruff`/`isort` enforce:** stdlib → third-party → local, each
group separated by a blank line.

⭐ **Absolute over relative imports** for anything but tightly-coupled siblings — relative
imports break the moment a module is run as a script.

⚠️ **`python module.py` vs `python -m package.module`** — the first puts the *file's*
directory on `sys.path` and sets `__package__` to `None`, so relative imports fail with
`attempted relative import with no known parent package`. **Use `-m`** for anything inside a
package.

**Circular imports** — see [execution_model.md §6](execution_model.md). Fixes: import inside
the function, import the module rather than the name, or extract the shared piece.

---

## 2. Project layout ⭐

```
myproject/
├── pyproject.toml          ⭐ the single source of truth (PEP 621)
├── README.md
├── src/                    ⭐ src-layout — see below
│   └── myapp/
│       ├── __init__.py
│       ├── __main__.py     enables `python -m myapp`
│       ├── core/
│       └── api/
├── tests/
└── .env                    ⚠️ never committed
```

⭐ **Use `src/` layout.** Without it, `import myapp` picks up the *source directory* rather
than the installed package — so your tests pass against uninstalled code and you discover
missing files only after publishing. The `src/` layout forces an actual install
(`pip install -e .`), which means you test what users get.

```toml
# pyproject.toml
[project]
name = "myapp"
version = "0.1.0"
requires-python = ">=3.11"
dependencies = ["httpx>=0.27", "pydantic>=2.0"]

[project.optional-dependencies]
dev = ["pytest", "mypy", "ruff"]

[project.scripts]
myapp = "myapp.cli:main"          # ⭐ creates a console command on install

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"
```

---

## 3. Environments & dependencies

```bash
python -m venv .venv && source .venv/bin/activate     # stdlib, always available
pip install -e ".[dev]"                                # ⭐ editable + dev extras
pip freeze > requirements.txt                          # ⚠️ see below

uv venv && uv pip install -e ".[dev]"                  # ⭐ uv — 10-100× faster
uv sync                                                # lockfile-driven
```

⭐ **Why virtual environments at all:** every project pins different versions; a global
install guarantees that upgrading one project breaks another. One env per project, always.

⚠️⚠️ **`pip freeze > requirements.txt` is not dependency management.** It flattens direct and
transitive dependencies into one undifferentiated list with no record of *why* anything is
there, and it's platform-specific. Declare **direct** dependencies with ranges in
`pyproject.toml`, and generate a **lockfile** (`uv.lock`, `poetry.lock`, `pip-tools`) for
reproducible installs.

| Tool | Note |
|---|---|
| `venv` + `pip` | stdlib, universally available, no locking |
| **`uv`** | ⭐ current best — resolver + installer + version manager, extremely fast |
| `poetry` | mature, integrated packaging + locking |
| `pipx` | install *applications* (black, httpie) in isolated envs |
| `conda` | scientific stacks with non-Python binary deps |

**Version pinning:** `~=1.2.3` (compatible patch) · `>=1.2,<2.0` (SemVer-safe) · `==1.2.3`
(exact — lockfiles only). ⭐ Ranges in `pyproject.toml`, exact pins in the lockfile.

**Config & secrets:**

```python
import os
DEBUG = os.getenv("DEBUG", "false").lower() == "true"   # ⚠️ env vars are ALWAYS strings
DB_URL = os.environ["DATABASE_URL"]                     # ⭐ fail loudly if missing
```

⚠️ Secrets belong in environment variables or a secret manager — **never** in source,
`settings.py`, or a committed `.env`. See [../../linux/git_interview.md](../../linux/git_interview.md)
for what to do when one leaks.

---

## 4. Stdlib worth reaching for ⭐

```python
# ---- paths: pathlib, not os.path ----
from pathlib import Path
p = Path("data") / "raw" / "file.csv"        # ⭐ operator-based joining
p.exists(); p.stem; p.suffix; p.parent
p.read_text(encoding="utf-8")
for f in Path("logs").rglob("*.log"): ...    # ⭐ recursive glob

# ---- dates: ALWAYS timezone-aware ----
from datetime import datetime, timezone, timedelta
datetime.now(timezone.utc)                   # ⭐⭐ not datetime.now()
from zoneinfo import ZoneInfo                # 3.9+, stdlib
dt.astimezone(ZoneInfo("Asia/Dhaka"))

# ---- structured collections ----
from collections import defaultdict, Counter, deque, ChainMap
from itertools import chain, islice, groupby, batched

# ---- json / csv ----
json.dumps(obj, default=str, indent=2)       # ⭐ default= handles datetime/Decimal
csv.DictReader(f)

# ---- logging (never print in libraries) ----
import logging
log = logging.getLogger(__name__)            # ⭐ per-module logger
log.info("processed %s rows", n)             # ⭐ LAZY formatting — not f-string
log.exception("failed")                      # ⭐ inside except: includes traceback

# ---- other ----
from functools import cache, partial, wraps, cached_property
import subprocess; subprocess.run([...], check=True, capture_output=True)  # ⚠️ no shell=True
import secrets      # ⭐ tokens/passwords — NOT `random`, which is predictable
import uuid, hashlib, base64, re, textwrap, tempfile, shutil, argparse
```

⚠️⚠️ **`datetime.now()` returns a naive datetime** — no timezone. Comparing naive and aware
datetimes raises `TypeError`, and storing naive UTC "works" until DST or a server in another
region. **Store UTC, aware; convert only for display.**

⚠️ **Use `%s` lazy formatting in logs, not f-strings.** `log.debug(f"...")` formats the string
even when DEBUG is disabled — measurable in hot paths, and it breaks log aggregation by
message template.

⚠️ **`random` is not cryptographically secure** — use `secrets` for tokens, passwords, and
session IDs.

⚠️ **`subprocess` with `shell=True` and user input is a shell injection.** Pass a list of
arguments.

---

## 5. `enum` ⭐

```python
from enum import Enum, IntEnum, StrEnum, auto, unique

@unique                              # ⭐ reject duplicate values
class Status(Enum):
    PENDING  = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"

Status.PENDING.value       # "pending"
Status.PENDING.name        # "PENDING"
Status("pending")          # ⭐ lookup by value
list(Status)               # iterable
```

**Why:** named constants beat magic strings — typo-proof (`Status.APROVED` is an
`AttributeError`, `"aproved"` is a silent bug), self-documenting, exhaustively checkable by
mypy (`assert_never`), and centralised.

```python
class Priority(IntEnum):     # ⭐ comparable and orderable as ints
    LOW = 1
    HIGH = 3
Priority.HIGH > Priority.LOW      # True

class Env(StrEnum):          # ⭐ 3.11+ — is a str, so JSON/DB serialisation just works
    PROD = "prod"
```

⭐ `StrEnum`/`IntEnum` members *are* `str`/`int`, so they drop straight into APIs, ORM
columns, and JSON without `.value` everywhere — that's usually what you want for a
persisted field.

---

## 6. Testing essentials

```python
# tests/test_service.py
import pytest

@pytest.fixture
def client():
    c = Client(); yield c; c.close()          # ⭐ setup / teardown around yield

@pytest.mark.parametrize("value,expected", [(1, 2), (2, 4), (0, 0)])
def test_double(value, expected):
    assert double(value) == expected          # ⭐ 3 tests, one function

def test_raises():
    with pytest.raises(ValueError, match="positive"):
        Circle(-1)

def test_api(mocker):                          # pytest-mock
    mocker.patch("myapp.service.requests.get", return_value=FakeResp())
```

```bash
pytest -x -q --cov=myapp --cov-report=term-missing
```

⭐ **Patch where the name is *used*, not where it's defined** — `myapp.service.requests.get`,
not `requests.get`. Getting this backwards is the most common reason a mock "doesn't work."

More on testing strategy: [../../SDLC/testing.md](../../SDLC/testing.md).

---

## 7. Interview points

- **What is a virtual environment and why?** An isolated interpreter + site-packages per
  project, so version requirements can't collide.
- **Is `pip freeze` good dependency management?** No — it flattens transitive deps with no
  intent recorded. Declare direct deps with ranges; lock for reproducibility.
- **Why the `src/` layout?** It prevents importing uninstalled source, so tests run against
  what ships.
- **`python file.py` vs `python -m pkg.file`?** `-m` imports it as part of the package, so
  relative imports and `__package__` work.
- **How do you avoid a circular import?** Import inside the function, import the module not
  the name, or extract shared code — usually it signals a design problem.
- **Why `getLogger(__name__)`?** Per-module loggers give hierarchical control and show the
  origin in output.
- **Why lazy `%s` logging?** Avoids formatting cost when the level is disabled and keeps
  message templates stable for aggregation.
- **`random` vs `secrets`?** `random` is a deterministic PRNG; `secrets` is
  cryptographically secure — use it for anything security-relevant.
- **Why is `datetime.now()` a problem?** It's naive; store timezone-aware UTC and convert for
  display.
- **Why use `Enum`?** Typo-proof named constants with iteration, value lookup, and static
  exhaustiveness checking.
- **Where do you patch in a test?** At the point of *use* in the module under test.
