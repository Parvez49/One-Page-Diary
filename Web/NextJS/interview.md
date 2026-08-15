# Next.js — Interview Questions

> Claim first, then the *why*. Depth lives in the linked files.

---

## 1. Rendering

**Explain CSR, SSR, SSG, and ISR. ⭐⭐**
Where and when HTML is produced: in the browser · per request on the server · at build ·
at build **plus background regeneration**. Trade freshness and server cost against first paint
and SEO.
⭐ **The rule:** *static by default; add revalidation for scheduled change; go dynamic only when
the response depends on the request.*
→ [rendering.md](rendering.md)

**What is ISR, and why not just SSG?**
Cached HTML regenerated in the background after `revalidate` seconds. Content updates without a
rebuild, and the current visitor gets the stale page immediately — nobody waits.
⭐ On-demand (`revalidateTag` from a CMS webhook) beats a timer: it fires when content actually
changes.

**What is hydration?**
Re-running React on the client to attach event handlers to server-rendered HTML. Between paint
and hydration the page looks ready but isn't interactive — the gap RSC and streaming close.

**What is a React Server Component? ⭐⭐**
A component that runs **only on the server**, ships **zero JavaScript**, and can access the
database, files, and secrets directly. The App Router default.

**Server vs Client Component — how do you choose?**
Client only for state, effects, event handlers, or browser APIs. Everything else stays on the
server.

**What's the danger of `"use client"`? ⭐⭐**
It's a **boundary, not a file marker** — every component imported below it becomes client code.
One `"use client"` near the root ships the whole subtree and erases every RSC benefit.
⭐ Push it to the leaves; pass server-rendered markup through as `children`.

**How do you keep a page fast when one query is slow?**
`<Suspense>` streaming (or `loading.tsx`) — the shell paints immediately and the slow region
streams in.

**What silently makes a route dynamic? ⚠️**
`cookies()`, `headers()`, `searchParams`, or a `no-store` fetch **anywhere in the tree**. Check
`○ Static` vs `ƒ Dynamic` in the build output.

---

## 2. Routing

**How does App Router routing work?**
File-system based: folders are segments, only `page.tsx`/`route.ts` create URLs, so tests and
components can be colocated.

**Layout vs template? ⭐**
Layouts **persist across navigation** — scroll position, open menus, and playing media survive.
Templates remount every time (enter animations, per-page analytics).

**Why can't a layout read `searchParams`?**
It doesn't re-render when the query changes. Use a client component with `useSearchParams`.

**What are route groups, parallel routes, and intercepting routes?**
`(name)` organises without a URL segment · `@slot` renders independent panels with their own
loading/error states · `(.)path` shows a route as a modal in context while a direct visit
renders the full page.

**Why must `error.tsx` be a client component?**
Error boundaries need client-side React lifecycle, and `reset` requires an event handler.
⚠️ It doesn't catch errors in its **own** layout — that needs a boundary one level up.

**`<Link>` vs `router.push`?**
`Link` renders a real `<a>` (accessible, crawlable, middle-clickable) and prefetches; `push` is
for navigation after an action.

**What does `router.refresh()` do?**
Re-runs Server Components and merges fresh data **without discarding client state or scroll**.
→ [app_router.md](app_router.md)

---

## 3. Data & caching

**How do you fetch data in the App Router? ⭐**
`async` Server Components awaiting `fetch` or the database directly — no `useEffect`, no
loading state, no `/api` hop.

**Why not call your own `/api` route from a Server Component? ⭐**
It's an HTTP round trip to your own process. Route handlers exist for **external** consumers.

**How do you avoid a fetch waterfall?**
`Promise.all` for independent calls; separate `<Suspense>` boundaries so slow sections stream
independently.

**What caches does Next.js have? ⭐⭐**
Four: **Request Memoization** (dedupes within one render), **Data Cache** (persists across
requests and deploys), **Full Route Cache** (rendered output), and the client **Router Cache**.

**Is `fetch` cached by default?**
⚠️ **Next 14 yes, Next 15 no.** Always name the version — this reversal causes most
cache confusion.

**How do you invalidate?**
`revalidateTag` (precise, webhook-driven), `revalidatePath`, or time-based `revalidate`.

**Why does the UI show stale data after a mutation?**
The **client Router Cache** reuses a cached RSC payload — `router.refresh()` or revalidate
inside the Server Action.

**What is a Server Action? ⭐**
A `"use server"` function called directly from the client for mutations — no API route, and
`<form action={...}>` works **without JavaScript** (progressive enhancement).

**What's the security risk with Server Actions? ⭐⭐**
They compile to **public POST endpoints**. Every one must authenticate, authorise, and validate
its own input — the UI only calling it from an admin page is irrelevant.

**When do you still fetch on the client?**
Polling, real-time, infinite scroll, and heavily interactive state — SWR/TanStack Query, ideally
seeded with server-rendered `initialData`.
→ [data_fetching.md](data_fetching.md)

---

## 4. API, middleware, runtime

**When do you need a route handler? ⭐**
Only for non-Next consumers: mobile apps, third-party clients, webhooks, OAuth callbacks,
uploads, cron. Your own pages use Server Components; your own forms use Server Actions.

**What belongs in middleware — and what doesn't?**
Redirects, rewrites, i18n, feature flags, security headers. ⚠️ **Not** database access or real
authorisation.

**Is middleware enough for auth? ⚠️**
No. Edge runtime can only check that a cookie *looks* valid, and it has been bypassable
(CVE-2025-29927). Re-check at every data access point.

**Node vs Edge runtime?**
Full Node APIs and TCP database drivers, slower cold start, one region — vs Web APIs only,
near-zero cold start, globally distributed.
⚠️ Edge compute with a single-region database is often **slower**: every query crosses the
network.

**Redirect vs rewrite?**
Redirect changes the browser URL; a **rewrite is invisible** — which is how you front an
existing Django API on the same origin and avoid CORS entirely.

**Why `req.text()` for a webhook?**
Signature verification needs the exact raw bytes; `req.json()` re-serialises and breaks the
HMAC.
→ [api_middleware.md](api_middleware.md)

---

## 5. Auth & security

**Where do you enforce auth? ⭐⭐**
At the **data access point** — page, Server Action, route handler, or a shared Data Access
Layer. Middleware is a UX redirect.

**Why isn't a check in `layout.tsx` enough? ⚠️**
Layouts don't re-render on every navigation and pages can be requested directly.

**Where should a token live? ⭐**
`httpOnly` + `secure` + `sameSite` cookie. **Never `localStorage`** — any XSS, including one
from a compromised dependency, reads it.

**Cookie/JWT session vs database session?**
No per-request lookup vs **instant revocation**. Statelessness costs you "log out everywhere."

**How do you prevent IDOR?**
Scope the query by the session user (`where: { id, userId }`) instead of fetching by id and
checking afterwards; return **404**, not 403.

**How do secrets leak in Next.js? ⭐**
`NEXT_PUBLIC_` variables are inlined into the client bundle, and **anything a Server Component
passes as props is in the RSC payload** — visible in the browser. `import "server-only"` guards
secret modules.

**Are client-side role checks security?**
No — they hide UI. The server must enforce.
→ [auth.md](auth.md)

---

## 6. Performance

**What are Core Web Vitals? ⭐⭐**
**LCP** < 2.5 s (loading), **INP** < 200 ms (responsiveness — replaced FID in 2024),
**CLS** < 0.1 (stability).

**How do you improve INP? ⭐**
Ship less JavaScript: keep components on the server, code split with `next/dynamic`, defer
third-party scripts, break up long tasks. INP is where Next apps usually fail.

**How do you fix CLS?**
Explicit image dimensions (`next/image` enforces them), reserved space for late content, and
`next/font`'s size-adjusted fallback.

**What does `next/image` do?** AVIF/WebP conversion, per-device variants, lazy loading, and
reserved space — improving LCP and CLS together.
⭐ `priority` on the **LCP image only** — it preloads and disables lazy loading.

**What does `next/font` solve?** Self-hosts at build (no third-party request) and eliminates
font-swap layout shift.

**The most common Next.js performance mistake? ⭐** `"use client"` too high in the tree.
→ [performance.md](performance.md)

---

## 7. Rapid fire

| Question | Answer |
|---|---|
| App Router vs Pages Router | Server Components, nested state-preserving layouts, streaming vs all-client and `getServerSideProps`. |
| `getServerSideProps` in App Router? | ⚠️ Doesn't exist — `async` Server Components replace it. |
| Which files create a URL? | Only `page.tsx` and `route.ts`. |
| What changed in Next 15? ⭐ | `params`/`searchParams`/`cookies()`/`headers()` are **async**; `fetch` no longer cached by default. |
| Can a Server Component use `useState`? | ❌ No — that's what `"use client"` is for. |
| Can a Client Component be `async`? | ❌ No. |
| Props across the boundary must be | **serialisable** — no functions or class instances. |
| `loading.tsx` does what? | Wraps the segment in Suspense → streaming. |
| Where does `middleware.ts` live? | Project root, one per app, with a `matcher`. |
| Import navigation hooks from | `next/navigation` (not `next/router`). |
| Static or dynamic — how do you check? | The `next build` output marks `○` vs `ƒ` per route. |
| Server Actions are which verb? | POST only, and sequential per client. |
| Why not `<img>`? | No optimisation, no lazy loading, no reserved space → worse LCP and CLS. |
| SEO benefit of Next? | Crawlers get real HTML with metadata instead of an empty div. |

---

## 8. The five to have ready

1. **Rendering strategies** — and the "static by default" decision rule.
2. **Server vs Client Components** — and why `"use client"` is a boundary.
3. **The caching layers** — plus the Next 14 → 15 `fetch` default change.
4. **Server Actions are public endpoints** — authenticate, authorise, validate.
5. **Core Web Vitals** — especially INP and how less JavaScript fixes it.
