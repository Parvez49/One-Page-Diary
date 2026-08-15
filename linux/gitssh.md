# SSH — Keys, Config, Tunnels

> Covers key management, multi-account Git, server access, and port forwarding.
> Git commands: **[git.md](git.md)**.

---

## 1. What SSH actually does

A protocol for an **encrypted channel to a remote machine** — shell, file transfer (`scp`,
`sftp`, `rsync`), port forwarding, and Git transport all ride on it. Default port **22**.

**The handshake, in the order it happens:**

1. **Server authenticates itself** to you — presents its host key; your client checks it
   against `~/.ssh/known_hosts`. This is what stops MITM, and why a changed host key is a
   loud warning rather than a prompt.
2. **Key exchange** → an ephemeral session key (forward secrecy: recording the traffic and
   stealing the private key later still doesn't decrypt it).
3. **You authenticate to the server** — the client signs a challenge with your **private**
   key; the server verifies it against a **public** key listed in `~/.ssh/authorized_keys`.

⚠️ **The private key never leaves your machine and is never sent.** Only a signature crosses
the wire. This is the whole reason key auth beats passwords.

---

## 2. The files in `~/.ssh/`

| File | What it is | Permissions |
|---|---|---|
| `id_ed25519` | **private key** — secret; the public key is derived from it | **`600`** |
| `id_ed25519.pub` | **public key** — safe to publish; goes on servers/GitHub | `644` |
| `authorized_keys` | public keys allowed to log in **as this user on this machine** | **`600`** |
| `known_hosts` | host keys of servers you've accepted (server → you trust) | `644` |
| `config` | per-host client settings | **`600`** |
| `~/.ssh/` | the directory itself | **`700`** |

⚠️ **SSH refuses to use over-permissive keys.** `Permissions 0644 ... are too open` means:

```bash
chmod 700 ~/.ssh && chmod 600 ~/.ssh/id_ed25519 ~/.ssh/config
```

**`authorized_keys` vs `known_hosts`** — the pair people mix up:
`authorized_keys` = *"who may log in to me."* `known_hosts` = *"which servers I have verified."*

---

## 3. Generating keys

```bash
ls -al ~/.ssh                                        # what already exists

ssh-keygen -t ed25519 -C "you@mail.com" -f ~/.ssh/gh_personal    # ⭐ preferred
ssh-keygen -t rsa -b 4096 -C "you@mail.com" -f ~/.ssh/legacy     # only for old servers
```

**Why `ed25519` over RSA:** far smaller keys (68 vs 800+ chars), faster signing, no key-size
footgun, immune to the weak-random-`e` class of RSA mistakes. Use RSA-4096 only when the
target is too old to support Ed25519.

```bash
cat ~/.ssh/gh_personal.pub          # paste into GitHub → Settings → SSH and GPG keys
ssh-keygen -lf ~/.ssh/gh_personal.pub    # fingerprint — compare against what GitHub shows
ssh-keygen -p -f ~/.ssh/gh_personal      # add/change the passphrase on an existing key
ssh-keygen -y -f ~/.ssh/gh_personal      # ⭐ regenerate the .pub from the private key
```

**Always set a passphrase.** An unencrypted private key is a plaintext credential; anything
that reads your disk owns your servers. The agent (§4) means you type it once per session.

### ssh-agent

```bash
eval "$(ssh-agent -s)"              # start it
ssh-add ~/.ssh/gh_personal          # unlock once; agent holds the decrypted key
ssh-add -l                          # list loaded keys
ssh-add -t 8h ~/.ssh/key            # ⭐ auto-expire
ssh-add -D                          # forget everything
```

⚠️ **Agent forwarding (`-A`)** lets the remote host use your local keys — convenient for
`git pull` on a server, but **root on that host can hijack your agent socket** and
authenticate as you anywhere. Prefer `ProxyJump` (§6). If you must, scope it per-host in
config, never globally.

---

## 4. `~/.ssh/config` — the highest-value file here

Turns long commands into one word, and is how multi-account Git works.

```sshconfig
# --- defaults for every host ---
Host *
    AddKeysToAgent yes
    ServerAliveInterval 60          # keep long sessions from dropping
    ServerAliveCountMax 3

# --- GitHub: personal (default) ---
Host github.com
    HostName github.com
    User git                        # ALWAYS git for GitHub, never your username
    IdentityFile ~/.ssh/gh_personal
    IdentitiesOnly yes              # ⭐ see below

# --- GitHub: work, under a fake Host alias ---
Host github-work
    HostName github.com             # the REAL host
    User git
    IdentityFile ~/.ssh/gh_work
    IdentitiesOnly yes

# --- a server ---
Host prod
    HostName 203.0.113.10
    User deploy
    Port 2222
    IdentityFile ~/.ssh/prod_key
```

⭐ **`IdentitiesOnly yes` is not optional.** Without it SSH offers *every* key in the agent in
turn. GitHub authenticates you as the owner of the **first key that works**, so your work push
silently lands as your personal account — and after ~5 wrong keys the server drops you with
`Too many authentication failures`.

**`Host` is a local alias; `HostName` is the real address.** That's the entire trick behind
multi-account Git.

---

## 5. Multiple GitHub accounts

```bash
ssh-keygen -t ed25519 -C "work@mail.com" -f ~/.ssh/gh_work
# add gh_work.pub to the WORK GitHub account (a key can only be on one account)
```

With the config above:

```bash
ssh -T git@github.com        # → Hi personal-user!
ssh -T git@github-work       # → Hi work-user!    ⭐ verifies which identity you get
```

Then point each repo at the right alias:

```bash
git clone git@github-work:company/repo.git       # new clone

git remote -v                                     # existing repo
git remote set-url origin git@github-work:company/repo.git
```

⚠️ **Also set the commit identity per repo** — the SSH key controls *push permission*, but
commit author comes from `user.email`. Wrong email = commits not attributed to you:

```bash
git config user.email "work@mail.com"
```

Better, automate it by directory (see `git.md §2` — `includeIf "gitdir:~/work/"`).

---

## 6. Server access

```bash
ssh user@203.0.113.10
ssh -p 2222 user@host              # non-default port
ssh prod                           # with the config alias
```

**Push your key to the server** (needs password auth once):

```bash
ssh-copy-id -i ~/.ssh/prod_key.pub deploy@203.0.113.10
# appends the .pub to the server's ~/.ssh/authorized_keys with correct permissions

# manual equivalent, if ssh-copy-id is unavailable:
cat ~/.ssh/prod_key.pub | ssh deploy@host "mkdir -p ~/.ssh && chmod 700 ~/.ssh \
  && cat >> ~/.ssh/authorized_keys && chmod 600 ~/.ssh/authorized_keys"
```

**Bastion / jump host** — reach a private box through a gateway:

```bash
ssh -J bastion.example.com deploy@10.0.1.50
```
```sshconfig
Host db-private
    HostName 10.0.1.50
    User deploy
    ProxyJump bastion.example.com      # ⭐ safer than agent forwarding: keys stay local
```

**Other transports over SSH:**

```bash
scp file.txt prod:/tmp/                       # copy up
scp prod:/var/log/app.log ./                  # copy down
rsync -avz --progress ./dist/ prod:/srv/app/  # ⭐ incremental, resumable — prefer for size
ssh prod 'systemctl status nginx'             # run one command and exit
```

---

## 7. Port forwarding (tunnels) ⭐

The most senior-flavoured part of SSH. Three directions:

```
Local   -L 5433:localhost:5432   me → remote     reach a remote port as if it were local
Remote  -R 8080:localhost:3000   remote → me     expose MY service to the remote side
Dynamic -D 1080                  SOCKS proxy     route arbitrary traffic through the host
```

**Local forward** — connect to a database that only listens on the server's localhost:

```bash
ssh -L 5433:localhost:5432 prod
# now: psql -h localhost -p 5433   → actually hits the remote Postgres
```

**Local forward through a bastion** — the DB is on a *third* machine:

```bash
ssh -L 5433:10.0.1.50:5432 bastion
# 10.0.1.50:5432 is resolved FROM the bastion, not from you
```

**Remote forward** — let a colleague or a webhook reach your local dev server:

```bash
ssh -R 8080:localhost:3000 prod
# requires GatewayPorts yes on the server to bind beyond its own localhost
```

**Dynamic (SOCKS5)** — a poor man's VPN:

```bash
ssh -D 1080 -N prod            # then point the browser at SOCKS5 localhost:1080
```

Useful flags: `-N` (no shell, tunnel only), `-f` (background), `-T` (no TTY).

---

## 8. Hardening `sshd` (server side)

`/etc/ssh/sshd_config` — then `sudo sshd -t && sudo systemctl reload ssh`.

```sshconfig
PasswordAuthentication no        # ⭐ the single biggest win — kills brute force
PermitRootLogin no               # log in as a user, then sudo (audit trail)
PubkeyAuthentication yes
AllowUsers deploy admin          # explicit allow-list
MaxAuthTries 3
X11Forwarding no
ClientAliveInterval 300
```

⚠️ **Keep your current session open** and verify from a *second* terminal before disconnecting.
Locking yourself out of a remote box with `PasswordAuthentication no` and no working key means
console/rescue-mode recovery.

⚠️ `sshd -t` first: a syntax error plus a restart can leave sshd down entirely — `reload` is
gentler than `restart` because existing sessions survive.

Also standard: `fail2ban` for repeat offenders, and moving off port 22 (stops log noise, not
attackers).

---

## 9. Troubleshooting

```bash
ssh -v  git@github.com          # verbose; -vv / -vvv for more
ssh -T  git@github.com          # GitHub: identity test (no shell is expected)
ssh -G  github-work             # ⭐ show the FINAL resolved config for a host
```

`ssh -v` lines that matter: `Offering public key: ...` (which key was tried) and
`Authentications that can continue:` (what the server will accept).

| Symptom | Cause / fix |
|---|---|
| `Permission denied (publickey)` | key not in `authorized_keys`, or wrong key offered → `IdentitiesOnly yes` |
| `Too many authentication failures` | agent offered too many keys before the right one → `IdentitiesOnly yes` |
| `Permissions 0644 ... too open` | `chmod 600` the private key, `700` the dir |
| `REMOTE HOST IDENTIFICATION HAS CHANGED` | server rebuilt/reimaged — **or MITM**. Verify out-of-band, then `ssh-keygen -R host` |
| Pushed as the wrong GitHub account | wrong key matched first → `IdentitiesOnly yes` + `ssh -T` per alias |
| Works with `ssh`, fails in cron/CI | no agent in that environment → use `IdentityFile` explicitly |
| Hangs then times out | firewall/port, not auth. `nc -zv host 22` first |

**Server side:** `sudo journalctl -u ssh -f` shows exactly why an attempt was rejected — far
faster than guessing from the client.

---

## 10. Interview points

- **Why is key auth safer than a password?** The private key never crosses the network; only a
  signature does. Nothing replayable is transmitted, and there's nothing to brute-force
  remotely.
- **Symmetric or asymmetric?** Both: asymmetric for the handshake and authentication,
  then a **symmetric session key** for the actual data (orders of magnitude faster).
- **What is `known_hosts` protecting against?** MITM — it pins the server's identity so a
  substituted server is detected rather than silently trusted.
- **Why is agent forwarding risky?** Root on the intermediate host can use your forwarded
  socket to authenticate as you to any host that trusts your key. `ProxyJump` avoids it.
- **How do deploy keys differ from user keys?** A deploy key is scoped to **one repository**
  (read-only by default) instead of carrying a whole user's access — the right choice for CI.
