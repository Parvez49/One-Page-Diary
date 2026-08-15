# Interview Process & Behavioural Prep

---

## 1. The Hiring Pipeline

```
Resume ──▶ Recruiter ──▶ Technical ──▶ Onsite Loop ──▶ Hiring ──▶ Offer
 screen      call         screen        (4–5 rounds)   committee
   │           │             │               │             │
 ~10s        30 min       45–60 min      4–6 hours      days–weeks
```

### 1. Initial Screening & Application
- **Resume screening** — the first filter, often ~10 seconds of attention. Highlight relevant
  skills, **quantified impact**, and keywords matching the job description (ATS systems filter on these).
- **Recruiter call** — role, team, timeline, **salary expectations** (see §6), visa/notice period.
  Non-technical, but it *is* an evaluation. Have a crisp 90-second "tell me about yourself".

### 2. Phone Screen(s)
- **Technical phone screen** — coding/algorithms, problem-solving, sometimes language-specific
  questions. Usually a shared editor.
- **Behavioural phone screen** — soft skills, past experience, how you handle situations.

### 3. On-Site / Virtual Loop
- **4–5 interviews** with different team members, **45–60 min** each.
- **Coding assessment** — some roles use an online test (HackerRank/Codility) before or instead.
- Typical loop composition:

| Round | What's assessed | Prepare with |
|---|---|---|
| **Coding / DSA** (1–2) | Problem solving, complexity, clean code | `../Algorithm/` |
| **System Design** | Trade-offs, scale, architecture (mid+ level) | [system_design.md](system_design.md) |
| **Domain / Deep dive** | Your actual stack — Django, DB, API design | `../Language/`, `../Database/` |
| **Behavioural / Culture** | Collaboration, conflict, ownership | §3 below |
| **Hiring manager** | Motivation, seniority, team fit | §5 questions |

### 4. Hiring Committee & Final Steps
- **Hiring committee recommendation** — reviews written feedback from all interviewers
  (why interviewers type while you talk — your reasoning must be *audible*).
- **Senior leader / executive review**
- **Team matching** — common at large companies; you may talk to several teams.
- **Compensation discussion** → **Offer**

---

## 2. Coding Interview — How to Behave ⭐

> They are evaluating **how you think**, not whether you memorised the answer. A working
> brute-force with clear communication beats a silent optimal solution.

**The 6-step approach**
1. **Repeat the problem** in your own words — confirm you understood it.
2. **Ask clarifying questions.** Input size? Sorted? Duplicates? Empty input? Negative numbers?
   Unicode? Can I mutate the input? *Never start coding immediately.*
3. **Walk through an example** by hand, including an edge case.
4. **State a brute-force solution + its complexity**, then optimise out loud:
   *"This is O(n²); I can trade space for time with a hash map to get O(n)."*
5. **Code it** — talk while you type. Meaningful names, small helper functions.
6. **Test it yourself** — trace through your example, then edge cases: empty, single element,
   all duplicates, max size, overflow. **State the final time & space complexity.**

**🚩 What loses offers:** silence; coding before clarifying; ignoring hints (a hint is the
interviewer *helping* — take it); not testing; arguing when told there's a bug; giving up.

**If you're stuck:** say what you're stuck on — *"I'm trying to avoid the nested loop; let me
think about what I could precompute."* Thinking aloud while stuck scores better than freezing.

---

## 3. Behavioural Interviews — the STAR Method ⭐

```
S — Situation   Context. Where, when, who. (~15%)
T — Task        Your specific responsibility & the goal. (~15%)
A — Action      What YOU did, step by step. ⭐ THE CORE (~55%)
R — Result      Outcome, ideally QUANTIFIED + what you learned. (~15%)
```

**Example — "Tell me about a time you handled a production incident":**
> **S:** *"At my last role our checkout API started returning 500s during a Friday sale — about
> 8% of requests."*
> **T:** *"I was on call and owned restoring service."*
> **A:** *"I checked our dashboards and saw DB connections maxed out. Rather than debug live, I
> first rolled back the release from two hours earlier, which restored service in ~10 minutes.
> Then I traced it to a new endpoint doing a query inside a loop — a classic N+1 — that was
> exhausting the connection pool. I fixed it with a prefetch, added a test asserting the query
> count, and added an alert on pool utilisation."*
> **R:** *"Downtime was 12 minutes instead of hours. The query-count assertion has since caught
> two similar regressions in CI. My takeaway was to mitigate first and diagnose second — I'd
> initially wanted to find the root cause before rolling back."*

**⚠️ Rules**
- Say **"I"**, not "we". They're hiring you, not your team. Credit others, but be specific about *your* action.
- **Quantify** — "reduced p95 latency from 800 ms to 120 ms", "cut deploy time by half".
- Keep it to **2–3 minutes**. Ask *"would you like more detail on any part?"*
- **Always end with the learning**, especially for failure questions.
- Prepare **6–8 stories** and map them to multiple questions — one good story covers conflict,
  ownership *and* failure depending on framing.

### Story bank — prepare one for each
| Theme | Question it answers |
|---|---|
| **Biggest achievement** | "Proudest project?" · "Biggest impact?" |
| **Failure / mistake** ⭐ | "Tell me about a time you failed." *(Own it fully. No "my weakness is perfectionism".)* |
| **Conflict with a teammate** | "Disagreed with a colleague?" |
| **Disagreed with a manager/decision** | "Pushed back on a decision?" |
| **Tight deadline / pressure** | "Delivered under pressure?" |
| **Learned something fast** | "New technology quickly?" |
| **Difficult technical problem** | "Hardest bug you've debugged?" |
| **Leadership / mentoring** | "Helped a teammate grow?" |
| **Handled ambiguity** | "Unclear requirements?" |
| **Feedback received** | "Tough feedback and what you did?" |
| **Went beyond scope** | "Above and beyond?" |

> **Failure questions are a trap only if you dodge them.** Choose a real failure with real
> consequences, take clear ownership, and show a **concrete process change** you made after.
> "I was late once because a dependency was slow" reads as evasive.

---

## 4. Answering "Tell me about yourself"

**90-second structure:**
1. **Now** — "I'm a backend engineer, ~N years, mostly Python/Django and Postgres."
2. **How you got here** — one or two career highlights relevant *to this role*.
3. **Why here** — what specifically attracts you to this company/role.

⚠️ Not a chronological life story. Tailor point 2 to the job description every single time.

---

## 5. Questions YOU Should Ask ⭐

Never say "no, I'm good" — it reads as disinterest. Have 3–4 ready per round.

**About the role & team**
- What does a typical week look like for this role?
- What would success look like in the first 3 and 6 months?
- How is the team structured, and who would I work with most closely?

**About engineering practice** *(these signal seniority)*
- How do you balance feature work against technical debt?
- What does your deploy process look like — how often do you ship, and what's the rollback story?
- How are decisions documented — do you use ADRs or RFCs?
- What's your test coverage / on-call situation like?
- What's the biggest technical challenge the team is facing right now?

**About culture & growth**
- How is feedback given? Are there regular 1:1s?
- What does career progression look like here?
- What's something you'd change about working here? *(⭐ honest answers are very revealing)*

**Closing** — *"Is there anything about my background that gives you hesitation?"* This is a
strong move: it surfaces objections while you can still address them.

---

## 6. Compensation Discussion

**Before the call:** research market rates (Levels.fyi, Glassdoor, local salary surveys) for
your level, location and company size. Know three numbers: **target**, **acceptable
minimum**, and **walk-away**.

**Handling "what's your expected salary?"** *(often asked in the very first call)*
- **Deflect once:** *"I'd like to learn more about the scope first — do you have a budgeted
  range for this role?"*
- **If pressed, give a researched range**, not a single number, and anchor at the upper end
  of your realistic band. Say it's based on market data for the role.
- ⚠️ In many places you are not obliged to disclose current salary. Redirect to *expectations*.

**Negotiating the offer**
- **Never accept on the spot.** *"Thank you — I'm excited. Could I have a couple of days to review?"*
- Negotiate on **evidence** (market data, competing offer, scope of role), not need.
- **Total compensation** is more than base: bonus, equity, signing bonus, PTO, remote/hybrid,
  learning budget, notice period, title, start date. If base is capped, ask about the others.
- Get everything **in writing** before resigning your current job.
- Stay warm throughout — you'll work with these people.

---

## 7. Red Flags to Watch For (evaluate them too)

🚩 Vague answers about on-call load or work hours · unpaid multi-day take-homes ·
"we're like a family" · high turnover on the team · no code review or testing process ·
constant "firefighting" described as normal · pressure to accept within 24 hours ·
the interviewer clearly hasn't read your resume.

---

## 8. Preparation Checklist

**2+ weeks out**
- [ ] DSA practice — arrays, hashing, two pointers, sliding window, trees, graphs, DP (`../Algorithm/`)
- [ ] Write out 6–8 STAR stories in full
- [ ] Re-read your own resume — **be ready to defend every single line**
- [ ] Deep-dive one of your own projects: architecture, trade-offs, what you'd do differently

**Day before**
- [ ] Research the company: product, business model, recent news, engineering blog
- [ ] Prepare questions per interviewer (look them up on LinkedIn)
- [ ] Test your setup — camera, mic, IDE/editor, internet backup
- [ ] Sleep. Rested judgment beats one more practice problem.

**After**
- [ ] Send a short thank-you note within 24 h
- [ ] Write down every question you were asked — build your own question bank
- [ ] If rejected, ask for feedback (politely, once). Some companies give it.

---

**Related:** [system_design.md](system_design.md) · [principles.md](principles.md) · [agile.md](agile.md) · [process.md](process.md) · `../Algorithm/`
