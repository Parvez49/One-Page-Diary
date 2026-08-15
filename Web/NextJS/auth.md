# Authentication & Security

> Handlers & middleware: **[api_middleware.md](api_middleware.md)** ·
> Backend equivalents: **[../Django/auth.md](../Django/auth.md)** · **[../Django/security.md](../Django/security.md)**

---

## 1. Where auth is enforced ⭐⭐

**The defining Next.js auth question, because there are four places to check and only three
are real.**

```
1. middleware.ts   ⚠️ UX redirect ONLY — Edge runtime, can't hit the DB
2. layout.tsx      ⚠️ NOT a security boundary — see below
3. page / Server Component   ⭐ real check, before rendering data
4. Server Action / route handler  ⭐⭐ MANDATORY — these are public endpoints
5. data access layer          ⭐ best — enforce once, close to the data
```

⚠️⚠️ **A check in a layout does not protect its pages.** Layouts don't re-render on every
navigation, and a page can be requested directly — the layout's guard may not run for that
request. The Next.js docs say this explicitly, and it's a common real-world hole.

⭐⭐ **The rule to state: authorise where the data is accessed, not where the UI is drawn.**
Middleware is an optimisation for the user's experience; the actual gate belongs next to the
query. The cleanest implementation is a **Data Access Layer**:

```ts
// lib/dal.ts
import "server-only";                          // ⭐ build error if imported by client code
import { cache } from "react";

export const getCurrentUser = cache(async () => {
  const session = await verifySession();
  return session ? db.user.findUnique({ where: { id: session.userId } }) : null;
});

export async function getOrder(id: string) {
  const user = await requireUser();
  return db.order.findFirst({ where: { id, userId: user.id } });   // ⭐ scoped — IDOR-proof
}
```

Every caller is safe by construction, and `cache()` means the session is verified once per
request.

---

## 2. Session strategies

| | **Cookie session (stateless JWT)** | **Database session** |
|---|---|---|
| Storage | signed/encrypted cookie | session id → DB row |
| Lookup per request | ⭐ none | one query (or cache hit) |
| Revocation | ⚠️ **hard** — valid until expiry | ⭐ **instant** — delete the row |
| Size limit | ⚠️ ~4 KB cookie | unlimited |
| Edge-compatible | ⭐ yes (verify with `jose`) | ⚠️ needs a DB reachable from the edge |

⭐ **Same trade-off as everywhere: statelessness costs revocation.** Short-lived access tokens
with a refresh flow, or database sessions when "log out everywhere" and instant bans matter
(most real products). See [../Django/auth.md](../Django/auth.md).

**Cookie settings — non-negotiable:**

```ts
cookies().set("session", token, {
  httpOnly: true,      // ⭐⭐ invisible to JS — an XSS can't steal it
  secure: true,        // HTTPS only
  sameSite: "lax",     // ⭐ CSRF mitigation
  path: "/",
  maxAge: 60 * 60 * 24 * 7,
});
```

⚠️⚠️ **Never store a token in `localStorage`.** Any XSS — including one from a compromised npm
dependency — reads it instantly. `httpOnly` cookies are the only storage a script can't touch.

---

## 3. Libraries

| Library | Notes |
|---|---|
| **Auth.js (NextAuth v5)** | ⭐ the default — OAuth providers, sessions, works with the App Router |
| **Clerk / Auth0 / WorkOS** | managed; fastest to ship, ⚠️ vendor lock-in and per-MAU cost |
| **Lucia** *(now a learning resource)* | teaches you to roll sessions yourself |
| **Supabase / Firebase Auth** | bundled with the backend |
| **Your own Django backend** | ⭐ Next holds an `httpOnly` cookie and proxies to Django |

```ts
// auth.ts — Auth.js v5
export const { handlers, auth, signIn, signOut } = NextAuth({
  providers: [GitHub, Credentials({ /* ... */ })],
  session: { strategy: "database" },
  callbacks: {
    session({ session, user }) { session.user.role = user.role; return session; },
  },
});

// app/api/auth/[...nextauth]/route.ts
export const { GET, POST } = handlers;
```

```tsx
const session = await auth();                    // ⭐ Server Component / Action / handler
if (!session) redirect("/login");
```

⭐ **Next.js + a Django backend is a common architecture** and worth having an opinion on:
let Django own users, tokens, and permissions; Next stores the session in an `httpOnly` cookie
and calls Django from **Server Components** — so the token never reaches the browser. Use a
`rewrite` to keep it same-origin and avoid CORS entirely
([api_middleware.md §6](api_middleware.md)).

---

## 4. Authorisation

```ts
// ⭐ scope every query by owner — don't fetch then check
const order = await db.order.findFirst({ where: { id, userId: session.user.id } });
if (!order) notFound();                          // ⭐ 404, not 403 — don't confirm existence

// role checks belong in the DAL, not scattered through components
export async function requireRole(role: Role) {
  const user = await getCurrentUser();
  if (!user || user.role !== role) throw new ForbiddenError();
  return user;
}
```

⚠️⚠️ **IDOR is as common here as in any backend** — `/orders/[id]` that fetches by id alone
returns anyone's order. Scoping the `where` clause makes it structurally impossible.

⚠️ **Client-side role checks are cosmetic.** `{user.isAdmin && <DeleteButton/>}` hides the
button; it does not stop a POST to the Server Action behind it. Hide *and* enforce.

---

## 5. Next.js-specific security ⚠️

| Risk | Detail |
|---|---|
| **Server Action = public endpoint** | ⭐⭐ Next generates a callable URL. Authenticate, authorise, and validate **inside every action** |
| **Middleware bypass** | ⚠️ CVE-2025-29927 allowed header spoofing past middleware — never rely on it alone |
| **`NEXT_PUBLIC_` leakage** | ⭐ inlined into the client bundle. `import "server-only"` to guard secret modules |
| **Props leak to the client** | ⚠️ everything a Server Component passes is in the RSC payload — pass a name, not the whole user row |
| **XSS** | React escapes by default; `dangerouslySetInnerHTML` is the hole. Sanitise with DOMPurify + a CSP |
| **Open redirect** | ⚠️ validate `?next=` against an allow-list before `redirect()` |
| **Supply chain** | ⚠️ one malicious dependency reads `localStorage`, env vars, and the DOM — lockfiles, `npm audit`, minimal deps |
| **Rate limiting** | none built in — Upstash Ratelimit or a WAF, especially on login and actions |

⭐ **CSRF:** Server Actions verify `Origin`/`Host` and are POST-only, and `SameSite=Lax`
covers most cases — but a cookie-authenticated **route handler** still needs explicit thought.
The CSRF-vs-CORS distinction is identical to the backend one
([../Django/security.md](../Django/security.md)): CORS is a browser permission mechanism, not
a CSRF defence.

```ts
// next.config.ts — security headers
headers: [{ key: "Content-Security-Policy", value: "default-src 'self'" },
          { key: "X-Frame-Options", value: "DENY" },
          { key: "Strict-Transport-Security", value: "max-age=63072000; includeSubDomains" }]
```

⚠️ CSP with Next requires a **nonce** for its inline scripts — via middleware.

---

## 6. Patterns

```tsx
// login — a Server Action, works without JS ⭐
"use server";
export async function login(prev: State, formData: FormData) {
  const parsed = LoginSchema.safeParse(Object.fromEntries(formData));
  if (!parsed.success) return { error: "Invalid credentials" };   // ⭐ generic message

  const user = await verifyCredentials(parsed.data);
  if (!user) return { error: "Invalid credentials" };             // ⭐ SAME message
  await createSession(user.id);
  redirect("/dashboard");
}
```

⭐ **Identical error text for "no such user" and "wrong password"** — different messages are an
account-enumeration oracle.

```tsx
// reading the session in a client component
"use client";
const { data: session } = useSession();          // Auth.js
// ⭐ or pass it down from a Server Component — no extra request
```

**Also:** rotate the session id on login (session fixation), rate-limit login attempts, keep
refresh tokens `httpOnly` and rotate them, and log auth failures with a request id.

---

## 7. Interview points

- **Where do you enforce auth in Next.js? ⭐⭐** At the data access point — page, Server Action,
  route handler, or ideally a shared DAL. Middleware is a UX redirect, not a security boundary.
- **Why isn't a check in `layout.tsx` enough?** Layouts don't re-render on every navigation and
  pages can be requested directly.
- **Why isn't middleware enough?** Edge runtime can't query the database, so it can only
  inspect a cookie — and it has been bypassable (CVE-2025-29927).
- **Cookie session vs database session?** No lookup vs instant revocation — statelessness
  costs you the ability to log someone out.
- **Where should the token live? ⭐** An `httpOnly`, `secure`, `sameSite` cookie — never
  `localStorage`, which any XSS reads.
- **What's the risk with Server Actions? ⭐⭐** They compile to public POST endpoints; each one
  needs its own authentication, authorisation, and validation.
- **How do you prevent IDOR?** Scope the query by the session user rather than fetching by id
  and checking after; return 404 rather than 403.
- **How do secrets leak?** `NEXT_PUBLIC_` inlining, and props passed to client components —
  everything in the RSC payload is public.
- **Are client-side role checks security?** No — they hide UI. The server must enforce.
- **How do you connect Next.js to a Django backend securely?** Session in an `httpOnly` cookie,
  server-side calls from Server Components so the token never reaches the browser, same-origin
  via rewrites.
- **Why the same error for unknown user and wrong password?** To prevent account enumeration.
