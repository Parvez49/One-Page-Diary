# Performance — Core Web Vitals & Bundle Size

> Rendering choices: **[rendering.md](rendering.md)** · Caching: **[data_fetching.md](data_fetching.md)**

---

## 1. Core Web Vitals ⭐⭐

The metrics Google ranks on and interviewers ask about by name.

| Metric | Measures | Good | Fix |
|---|---|---|---|
| **LCP** Largest Contentful Paint | when the main content appears | **< 2.5 s** | ⭐ SSG/ISR, `next/image` with `priority`, preload fonts, cut TTFB |
| **INP** Interaction to Next Paint | responsiveness (replaced FID in 2024) | **< 200 ms** | ⭐ **less client JS**, break up long tasks, defer non-critical work |
| **CLS** Cumulative Layout Shift | visual stability | **< 0.1** | ⭐ width/height on images, reserve ad/embed space, `font-display: swap` |
| TTFB | server response | < 800 ms | static/CDN, faster queries, streaming |

⭐ **INP is where Next.js apps typically fail** — it's dominated by main-thread JavaScript.
This is exactly the problem React Server Components target: code that never ships can't block
an interaction.

⭐ **CLS is nearly free to fix and constantly neglected**: always give images explicit
dimensions (`next/image` enforces this), and reserve space for anything that loads late.

```tsx
// app/layout.tsx — report real user metrics
"use client";
useReportWebVitals(metric => sendToAnalytics(metric));
```

⚠️ **Lab data ≠ field data.** Lighthouse on your laptop is not a mid-range Android on 4G;
ship real-user monitoring (Vercel Analytics, `web-vitals`) and judge on p75.

---

## 2. JavaScript bundle ⭐

**The core lever. Everything else is secondary.**

```bash
ANALYZE=true next build          # @next/bundle-analyzer
next build                       # ⭐ read the per-route First Load JS table
```

⭐ **Read the build output every deploy.** Next prints First Load JS per route and marks
`○ Static` vs `ƒ Dynamic` — a route that jumps 200 KB or flips to dynamic is visible right
there.

**The four levers, in order of impact:**

**1. Keep components on the server.**

```tsx
// ⚠️ "use client" at the top of a page ships the ENTIRE subtree
// ⭐ push it to the leaves — only the interactive bit
```
This is the single biggest win and the whole point of RSC
([rendering.md §3](rendering.md)).

**2. Dynamic imports for heavy client code.**

```tsx
import dynamic from "next/dynamic";

const Chart = dynamic(() => import("@/components/Chart"), {
  loading: () => <Skeleton />,
  ssr: false,                                  // ⭐ chart libs that touch window
});
```
⭐ Ideal for editors, charts, maps, video players, and modals — anything below the fold or
behind an interaction.

**3. Import precisely.**

```tsx
import _ from "lodash";                        // ⚠️ ~70 KB
import debounce from "lodash/debounce";        // ⭐ ~2 KB
import { format } from "date-fns";             // ⭐ tree-shakes
```
⚠️ Check bundle cost before adding a dependency — `moment` (~70 KB, no tree-shaking) vs
`date-fns`/`Temporal`. A "small" UI library that pulls in an icon set is a common surprise.

**4. `optimizePackageImports`** in `next.config.ts` for large icon/component libraries.

---

## 3. Images ⭐

```tsx
import Image from "next/image";

<Image src="/hero.jpg" alt="" width={1200} height={600}
       priority                                    // ⭐ LCP image — preloads, no lazy-load
       sizes="(max-width: 768px) 100vw, 50vw" />   // ⭐ correct srcset selection

<Image src={url} alt="" fill className="object-cover" />   // unknown dimensions
```

**What `next/image` does for free:** modern formats (AVIF/WebP), correctly sized variants per
device, **lazy loading below the fold**, and reserved space — so it fixes CLS and helps LCP at
once.

⚠️⚠️ **`priority` on the LCP image is the highest-leverage single line in a Next.js app.**
Without it, your hero image is lazy-loaded and discovered late, adding a second or more to LCP.
⚠️ But putting `priority` on *many* images is worse than none — it removes lazy loading and
floods the connection.

⚠️ **`sizes` is required with `fill` or responsive layouts** — omit it and the browser
downloads the largest variant on every device.

⚠️ Remote images need `remotePatterns` in `next.config.ts` (an allow-list, so an attacker can't
use your optimiser as an open proxy).

---

## 4. Fonts

```tsx
import { Inter } from "next/font/google";
const inter = Inter({ subsets: ["latin"], display: "swap", variable: "--font-inter" });
```

⭐ **`next/font` self-hosts the font at build time** — no request to Google, no extra DNS/TLS
handshake, and it generates a size-adjusted fallback so swapping in the real font causes
**no layout shift**. Privacy and CLS solved together.

⚠️ Every extra weight/subset is another download — ship two weights, not six.

---

## 5. Server-side performance

- ⭐ **Static beats everything.** A CDN-served page has no server cost and ~20 ms TTFB. Every
  step toward dynamic must be justified ([rendering.md](rendering.md)).
- ⭐ **`Promise.all` your independent fetches** — serial awaits are the most common source of a
  slow TTFB ([data_fetching.md §1](data_fetching.md)).
- ⭐ **Stream with `<Suspense>`** so one slow query doesn't hold the whole page.
- ⚠️ **The database is usually the bottleneck**, not React. N+1 queries and missing indexes
  behave the same here as anywhere — see [../Django/queries.md](../Django/queries.md).
- ⚠️ **Serverless cold starts + a non-pooling driver = connection exhaustion.** Each lambda
  opens its own connection; use a pooler (PgBouncer, Prisma Accelerate, Neon serverless
  driver).
- ⭐ **Colocate compute and data.** Edge functions querying a single-region database are slower
  than a regional function next to it ([api_middleware.md §4](api_middleware.md)).

---

## 6. Other wins

```tsx
<Link href="/products" prefetch />               // ⭐ default: prefetches in viewport
```

```tsx
import Script from "next/script";
<Script src="https://analytics.example.com/s.js" strategy="lazyOnload" />
```
⭐ `strategy`: `beforeInteractive` (rare) · `afterInteractive` (default) ·
**`lazyOnload`** (analytics, chat widgets) · `worker` (experimental, off the main thread).

⚠️ **Third-party scripts are frequently the biggest INP problem** and the one you don't control
— audit them, defer them, and question whether each is worth its cost.

**Also:** `<link rel="preconnect">` for critical third-party origins, route-level code
splitting (automatic), and `experimental.ppr` for partial prerendering.

---

## 7. Diagnosing ⭐

```
1. next build            ⭐ First Load JS per route; Static vs Dynamic
2. Lighthouse / PageSpeed   lab metrics + specific opportunities
3. Chrome DevTools Performance  ⭐ long tasks — the cause of bad INP
4. Coverage tab          how much shipped JS actually executes
5. bundle-analyzer       which dependency is fat
6. RUM (field data)      ⭐ p75 of real users — the only score that counts
```

⭐ **Measure before optimising.** "Slow" is usually one of four things: an unnecessarily
dynamic route, a serial fetch waterfall, an oversized client bundle, or a slow database query.
Identify which before changing anything.

---

## 8. Interview points

- **What are Core Web Vitals? ⭐⭐** LCP (< 2.5 s, loading), INP (< 200 ms, responsiveness,
  replaced FID), CLS (< 0.1, stability).
- **How do you improve LCP?** Static/ISR, `priority` on the hero image, `next/font`, fewer
  render-blocking resources, faster TTFB.
- **How do you improve INP? ⭐** Ship less JavaScript — keep components on the server, code
  split, defer third-party scripts, break long tasks.
- **How do you fix CLS?** Explicit image dimensions, reserved space for late content,
  `font-display: swap` with a size-adjusted fallback (`next/font` does this).
- **How does Next.js reduce bundle size?** Server Components ship nothing, automatic route
  splitting, `next/dynamic`, tree shaking.
- **What does `next/image` do?** Format conversion, responsive variants, lazy loading, and
  reserved space — improving both LCP and CLS.
- **When should you use `priority`?** Only on the LCP image — it disables lazy loading and
  preloads.
- **What does `next/font` solve?** Self-hosting (no third-party request), plus a size-adjusted
  fallback that eliminates font-swap layout shift.
- **How do you find what's slow?** Build output → Lighthouse → DevTools long tasks → bundle
  analyzer → real-user p75.
- **Why might the edge be slower than a regional function?** Compute far from the data means
  every query pays a cross-region round trip.
- **What's the most common Next.js performance mistake? ⭐** `"use client"` too high in the
  tree, which ships the whole subtree and wipes out the RSC benefit.
