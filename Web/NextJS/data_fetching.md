# Data Fetching, Caching & Server Actions

> Rendering modes: **[rendering.md](rendering.md)** · Route handlers: **[api_middleware.md](api_middleware.md)**

---

## 1. Fetching in Server Components ⭐

```tsx
export default async function Page() {
  const products = await fetch("https://api.example.com/products").then(r => r.json());
  // or, in a Server Component, hit the database DIRECTLY — no API layer needed
  const users = await db.user.findMany();
  return <List items={products} />;
}
```

⭐ **No `useEffect`, no loading state, no `/api` round trip.** The component awaits its own
data on the server. This removes the classic client waterfall
(*render → effect → fetch → re-render*) entirely.

⚠️ **Never call your own `/api/*` route from a Server Component.** It's an HTTP round trip to
yourself — a needless serialisation hop and an extra process. Call the database or service
function directly; `/api` routes exist for *external* clients.

**Parallel vs sequential — the thing to get right:**

```tsx
const user = await getUser(id);              // ⚠️ SEQUENTIAL waterfall: 200ms
const posts = await getPosts(id);            //    + 200ms = 400ms

const [user, posts] = await Promise.all([    // ⭐ PARALLEL: 200ms total
  getUser(id), getPosts(id),
]);
```

⭐ Only sequence when the second call genuinely needs the first's result. Otherwise
`Promise.all` — and for independent slow sections, put each in its own `<Suspense>` so they
stream separately.

---

## 2. Caching ⭐⭐

**Next.js has four caches. Knowing they exist — and that they're layered — is the senior
answer.**

| Cache | Scope | Lifetime |
|---|---|---|
| **Request Memoization** | one render pass | ⭐ dedupes identical `fetch`es in the same request |
| **Data Cache** | ⭐ server, **across requests and deploys** | until revalidated |
| **Full Route Cache** | server, rendered HTML/RSC payload | until revalidated |
| **Router Cache** | ⚠️ **client**, in-memory | seconds; cleared on refresh |

```tsx
fetch(url)                                    // ⚠️ Next 15: NOT cached by default
fetch(url, { cache: "force-cache" })          // ⭐ persist in the Data Cache
fetch(url, { cache: "no-store" })             // never cache → makes the route dynamic
fetch(url, { next: { revalidate: 3600 } })    // ⭐ ISR: refresh after an hour
fetch(url, { next: { tags: ["products"] } })  // ⭐ tag for on-demand invalidation
```

⚠️⚠️ **Next 14 cached `fetch` by default; Next 15 does not.** This reversal is the single
biggest source of confusion — code that "worked" now hits the origin every request, or vice
versa. Always state which version you mean.

⭐ **Request memoization** is why calling `getUser(id)` in both `generateMetadata` and the page
costs **one** query — React dedupes identical fetches within a render. It only applies to
`fetch`; wrap database calls in React's `cache()` to get the same behaviour:

```tsx
import { cache } from "react";
export const getUser = cache(async (id: string) => db.user.findUnique({ where: { id } }));
```

**Invalidation:**

```tsx
import { revalidatePath, revalidateTag } from "next/cache";

revalidateTag("products");          // ⭐ everything tagged — the precise tool
revalidatePath("/products/[id]", "page");
```

⭐ **Tag-based revalidation from a CMS webhook** beats a `revalidate` timer: content updates
propagate the moment it changes, not up to an hour later
([rendering.md §2](rendering.md)).

⚠️ **The client Router Cache is why data looks stale after a mutation** — the browser reuses a
cached RSC payload for up to 30 seconds. `router.refresh()` or a Server Action's revalidation
clears it.

---

## 3. Server Actions ⭐⭐

**Functions that run on the server, callable directly from the client — no API route, no
`fetch`, no manual serialisation.**

```tsx
// app/actions.ts
"use server";

import { revalidatePath } from "next/cache";
import { redirect } from "next/navigation";
import { z } from "zod";

const Schema = z.object({ name: z.string().min(1), price: z.coerce.number().positive() });

export async function createProduct(prevState: State, formData: FormData) {
  const session = await auth();                          // ⭐⭐ AUTHORISE — see below
  if (!session) return { error: "Unauthorized" };

  const parsed = Schema.safeParse(Object.fromEntries(formData));   // ⭐ VALIDATE
  if (!parsed.success) return { error: parsed.error.flatten() };

  await db.product.create({ data: { ...parsed.data, ownerId: session.user.id } });

  revalidatePath("/products");                           // ⭐ refresh the cache
  redirect("/products");
}
```

```tsx
// the form — works WITHOUT JavaScript (progressive enhancement) ⭐
"use client";
import { useActionState, useFormStatus } from "react";

export function ProductForm() {
  const [state, action, pending] = useActionState(createProduct, { error: null });
  return (
    <form action={action}>
      <input name="name" />
      <button disabled={pending}>{pending ? "Saving…" : "Save"}</button>
      {state.error && <p role="alert">{String(state.error)}</p>}
    </form>
  );
}
```

⚠️⚠️ **A Server Action is a public HTTP endpoint.** Next generates a URL for it and anyone can
POST to it — the fact that your UI only calls it from an admin page is irrelevant. **Every
action must authenticate, authorise, and validate its own input**, exactly like a REST
endpoint. Forgetting this is the #1 Next.js security bug, and a great thing to raise unasked.

⭐ **Progressive enhancement** is the real selling point: `<form action={serverAction}>` submits
natively when JS hasn't loaded or has failed. That's a genuine accessibility and resilience
win over a `fetch`-based handler.

⚠️ Server Actions are **POST only** and execute **sequentially** per client — fine for
mutations, wrong for reads. Fetch reads in Server Components instead.

⭐ **Optimistic UI:**

```tsx
const [optimistic, addOptimistic] = useOptimistic(items, (s, n) => [...s, n]);
```

---

## 4. Client-side fetching — when it's still right ⭐

Server Components don't replace client fetching for **interactive, frequently-changing, or
user-specific** data.

```tsx
"use client";
import useSWR from "swr";

const { data, error, isLoading } = useSWR("/api/notifications", fetcher,
  { refreshInterval: 5000 });
```

| Use | Tool |
|---|---|
| Initial page data, SEO content | ⭐ **Server Component** |
| Mutations | ⭐ **Server Action** |
| Polling, live data, infinite scroll | **SWR / TanStack Query** |
| Optimistic updates, complex client cache | TanStack Query |
| Real-time | WebSocket / SSE in a client component |

⭐ **The hybrid pattern:** render the first page on the server (fast paint, SEO) and hand it to
TanStack Query as `initialData` for subsequent client-side pages. You get both.

---

## 5. Patterns & pitfalls

**Pre-render dynamic routes at build:**

```tsx
export async function generateStaticParams() {
  const products = await db.product.findMany({ select: { id: true } });
  return products.map(p => ({ id: p.id }));      // ⭐ SSG for each
}
```

⚠️ For 100,000 products this makes builds unusable — generate the top N and let the rest render
on demand (`dynamicParams = true`, the default).

⚠️⚠️ **Secrets leak through client components.** Any variable prefixed `NEXT_PUBLIC_` is
**inlined into the browser bundle**. A non-prefixed secret read inside a `"use client"` file is
`undefined` at best — and if you pass it as a prop from a server component, it's **embedded in
the HTML payload**. Keep secrets in server-only modules; `import "server-only"` makes a
mistaken client import a build error.

⚠️ **Everything a Server Component passes as props is serialised into the RSC payload and
visible in the browser.** Don't pass a full user record when the component needs a name — you
are shipping the password hash to the client.

⚠️ **`cookies()`/`headers()` make the route dynamic**, killing static optimisation for the
whole page ([rendering.md §5](rendering.md)).

---

## 6. Interview points

- **How do you fetch data in the App Router? ⭐** `async` Server Components awaiting `fetch` or
  the database directly — no `useEffect`, no loading state.
- **Why not call your own `/api` route from a Server Component?** It's an HTTP round trip to
  your own process; call the function directly.
- **How do you avoid a fetch waterfall?** `Promise.all` for independent calls, and separate
  `<Suspense>` boundaries so slow sections stream independently.
- **What caches does Next have? ⭐⭐** Request memoization (per render), Data Cache (across
  requests), Full Route Cache (rendered output), and the client Router Cache.
- **Is `fetch` cached by default?** ⚠️ In Next 14 yes; **Next 15 no**. Say which version.
- **How do you invalidate?** `revalidateTag` (precise, webhook-driven) or `revalidatePath`;
  time-based `revalidate` for predictable churn.
- **Why does my UI show stale data after a mutation?** The client Router Cache —
  `router.refresh()` or revalidate inside the Server Action.
- **What is a Server Action?** A `"use server"` function invoked directly from the client; it
  handles mutations without an API route and works without JavaScript.
- **What's the security risk with Server Actions? ⭐⭐** They're public POST endpoints — you
  must authenticate, authorise, and validate inside every one.
- **When do you still fetch on the client?** Polling, real-time, infinite scroll, and
  highly interactive state — SWR/TanStack Query, ideally seeded with server-rendered data.
- **How do secrets leak in Next.js?** `NEXT_PUBLIC_` inlining, and props passed from server to
  client components — everything in the RSC payload is visible.
