# Linux Filesystem — Layout, Inodes, Links, Disk

> Permissions: **[permissions.md](permissions.md)** · Searching files: **[text_processing.md](text_processing.md)**

---

## 1. Filesystem Hierarchy Standard (FHS)

Everything hangs off `/`. There are no drive letters — devices are **mounted into** the tree.

```
/
├── bin  → usr/bin     essential user binaries (ls, cp)      [symlink on modern distros]
├── sbin → usr/sbin    system binaries (fdisk, iptables)
├── lib  → usr/lib     shared libraries
├── boot               kernel, initramfs, GRUB   ⚠️ fills up with old kernels
├── dev                device files — sda, null, zero, random  (managed by udev)
├── etc                ⭐ system-wide CONFIG. Text files. Back this up.
├── home               regular users' home dirs
├── root               root's home (NOT /)
├── mnt, /media        manual mounts / removable media
├── opt                self-contained third-party software
├── proc               ⭐ virtual: kernel + process state, 0 bytes on disk
├── sys                virtual: devices, kernel tunables
├── run                volatile runtime state (PIDs, sockets) — tmpfs, cleared on boot
├── srv                data served by this host (web, ftp)
├── tmp                world-writable scratch, cleared on boot (sticky bit)
├── usr                read-only program data — the "installed OS"
│   ├── bin  sbin  lib
│   ├── local          ⭐ software YOU installed manually — package managers don't touch it
│   └── share          docs, icons, locale
└── var                ⭐ variable data that GROWS: logs, spool, caches, DBs
    ├── log            /var/log/syslog, journal   ← first place to look in an incident
    ├── lib            app state (docker, mysql, dpkg)
    └── cache          apt archives
```

**The distinctions interviewers probe:**

| Pair | Difference |
|---|---|
| `/bin` vs `/usr/local/bin` | distro-managed vs **your** manual installs (`/usr/local` survives upgrades) |
| `/etc` vs `/var` | config (static, versionable) vs state (grows, changes) |
| `/tmp` vs `/var/tmp` | cleared **on reboot** vs **persists** across reboots |
| `/proc` vs `/sys` | process/kernel info vs device & driver model |
| `/run` vs `/var/run` | `/var/run` is now a symlink to `/run` (tmpfs) |

⚠️ **A full `/var` takes services down** — logs, Docker images, and DB files all live there.
`/boot` filling with old kernels is the other classic: `sudo apt autoremove --purge`.

---

## 2. Navigation & listing

```bash
pwd                    # where am I (physical path)
cd /etc                # absolute
cd ../logs             # relative
cd ~                   # home;  cd  alone does the same
cd -                   # ⭐ previous directory (toggle)

ls -lh                 # long + human sizes
ls -lha                # + hidden (dotfiles)
ls -lt                 # ⭐ newest first — "what changed recently?"
ls -lS                 # largest first
ls -li                 # show INODE numbers
ls -ld /var/log        # the DIRECTORY itself, not its contents  ⭐ common mistake
tree -L 2              # depth-limited tree
```

**Reading `ls -l`:**

```
-rw-r--r--  1 parvez devs  4096 Aug 15 12:00 app.log
│└────┬───┘ │  │      │      │       │
│     │     │  │      │      │       └─ mtime (last CONTENT change)
│     │     │  │      │      └───────── size in bytes
│     │     │  │      └──────────────── group
│     │     │  └─────────────────────── owner
│     │     └────────────────────────── hard link count  ⭐ (dirs: 2 + subdir count)
│     └──────────────────────────────── permissions → permissions.md
└────────────────────────────────────── type: - f  d dir  l link  s sock  c/b device  p pipe
```

**Three timestamps** — `stat file`:
- **atime** — last read (often disabled via `relatime` for performance)
- **mtime** — last **content** change ← what `ls -l` shows
- **ctime** — last **inode** change (permissions, owner, links). ⚠️ Not "creation time";
  you cannot backdate it, which is why forensics uses it.

---

## 3. Files & directories

```bash
mkdir -p a/b/c              # ⭐ -p: create parents, no error if exists (script-safe)
rmdir dir                   # only if EMPTY
rm -rf dir                  # ⚠️ recursive force — no undo, no trash
touch file                  # create empty, or bump mtime
cp -a src/ dst/             # ⭐ archive: recursive + preserve perms/times/links
cp -r src dst
mv old new                  # rename or move (same filesystem = just a rename, instant)
ln -s /opt/app/current link # symlink
```

⚠️ **Trailing slash on `cp`/`rsync` changes the meaning:**
`rsync -a src/ dst/` copies the *contents*; `rsync -a src dst/` creates `dst/src/`.

```bash
rsync -avz --progress src/ user@host:/dst/     # resumable, incremental, over SSH
rsync -a --delete src/ dst/                    # ⚠️ mirror: deletes extras in dst
```

### Reading files

```bash
cat file                        # whole file to stdout; concatenates multiple
cat -n file                     # numbered
less file                       # ⭐ pager: / search, n next, G end, q quit
head -20 file / tail -20 file
tail -f  /var/log/syslog        # follow appends
tail -F  /var/log/app.log       # ⭐ survives log ROTATION — use this one
wc -l file                      # line count
```

⚠️ **`cat` a 4 GB log and you flood the terminal** — reach for `less`, `head`, or `grep`.
`cat file | grep x` is a useless use of cat: `grep x file`.

---

## 4. Inodes, hard links, symlinks ⭐⭐

**An inode holds a file's metadata and data pointers — but *not* its name.** Names live in
directory entries, which map `name → inode`. A directory *is* just that table.

```
  directory entry            inode #1234              data blocks
  ┌──────────────┐          ┌──────────────┐         ┌─────────┐
  │ "report.txt" │──1234──▶ │ perms, owner │────────▶│ content │
  │ "backup.txt" │──1234──▶ │ size, times  │         └─────────┘
  └──────────────┘          │ link count: 2│
                            └──────────────┘
```

```bash
ln  file.txt   hard.txt     # hard link: a second NAME for the same inode
ln -s file.txt soft.txt     # symlink: a tiny file containing a PATH
ls -li                      # compare inode numbers
stat file.txt               # inode, links, all three timestamps
```

| | **Hard link** | **Symbolic link** |
|---|---|---|
| Points to | the **inode** | a **path string** |
| Across filesystems | ❌ no | ✅ yes |
| To a directory | ❌ no (would cycle the tree) | ✅ yes |
| Original deleted | data **survives** — link count > 0 | ⚠️ **dangles**, broken |
| Own permissions | none — same inode | yes (usually `777`, ignored) |
| `ls -li` inode | **same** as original | different |

**Why deleting a file frees no space** — one of the best senior questions:

> `rm` only removes a directory entry and decrements the link count. Space is reclaimed when
> the link count hits 0 **and no process still has the file open**. A running service holding
> a deleted 10 GB log keeps that space allocated until it's restarted.

```bash
lsof +L1                    # ⭐ open files with link count 0 — the "deleted but held" list
lsof /var/log/app.log
: > /var/log/app.log        # ⭐ TRUNCATE in place — frees space without breaking the fd
```

**Running out of inodes** — `df -h` says space is free but writes fail with "No space left on
device". Millions of tiny files (sessions, cache) exhausted the inode table:

```bash
df -i                       # ⭐ inode usage — check this whenever df -h looks fine
```

---

## 5. Disk usage & mounts

```bash
df -h                       # free space per FILESYSTEM
df -i                       # ⭐ inode usage
du -sh /var/log             # total size of a directory
du -h --max-depth=1 /var | sort -rh | head    # ⭐ what's eating the disk
ncdu /var                   # interactive, if installed

lsblk                       # ⭐ block devices as a tree — clearest view
blkid                       # UUIDs and filesystem types
mount | column -t
findmnt                     # tree of mounts
```

⚠️ **`df` vs `du` disagreeing** is the deleted-but-open-file case above — `du` walks names,
`df` asks the filesystem. `lsof +L1` reconciles them.

**Mounting:**

```bash
sudo mount /dev/sdb1 /mnt/data
sudo umount /mnt/data                 # "target is busy" → fuser -vm /mnt/data
```

`/etc/fstab` — persistent mounts. **Use UUIDs**, not `/dev/sdb1` (device names reorder
across boots):

```fstab
UUID=1a2b-3c4d  /data  ext4  defaults,noatime  0  2
```

⚠️ A bad `/etc/fstab` **stops the machine booting**. Always `sudo mount -a` to test before
rebooting, and prefer `nofail` for non-critical mounts.

---

## 6. Finding things

```bash
find /var/log -name "*.log" -mtime +30 -delete    # ⭐ older than 30 days
find . -type f -size +100M
find . -type d -name node_modules -prune -o -name "*.py" -print
which python3          # first match in $PATH
type -a python3        # ⭐ ALL matches + aliases/functions — better than which
locate nginx.conf      # indexed, instant (updatedb)
readlink -f ./link     # resolve to the real absolute path
```

Full treatment in **[text_processing.md](text_processing.md)**.

---

## 7. Interview points

- **Why is everything a file?** One uniform API (`open/read/write/close`) for regular files,
  devices, sockets, and pipes — so `cat`, `>` and `dd` work against hardware.
- **What is `/proc`?** A virtual filesystem the kernel generates on read — `/proc/<pid>/`
  exposes each process's cmdline, fds, memory maps; `/proc/meminfo`, `/proc/mounts`. Zero
  bytes on disk.
- **Hard vs soft link** — see the table above; the answer they want is *inode vs path*, plus
  "hard links can't cross filesystems or point at directories."
- **Disk full but `df` shows space?** Inode exhaustion (`df -i`) or a deleted-but-open file
  (`lsof +L1`).
- **`mv` vs `cp` cost** — within one filesystem `mv` just rewrites a directory entry (instant,
  regardless of size); across filesystems it's a copy + delete.
- **Why UUIDs in fstab?** Device names (`/dev/sdb`) depend on enumeration order and can change
  between boots; UUIDs are stable.
