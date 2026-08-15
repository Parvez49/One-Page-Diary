# Engineering Process — Code Review, Git, Tech Debt, Versioning

> This is the "how a real team actually works" file. Interviewers use these questions to check
> whether you've worked on a **team** or only on solo projects.

---

## 1. Git Branching Strategies ⭐

### GitFlow
```
main     ──●──────────────────●──────────▶  (production, tagged releases)
            ╲                ╱ ╲
hotfix       ╲              ╱   ●──────▶
              ╲            ╱
release        ╲      ●───●
                ╲    ╱
develop  ────●───●──●────────●──────────▶  (integration branch)
              ╲ ╱          ╱
feature        ●──────────●
```
**Branches:** `main` (production) · `develop` (integration) · `feature/*` · `release/*` · `hotfix/*`

- **✅ Pros:** clear structure, supports **multiple versions in production**, dedicated release
  stabilisation window, good for scheduled releases.
- **❌ Cons:** ⚠️ **heavy** — long-lived branches mean **painful merges** and delayed integration;
  hostile to continuous delivery; too much ceremony for web apps. Its own author now
  recommends against it for most teams.
- **📌 Use for:** versioned/installed software (desktop apps, mobile SDKs, on-prem releases).

### GitHub Flow
```
main ──●────●────●────●────●──▶  (always deployable)
        ╲  ╱      ╲  ╱
         ●●        ●●            short-lived feature branches → PR → merge → deploy
```
One rule: **`main` is always deployable.** Branch → commit → PR → review → merge → deploy immediately.
- **✅ Pros:** simple, fast feedback, ideal for **CD and SaaS**.
- **❌ Cons:** needs strong CI and test coverage; no built-in support for multiple live versions.
- **📌 Use for:** web apps / SaaS deploying multiple times a day. **Best default.**

### Trunk-Based Development
Everyone commits to `main` (trunk) at least daily; branches live **hours**, not days.
Unfinished work is hidden behind **feature flags**.
- **✅ Pros:** ⚠️ **merge conflicts nearly disappear** — the root cause is branch age. Highest
  deployment frequency; the DORA-research-backed choice for elite performers.
- **❌ Cons:** demands excellent automated tests + feature flags + discipline; flags accumulate
  as their own debt if never cleaned up; scary without a strong CI safety net.

### GitLab Flow
GitHub Flow + environment branches (`main` → `staging` → `production`) or release branches.
Good middle ground when you need a controlled promotion path.

| | GitFlow | GitHub Flow | Trunk-Based |
|---|---|---|---|
| Branch lifetime | Weeks | Days | **Hours** |
| Release cadence | Scheduled | Continuous | Continuous |
| Merge pain | High | Low | **Minimal** |
| CI requirement | Moderate | Strong | **Very strong** |
| Feature flags | Optional | Helpful | **Required** |

---

## 2. Merge vs Rebase vs Squash

| | **Merge** | **Rebase** | **Squash merge** |
|---|---|---|---|
| History | Preserved, with merge commits | Linear, rewritten | One commit per PR |
| Readability | Noisy graph | **Clean linear** | **Cleanest** |
| Traceability | Full detail | Full detail | Individual commits lost |
| Risk | Safe | ⚠️ **Never rebase a shared/pushed branch** — it rewrites history others have | Safe |
| Revert | Revert the merge commit | Harder | **Easiest** — revert one commit |

**Practical rule:** rebase your **own** feature branch onto latest `main` before opening a PR
(keeps history clean, resolves conflicts early), then **squash-merge** the PR into `main`.
Never rebase `main` or any branch someone else has pulled.

**Conventional Commits:**
```
feat(auth): add password reset via email
fix(cart): prevent negative quantity on decrement
docs(readme): document env vars
refactor|test|chore|perf|build|ci
BREAKING CHANGE: <description>     ← triggers a major version bump
```
**✅ Why:** enables automated changelogs and **semantic-release** version bumping, and makes
`git log` scannable.

---

## 3. Code Review

### What to actually look for (in priority order)
1. **Correctness** — does it do what the ticket says? Edge cases, off-by-one, null/empty.
2. **Security** — injection, authz checks, secrets in code, unvalidated input, IDOR.
3. **Tests** — do they exist, and do they test *behaviour* (would they fail if the logic broke)?
4. **Design** — right place for this logic? Duplication? Will this be painful in 6 months?
5. **Performance** — **N+1 queries** ⭐, missing indexes, unbounded loops, memory growth.
6. **Readability** — naming, function length, dead code, misleading comments.
7. **Style** — ⚠️ this should be **automated** (linter/formatter), never debated in review.

### Giving good feedback
| ❌ Don't | ✅ Do |
|---|---|
| "This is wrong." | "This breaks if `items` is empty — should we return 0 or raise?" |
| "Why did you do it this way?" (reads as attack) | "What made you choose a list here over a set? Wondering about lookup cost." |
| Blocking a PR over a preference | Prefix with **nit:** — "nit: could inline this, non-blocking" |
| Reviewing a 2 000-line PR line by line | Ask for it to be split; then review properly |

- Review the **code, not the person** ("this function" not "you").
- **Explain the why**, and link docs — reviews are teaching moments.
- Approve with minor comments rather than blocking; trust people to address nits.
- **As the author:** small PRs (< 400 lines — review effectiveness collapses past that),
  a clear description with context and screenshots, self-review first, respond to every comment.

**✅ Benefits:** catches bugs early, spreads knowledge (**bus factor**), enforces standards,
onboards juniors.
**❌ Costs:** ⚠️ **PR latency blocks the team** — a review sitting for 2 days is a bigger cost
than the bug it catches; bikeshedding on trivia; can become a power/gatekeeping dynamic.
*Mitigation:* SLA on review time (e.g. within 4 working hours), automate all style checks,
pair-programming as an alternative for complex work.

---

## 4. Technical Debt

> Shipping a suboptimal solution now, accepting future interest payments (slower changes, more bugs).

### The Technical Debt Quadrant (Martin Fowler)
| | **Reckless** | **Prudent** |
|---|---|---|
| **Deliberate** | "We don't have time for design" 🚩 | "Ship now, refactor after launch — we accept the cost" ✅ |
| **Inadvertent** | "What's layering?" (ignorance) 🚩 | "Now we know what we should have done" ✅ (unavoidable, healthy) |

**Types:** code debt · architecture debt · **test debt** · documentation debt · dependency debt
(unpatched/outdated libs — also a **security** issue) · infrastructure debt.

**How to manage it**
- **Make it visible** — track debt items as real backlog tickets, not tribal knowledge.
- **Budget it** — reserve ~10–20% of each sprint. Debt work that must "win" against features
  never gets prioritised.
- **Boy Scout Rule** — leave code cleaner than you found it; opportunistic small cleanups.
- **Prioritise by pain × frequency** — only refactor code you keep touching. Ugly code that
  nobody edits costs nothing.
- **Never do a big-bang rewrite** — prefer the **Strangler Fig** (incrementally replace).

> 🗣️ **How to sell it to management:** never say "the code is ugly." Say *"this module causes
> 40% of our production incidents and doubles our estimates for anything touching checkout."*
> Translate debt into **cost, risk and delivery speed**.

---

## 5. Versioning — Semantic Versioning (SemVer)

```
    MAJOR . MINOR . PATCH        e.g. 2.4.1
      │       │       └── backward-compatible BUG FIXES
      │       └────────── backward-compatible NEW FEATURES
      └────────────────── BREAKING changes
```
- `1.0.0` signals the first stable public API. `0.x.y` means anything can change.
- Pre-release: `2.0.0-beta.1` · Build metadata: `2.0.0+20260815`.
- **Ranges:** `^1.2.3` = any `1.x.x` ≥ 1.2.3 (minor+patch) · `~1.2.3` = `1.2.x` only (patch).
- ⚠️ **Always commit a lock file** (`package-lock.json`, `poetry.lock`, `requirements.txt` with
  pins) — otherwise "works on my machine" is guaranteed.

**Calendar Versioning (CalVer)** — `2026.08.1`, used by Ubuntu, pip. Good when there's no
meaningful API contract.

**API deprecation policy:** announce → `Deprecation`/`Sunset` headers → support both versions
for a stated window → remove. Never break an API silently.

---

## 6. Documentation

| Doc | Purpose |
|---|---|
| **README** | What it is, how to run it, how to contribute. The first thing anyone reads |
| **ADR** (Architecture Decision Record) ⭐ | *Context → Decision → Consequences* for one significant decision. **Immutable** — superseded, never edited |
| **API docs** | OpenAPI/Swagger, generated from code so they can't drift |
| **Runbook** | "The queue is backing up — here's what to do at 3 a.m." |
| **Postmortem** | **Blameless** incident analysis: timeline, root cause, action items |
| **Onboarding guide** | Fastest way to reduce ramp-up time |

> **Best practice:** documentation lives **next to the code** and is updated in the same PR.
> A wiki in a separate tool is stale within a month. Prefer self-documenting code +
> comments explaining **why**, not what.

---

## 7. Working Practices

**Pair / Mob programming** — *✅* instant review, knowledge sharing, fewer defects; *❌* two
people's time, exhausting, not for routine work.

**DevOps & CI/CD** — CI: every push builds and runs tests. CD: every green build is deployable
(delivery) or auto-deployed (deployment).
**Deployment strategies:** blue-green (instant rollback, 2× infra) · **canary** (5% of traffic
first, best risk/cost balance) · rolling (gradual, no extra infra, slow rollback) ·
**feature flags** (decouple deploy from release — the most powerful of the four).

**The 4 DORA metrics** ⭐ — the standard measure of team performance:
1. **Deployment frequency** · 2. **Lead time for changes** · 3. **Change failure rate** ·
4. **MTTR** (mean time to restore). Elite teams deploy on demand with < 1 h lead time and
< 15% failure rate.

**Incident management:** detect → triage/severity → mitigate (**restore service first, root
cause later**) → communicate → **blameless postmortem** → action items with owners.

---

## 8. Common Interview Questions

- **Q: You disagree with a reviewer. What do you do?**
  → Ask for their reasoning first — they may know context you don't. Present data (benchmark,
  spec, docs) rather than opinion. If it's a preference, defer; if it's correctness or security,
  escalate to a third opinion. **Never** let a PR rot in a comment war — take it to a 5-minute call.

- **Q: How do you handle a production outage?**
  → **Mitigate first** (roll back / disable the feature flag), communicate status to
  stakeholders, *then* investigate root cause. Write a blameless postmortem with concrete
  action items and owners. Blame kills the reporting culture that prevents the next outage.

- **Q: How do you review a PR in code you don't know?**
  → Start with the ticket and the PR description, then read the tests — they tell you the
  intended behaviour. Ask questions rather than assuming; "I don't understand this" is itself
  valid feedback, because the next maintainer won't either.

- **Q: When would you rewrite instead of refactor?**
  → Almost never for a whole system (Netscape's rewrite is the cautionary tale). Justified only
  when the platform is genuinely dead (unsupported language/runtime), or the module is small
  and well-bounded. Otherwise **strangle it** incrementally so you keep shipping throughout.

---

**Related:** [agile.md](agile.md) · [testing.md](testing.md) · [sdlc_models.md](sdlc_models.md) · `../CICD/` · `../Deploy/`
