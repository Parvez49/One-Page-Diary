# Next.js — Index

Domain knowledge for **senior frontend/full-stack interviews** and production work. Assumes
React fluency — the focus is on the App Router model, the caching layers, and the traps that
only appear once real traffic hits.

**Conventions:** ⭐ = high interview value · ⚠️ = a trap that causes real incidents ·
every file ends with an **Interview points** section.
Examples target **Next.js 15 + App Router**; ⚠️ marks behaviour that changed from 14.

---

## Files

| File | Covers | Interview weight |
|---|---|---|
| [rendering.md](rendering.md) | **CSR/SSR/SSG/ISR**, hydration, **React Server Components**, `"use client"` boundary, streaming, what makes a route dynamic | ⭐⭐⭐ |
| [app_router.md](app_router.md) | File routing, **layouts vs templates**, navigation, `loading`/`error`, route groups, **parallel & intercepting routes**, metadata | ⭐⭐⭐ |
| [data_fetching.md](data_fetching.md) | Server-side fetching, **the four caches**, revalidation, **Server Actions**, client fetching, secret leakage | ⭐⭐⭐ |
| [auth.md](auth.md) | **Where to enforce auth**, sessions vs JWT, cookies, Auth.js, **IDOR**, Next-specific risks | ⭐⭐⭐ |
| [performance.md](performance.md) | **Core Web Vitals**, bundle size, `next/image`, `next/font`, diagnosing slowness | ⭐⭐⭐ |
| [api_middleware.md](api_middleware.md) | Route handlers (**and when not to use them**), middleware limits, **Node vs Edge**, headers & rewrites | ⭐⭐ |
| [interview.md](interview.md) | **Q&A across every topic** + rapid fire | ⭐⭐⭐ |

---

## Suggested study order

1. **[rendering.md](rendering.md)** — Server Components and the rendering strategies are the
   foundation; nearly every other answer refers back to them.
2. **[data_fetching.md](data_fetching.md)** — the caching layers are the most confusing part of
   modern Next.js and the strongest signal that you've actually shipped it.
3. **[app_router.md](app_router.md)** — routing, layouts, and streaming primitives.
4. **[auth.md](auth.md)** — "where do you enforce auth" separates people who read the docs from
   people who read the CVEs.
5. **[performance.md](performance.md)** — Core Web Vitals get asked by name.
6. **[api_middleware.md](api_middleware.md)** — knowing when *not* to write an API route is the
   senior signal.
7. **[interview.md](interview.md)** — rehearse out loud the day before.

---

## The senior answers worth memorising

| Question | Short answer |
|---|---|
| Which rendering strategy? ⭐ | **Static by default**; revalidate for scheduled change; dynamic only when the response depends on the request. |
| What is an RSC? | Runs server-only, ships **zero JS**, can hit the database directly. |
| `"use client"` risk ⭐⭐ | It's a **boundary** — everything imported below ships to the browser. Put it at the leaves. |
| What makes a route dynamic? | `cookies()`, `headers()`, `searchParams`, `no-store` — anywhere in the tree. |
| Is `fetch` cached? | ⚠️ Next 14 yes, **Next 15 no**. Name the version. |
| The four caches | Request memoization · Data Cache · Full Route Cache · client Router Cache. |
| Stale UI after a mutation | Client Router Cache — `router.refresh()` or revalidate in the action. |
| Server Action security ⭐⭐ | It's a **public POST endpoint** — authenticate, authorise, validate in every one. |
| Is middleware an auth layer? | ⚠️ No — Edge can't reach the DB, and it's been bypassable. Enforce at data access. |
| Does a layout check protect pages? | ⚠️ No — layouts don't re-render per navigation. |
| Token storage | `httpOnly` cookie, never `localStorage`. |
| How do secrets leak? | `NEXT_PUBLIC_` inlining and props in the RSC payload. |
| Need an `/api` route? | Only for **external** consumers — not for your own pages. |
| Worst performance mistake | `"use client"` too high in the tree. |
| INP too high | Ship less JavaScript. |
| Edge slower than regional? | Compute far from the data — every query crosses the network. |

---

## Full-stack notes

Pairing this with a Django backend ([../Django/](../Django/)):

- ⭐ Let Django own users, permissions, and business logic; Next holds an **`httpOnly` cookie**
  and calls Django from **Server Components**, so the token never reaches the browser.
- ⭐ Use a **rewrite** (`/api/:path*` → Django) to keep everything same-origin and sidestep
  CORS entirely.
- The security fundamentals are identical on both sides: **CSRF vs CORS**, **IDOR**, and "never
  trust the client" — see [../Django/security.md](../Django/security.md).
- N+1 queries behave the same whether the caller is a DRF serializer or a Server Component —
  [../Django/queries.md](../Django/queries.md).

---

## Related directories

`../Django/` backend · `../basics.md` web fundamentals · `../react.txt` React ·
`../../Language/JavaScript/` JS · `../../HTMLCSS/` markup & styling ·
`../../SDLC/` architecture · `../../Deploy/` Docker, K8s, nginx · `../../CICD/` pipelines
