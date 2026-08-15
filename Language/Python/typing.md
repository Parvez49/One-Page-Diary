# Type Hints & Static Typing

> Runtime validation at boundaries: **[modules.md](modules.md)** · ABCs vs Protocols: **[oop.md](oop.md)**

---

## 1. What hints are (and aren't) ⭐

```python
def greet(name: str, times: int = 1) -> str:
    return f"hi {name} " * times

greet(42, "x")        # ⚠️ RUNS FINE — Python does NOT enforce hints
```

⭐⭐ **Type hints are not enforced at runtime.** They're metadata stored in
`__annotations__`, consumed by **static checkers** (mypy, pyright/Pylance, ty), IDEs, and
libraries that *choose* to read them (Pydantic, FastAPI, dataclasses, attrs).

**Why bother, then?** The senior answer: they catch a whole class of bug before the code
runs, they make refactoring across a large codebase safe, and they're the only documentation
that can't silently go stale. On a 100k-line service the payoff is large; on a 200-line
script it isn't.

---

## 2. Modern syntax (3.9+ / 3.10+)

```python
# ⭐ Built-in generics — no more typing.List/Dict (3.9+)
def process(items: list[str], lookup: dict[str, int]) -> tuple[int, ...]: ...

# ⭐ Union with | (3.10+)
def find(id: int) -> User | None: ...        # was Optional[User]
value: int | str

from typing import Any, Callable, Iterable, Iterator, Literal, Final, TypeAlias

handler: Callable[[str, int], bool]          # (args) -> return
mode: Literal["r", "w", "a"]                 # ⭐ exact allowed values
MAX: Final = 100                             # never reassigned
UserId: TypeAlias = int                      # (3.12: `type UserId = int`)
```

⚠️ **`Optional[X]` means `X | None`, not "optional argument."** A parameter with a default is
optional; `Optional` is purely about `None` being allowed.

⚠️ **`Any` disables checking entirely** for that value — it's an escape hatch, and every
`Any` is a hole in your type coverage. Prefer `object` when you truly mean "anything" and
will narrow before use.

```python
from __future__ import annotations           # ⭐ lazy evaluation of annotations

class Node:
    def clone(self) -> Node: ...             # self-reference without quotes
```

---

## 3. Variance — the part people get wrong ⭐

```python
def total(nums: list[float]) -> float: ...
total([1, 2, 3])          # ⚠️ mypy error: list[int] is not list[float]
```

**Mutable containers are invariant.** `list[int]` is *not* a `list[float]`, because the
function could append a `float` and corrupt the caller's list of ints.

⭐ **The rule: accept the most general type, return the most specific.**

```python
from collections.abc import Iterable, Sequence, Mapping

def total(nums: Iterable[float]) -> float:        # ⭐ accepts list, tuple, set, generator
    return sum(nums)
```

Use `Iterable`/`Sequence`/`Mapping` (covariant, read-only) in **parameters**; use concrete
`list`/`dict` in **return types**.

---

## 4. Generics & TypeVar

```python
from typing import TypeVar, Generic

T = TypeVar("T")

def first(items: Sequence[T]) -> T | None:        # ⭐ relates input to output
    return items[0] if items else None

class Repository(Generic[T]):                     # pre-3.12 syntax
    def get(self, id: int) -> T | None: ...
    def add(self, item: T) -> None: ...

class UserRepo(Repository[User]): ...
```

```python
# ⭐ 3.12+ — much cleaner
def first[T](items: Sequence[T]) -> T | None: ...
class Repository[T]:
    def get(self, id: int) -> T | None: ...
```

```python
Num = TypeVar("Num", int, float)          # constrained: ONLY these
S = TypeVar("S", bound=Shape)             # ⭐ bounded: Shape or any subclass
```

⭐ Without a TypeVar, `def first(items: list) -> Any` tells the checker nothing. The TypeVar
is what carries "whatever went in comes out."

---

## 5. Protocols — structural typing ⭐⭐

```python
from typing import Protocol, runtime_checkable

class Closeable(Protocol):
    def close(self) -> None: ...

def cleanup(resource: Closeable) -> None:     # ⭐ ANY object with .close()
    resource.close()
```

⭐⭐ **This is duck typing made checkable.** A class satisfies a Protocol by *having the right
methods* — no inheritance, no registration, and it works on third-party classes you can't
modify. It's the type-system expression of "if it quacks like a duck."

| | **ABC** | **Protocol** |
|---|---|---|
| Relationship | nominal — must inherit | ⭐ structural — just match the shape |
| Third-party classes | must be `.register()`ed | ✅ work automatically |
| Enforcement | runtime, at instantiation | static; `@runtime_checkable` for a shallow `isinstance` |
| Use when | you own the hierarchy and want enforcement | you're typing a duck-typed interface |

⚠️ `@runtime_checkable` only checks **method names exist** — not signatures or types.

---

## 6. Narrowing & special forms

```python
def handle(x: int | str | None) -> str:
    if x is None:
        return "none"          # narrowed to None
    if isinstance(x, int):
        return str(x + 1)      # ⭐ narrowed to int
    return x.upper()           # narrowed to str

from typing import assert_never
def area(s: Shape) -> float:
    match s:
        case Circle(): return ...
        case Square(): return ...
        case _: assert_never(s)     # ⭐ compile-time EXHAUSTIVENESS check
```

```python
from typing import TypedDict, NotRequired, Self, overload, cast

class UserDict(TypedDict):              # ⭐ typing real dicts (JSON payloads)
    name: str
    age: NotRequired[int]

class Builder:
    def add(self, x: int) -> Self:      # ⭐ 3.11+ — correct for subclasses
        return self

@overload
def get(k: str) -> str: ...
@overload
def get(k: str, default: T) -> str | T: ...
def get(k, default=None): ...           # the real implementation

value = cast(User, raw)                 # ⚠️ tells the checker to trust you; no runtime check
```

⭐ `assert_never` turns "I added a new enum variant and forgot a branch" into a **type error
at check time** — genuinely valuable in large codebases.

---

## 7. Static vs runtime validation ⭐

**They solve different problems, and the distinction is a good senior answer:**

| | Static (mypy) | Runtime (Pydantic) |
|---|---|---|
| When | before the code runs | as data arrives |
| Catches | wrong types in **your** code | bad **external** data |
| Cost | CI time | per-request CPU |

⭐ **Use both, at different layers:** type hints throughout the codebase, and *runtime*
validation at every trust boundary — HTTP request bodies, config files, message payloads,
third-party API responses. Hints alone will not stop a JSON body with `"age": "abc"`.

```python
from pydantic import BaseModel, Field, field_validator

class UserIn(BaseModel):
    name: str = Field(min_length=1)
    age: int = Field(ge=0, le=150)
    email: str

    @field_validator("email")
    @classmethod
    def check_email(cls, v: str) -> str:
        if "@" not in v: raise ValueError("invalid email")
        return v

UserIn(**request.json())        # ⭐ raises ValidationError with a precise field path
```

---

## 8. Tooling

```bash
mypy src/ --strict              # ⭐ strict is where the value is
pyright src/                    # faster; what Pylance runs in VS Code
ruff check . && ruff format .   # ⭐ linter + formatter, replaces flake8/isort/black
```

```ini
# pyproject.toml
[tool.mypy]
python_version = "3.12"
strict = true
warn_unreachable = true

[[tool.mypy.overrides]]         # ⭐ untyped third-party libs
module = ["legacy.*"]
ignore_errors = true
```

⭐ **Adopting types on an existing codebase:** don't attempt a big-bang conversion. Start
non-strict, type **new code and public function signatures** first, enable `strict` per
module via overrides, and gate it in CI so coverage only moves forward. `# type: ignore[code]`
with the specific error code — never a bare ignore.

---

## 9. Interview points

- **Are type hints enforced at runtime?** No — they're metadata for static checkers and
  libraries that opt in.
- **Then what's the value?** Bugs caught before running, safe large-scale refactors, and
  documentation that can't drift; the payoff scales with codebase size.
- **`Optional[X]` — what does it mean?** `X | None`. Unrelated to whether the argument has a
  default.
- **Why can't I pass `list[int]` where `list[float]` is expected?** Mutable generics are
  invariant. Accept `Iterable[float]` instead.
- **ABC vs Protocol?** Nominal (must inherit) vs structural (matching methods suffice);
  Protocols type third-party and duck-typed code.
- **What is a `TypeVar` for?** Expressing that input and output types are related, instead of
  degrading to `Any`.
- **`Any` vs `object`?** `Any` silences the checker entirely; `object` is the top type and
  forces you to narrow before use.
- **How do hints relate to Pydantic/FastAPI?** Those libraries *read* the annotations and
  generate runtime validation and OpenAPI schemas from them.
- **Static checking vs runtime validation?** Static verifies your code's internal consistency;
  runtime validation guards untrusted data at boundaries. You need both.
- **How would you introduce typing to a legacy codebase?** Incrementally: new code and public
  APIs first, per-module strictness, CI gate to prevent regression.
