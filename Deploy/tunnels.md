# Tunnels — exposing localhost (ngrok)

> Real ingress: **[nginx.md](nginx.md)** · Certificates: **[tls_certbot.md](tls_certbot.md)**

---

## 1. What it's for ⭐

A tunnel gives a public HTTPS URL that forwards to a port on your laptop, without a public IP,
port forwarding, a domain, or a certificate. The agent dials **out** to the provider, so it
works from behind NAT and corporate firewalls.

The cases where it's the right tool — all of them involve *someone else's server needing to
reach your machine*:

- ⭐ **Webhook development** — Stripe, GitHub, Twilio, payment gateways must POST to a public
  URL. This is the main reason tunnels exist.
- OAuth redirect URIs that reject `localhost`.
- Showing a work-in-progress to a client or tester.
- Testing on a real phone against your dev machine.

⚠️ **Not a deployment.** The URL dies with the process, throughput is limited, and every byte
of traffic transits a third party.

---

## 2. Single port

```bash
ngrok http 80        # free tier: ONE tunnel at a time
```

⚠️ The free tier gives a **random subdomain that changes on every restart** — so every restart
means re-registering the webhook URL with the provider. A reserved domain is the paid feature
that actually matters for webhook work.

---

## 3. Multiple ports at once ⭐

The config file is how you get several tunnels from one agent (frontend + API + admin):

```bash
ngrok config check          # ⭐ prints the path to ngrok.yml
```

```yaml
version: "2"
authtoken: <YOUR_AUTHTOKEN>      # ⚠️ a credential — never commit this file

tunnels:
  first:
    addr: 8001
    proto: http
  second:
    addr: 8002
    proto: http
  third:
    addr: 8003
    proto: http
```

```bash
ngrok start --all            # every tunnel in the file
ngrok start first second     # or a named subset
```

⚠️⚠️ **The authtoken is a live credential.** It's tied to your account and lets anyone who has
it open tunnels as you. Keep `ngrok.yml` out of git and out of notes; if one leaks, rotate it
in the ngrok dashboard immediately.

⭐ The local inspector at **http://127.0.0.1:4040** replays every request — the fastest way to
debug a webhook payload without re-triggering the provider.

---

## 4. What it breaks ⭐

| Issue | Why | Fix |
|---|---|---|
| `DisallowedHost` / 400 | app doesn't recognise the random hostname | add it to `ALLOWED_HOSTS` |
| Redirect loop / `http://` links | ⚠️ TLS terminates at ngrok; the app sees plain HTTP | trust `X-Forwarded-Proto` — same rule as [nginx.md](nginx.md) §3 |
| CSRF failures | origin doesn't match | add the tunnel URL to `CSRF_TRUSTED_ORIGINS` |
| Vite/webpack HMR fails | websocket + host-check | allow the host in the dev-server config |
| Anyone can reach it | ⚠️ **the URL is public** — no auth by default | `ngrok http --basic-auth`, and never tunnel a database or admin panel |

⚠️ A tunnel to a dev box typically exposes `DEBUG=True`, seeded data, and an unlocked admin to
the entire internet. Random URLs are not authentication — they get scanned. Keep tunnels
short-lived and shut them down when you're done.

**Alternatives:** `cloudflared tunnel` (free, named tunnels, ties into Cloudflare), `localtunnel`,
or `ssh -R` if you already have a public box.

---

## Interview points

- **What problem does a tunnel solve?** ⭐ An external service needs to reach a machine with no
  public IP — webhooks, OAuth callbacks, mobile testing.
- **Why does it work behind NAT?** The agent makes an **outbound** connection; traffic is
  reverse-proxied back down it.
- **Why isn't it a deployment?** ⚠️ Ephemeral URL, third-party dependency, throughput limits,
  no availability guarantee.
- **What breaks the app behind a tunnel?** ⭐ Host validation and `X-Forwarded-Proto` — the same
  two things that break behind any reverse proxy.
- **The security posture** ⚠️ — the URL is public and unauthenticated; a random subdomain is
  obscurity, not access control.
