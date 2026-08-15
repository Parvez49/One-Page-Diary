# Linux Networking — Diagnosis & Tools

> SSH & tunnels: **[gitssh.md](gitssh.md)** · Ports held by processes: **[process.md](process.md)**

---

## 1. The debugging ladder ⭐⭐

"The service is unreachable" — climb the layers in order and you find the fault in minutes.
Guessing means you'll be reading nginx configs when the problem is DNS.

```
 7  Application   curl -v https://api.example.com/health     → TLS, HTTP status, headers
 4  Transport     nc -zv api.example.com 443                 → is the PORT open?
 3  Network       ping / traceroute / ip route               → is the HOST reachable?
 —  Naming        dig api.example.com                        → does the name RESOLVE?
 2  Link          ip link / ip addr                          → is the interface UP?
 0  Local         ss -tlnp                                   → is it even LISTENING here?
```

**Ask these five in this order:**

1. **Is it listening?** `ss -tlnp | grep 8080`
2. **On the right address?** ⭐ `127.0.0.1:8080` is reachable *only from the box*.
   `0.0.0.0:8080` accepts from anywhere. This single distinction explains a large share of
   "works locally, not remotely" reports.
3. **Does the name resolve?** `dig +short host`
4. **Is the port reachable from outside?** `nc -zv host 8080` — a hang means a firewall is
   *dropping*; instant "refused" means nothing is listening.
5. **Does the app respond correctly?** `curl -v`

---

## 2. Interfaces & routing (`ip` — `ifconfig` is deprecated)

```bash
ip a                          # ⭐ addresses (= ip addr show)
ip link                       # interfaces + state UP/DOWN + MAC
ip r                          # ⭐ routing table (= ip route)
ip neigh                      # ARP cache — MAC ↔ IP on the local segment

ip route get 8.8.8.8          # ⭐ WHICH interface/gateway would be used for this dest
ip -s link show eth0          # per-interface stats — errors, drops
```

**Reading `ip r`:**

```
default via 192.168.1.1 dev eth0        ← the DEFAULT GATEWAY: everything not matched below
192.168.1.0/24 dev eth0 scope link      ← local subnet, no gateway needed
```

⭐ **`ip route get <ip>` is the fastest routing answer** — it resolves policy, multiple NICs,
and VPN split-tunnels for you instead of making you read tables.

```bash
sudo ip addr add 192.168.1.50/24 dev eth0     # temporary, gone on reboot
sudo ip link set eth0 up
```

Permanent config: `/etc/netplan/*.yaml` (Ubuntu), `nmcli` (NetworkManager), or
`/etc/network/interfaces` (older Debian).

---

## 3. Sockets — `ss` (replaces `netstat`)

```bash
ss -tlnp        # ⭐⭐ THE one to memorise: TCP, Listening, Numeric, Process
ss -tunlp       # + UDP
ss -tp          # established TCP connections with processes
ss -s           # summary counts by state
ss -tn state established '( dport = :443 )'
ss -tn dst 10.0.0.5          # everything to one host
```

**Flags:** `-t` TCP · `-u` UDP · `-l` listening · `-n` numeric (**⭐ skips DNS — much faster**)
· `-p` process (needs root) · `-a` all.

```bash
ss -tlnp
# LISTEN 0 511  127.0.0.1:8000  0.0.0.0:*  users:(("gunicorn",pid=1234,fd=8))
#              └────┬─────────┘
#                   └─ ⭐ localhost-only: nginx on the same box can reach it, nothing else can
```

```bash
sudo lsof -i :8080          # ⭐ who holds this port ("Address already in use")
sudo fuser -k 8080/tcp      # ⚠️ kill whatever holds it
```

**TCP states you should recognise:**

- **`TIME_WAIT`** — normal, on the side that closed first, held ~60s to absorb stray packets.
  Thousands of them is usually fine, not a leak.
- **`CLOSE_WAIT`** ⚠️ — **the peer closed and your application never called `close()`**. This
  *is* an application bug (leaked sockets) and it will exhaust file descriptors.
- **`SYN_SENT`** piling up — packets are leaving and nothing answers: firewall dropping, or
  the host is down.

---

## 4. Connectivity tests

```bash
ping -c 4 8.8.8.8              # ICMP reachability + latency
ping -c 4 google.com           # ⭐ if the IP pings and the name doesn't → DNS
traceroute example.com         # hop-by-hop path
mtr example.com                # ⭐ traceroute + continuous loss stats — best for flaky links

nc -zv host 5432               # ⭐ is the TCP port open? (-z scan, -v verbose)
nc -zv -w3 host 5432           # with timeout
telnet host 5432               # older equivalent
timeout 3 bash -c '</dev/tcp/host/5432' && echo open    # ⭐ no tools installed
```

⚠️ **`ping` failing does not mean the host is down** — cloud providers and firewalls routinely
block ICMP while TCP works fine. Confirm with `nc -zv` before declaring an outage.

⭐ **Refused vs timeout is the most useful signal in network debugging:**

| Result | Means |
|---|---|
| **Connection refused** (instant) | reached the host, **nothing listening** on that port (RST) |
| **Timeout** (hangs) | ⭐ a **firewall/security group is silently DROPPING** packets, or wrong host |
| **No route to host** | routing/gateway problem |

---

## 5. DNS

```bash
dig example.com                # ⭐ full answer with TTL
dig +short example.com
dig @8.8.8.8 example.com       # ⭐ bypass local resolver — is it MY resolver that's broken?
dig example.com MX / NS / TXT / AAAA
dig +trace example.com         # follow delegation from the root
host example.com               # quick
getent hosts example.com       # ⭐ what the SYSTEM resolves (honours /etc/hosts + nsswitch)
```

⭐ **`dig` bypasses `/etc/hosts` and NSS; `getent hosts` doesn't.** When `dig` works but your
app can't resolve, the difference is `/etc/hosts` or `nsswitch.conf` — check with `getent`.

**Resolution order** is set by `/etc/nsswitch.conf` (`hosts: files dns`) → `/etc/hosts` first,
then DNS from `/etc/resolv.conf`.

```bash
cat /etc/resolv.conf
resolvectl status              # ⭐ systemd-resolved: the ACTUAL upstream servers
resolvectl flush-caches
```

⚠️ On systemd-resolved systems `/etc/resolv.conf` shows the stub `127.0.0.53` — reading it
tells you nothing about the real upstream. Use `resolvectl status`.

⚠️ **A DNS record you changed but nothing picks up = TTL caching.** `dig` shows the remaining
TTL; that's the wait.

---

## 6. HTTP debugging with curl ⭐

```bash
curl -v https://api.example.com/health          # ⭐ request + response headers + TLS
curl -I https://example.com                     # headers only (HEAD)
curl -sS -o /dev/null -w '%{http_code} %{time_total}s\n' https://example.com
curl -L url                                     # follow redirects
curl -X POST -H 'Content-Type: application/json' -d '{"a":1}' url
curl --resolve api.example.com:443:10.0.0.5 https://api.example.com/   # ⭐ test a specific
                                                # backend without touching DNS or /etc/hosts
curl -k https://self-signed                     # ⚠️ skip TLS verification — debugging only
curl --unix-socket /var/run/docker.sock http://localhost/version
```

```bash
# ⭐ full timing breakdown — where the latency actually is
curl -w '@-' -o /dev/null -s https://example.com <<'EOF'
dns: %{time_namelookup}  connect: %{time_connect}  tls: %{time_appconnect}
ttfb: %{time_starttransfer}  total: %{time_total}
EOF
```

**TLS:**

```bash
openssl s_client -connect example.com:443 -servername example.com </dev/null
echo | openssl s_client -connect example.com:443 2>/dev/null | openssl x509 -noout -dates
```

⚠️ **`-servername` matters.** Without SNI you may get the default vhost's certificate and
chase a "wrong certificate" that isn't real.

---

## 7. Firewall

```bash
sudo ufw status verbose           # Ubuntu's friendly frontend
sudo ufw allow 443/tcp
sudo ufw allow from 10.0.0.0/8 to any port 5432    # ⭐ scope by source

sudo iptables -L -n -v            # legacy, still everywhere
sudo nft list ruleset             # modern nftables
```

⚠️ **Before enabling a firewall on a remote box, allow SSH first** (`sudo ufw allow 22`) —
`ufw enable` will otherwise cut your session and lock you out.

⚠️ **Docker bypasses ufw.** Published container ports are inserted into `DOCKER` iptables
chains ahead of ufw's rules, so `-p 5432:5432` is world-reachable despite a "deny" policy.
Bind to localhost instead: `-p 127.0.0.1:5432:5432`.

⭐ In cloud environments check the **security group / network ACL** before the host firewall —
a dropped-packet timeout is far more often the cloud layer.

---

## 8. Packet capture & bandwidth

```bash
sudo tcpdump -i any -n port 5432                  # ⭐ -n: no DNS, much faster
sudo tcpdump -i eth0 -n host 10.0.0.5 and port 443
sudo tcpdump -i any -n -A port 80                 # ASCII payload (plain HTTP)
sudo tcpdump -i any -w cap.pcap port 443          # ⭐ write for Wireshark
sudo tcpdump -i any -n 'tcp[tcpflags] & tcp-syn != 0'   # SYNs only — connection attempts
```

⭐ **tcpdump settles arguments.** "Our service never got the request" vs "your service never
sent it" — capture on both sides and the packets say who's right.

```bash
iftop -i eth0        # bandwidth by connection
nethogs              # ⭐ bandwidth by PROCESS
vnstat               # historical totals
```

---

## 9. Interview points

- **"Works locally, not remotely."** The service is bound to `127.0.0.1` instead of `0.0.0.0`
  — check `ss -tlnp`. Then firewall, then security group.
- **Connection *refused* vs *timeout*?** Refused = host reached, nothing listening (RST sent).
  Timeout = packets silently dropped by a firewall, or wrong host. Refused is progress.
- **Many `CLOSE_WAIT` sockets — what's wrong?** Your application isn't calling `close()` on
  sockets the peer already closed. Application bug, will exhaust FDs.
- **Is `TIME_WAIT` a problem?** Usually no — it's the correct behaviour of whichever side
  closed first, cleared after ~60s.
- **`netstat` vs `ss`?** `ss` is the modern replacement — reads netlink instead of walking
  `/proc`, so it's much faster on busy hosts.
- **How do you find which process owns a port?** `ss -tlnp` or `sudo lsof -i :PORT`.
- **DNS resolves with `dig` but the app fails.** `dig` skips `/etc/hosts` and NSS — test with
  `getent hosts` instead.
- **How do you test a specific backend behind a load balancer?**
  `curl --resolve host:443:<backend-ip>`.
- **`ping` fails but the site loads.** ICMP is blocked; it says nothing about TCP.
