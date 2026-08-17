# Transactional email in production

> DNS records go in alongside the A-record: **[tls_certbot.md](tls_certbot.md)** ·
> Sending asynchronously (never in the request cycle): `../Web/Django/async_tasks.md`

> Note to self: env-based SMTP config is NOT the whole story. The config is standard;
> the constraint I didn't know about is **who is on the other end of that SMTP connection**.

## Two separate concerns

1. **Config mechanism** — env vars read by the framework's SMTP backend
   (Django example, works the same idea in any stack):

   ```env
   EMAIL_HOST=smtp.resend.com
   EMAIL_PORT=587
   EMAIL_USE_TLS=True
   EMAIL_HOST_USER=resend
   EMAIL_HOST_PASSWORD=<api-key>
   DEFAULT_FROM_EMAIL=noreply@yourdomain.com
   ```

   This IS production-grade, and provider-agnostic: switching providers later = edit
   4 env values, zero code changes. Always do it this way.

2. **The provider** — something real must be behind `EMAIL_HOST` actually delivering
   mail. The env vars cannot point at nothing. This is the part that needs a decision.

## Provider options (the constraint)

| Option | Verdict |
|---|---|
| Transactional provider (Resend / SES / Mailgun / Postmark) | ✅ What every production system uses |
| Self-hosted postfix on the VPS | ❌ Trap: Gmail/Outlook distrust unknown VPS IPs (hosting-provider ranges especially) → spam folder or rejected. You inherit DKIM/SPF/DMARC + IP-reputation maintenance forever |
| Gmail account over SMTP | 🟡 OK for **local dev only** — see breakdown below |

### 🔴 Gmail SMTP — why not production

```env
EMAIL_HOST=smtp.gmail.com
EMAIL_HOST_USER=you@gmail.com
EMAIL_HOST_PASSWORD=<16-char app password>
```

**✅ Pros (why it's tempting)**
- Zero setup — no signup, no domain, works with any Gmail account in minutes
- Free
- Good enough to sanity-check "does my SMTP code even fire" during local dev

**❌ Cons (why it breaks in production)**
- **Hard send caps** — ~500 msgs/day, and bursts get throttled well before that
- **From-address spoofing flag** — if `DEFAULT_FROM_EMAIL=noreply@yourdomain.com` but
  you authenticate as `you@gmail.com`, SPF/DKIM don't line up for your domain →
  looks like spoofing to receiving servers → spam or rejected
- **No deliverability tooling** — no bounce/complaint webhooks, no analytics, no
  dedicated reputation; you're flying blind on whether verification/reset emails
  actually land
- **Silent account risk** — Google can revoke the app password or flag the account
  for "unusual automated activity" with no warning, which quietly kills
  signup/login emails in prod
- Arguably against Google's ToS for transactional app traffic at any real volume

> **Rule of thumb:** great for `manage.py test_email` on your laptop, never wire it
> into a deployed `.env`.

### Other providers — quick notes

- **Resend** ✅ — easiest setup, free ~100 emails/day, plenty for staging/demo and
  fine to carry into production (paid tier if volume grows). Good default choice.
- **Amazon SES** 💸 — cheapest at scale, but starts in *sandbox mode*: can only send
  to pre-verified recipients until you request production access. Annoying for demos
  where clients register with arbitrary addresses.
- **Mailgun** 🟡 — solid, but the free tier is basically a short trial now — budget
  for it from day one.
- **Postmark** ✅ — excellent deliverability reputation, slightly pricier, great if
  email reliability is critical (e.g. password resets).

## Domain verification (always required)

Every provider requires **verifying your sending domain** before you can send from
`noreply@yourdomain`: add SPF + DKIM DNS records they give you (~5 min, do it
alongside the A-records when setting up a new domain). Without this, mail is
rejected or spam-foldered regardless of provider.

## Why it matters at all

Flows that silently break without a working provider: email verification before
login, password reset, invite/notification emails. Local dev hides this (console
email backend prints to stdout) — the gap only shows on the first real deployment.

## Sending it correctly ⭐

⚠️ **Never send email inside the request/response cycle.** SMTP is a network call to a third
party; a slow or down provider turns a 200ms signup into a 30-second timeout and holds an
application worker the whole time ([app_servers.md](app_servers.md)). Queue it —
`send_mail` goes in a Celery task, enqueued inside `transaction.on_commit` so the task can't
run before the user row is committed (`../Web/Django/async_tasks.md`).

⚠️ Email delivery is **at-least-once and unverifiable**: the provider accepting a message is
not the recipient receiving it. Handle bounce/complaint webhooks, make the task idempotent
(a retry must not send a second "reset your password" with a fresh token), and never treat a
send as a state transition.

---

## Interview points

- **Why not self-host postfix?** ⚠️ IP reputation. VPS ranges are distrusted by Gmail/Outlook,
  and you inherit SPF/DKIM/DMARC plus reputation maintenance forever.
- **Why not Gmail SMTP in production?** ⭐ ~500/day cap, no bounce webhooks, silent account
  revocation, and a `From:` that doesn't match the authenticated account looks like spoofing.
- **What are SPF, DKIM and DMARC?** ⭐ SPF authorises sending IPs, DKIM signs the message,
  DMARC tells receivers what to do when either fails — and where to report. Without them,
  mail is spam-foldered or rejected regardless of provider.
- **Why is provider config in env vars?** ⭐ Swapping providers becomes 4 value edits and zero
  code changes.
- **Where does the send happen?** ⚠️ In a background task, not the request — and enqueued via
  `on_commit`.
- **What does "sent" mean?** ⚠️ Only that the provider accepted it. Delivery is observed via
  bounce/complaint webhooks.
- **SES sandbox** — new accounts can only send to pre-verified addresses until you request
  production access. Plan for the lead time before a demo.
