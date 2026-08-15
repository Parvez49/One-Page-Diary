# Route Handlers, Middleware & Runtimes

> Server Actions for mutations: **[data_fetching.md](data_fetching.md)** · Auth: **[auth.md](auth.md)**

---

## 1. Route Handlers

```ts
// app/api/products/route.ts
import { NextRequest, NextResponse } from "next/server";

export async function GET(req: NextRequest) {
  const q = req.nextUrl.searchParams.get("q");
  const products = await db.product.findMany({ where: { name: { contains: q } } });
  return NextResponse.json(products, {
    headers: { "Cache-Control": "s-maxage=60, stale-while-revalidate=300" },
  });
}

export async function POST(req: NextRequest) {
  const session = await auth();                       // ⭐ authenticate
  if (!session) return NextResponse.json({ error: "Unauthorized" }, { status: 401 });

  const parsed = Schema.safeParse(await req.json());  // ⭐ validate
  if (!parsed.success) {
    return NextResponse.json({ error: parsed.error.flatten() }, { status: 400 });
  }
  const product = await db.product.create({ data: parsed.data });
  return NextResponse.json(product, { status: 201 });
}

// dynamic route: app/api/products/[id]/route.ts
export async function GET(req: NextRequest, { params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;                        // ⚠️ async in Next 15
}
```

Export one function per verb: `GET POST PUT PATCH DELETE HEAD OPTIONS`.
⚠️ A `route.ts` and a `page.tsx` **cannot** live in the same folder.

⭐⭐ **When do you actually need a route handler?** Only for **non-Next consumers**:

| Need it | Don't need it |
|---|---|
| ⭐ mobile app / third-party API clients | data for your own pages → **Server Component** |
| ⭐ webhooks (Stripe, GitHub) | mutations from your own forms → **Server Action** |
| OAuth callbacks | |
| file uploads / streaming downloads | |
| cron endpoints, health checks | |

⚠️ **Building `/api/*` routes and calling them from your own Server Components is the most
common App Router anti-pattern** — an HTTP round trip to your own process for no benefit.

---

## 2. Caching & streaming responses

```ts
export const dynamic = "force-dynamic";   // never cache
export const revalidate = 60;             // ISR for this handler
export const runtime = "edge";            // see §4
```

⚠️ `GET` handlers were cached by default in Next 14 and are **not** in Next 15 — the same
reversal as `fetch` ([data_fetching.md §2](data_fetching.md)).

```ts
// ⭐ streaming (SSE, LLM tokens, large exports)
export async function GET() {
  const stream = new ReadableStream({
    async start(controller) {
      for await (const chunk of source) controller.enqueue(encoder.encode(chunk));
      controller.close();
    },
  });
  return new Response(stream, { headers: { "Content-Type": "text/event-stream" } });
}
```

⚠️ **Webhooks need the raw body** for signature verification — `await req.text()`, not
`req.json()`, because re-serialising changes the bytes and the HMAC won't match.

---

## 3. Middleware ⭐

**Runs before every matching request, at the edge, before rendering.**

```ts
// middleware.ts — at the project root
import { NextRequest, NextResponse } from "next/server";

export function middleware(req: NextRequest) {
  const token = req.cookies.get("session")?.value;

  if (!token && req.nextUrl.pathname.startsWith("/dashboard")) {
    const url = new URL("/login", req.url);
    url.searchParams.set("from", req.nextUrl.pathname);
    return NextResponse.redirect(url);
  }

  const res = NextResponse.next();
  res.headers.set("x-request-id", crypto.randomUUID());     // ⭐ trace requests
  return res;
}

export const config = {
  matcher: ["/((?!api|_next/static|_next/image|favicon.ico).*)"],   // ⭐ skip static
};
```

**Good uses:** redirects/rewrites, i18n locale routing, A/B tests and feature flags, security
headers, bot blocking, and a **cheap auth gate**.

⚠️⚠️ **Middleware is not an authorisation layer.** It runs on the **Edge runtime** — no
database, no Node APIs — so it can only check that a cookie *looks* valid, not that the
session exists or the user has the right role. A CVE-2025-29927 class bug even allowed header
spoofing to bypass it entirely.

⭐ **The correct model: middleware is a fast redirect for UX; the real check happens in the
page, the Server Action, and the route handler.** Verify authorisation where the data is
accessed — every time.

⚠️ Middleware runs on **every matched request**, so keep it under a few milliseconds. Always
narrow the `matcher`; the default matches everything including static assets.

---

## 4. Node vs Edge runtime ⭐

| | **Node.js runtime** (default) | **Edge runtime** |
|---|---|---|
| APIs | ⭐ full Node — `fs`, `crypto`, TCP | ⚠️ Web APIs only — **no TCP, no `fs`** |
| Database | ⭐ any driver (`pg`, Prisma) | ⚠️ HTTP-based only (Neon/PlanetScale serverless, Upstash) |
| Cold start | slower (~100s of ms) | ⭐ near zero |
| Location | one region | ⭐ **globally distributed**, near the user |
| Size limit | generous | ⚠️ small (~1–4 MB) |

⭐ **Edge is a latency optimisation, not a default.** It wins for middleware, redirects,
geolocation, and simple personalisation — anything that must run close to the user with no
heavy dependencies. ⚠️ But "edge near the user, database in `us-east-1`" makes things
**slower**: each query crosses the ocean. Colocate compute with data unless the work is truly
data-free.

---

## 5. Security for handlers & actions ⭐

⚠️⚠️ **Route handlers and Server Actions are both public HTTP endpoints.** Obscurity is not
access control.

**Every one of them must:**

1. **Authenticate** — `await auth()` inside the handler, not only in middleware.
2. **Authorise** — does *this* user own *this* record? (IDOR is as real here as in Django.)
3. **Validate** — parse the body with Zod; never trust shapes or types.
4. **Scope the query** — `where: { id, ownerId: session.user.id }` rather than fetching by id
   and checking afterwards.
5. **Rate limit** — Upstash Ratelimit or a WAF rule; auth and mutation endpoints especially.

```ts
const product = await db.product.findFirst({
  where: { id, ownerId: session.user.id },     // ⭐ scoped — can't reach another user's row
});
if (!product) return NextResponse.json({ error: "Not found" }, { status: 404 });
```

**Other essentials:** CORS headers only if external browsers call you (`OPTIONS` handler);
**verify webhook signatures** rather than trusting the source; and never return raw Prisma
errors (they leak schema).

⭐ **CSRF:** Server Actions have built-in origin checking, and `SameSite=Lax` cookies cover
most cases — but a cookie-authenticated `POST /api/*` route handler still needs thought. See
[../Django/security.md](../Django/security.md) for the CSRF-vs-CORS distinction; it's
identical here.

---

## 6. Config & headers

```ts
// next.config.ts
export default {
  async redirects()  { return [{ source: "/old", destination: "/new", permanent: true }]; },
  async rewrites()   { return [{ source: "/api/:p*", destination: "https://backend/:p*" }]; },
  async headers() {
    return [{ source: "/(.*)", headers: [
      { key: "X-Frame-Options", value: "DENY" },
      { key: "Content-Security-Policy", value: "default-src 'self'" },   // ⭐
      { key: "Strict-Transport-Security", value: "max-age=63072000" },
    ]}];
  },
  images: { remotePatterns: [{ protocol: "https", hostname: "cdn.example.com" }] },
};
```

⭐ **Redirect vs rewrite:** a redirect changes the browser's URL (301/302); a **rewrite** is
invisible — the user sees `/api/x` while the response comes from another backend. Rewrites are
how you put Next.js in front of an existing Django API on one domain, sidestepping CORS
entirely.

---

## 7. Interview points

- **When do you need a route handler vs a Server Component or Action? ⭐⭐** Only for
  non-Next consumers — mobile clients, webhooks, OAuth callbacks. Your own pages should call
  the database directly; your own forms should use Server Actions.
- **What runs in middleware, and what shouldn't?** Redirects, headers, i18n, flags — not
  database access or real authorisation.
- **Is middleware enough for auth? ⚠️** No — Edge runtime can only inspect the cookie, and it
  has been bypassable. Re-check authorisation at every data access point.
- **Node vs Edge runtime?** Full Node APIs and TCP database drivers vs globally distributed,
  near-zero cold start with Web APIs only.
- **Why can Edge be slower?** Compute near the user but data in one region means every query
  crosses the network.
- **How do you secure a Server Action?** Treat it as a public POST endpoint: authenticate,
  authorise, validate, scope the query, rate limit.
- **Why `req.text()` for a webhook?** Signature verification needs the exact raw bytes.
- **Redirect vs rewrite?** Visible URL change vs invisible proxying — rewrites let you front an
  existing API on the same origin and avoid CORS.
- **How do you prevent IDOR here?** Scope the query by owner instead of fetching by id and
  checking afterwards.
