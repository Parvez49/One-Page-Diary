# Types of Software Projects & Business Models

> Useful in interviews for two reasons: it shows **domain awareness**, and it lets you answer
> *"what kind of systems have you worked on?"* with the vocabulary the interviewer uses.
> Each type comes with its **own set of hard technical problems** — that's the part to remember.

---

## Quick Comparison

| Type | Who pays | Who uses | Defining technical challenge |
|---|---|---|---|
| **SaaS** | Subscribing company | That company's staff | **Multi-tenancy** + billing |
| **B2B** | A business | Employees of another business | **RBAC**, org hierarchy, integrations |
| **B2C** | End user (or ads) | Millions of consumers | **Scale**, latency, real-time |
| **ERP** | Enterprise | Internal departments | Breadth of modules, data integrity |
| **CRM** | Sales org | Sales & support teams | Pipeline modelling, reporting |
| **FinTech** | Consumers/businesses | Anyone moving money | **Correctness, security, compliance** |
| **Marketplace** | Both sides + commission | Buyers & sellers | Two-sided liquidity, matching, payouts |

---

## 1. SaaS — Software as a Service

Cloud-based software on a **subscription model**, usually **multi-tenant** (many companies,
one shared application).

**Examples:** Slack, Notion, Zoom, Stripe, Shopify
**Scenario:** a project management tool where companies create workspaces, manage teams and
tasks, and pay monthly.

**Core technical concerns**
- **Multi-tenancy strategy** ⭐ — the defining architectural decision:

| Strategy | Isolation | Cost | Best for |
|---|---|---|---|
| **Shared DB, shared schema** (`tenant_id` column) | Lowest | **Cheapest**, easiest to scale | Many small tenants |
| **Shared DB, schema per tenant** | Medium | Medium | Mid-market |
| **DB per tenant** | **Highest** | Expensive, hard to migrate | Enterprise, regulated, big customers |

  > ⚠️ With a shared schema, a **single missing `tenant_id` filter leaks another company's
  > data** — the classic catastrophic SaaS bug. Enforce it at the framework layer
  > (row-level security, a base queryset/manager), never per-query by hand.

- **Subscription & billing** — plans, tiers, seats, trials, proration, upgrades/downgrades,
  dunning (failed payments), invoices, taxes/VAT. Usually Stripe + webhooks.
- **Feature flags / entitlements** per plan (Free vs Pro vs Enterprise).
- **Usage metering** for usage-based pricing.
- **Onboarding & self-service signup**, since there's no salesperson in the loop.
- **Noisy-neighbour problem** — one heavy tenant degrading everyone → rate limits and quotas per tenant.

**Key metrics to know:** MRR/ARR, churn, CAC, LTV, ARPU.

---

## 2. B2B — Business to Business

Software one business uses to serve another business.

**Examples:** AWS, Salesforce, Twilio, SAP

**Core technical concerns**
- **Organisation-based access**: `Organization → Teams → Users` hierarchy.
- **RBAC / permissions** — Admin, Manager, Staff, Viewer; often custom roles per customer.
- **SSO / SAML / SCIM** — enterprise buyers *require* Okta/Azure AD integration and automated
  user provisioning. Frequently a deal-blocker.
- **Audit logs** — who did what, when. Non-negotiable for compliance.
- **SLAs & uptime guarantees** with financial penalties.
- **Compliance:** SOC 2, ISO 27001, GDPR, data residency.
- **Integrations & webhooks** — B2B products live inside other systems.
- Long sales cycles → **customisation pressure** ("we'll buy it if you add X") is the main
  engineering risk; resist forking per customer, use configuration.

---

## 3. B2C — Business to Consumer

Software used directly by end users.

**Examples:** Facebook, Instagram, Netflix, Uber, Foodpanda

**Core technical concerns**
- **High traffic & horizontal scale** — millions of concurrent users, aggressive caching, CDN.
- **Low latency** — every 100 ms costs conversion; p99 matters more than average.
- **Real-time updates** — WebSockets, push notifications, live feeds.
- **Personalisation & recommendations** (ML ranking, feed generation).
- **Mobile-first** — offline support, sync, battery/data constraints.
- **Performance optimisation** — image optimisation, lazy loading, bundle size.
- **A/B testing & analytics** baked into everything.
- **Abuse & moderation** — spam, bots, fraud, content moderation at scale.
- **Availability over consistency (AP)** — a slightly stale like count is fine; downtime is not.

---

## 4. ERP — Enterprise Resource Planning

A large internal system managing whole-company operations in one integrated data model.

**Examples:** SAP, Oracle NetSuite, Odoo, Microsoft Dynamics

**Modules:** HR & Payroll · Inventory & Warehouse · Accounting & Finance · Sales & Purchase ·
Production/Manufacturing · Procurement · Assets

**Core technical concerns**
- **Data integrity above all** — double-entry accounting, strict transactional correctness.
- **Complex domain modelling** — a single "Product" means different things to sales,
  warehouse and finance.
- **Workflow & approval chains** (purchase requisition → approval → PO → GRN → invoice → payment).
- **Fiscal periods, multi-currency, multi-company, multi-warehouse.**
- **Heavy reporting** — separate OLAP/warehouse so reports don't crush the OLTP database.
- **Migration & legacy data** is usually the hardest part of the project.

**❌ Why ERP projects famously fail:** enormous scope, deep customisation, business-process
change resistance, and data migration from decades-old systems.

---

## 5. CRM — Customer Relationship Management

Focused on customer data and the sales process.

**Examples:** Salesforce, HubSpot, Zoho

**Core objects:** Leads → Contacts → Accounts → **Opportunities** → Deals → Activities
**Core concerns**
- **Sales pipeline** modelling and stage transitions (a **State pattern** fit).
- **Lead scoring & assignment rules**, territory management.
- **Email/calendar/telephony integration**; activity timelines.
- **Deduplication & data quality** — the perennial CRM problem.
- **Forecasting & dashboards.**
- **Highly customisable schemas** — customers add their own fields → EAV or JSONB modelling
  trade-offs (flexible vs queryable).

---

## 6. FinTech

Financial technology products.

**Examples:** PayPal, Stripe, Wise, bKash, Nagad, digital wallets, lending platforms
**Scenario:** a digital wallet with balance, transfers and transaction history.

**Core technical concerns ⭐ (highest bar of any category)**
- **Correctness is absolute** — money can never be created or lost.
  - Use **integer minor units** (cents/paisa) or `Decimal`. **Never floats** — `0.1 + 0.2 != 0.3`.
  - **Double-entry bookkeeping** — every transaction is balanced debits and credits; the
    balance is derived from an immutable ledger, not an updatable column.
  - **Idempotency keys** — a retried request must never double-charge.
  - **Optimistic locking / row locks** to prevent double-spend race conditions.
- **Immutable audit trail** — records are appended, never updated or deleted (a natural fit for
  **event sourcing**).
- **Security & compliance:** **KYC/AML**, PCI-DSS (never store raw card data — tokenise),
  encryption at rest and in transit, 2FA, fraud detection.
- **Reconciliation** — daily matching against bank/processor statements to catch drift.
- **Distributed transactions** — cross-service money movement needs the **Saga** pattern with
  compensating transactions.
- **Regulatory reporting**, transaction limits, sanctions screening.

> 🗣️ Great interview line: *"In FinTech I'd choose **CP over AP** — I'd rather reject a
> transaction during a partition than allow a double-spend. Availability can be apologised for;
> a lost 10 000 taka cannot."*

---

## 7. Other Categories Worth Knowing

| Type | Description | Defining challenge |
|---|---|---|
| **Marketplace** | Connects buyers & sellers (Uber, Airbnb, Daraz) | Two-sided liquidity, matching, split payments, ratings, geo-search |
| **E-commerce** | Direct online selling (Shopify stores) | Inventory accuracy, cart/checkout, payments, order lifecycle |
| **EdTech** | Learning platforms (Coursera) | Video delivery/DRM, progress tracking, assessments |
| **HealthTech** | Clinical systems | **HIPAA**, PHI privacy, interoperability (HL7/FHIR), high stakes |
| **IoT** | Connected devices | Intermittent connectivity, time-series data volume, OTA firmware updates, edge compute |
| **Gaming** | Real-time multiplayer | Latency, state sync, cheat prevention, matchmaking |
| **DevTools / API-first** | Stripe, Twilio, Auth0 | Developer experience, SDKs, docs, versioning, backward compatibility forever |
| **Internal Tools** | Admin panels, ops dashboards | Speed of delivery over polish; access control |

---

## 8. Common Interview Questions

- **Q: What kind of project have you worked on?**
  → Name the **category**, then the **hard problem you solved in it**. *"A B2B SaaS product —
  the interesting part was multi-tenancy: we used a shared schema with row-level security so
  a missing tenant filter couldn't leak data across customers."* That's far stronger than
  listing your tech stack.

- **Q: How does the domain change your architecture?**
  → FinTech pushes toward **CP, strong consistency, immutable ledgers**. B2C pushes toward
  **AP, caching, eventual consistency**. ERP pushes toward **a single integrated relational
  model with strong transactions**. The business requirement drives the CAP choice, not preference.

---

**Related:** [system_design.md](system_design.md) · [architecture.md](architecture.md) · `../CyberSecurity/`
