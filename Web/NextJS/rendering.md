# Rendering Strategies — CSR, SSR, SSG, ISR, RSC

> Routing & components: **[app_router.md](app_router.md)** · Data & caching: **[data_fetching.md](data_fetching.md)**

---

## 1. The five strategies ⭐⭐

**The most-asked Next.js question. Answer with the trade-off, not the acronym.**

| | **CSR** | **SSR** | **SSG** | **ISR** | **RSC** |
|---|---|---|---|---|---|
| HTML built | in the browser | ⭐ per request, on the server | ⭐ at **build** time | build + **regenerated** | per request/build, on the server |
| First paint | ⚠️ slowest — blank until JS runs | fast | ⭐ **fastest** (CDN) | ⭐ fastest | fast |
| Data freshness | live | ⭐ **always fresh** | ⚠️ stale until rebuild | ⭐ fresh within `revalidate` | configurable |
| SEO | ⚠️ weak | ⭐ good | ⭐ good | ⭐ good | ⭐ good |
| Server cost | none | ⚠️ per request | ⭐ ~zero | near zero | per request |
| Use for | dashboards behind auth | personalised pages, live data | marketing, docs, blogs | ⭐ catalogues, news | ⭐ the default in App Router |

⭐ **The decision rule to say out loud:**

> *"Static by default. Add revalidation when the data changes on a schedule. Go dynamic only
> when the response depends on the request — user, cookies, or real-time data."*

Every step away from static costs latency and server spend, so make each one deliberate.

---

## 2. How each works

**CSR** — server sends a near-empty shell; React fetches and renders in the browser.

```
HTML (empty div) → JS bundle → fetch → render     ⚠️ user sees nothing until the last step
```

⚠️ Bad for SEO (crawlers may not wait for JS), bad on slow devices, and the waterfall is
serial. Fine for a logged-in dashboard where SEO is irrelevant.

**SSR** — HTML rendered per request, then **hydrated**.

```
request → server renders → HTML sent (visible!) → JS hydrates → interactive
```

⭐ **Hydration is the concept to know:** the server HTML is inert; React must re-run the
component tree on the client to attach event handlers. Between paint and hydration the page
*looks* ready but doesn't respond — that's the gap RSC and streaming attack.

**SSG** — HTML generated at build, served from a CDN. ⚠️ Content changes require a rebuild and
redeploy; a 10,000-page site is a slow build.

**ISR** — SSG plus background regeneration:

```ts
export const revalidate = 60   // ⭐ serve cached; after 60s the next request triggers a rebuild
```

⭐ **ISR is stale-while-revalidate**: the *current* visitor gets the stale page immediately and
the refresh happens in the background, so nobody waits. Best of both for catalogues, blogs,
and news.

⭐ **On-demand ISR** is usually better than a timer — revalidate from a CMS webhook when the
content actually changes:

```ts
revalidatePath("/blog/[slug]");  revalidateTag("products")
```

---

## 3. React Server Components ⭐⭐

**The App Router's default. Components that run *only* on the server and never ship their JS.**

```tsx
// app/products/page.tsx — a Server Component by default
export default async function Products() {
  const products = await db.product.findMany();   // ⭐ direct DB access, no API layer
  return <ProductList products={products} />;
}
```

**What that buys you:**

- ⭐ **Zero client JS** for the component — a 400 KB markdown renderer stays on the server.
- ⭐ **Direct backend access** — query the database, read files, use secrets. No `/api` hop.
- ⭐ **No waterfall** — data is fetched where it's rendered, on the server, close to the data.

| | **Server Component** (default) | **Client Component** (`"use client"`) |
|---|---|---|
| Runs | server only | server (SSR pass) **and** client |
| Ships JS | ⭐ **none** | ⚠️ yes — adds to the bundle |
| `useState`/`useEffect` | ❌ | ✅ |
| `onClick`, event handlers | ❌ | ✅ |
| `async`/`await` in the component | ⭐ ✅ | ❌ |
| DB / secrets / `fs` | ⭐ ✅ | ❌ **never** |
| Browser APIs (`window`) | ❌ | ✅ |

⚠️⚠️ **`"use client"` marks a *boundary*, not a file.** Every component imported by a client
component also becomes client-side. One `"use client"` near the root of your tree ships the
entire subtree to the browser — this is the mistake that erases every RSC benefit.

⭐ **Push `"use client"` to the leaves.** Keep pages and layouts as Server Components and make
only the interactive bits (a like button, a dropdown) client components. Pass server-rendered
markup **as `children`** so it stays on the server:

```tsx
// ⭐ ServerContent stays on the server even though the wrapper is interactive
<ClientAccordion>
  <ServerContent />
</ClientAccordion>
```

⚠️ Props crossing the boundary must be **serialisable** — no functions, class instances,
`Date` is OK-ish, `Map`/`Set` are not.

---

## 4. Streaming & Suspense ⭐

Instead of waiting for the slowest query, send HTML as it becomes ready.

```tsx
export default function Page() {
  return (
    <>
      <Header />                                    {/* ⭐ sent immediately */}
      <Suspense fallback={<ReviewsSkeleton />}>
        <Reviews />                                 {/* streams in when ready */}
      </Suspense>
    </>
  );
}
```

⭐ **This is how you keep TTFB fast with slow data.** One 2-second query no longer blocks the
whole page — the shell paints instantly and the slow region fills in. `loading.tsx` in a route
folder does the same thing automatically for the whole segment.

⭐ **Partial Prerendering (PPR)** — the newest model: a static shell served from the CDN with
dynamic holes streamed in per request. It removes the all-or-nothing static/dynamic choice.

---

## 5. What makes a route dynamic ⚠️

Next.js statically renders by default and **switches to dynamic automatically** when you use a
request-dependent API:

```ts
cookies(), headers(), searchParams, draftMode()
fetch(url, { cache: "no-store" })
export const dynamic = "force-dynamic"
```

⚠️⚠️ **One `cookies()` call anywhere in the tree makes the whole route dynamic**, silently
turning a CDN-cached page into a per-request render. This is the most common "why is my site
suddenly slow" cause. Check the build output — Next prints `○ Static` vs `ƒ Dynamic` per
route; read it on every deploy.

⭐ **Isolate the dynamic part** behind `<Suspense>` so the rest of the page stays static (PPR).

---

## 6. Choosing — worked examples

| Page | Strategy | Why |
|---|---|---|
| Marketing homepage | **SSG** | never changes per user; CDN |
| Blog post | **ISR** (`revalidate: 3600`) or on-demand | edited occasionally |
| Product listing | ⭐ **ISR + on-demand revalidate** on stock change | mostly static, must not be badly stale |
| Product page with live stock | static shell + `<Suspense>` for stock | ⭐ SEO from the shell, freshness where it matters |
| Search results | **dynamic** (`searchParams`) | depends on the request |
| User dashboard | ⭐ **dynamic** or CSR | personalised, no SEO value |
| Admin panel | **CSR** | behind auth, highly interactive |

---

## 7. Interview points

- **Explain CSR / SSR / SSG / ISR. ⭐⭐** Where and when HTML is generated, traded off against
  freshness, SEO, and server cost. Static by default; go dynamic only when the response
  depends on the request.
- **What is ISR, and why is it better than SSG here?** Cached HTML regenerated in the
  background after `revalidate` — content updates without a rebuild, and no visitor waits.
- **On-demand vs time-based revalidation?** Webhook-triggered `revalidateTag`/`revalidatePath`
  updates exactly when content changes, instead of guessing an interval.
- **What is hydration, and why does it matter?** Re-running React on the client to attach
  handlers to server HTML — the page looks ready but isn't interactive until it completes.
- **What is a React Server Component? ⭐⭐** A component that runs only on the server, ships no
  JS, and can access the database directly.
- **Server vs Client Component — how do you decide?** Client only for state, effects, event
  handlers, or browser APIs. Everything else stays on the server.
- **What's the danger of `"use client"`? ⭐** It's a boundary — everything imported below it
  becomes client code. Put it at the leaves, not the root.
- **How do you keep a page fast when one query is slow?** `<Suspense>` streaming — send the
  shell immediately and stream the slow region.
- **What silently makes a route dynamic?** `cookies()`, `headers()`, `searchParams`, or
  `no-store` fetches anywhere in the tree.
- **Which strategy for an e-commerce product page?** Static/ISR shell for SEO and speed, with
  price/stock streamed dynamically inside Suspense.
