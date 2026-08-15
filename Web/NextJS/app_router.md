# App Router — Routing, Layouts, Components

> Rendering model: **[rendering.md](rendering.md)** · Fetching: **[data_fetching.md](data_fetching.md)**

---

## 1. File-based routing

```
app/
├── layout.tsx              ⭐ ROOT layout (required) — must render <html> and <body>
├── page.tsx                → /
├── loading.tsx             ⭐ Suspense fallback for this segment
├── error.tsx               ⭐ error boundary ("use client" required)
├── not-found.tsx           404
├── template.tsx            like layout, but REMOUNTS on navigation
├── global-error.tsx        catches root layout errors
│
├── products/
│   ├── page.tsx            → /products
│   ├── layout.tsx          wraps everything below
│   └── [id]/
│       ├── page.tsx        → /products/123
│       └── opengraph-image.tsx
│
├── (marketing)/            ⭐ ROUTE GROUP — organises, no URL segment
│   ├── layout.tsx          a different layout for these routes
│   └── about/page.tsx      → /about
│
├── shop/
│   └── @modal/             ⭐ PARALLEL route — renders alongside `children`
│       └── (.)cart/        ⭐ INTERCEPTING route — modal over the current page
│
├── blog/[...slug]/         catch-all      → /blog/a/b/c
├── docs/[[...slug]]/       optional catch-all (matches /docs too)
└── api/products/route.ts   → API endpoint (see api_middleware.md)
```

**Only `page.tsx` and `route.ts` create a public URL.** Everything else in a folder is
colocated support — components, tests, styles — which is why you can keep files next to the
route that uses them.

**Dynamic params:**

```tsx
export default async function Page({ params, searchParams }: {
  params: Promise<{ id: string }>;                    // ⚠️ Next 15: params is a PROMISE
  searchParams: Promise<{ q?: string }>;
}) {
  const { id } = await params;
  ...
}
```

⚠️ **Next 15 made `params`, `searchParams`, `cookies()`, and `headers()` async.** Old
synchronous code silently breaks on upgrade — a likely "have you used Next recently?" tell.

---

## 2. Layouts vs templates ⭐

```tsx
// app/layout.tsx — the root layout
export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>
        <Nav />
        {children}
      </body>
    </html>
  );
}
```

⭐⭐ **Layouts preserve state across navigation.** Move between `/products/1` and
`/products/2` and the shared layout **does not re-render** — scroll position, open menus, and
a playing video all survive. That's the headline App Router improvement over the Pages Router,
where every navigation remounted `_app`.

**`template.tsx`** is the opposite: a new instance per navigation. Use it when you *want* a
remount — enter animations, per-page analytics, resetting a form.

⚠️ **Layouts can't access `searchParams`** (they don't re-render when the query changes) or
know the current pathname on the server. Use a client component with `usePathname()`.

⚠️ **The root layout must contain `<html>` and `<body>`** and can't be a client component.

---

## 3. Navigation

```tsx
import Link from "next/link";
<Link href="/products/1" prefetch>Product</Link>     // ⭐ prefetches on viewport/hover
```

```tsx
"use client";
import { useRouter, usePathname, useSearchParams, useParams } from "next/navigation";

const router = useRouter();
router.push("/checkout");
router.replace("/login");        // no history entry
router.refresh();                // ⭐ re-fetch server components, KEEP client state
```

```tsx
import { redirect, notFound } from "next/navigation";     // ⭐ server-side
if (!user) redirect("/login");
if (!product) notFound();
```

⭐ **`<Link>` beats `router.push`** — it renders a real `<a>` (accessible, middle-clickable,
crawlable) and prefetches the route automatically. Reserve `router.push` for navigation after
an action.

⭐ **`router.refresh()` is the RSC-era "reload"** — it re-runs server components and merges
new data without losing client state or scroll position. That's what you call after a
mutation that isn't a Server Action.

⚠️ Import from **`next/navigation`**, not `next/router` (that's the Pages Router).

---

## 4. Loading, errors, and not-found

```tsx
// app/products/loading.tsx — ⭐ automatic Suspense boundary for the segment
export default function Loading() { return <ProductSkeleton />; }
```

```tsx
// app/products/error.tsx
"use client";                                  // ⭐⭐ error boundaries MUST be client
export default function Error({ error, reset }: { error: Error; reset: () => void }) {
  useEffect(() => { logToSentry(error); }, [error]);
  return <><p>Something went wrong.</p><button onClick={reset}>Try again</button></>;
}
```

⭐ `loading.tsx` gives you streaming for free — the shell renders instantly while the segment's
data resolves ([rendering.md §4](rendering.md)).

⚠️ **`error.tsx` does not catch errors in the *layout* of the same segment** (the boundary sits
inside it) — you need `error.tsx` one level up, or `global-error.tsx` for the root.

⚠️ In production, error messages are **redacted** before reaching the client (they'd leak
server internals). Log the real one server-side; `error.digest` correlates the two.

---

## 5. Advanced routing ⭐

**Route groups `(name)`** — organise files or apply a different layout without touching the
URL. `app/(marketing)/about/page.tsx` → `/about`.

**Parallel routes `@slot`** — render several independent pages in one layout, each with its
own loading and error state:

```tsx
export default function Layout({ children, analytics, team }) {
  return <>{children}<aside>{analytics}{team}</aside></>;
}
```

⭐ Perfect for dashboards where one panel is slow — it streams independently instead of
blocking the others.

**Intercepting routes `(.)`, `(..)`, `(...)`** — the "photo modal" pattern: clicking a
thumbnail opens `/photos/5` **as a modal** over the feed, but a direct visit or refresh renders
the full page. `(.)`= same level, `(..)`= one up, `(...)`= from root.

---

## 6. Metadata & SEO ⭐

```tsx
export const metadata: Metadata = { title: "Products", description: "..." };   // static

export async function generateMetadata({ params }): Promise<Metadata> {        // ⭐ dynamic
  const { id } = await params;
  const p = await getProduct(id);                    // ⭐ deduped with the page's own fetch
  return {
    title: p.name,
    openGraph: { title: p.name, images: [p.image] },
    alternates: { canonical: `/products/${id}` },
  };
}
```

⭐ `generateMetadata` runs on the server and its `fetch` calls are **deduplicated** with the
page's, so you don't pay twice. Also: `app/sitemap.ts`, `app/robots.ts`, and
`opengraph-image.tsx` (generates OG images at build).

⭐ **SSR/SSG is the SEO argument for Next.js** — crawlers get real HTML with content and
metadata instead of an empty div.

---

## 7. App Router vs Pages Router

| | **Pages Router** (`pages/`) | **App Router** (`app/`) |
|---|---|---|
| Data | `getServerSideProps` / `getStaticProps` | ⭐ `async` components, `fetch` anywhere |
| Components | all client | ⭐ **Server Components** by default |
| Layouts | `_app.tsx`, remounts | ⭐ nested, **state-preserving** |
| Streaming | ❌ | ⭐ ✅ Suspense |
| Bundle | everything ships | ⭐ server components ship nothing |
| Maturity | ⚠️ stable, huge ecosystem | newer; some libraries still catching up |

⭐ **App Router for new projects**; Pages Router is supported, not deprecated, and they can
coexist in one app during migration. ⚠️ Many older libraries assume client-side React and need
a `"use client"` wrapper.

---

## 8. Interview points

- **How does routing work in the App Router?** File-system based — folders are segments, only
  `page.tsx`/`route.ts` create URLs, so support files can be colocated.
- **Layout vs template? ⭐** Layouts persist across navigation (state and scroll preserved);
  templates remount every time.
- **Why can't a layout read `searchParams`?** It doesn't re-render when the query changes —
  use a client component with `useSearchParams`.
- **What are route groups for?** Organisation and per-section layouts without adding a URL
  segment.
- **When would you use parallel routes?** Independent dashboard panels that should stream and
  fail independently.
- **What are intercepting routes for?** Showing a route as a modal in context while keeping a
  shareable, refreshable full page.
- **`loading.tsx` — what does it actually do?** Wraps the segment in a Suspense boundary,
  enabling streaming.
- **Why must `error.tsx` be a client component?** Error boundaries rely on React client-side
  lifecycle; it also needs `onClick` for `reset`.
- **`<Link>` vs `router.push`? ⭐** `Link` renders a real anchor and prefetches; `push` is for
  post-action navigation.
- **What does `router.refresh()` do?** Re-runs server components and merges fresh data without
  discarding client state.
- **What changed in Next 15?** `params`, `searchParams`, `cookies()`, `headers()` became async,
  and `fetch` is no longer cached by default.
