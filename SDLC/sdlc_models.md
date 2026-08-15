# SDLC — Phases & Models

> **SDLC (Software Development Life Cycle)** = the structured process a team follows to build,
> deliver and maintain software. Every methodology (Waterfall, Agile, Spiral…) is just a
> **different ordering / repetition** of the same 6 phases.

---

## 1. The 6 Phases

```
 ┌─────────────┐   ┌──────────┐   ┌──────────────┐
 │ 1. Require- │──▶│ 2. Design│──▶│ 3. Develop-  │
 │    ments    │   │          │   │    ment      │
 └─────────────┘   └──────────┘   └──────┬───────┘
                                         │
 ┌─────────────┐   ┌──────────┐   ┌──────▼───────┐
 │ 6. Maintain │◀──│5. Deploy │◀──│ 4. Testing   │
 └─────────────┘   └──────────┘   └──────────────┘
        │                                  ▲
        └──────── feedback loop ───────────┘
```

| # | Phase | What actually happens | Output (artifact) | Who owns it |
|---|-------|----------------------|-------------------|-------------|
| 1 | **Requirement Analysis** | Talk to stakeholders, find *what* to build & *why*. Split functional vs non-functional. | SRS document, user stories | BA / Product Owner |
| 2 | **Design** | Decide *how*. HLD (architecture, DB schema, APIs) then LLD (classes, functions). | HLD/LLD docs, ER diagram, API spec | Architect / Tech Lead |
| 3 | **Development** | Write the code, review it, merge it. | Source code, PRs | Developers |
| 4 | **Testing** | Verify against requirements. Unit → integration → system → UAT. | Test cases, bug reports | QA |
| 5 | **Deployment** | Ship to production (often staged: dev → staging → prod). | Release build, CI/CD pipeline | DevOps |
| 6 | **Maintenance** | Bug fixes, patches, performance tuning, new small features. | Hotfixes, changelogs | Whole team |

### Functional vs Non-Functional Requirements ⭐ *asked a lot*

| | **Functional** | **Non-Functional (NFR)** |
|---|---|---|
| Question it answers | *What* the system does | *How well* the system does it |
| Example | "User can reset password via email" | "Password reset email must arrive < 30 s" |
| More examples | Login, checkout, generate invoice | Performance, security, scalability, availability, usability |
| Failure looks like | Feature missing / wrong output | Feature works but slow, insecure, or crashes at load |

---

## 2. Waterfall Model

Sequential — each phase must **fully finish** before the next begins. No going back.

```
Requirements ▸ Design ▸ Development ▸ Testing ▸ Deployment ▸ Maintenance
    (each phase gated by a sign-off document)
```

**✅ Advantages**
- Simple, easy to manage — clear milestones & deliverables.
- Heavy documentation → good for **audit / compliance** heavy domains.
- Works well when requirements are **frozen and well understood**.
- Easy to estimate cost & timeline upfront (fixed-price contracts).

**❌ Drawbacks**
- **No working software until very late** — biggest risk.
- Change is expensive; a requirement error found in testing means redoing design + code.
- Customer sees the product only at the end → high chance of "this isn't what I wanted".
- Testing squeezed at the end, so it gets cut when the schedule slips.

**📌 Use when:** short project, stable requirements, regulated domain (medical devices, aviation, government tenders).

---

## 3. Waterfall vs Agile ⭐⭐ *classic interview question*

| Aspect | **Waterfall** | **Agile** |
|---|---|---|
| Approach | Sequential, phase-gated | Iterative & incremental |
| Delivery | One big release at the end | Working increment every 1–4 weeks |
| Requirements | Frozen upfront | Evolve continuously |
| Cost of change | **Very high** (grows over time) | **Low** (expected & welcomed) |
| Customer involvement | Start & end only | Continuous, every sprint |
| Testing | Separate phase at the end | Continuous, inside every sprint |
| Documentation | Heavy, formal | Light — "working software over comprehensive documentation" |
| Team structure | Siloed specialists, hierarchical | Cross-functional, self-organising |
| Risk visibility | Late (found in testing) | Early (found each sprint) |
| Best for | Fixed scope, compliance | Evolving product, startups, SaaS |

> **One-liner answer:** *"Waterfall optimises for predictability with fixed requirements;
> Agile optimises for adaptability when requirements will change. Waterfall discovers problems
> late and expensively, Agile discovers them early and cheaply."*

---

## 4. Other Models (know them at one-line depth)

### V-Model (Verification & Validation)
Waterfall bent into a **V** — each development phase has a matching test phase planned at the same time.

```
Requirements ─────────────────▶ Acceptance Testing (UAT)
   High-Level Design ─────────▶ System Testing
      Low-Level Design ──────▶ Integration Testing
          Coding ────────────▶ Unit Testing
```
- **✅ Pro:** testing planned early, defects caught sooner than Waterfall.
- **❌ Con:** still rigid, still no early working software.

### Iterative / Incremental
Build a small working version, then repeat and enlarge it each cycle.
- **✅ Pro:** working software early, feedback per iteration.
- **❌ Con:** needs good architecture upfront or you rewrite constantly.

### Spiral (risk-driven)
Repeating loops of **Plan → Risk Analysis → Engineer → Evaluate**.
- **✅ Pro:** best for **high-risk, large, expensive** projects — risk is explicitly analysed each loop.
- **❌ Con:** expensive, complex, needs risk-analysis expertise.

### Big Bang
No process — just start coding.
- **✅ Pro:** fine for tiny experiments / POCs / a single dev.
- **❌ Con:** unpredictable, high failure risk. Never for real products.

---

## 5. Quick Comparison Cheat Sheet

| Model | Requirements | Feedback | Risk handling | Typical use |
|---|---|---|---|---|
| Waterfall | Fixed | End only | Weak | Compliance, fixed-bid |
| V-Model | Fixed | End only | Medium (early test plan) | Embedded, safety-critical |
| Iterative | Evolving | Per iteration | Medium | Medium products |
| Spiral | Evolving | Per loop | **Strongest** | Large, high-risk |
| Agile/Scrum | Evolving | Per sprint | Strong | Product/SaaS teams |

---

## 6. Common Interview Questions

- **Q: Why can't we just skip the design phase and start coding?**
  → You can for a POC. For a product, skipping design produces an accidental architecture:
  no clear module boundaries, duplicated logic, and a rewrite within a year. Design is where
  you decide the **expensive-to-change** things (DB schema, service boundaries, API contracts).

- **Q: What's the cheapest phase to fix a bug?**
  → **Requirements.** Cost of fixing a defect grows roughly **10× per phase** it escapes into.
  A misunderstood requirement costs a conversation; the same bug found in production costs
  a hotfix, a rollback plan, and possibly customer trust.

- **Q: Can Waterfall and Agile be mixed?**
  → Yes — "**Water-Scrum-Fall**" is common in enterprises: upfront fixed budget/scope
  (waterfall), Agile sprints for the build, gated release process for deployment.

---

**Related:** [agile.md](agile.md) · [testing.md](testing.md) · [process.md](process.md)
