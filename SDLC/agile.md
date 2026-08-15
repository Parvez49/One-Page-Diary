# Agile, Scrum & Kanban

> **Agile** is a time-boxed, iterative approach to software development that delivers the
> product **incrementally** instead of all at once — so feedback arrives early and change is cheap.

```
Functionality ──▶ Plan ──▶ Implement ──▶ Test ──▶ Review
                   ▲                                │
                   │                    Satisfactory?│
                   │                       │        │
                   └──── No ───────────────┘   Yes ─┴──▶ Build / Release
```

---

## 1. The Agile Manifesto — 4 Values

> *"We value the items on the left **more**, but there is value in the items on the right."*
> ⚠️ Common mistake in interviews: saying Agile means "no documentation". It means **less
> ceremony, not zero rigour**.

| We value… | …over… |
|---|---|
| **Individuals and interactions** | processes and tools |
| **Working software** | comprehensive documentation |
| **Customer collaboration** | contract negotiation |
| **Responding to change** | following a plan |

### The 12 Principles (grouped, so they're memorable)

- **Customer** — early & continuous delivery of valuable software; welcome changing requirements even late.
- **Delivery** — deliver working software frequently (weeks, not months); working software is the primary measure of progress.
- **People** — business & devs work together daily; build projects around motivated individuals; face-to-face conversation is best.
- **Sustainability** — maintain a constant pace indefinitely (no death marches).
- **Excellence** — continuous attention to technical excellence & good design; simplicity (maximising work *not* done).
- **Improvement** — self-organising teams; the team reflects & tunes its behaviour regularly.

---

## 2. Scrum

The most widely used Agile framework. Scrum = **3 roles + 3 artifacts + 5 events**.

### 🧑‍🤝‍🧑 The 3 Roles

| Role | Responsible for | **NOT** responsible for |
|---|---|---|
| **Product Owner (PO)** | *What* & *why*. Owns and prioritises the Product Backlog, maximises value, is the single voice of the customer. | Telling devs *how* to build it, or assigning tasks |
| **Scrum Master (SM)** | The *process*. Facilitates events, removes blockers, coaches the team, shields it from outside interference. | Being a manager/boss — it is a **servant-leader**, not a team lead |
| **Development Team** | *How*. Cross-functional (dev + QA + design), self-organising, 3–9 people. Owns the Sprint Backlog & estimates. | Being told task-by-task what to do |

> ⭐ **Trap question:** *"Is the Scrum Master the project manager?"* → **No.** The SM has no
> authority over the team, doesn't assign work, and doesn't own the schedule. Those
> responsibilities are split: scope/priority → PO, execution → the team.

### 📦 The 3 Artifacts

| Artifact | What it is | Owner |
|---|---|---|
| **Product Backlog** | Ordered, living list of *everything* that might be needed. Refined continuously. | Product Owner |
| **Sprint Backlog** | The subset of items the team commits to this sprint + the plan to deliver them. | Development Team |
| **Increment** | The sum of all completed backlog items — must be **potentially shippable** and meet the DoD. | Development Team |

### 🔁 The 5 Events (Ceremonies)

| Event | When | Time-box (2-wk sprint) | Purpose |
|---|---|---|---|
| **Sprint** | The container | 1–4 weeks (usually 2) | Deliver a usable increment |
| **Sprint Planning** | Day 1 | ≤ 4 h | Pick items & define the Sprint Goal. Answers *what* + *how* |
| **Daily Scrum / Standup** | Every day | **15 min**, same time & place | Sync & surface blockers |
| **Sprint Review** | Last day | ≤ 2 h | **Demo** the increment to stakeholders, gather feedback → adapt the *product* |
| **Sprint Retrospective** | After review | ≤ 1.5 h | Inspect the *team & process*, pick 1–2 improvements → adapt the *process* |
| *(Backlog Refinement)* | Ongoing | ~10% of capacity | Not officially an event — groom, estimate, split upcoming items |

**Daily Standup — the 3 questions:**
1. What did I do yesterday?  2. What will I do today?  3. What is **blocking** me?

> ⚠️ It is a **sync**, not a status report to the manager. Problem-solving is deferred to a
> "parking lot" discussion after the 15 minutes.

> ⭐ **Review vs Retrospective** (very commonly confused):
> **Review = the product**, stakeholders present, "did we build the right thing?"
> **Retrospective = the process**, team only, "how can we work better?"

---

## 3. User Stories

**Format:**
```
As a <role>, I want <goal / capability>, so that <benefit / why>.
```
**Example:**
> *As a registered customer, I want to save my card details, so that I can check out
> without re-entering them.*

### INVEST — what makes a good story

| Letter | Means | Smell if violated |
|---|---|---|
| **I**ndependent | Can be built in any order | Story blocked by 3 others |
| **N**egotiable | A conversation starter, not a spec | Story reads like a 5-page contract |
| **V**aluable | Delivers value to a *user* | "Refactor the DAO layer" (no user value) |
| **E**stimable | Team understands it enough to size it | "Make it scalable" |
| **S**mall | Fits comfortably in one sprint | Story carried over 3 sprints |
| **T**estable | Clear pass/fail | "It should be fast" |

### Acceptance Criteria vs Definition of Done ⭐

| | **Acceptance Criteria (AC)** | **Definition of Done (DoD)** |
|---|---|---|
| Scope | **Per story** — unique to it | **Global** — same for every story |
| Written by | Product Owner | The whole team, agreed once |
| Answers | "Does this story do what was asked?" | "Is this work *finished* to our quality bar?" |
| Example | *Given* invalid card, *when* submitted, *then* show "card declined" | Code reviewed, unit tests pass, CI green, docs updated, deployed to staging |

**Gherkin / BDD style AC:**
```gherkin
Given I am a logged-in customer with a saved card
When  I click "Buy now"
Then  the order is placed without asking for card details
```

---

## 4. Estimation

### Story Points
A **relative** measure of *effort + complexity + uncertainty* — **not hours**.

- Usually a **Fibonacci** scale: `1, 2, 3, 5, 8, 13, 21` — gaps widen because big things are inherently less precise.
- Anything ≥ 13 → it is an **Epic**; split it.

**✅ Why points instead of hours?**
- Removes the "8 hours for me = 3 hours for a senior" problem — points are team-relative.
- People are bad at absolute estimates but good at **comparison** ("this is twice that").
- Stops estimates being treated as commitments/deadlines.

**❌ Drawback:** meaningless across teams (Team A's 5 ≠ Team B's 5); easily abused by
management as a productivity metric, which corrupts it (teams inflate points).

### Planning Poker
Everyone estimates privately, reveals simultaneously, and the **outliers explain their reasoning**.
The value is the *discussion* that surfaces hidden complexity — not the number.

### Velocity
Story points **completed** (meeting DoD) per sprint. Averaged over ~3 sprints → forecasting tool.

> ⚠️ Velocity is a **planning aid, not a performance metric**. Comparing velocity between
> teams is meaningless, and targeting velocity guarantees inflation.

---

## 5. Kanban

Continuous flow — no sprints, no fixed iterations. Pull work when there is capacity.

```
┌──────────┬────────────┬───────────┬────────────┬──────┐
│ Backlog  │ To Do (3)  │ Doing (2) │ Review (2) │ Done │
├──────────┼────────────┼───────────┼────────────┼──────┤
│ ▩ ▩ ▩ ▩ │ ▩ ▩        │ ▩ ▩       │ ▩          │ ▩ ▩  │
└──────────┴────────────┴───────────┴────────────┴──────┘
                          ▲ WIP limits in ()
```

### Core practices
- **Visualise the workflow** — the board is the single source of truth.
- **Limit WIP (Work In Progress)** — the heart of Kanban. A column at its limit **blocks new
  work**, forcing the team to finish (or unblock) before starting more.
- **Manage flow** — track *Lead Time* (request → delivered) and *Cycle Time* (started → delivered).
- **Continuous improvement**.

**Why WIP limits matter:** multitasking is the silent killer. 5 items at 80% done deliver
**zero value**; 4 finished + 1 in progress delivers 4. WIP limits also make **bottlenecks
visible** — the column that's always full is your constraint.

### Scrum vs Kanban ⭐

| | **Scrum** | **Kanban** |
|---|---|---|
| Cadence | Fixed sprints (1–4 wks) | Continuous flow |
| Release | End of sprint | Anytime |
| Roles | PO, SM, Dev Team (prescribed) | No prescribed roles |
| Commitment | Team commits to a sprint scope | No sprint commitment |
| Change mid-cycle | Discouraged — sprint scope is protected | Allowed anytime — just re-prioritise the queue |
| Key metric | Velocity | Cycle time / throughput |
| Board resets | Each sprint | Persistent |
| **Best for** | Feature/product teams with plannable work | **Support, ops, maintenance** — unpredictable, interrupt-driven work |

> **Scrumban** = Kanban's WIP limits + flow applied on top of Scrum ceremonies. Common in
> teams that do both feature work and production support.

---

## 6. Scaling & Common Failure Modes

**Scaling frameworks** (know the names): **SAFe** (heavy, enterprise), **LeSS** (lightweight
multi-team Scrum), **Spotify Model** (squads/tribes/chapters/guilds — an *anecdote*, not a framework).

**⚠️ "Dark Agile" / anti-patterns worth naming in an interview:**
- Standup turned into a **status report** to a manager.
- Retrospectives held but **no action items ever executed** → team stops caring.
- **Velocity used as a KPI** → point inflation, quality drops.
- **No Definition of Done** → "done" means "works on my machine".
- Sprint scope changed mid-sprint every sprint → the sprint stops meaning anything.
- Ceremonies kept, values dropped — *"we do Agile"* instead of *"we are agile"*.

---

## 7. Common Interview Questions

- **Q: How do you handle a requirement change mid-sprint?**
  → Protect the sprint by default: add it to the Product Backlog for the next sprint. If it's
  genuinely urgent, the PO must **trade out** equivalent work — scope in, scope out. If it
  invalidates the Sprint Goal entirely, the sprint can be **cancelled** (PO's call, rare).

- **Q: What if the team can't finish a story by sprint end?**
  → It does **not** count toward velocity. Move it back to the backlog and re-estimate the
  remainder. Never mark it "80% done" — partial work has no value. Then ask *why* in the retro.

- **Q: How do you deal with a teammate who is silent in retros?**
  → Use written/anonymous formats first (sticky notes, Retrium), then round-robin so everyone
  speaks. Silence usually signals a **psychological safety** problem, not disinterest.

---

**Related:** [sdlc_models.md](sdlc_models.md) · [principles.md](principles.md) · [process.md](process.md)
