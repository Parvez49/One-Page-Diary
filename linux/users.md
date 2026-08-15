# Linux Users, Groups & Privilege

> File access rules: **[permissions.md](permissions.md)** · SSH login: **[gitssh.md](gitssh.md)**

---

## 1. Users are numbers, not names

The kernel only knows **UIDs**. Names are a userspace convenience resolved through
`/etc/passwd` — which is why two names sharing UID 0 are *both* root.

| Type | UID range | Purpose |
|---|---|---|
| **root** | **0** | superuser — bypasses all permission checks |
| **system / service** | 1–999 | created by packages: `www-data`, `postgres`, `nobody`. **No login shell**, often no home |
| **regular** | **1000+** | humans |

```bash
id                     # uid, gid, all groups for me
id alice
whoami                 # effective username
who / w                # who is logged in now (w adds what they're running)
last -n 10             # ⭐ login history (from /var/log/wtmp)
getent passwd alice    # ⭐ queries passwd AND LDAP/SSSD — `grep /etc/passwd` misses those
```

⭐ **Root is UID 0, not the name "root."** A service account accidentally created with
`uid=0` has full root power under a harmless-looking name — a real audit finding:

```bash
awk -F: '$3==0 {print $1}' /etc/passwd     # should print exactly: root
```

---

## 2. The account files

### `/etc/passwd` — world-readable, **no passwords** despite the name

```
alice:x:1000:1000:Alice Rahman:/home/alice:/bin/bash
  │   │   │    │        │            │          └── login shell
  │   │   │    │        │            └───────────── home directory
  │   │   │    │        └────────────────────────── GECOS (full name, phone)
  │   │   │    └─────────────────────────────────── primary GID
  │   │   └──────────────────────────────────────── UID
  │   └──────────────────────────────────────────── 'x' = hash lives in /etc/shadow
  └──────────────────────────────────────────────── username
```

### `/etc/shadow` — mode `640`, root-only ⭐

```
alice:$6$xyz$hash...:19700:0:99999:7:::
  │        │           │   │   │   │
  │        │           │   │   │   └── warn days before expiry
  │        │           │   │   └────── max age (force change)
  │        │           │   └────────── min days between changes
  │        │           └────────────── last change (days since 1970-01-01)
  │        └──────────────────────────  $6$ = SHA-512  ($y$ = yescrypt on new distros)
  └───────────────────────────────────  username
```

**Why the split:** `/etc/passwd` must be world-readable so any program can map UID → name.
Hashes moved to `/etc/shadow` (root-only) so they can't be harvested and cracked offline.
A `!` or `*` in the hash field means **login disabled**; empty means **no password required** ⚠️.

### `/etc/group`

```
devs:x:1001:alice,bob        # group : x : GID : SECONDARY members
```

⭐ **A user's *primary* group is in `/etc/passwd`, not here.** That's why `alice` may not
appear in her own primary group's member list — a genuinely confusing detail.

---

## 3. Managing users

```bash
sudo useradd -m -s /bin/bash -c "Alice Rahman" alice   # ⭐ -m creates the home dir
sudo passwd alice
sudo adduser alice                # ⭐ Debian/Ubuntu: interactive wrapper, does the right thing

sudo usermod -aG docker alice     # ⭐⭐ -aG = APPEND to secondary groups
sudo usermod -g devs alice        # change PRIMARY group
sudo usermod -s /usr/sbin/nologin alice    # revoke shell access, keep the account
sudo usermod -L alice             # lock password
sudo usermod -U alice             # unlock

sudo userdel alice                # keeps /home/alice
sudo userdel -r alice             # ⚠️ also deletes home + mail spool
```

⚠️⚠️ **`usermod -G` without `-a` REPLACES all secondary groups.** `usermod -G docker alice`
silently removes her from `sudo`, `adm`, everything else. Locking an admin out of `sudo` this
way is a classic outage. **Always `-aG`.**

⚠️ **Group changes don't apply to existing sessions.** The group list is stamped on the
process at login. After `usermod -aG docker alice`, `id` still shows the old set until she
logs out and back in (`newgrp docker` gives a subshell in the meantime). Same for services —
a restart is required.

**Service accounts** get no login:

```bash
sudo useradd -r -s /usr/sbin/nologin -d /srv/app appuser    # -r = system UID (<1000)
```

⭐ Run every service as its own unprivileged user. If nginx is compromised while running as
root, the attacker owns the box; as `www-data`, they own the web files.

---

## 4. Groups

- **Primary group** — one per user, recorded in `/etc/passwd`, owns the files they create.
- **Secondary groups** — any number, from `/etc/group`, grant additional access.

```bash
sudo groupadd devs
sudo groupadd -g 1500 devs        # explicit GID (match across machines/NFS)
groups alice                      # her groups
getent group devs                 # members
sudo gpasswd -d alice devs        # remove from a group
sudo groupdel devs                # ⚠️ fails if it's someone's primary group
newgrp devs                       # subshell with devs as primary — no logout needed
```

**Shared team directory** — this is the pattern to know:

```bash
sudo chgrp -R devs /srv/project
sudo chmod -R 2775 /srv/project     # ⭐ setgid(2): new files inherit group `devs`
```

Without setgid every file lands in the creator's primary group and the team can't write to
each other's work. See `permissions.md §3`.

**Groups worth recognising:** `sudo`/`wheel` (admin), `adm` (read logs), `docker`
(⚠️ **equivalent to root** — a container can mount `/`), `www-data`, `systemd-journal`.

---

## 5. `sudo` vs `su` ⭐⭐

| | **`sudo`** | **`su`** |
|---|---|---|
| Stands for | *substitute user **do*** | *substitute user* |
| Password asked | **your own** | the **target user's** (i.e. root's) |
| Scope | **one command** | a whole shell until `exit` |
| Granularity | per-user, per-command rules | all-or-nothing |
| Auditing | ⭐ every command logged with who ran it | one "session opened" line |
| Root password needed | **no** | yes |

```bash
sudo apt update
sudo -u postgres psql        # ⭐ run as a specific NON-root user
sudo -i                      # root LOGIN shell (root's env, root's ~)
sudo -s                      # root shell, YOUR env
sudo -l                      # ⭐ what am I allowed to run?
sudo -k                      # forget the cached credential

su -                         # login shell as root (needs root's password)
su - alice                   # switch to alice
```

⭐ **Why `sudo` won:** Ubuntu ships with the root password **locked** (`!` in shadow). Nobody
knows a root password, so it can't leak or be brute-forced; access is granted per-user and
revoked by editing one file. And the audit trail (`/var/log/auth.log`) attributes every
privileged command to a **human**, which "everyone shares the root password" cannot.

⚠️ **`su -` vs `su`** — the dash loads the target's full login environment (`$PATH`, `$HOME`,
profile). Without it you keep *your* environment while being root, which produces confusing
`command not found` for `/sbin` binaries and files written into the wrong `$HOME`.

### sudoers

```bash
sudo visudo                     # ⭐ ALWAYS — it syntax-checks before saving
sudo visudo -f /etc/sudoers.d/deploy    # preferred: a drop-in file
```

```sudoers
alice   ALL=(ALL:ALL) ALL                          # full sudo
%devs   ALL=(ALL) NOPASSWD: /usr/bin/systemctl restart app   # ⭐ group, one command, no password
deploy  ALL=(ALL) NOPASSWD: /usr/bin/docker
```

Format: `user  HOST=(RUN_AS_USER:GROUP)  COMMANDS`. `%` prefixes a group.

⚠️ **A syntax error in `/etc/sudoers` locks everyone out of sudo.** `visudo` validates on
save — never edit it with a plain editor. Recovery means a root shell or single-user mode.

⚠️ **Restricting the command isn't restricting the power.** `NOPASSWD: /usr/bin/vim` is full
root — vim can shell out (`:!sh`). Same for `find -exec`, `less`, `awk`, `python`, and
anything with a `docker` socket. Grant specific, non-escaping binaries.

```bash
# Ubuntu: add to admin group
sudo usermod -aG sudo alice
```

---

## 6. Passwords & account policy

```bash
passwd                          # change my own
sudo passwd alice               # set someone else's
sudo passwd -l alice            # lock  (! in shadow)
sudo passwd -e alice            # ⭐ expire now — force change at next login
sudo chage -l alice             # view aging policy
sudo chage -M 90 -W 7 alice     # max 90 days, warn 7
```

**Login is not one thing — PAM decides.** `/etc/pam.d/` stacks modules for auth, account,
password, and session. It's why password complexity (`pam_pwquality`), MFA, LDAP, and
`pam_faillock` lockouts can be added without changing `login`, `sshd`, or `sudo` themselves.
You rarely edit PAM, but naming it as *the pluggable authentication layer* is the expected
senior answer.

---

## 7. Interview points

- **Difference between `sudo` and `su`?** Own password vs root's; one command vs a shell;
  per-command rules and a real audit trail vs all-or-nothing.
- **Why is `/etc/shadow` separate from `/etc/passwd`?** `passwd` must be world-readable for
  UID→name lookups; hashes would then be harvestable for offline cracking.
- **`usermod -G` vs `-aG`?** `-G` **replaces** the secondary group list — the classic way to
  remove yourself from `sudo`.
- **Added a user to `docker`/`sudo` but it doesn't work?** Groups are evaluated at login;
  log out and back in, or restart the service.
- **Primary vs secondary group?** Primary is in `/etc/passwd` and owns newly created files;
  secondary come from `/etc/group` and only grant access.
- **Why run services as non-root?** Blast radius — a compromised process is confined to that
  account's access instead of owning the host.
- **Is `docker` group membership safe?** No — it is effectively root, since you can mount the
  host filesystem into a container.
- **How do you check what sudo rights you have?** `sudo -l`.
- **What is PAM?** The pluggable stack that `login`, `sshd`, and `sudo` all delegate
  authentication to — where MFA, LDAP and lockout policies get inserted.
