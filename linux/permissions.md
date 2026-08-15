# Linux Permissions — chmod, Special Bits, umask, ACL

> Users & groups: **[users.md](users.md)** · File types & inodes: **[filesystem.md](filesystem.md)**

---

## 1. Reading a permission string

```bash
ls -l app.py
-rwxr-xr--  1 parvez devs  1234 Aug 15 12:00 app.py
```

```
   -    rwx      r-x      r--
   │    └─┬─┘    └─┬─┘    └─┬─┘
   │    owner    group    others
   └─ type
```

**Type character:** `-` regular · `d` directory · `l` symlink · `s` socket · `p` named pipe
· `c` character device (tty, random) · `b` block device (disks).

**The permission triads** — and this is the part that trips people up, because
**they mean different things for files and directories:**

| Bit | On a **file** | On a **directory** |
|---|---|---|
| **r** (4) | read contents | **list names** (`ls`) |
| **w** (2) | modify contents | **create/delete/rename entries** ⚠️ |
| **x** (1) | execute it | **enter/traverse** (`cd`, access anything inside) |

⭐ **Three consequences worth saying out loud:**

1. **`r` without `x` on a directory is nearly useless** — you can list names but `stat`
   nothing, so `ls -l` shows `?????????`. `x` without `r` is the opposite and is genuinely
   useful: you can `cd` in and open a known path, but not enumerate. That's how `/home/user`
   at `701` shares one file without exposing the directory.

2. **Deleting a file depends on the DIRECTORY's `w`, not the file's.** A read-only file in a
   writable directory can be deleted. This is *the* permissions question senior candidates
   still get wrong — and the reason `/tmp` needs the sticky bit (§3).

3. **Permissions are checked in order: owner → group → others, first match wins.** So
   `----rwx---` denies the *owner* everything while the group has full access. Being the
   owner is not automatically better.

---

## 2. chmod

### Numeric (octal)

```
 r = 4    w = 2    x = 1    - = 0
```

| Octal | Bits | Means |
|---|---|---|
| **7** | rwx | full |
| **6** | rw- | read + write |
| **5** | r-x | read + execute |
| **4** | r-- | read only |
| **0** | --- | none |

```bash
chmod 755 script.sh      # rwx owner, r-x group+others   ← executables, directories
chmod 644 notes.txt      # rw- owner, r-- others         ← normal files
chmod 600 ~/.ssh/id_ed25519   # ⭐ owner only            ← keys, secrets, .env
chmod 700 ~/.ssh              # ⭐ private directory
chmod 640 /etc/app.conf       # owner writes, group reads, others nothing
```

**Common defaults:** files `644`, directories `755`, scripts `755`, secrets `600`.

### Symbolic

```bash
chmod u+x script.sh          # add execute for owner
chmod g-w file               # remove group write
chmod o= file                # ⭐ strip others entirely (= sets EXACTLY)
chmod a+r file               # all
chmod u=rw,go=r file         # explicit set
chmod -R u+rwX,go+rX dir/    # ⭐ capital X: x on DIRECTORIES only, not every file
```

⭐ **`X` vs `x`** — `chmod -R a+x dir/` marks every `.txt` and `.jpg` executable, which is
sloppy and a mild security smell. `X` applies execute only where it already exists or to
directories. Use `X` for recursive operations, always.

```bash
chmod -R 755 dir/            # recursive
chmod -Rv 755 dir/           # verbose: report every file
chmod -Rc 755 dir/           # ⭐ only report actual CHANGES
chmod --reference=good.txt target.txt    # copy another file's mode
```

⚠️ **`chmod -R 777` is never the answer.** It's what people reach for when a service can't
read a file, and it makes the file world-writable — any local process or compromised account
can rewrite your code or config. Diagnose the actual owner/group instead (`namei -l /path`).

⚠️ **`chmod 777 -R /` or `chmod 000` on `/usr/bin`** bricks the system: `sudo` itself becomes
non-executable or refuses to run, so you can't undo it without rescue media.

---

## 3. Special bits — setuid, setgid, sticky ⭐⭐

A **fourth leading octal digit**: `chmod 4755`, `2775`, `1777`.

| Bit | Octal | Shown as | Effect |
|---|---|---|---|
| **setuid** | 4 | `s` in **owner** x slot | file runs with the **file owner's** privileges |
| **setgid** | 2 | `s` in **group** x slot | file runs as its group; **on a dir: new files inherit the dir's group** ⭐ |
| **sticky** | 1 | `t` in **others** x slot | on a dir: **only the file's owner may delete it** |

**setuid in the wild:**

```bash
ls -l /usr/bin/passwd
-rwsr-xr-x 1 root root ... /usr/bin/passwd
#   ↑ s
```

`passwd` must write `/etc/shadow`, which is `root`-only — setuid lets an ordinary user run it
**as root** for that one task.

⚠️ **setuid is the classic privilege-escalation vector.** A setuid-root binary with a bug =
instant root. Audit them:

```bash
find / -perm -4000 -type f 2>/dev/null      # ⭐ all setuid-root binaries
find / -perm -2000 -type f 2>/dev/null      # setgid
```

⚠️ **setuid is ignored on scripts** on Linux (a deliberate kernel refusal — the shebang race
was unfixable). It only works on compiled binaries; scripts need `sudo` rules instead.

**setgid on a directory** — the practical one for shared team folders:

```bash
sudo chgrp devs /srv/shared
sudo chmod 2775 /srv/shared        # ⭐ 2 = setgid
# every file created inside now belongs to group `devs`, whoever creates it
```

Without it, each user's file lands in *their* primary group and teammates can't write.

**Sticky bit** — how `/tmp` is safe:

```bash
ls -ld /tmp
drwxrwxrwt 10 root root ... /tmp
#        ↑ t
chmod 1777 /shared/uploads
```

`/tmp` is world-writable, so without sticky **anyone could delete anyone's files** (rule 2 in
§1). Sticky restricts deletion to the file's owner (or root).

⚠️ A capital **`S`/`T`** instead of `s`/`t` means the bit is set but the underlying `x` is
**not** — usually a mistake.

---

## 4. Ownership

```bash
chown alice file.txt                # owner
chown alice:devs file.txt           # owner + group
chown :devs file.txt                # group only
chown -R app:app /srv/app           # recursive
chown --reference=good.txt target
chgrp devs file.txt                 # group only (a file has exactly ONE group)

sudo chown -h alice link            # ⭐ -h: the SYMLINK itself, not its target
```

⚠️ **Only root can give a file away.** A regular user can't `chown` their file to another user
(that would let you dodge disk quotas and plant files). You *can* `chgrp` to a group you
belong to.

⚠️ **`chown -R` on `/` or with a stray space** (`chown -R app: /srv /app`) is a system-wrecker.
Dry-run the path with `ls -ld` first.

---

## 5. umask — why new files aren't 777

`umask` is a **mask of bits to remove** from the requested mode at creation.

```
                 files            directories
base mode        666              777          ← the kernel never grants x to new files
umask 022      - 022            - 022
                 ────             ────
result           644              755
```

```bash
umask                # 0022
umask -S             # u=rwx,g=rx,o=rx
umask 077            # ⭐ private-by-default: 600 files, 700 dirs
```

**Common values:** `022` (default, others can read) · `002` (group-writable, for setgid team
dirs) · `077` (nothing for group/others — servers handling secrets).

Set it in `/etc/profile`, `~/.bashrc`, or a systemd unit's `UMask=`.

⚠️ umask is **subtractive only** — it can never *add* a permission, so it can't make a new
file executable.

---

## 6. ACLs — when three triads aren't enough ⭐

Standard permissions give you exactly one owner and one group. ACLs add per-user and
per-group entries.

```bash
getfacl file                            # view
setfacl -m u:alice:rw file              # ⭐ grant one user
setfacl -m g:auditors:r file
setfacl -x u:alice file                 # remove entry
setfacl -b file                         # strip all ACLs

setfacl -d -m g:devs:rwx /srv/shared    # ⭐ DEFAULT acl: inherited by new files
setfacl -R -m g:devs:rwX /srv/shared
```

⭐ **A `+` at the end of `ls -l` means ACLs are present:** `-rw-rw-r--+`. If permissions look
right but access still fails, run `getfacl` — the mask entry may be clamping effective rights.

Requires the filesystem to be mounted with `acl` (default on modern ext4/xfs).

---

## 7. Debugging "Permission denied" — the checklist

```bash
namei -l /srv/app/config.yml    # ⭐ BEST FIRST STEP: perms of EVERY component in the path
```

Work down this list:

1. **Every parent directory needs `x`.** `/srv` at `750` blocks access to a `777` file inside.
   `namei -l` shows this instantly.
2. **Which identity is actually failing?** `sudo -u www-data ls /srv/app` — test *as* the
   service user rather than guessing.
3. **Group membership isn't live.** Adding a user to a group doesn't affect existing
   sessions/processes — they must log out and back in (or `newgrp`). A restarted service picks
   it up; a running one does not.
4. **ACLs** — look for the `+` in `ls -l`, then `getfacl`.
5. **Deleting?** Check the **directory's** `w` and the **sticky bit**, not the file.
6. **Mount options** — `mount | grep /srv`; a `ro` or `noexec` mount overrides everything.
7. **SELinux / AppArmor** — permissions perfect but still denied is the signature.
   `getenforce`, `ausearch -m avc -ts recent`, or `dmesg | grep -i denied`.

---

## 8. Interview points

- **Can a user delete a file they can't write?** **Yes** — deletion needs write on the
  *directory*. Sticky bit is the fix.
- **What does `x` mean on a directory?** Traverse/enter. Without it you can't reach anything
  inside, whatever the child permissions say.
- **Why is `/usr/bin/passwd` setuid?** It must write root-owned `/etc/shadow` on behalf of an
  unprivileged user.
- **Why doesn't setuid work on my shell script?** Linux ignores it on interpreted scripts by
  design (shebang race condition). Use `sudo` rules.
- **What does `umask 022` produce?** `644` files, `755` directories — it *removes* bits from
  `666`/`777`.
- **Difference between `chmod 755` and `chmod u=rwx,go=rx`?** None — octal vs symbolic.
- **When would you use an ACL?** When more than one user or group needs distinct access and
  you can't express it with a single owner + single group.
- **Why never `chmod 777`?** World-writable means any local process can modify the file;
  it also silently masks the real problem, which is wrong ownership.
