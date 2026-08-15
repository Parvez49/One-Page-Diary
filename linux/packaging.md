# Packages, Distro Info & Building a .deb

> Services: **[systemd.md](systemd.md)** · Filesystem layout: **[filesystem.md](filesystem.md)**

---

## 1. Identifying the system

```bash
cat /etc/os-release        # ⭐ the portable answer — works on every modern distro
lsb_release -a             # Debian/Ubuntu (may need lsb-release installed)
uname -a                   # kernel, arch, hostname
uname -r                   # kernel version only
hostnamectl                # ⭐ OS + kernel + virtualisation + machine ID in one
arch                       # x86_64 / aarch64
nproc && free -h           # cores and RAM
uptime -p                  # how long it's been up
```

⭐ **Use `/etc/os-release` in scripts** — it's a shell-sourceable file (`ID`, `VERSION_ID`)
present on all systemd distros. `lsb_release` is an optional package and often missing on
minimal/container images.

⚠️ **`uname -r` gives the *running* kernel, not the installed one.** After a kernel upgrade
they differ until reboot — that's how you detect a machine that needs restarting:

```bash
[ -f /var/run/reboot-required ] && echo "reboot needed"
```

---

## 2. The layers: apt vs dpkg ⭐

| | **`dpkg`** | **`apt`** |
|---|---|---|
| Level | **low** — one `.deb` file | **high** — repositories |
| Dependencies | ❌ **fails and complains** | ✅ resolves and downloads |
| Source | a local file | configured repos |
| Use | installing a downloaded `.deb` | everything else |

`apt` is a front-end that *uses* `dpkg`. `apt` (the modern CLI) vs `apt-get` — use `apt`
interactively, **`apt-get` in scripts** (its output and flags are stable by design).

```bash
sudo apt update                  # ⭐ refresh the package INDEX (downloads nothing else)
sudo apt upgrade                 # upgrade installed packages
sudo apt full-upgrade            # ⚠️ may REMOVE packages to resolve conflicts
sudo apt install nginx
sudo apt install ./local.deb     # ⭐ apt handles deps for a local file too
sudo apt remove nginx            # keep config files
sudo apt purge nginx             # ⭐ also delete config
sudo apt autoremove              # orphaned deps  (⭐ clears old kernels from /boot)
sudo apt-mark hold docker-ce     # ⭐ pin: exclude from upgrades

apt search keyword
apt show nginx
apt list --installed | grep nginx
apt policy nginx                 # ⭐ candidate version + which repo it comes from
apt depends / rdepends nginx     # dependencies / reverse dependencies
```

⚠️ **`apt update` ≠ `apt upgrade`.** `update` only refreshes the index; `upgrade` installs.
Running `install` without a recent `update` gives "package not found" or a stale version.

```bash
dpkg -i package.deb              # install a local .deb (no dep resolution)
sudo apt install -f              # ⭐ fix the deps dpkg just complained about
dpkg -l                          # list installed
dpkg -L nginx                    # ⭐ every FILE this package installed
dpkg -S /usr/sbin/nginx          # ⭐ which PACKAGE owns this file
dpkg -s nginx                    # status/metadata
dpkg --get-selections | grep hold
dpkg -c package.deb              # contents WITHOUT installing
dpkg -x package.deb ./out/       # extract without installing
```

⭐ **`dpkg -S` and `dpkg -L` are the two to remember** — "where did this binary come from?" and
"what did this package drop on my system?"

**Repositories:** `/etc/apt/sources.list` + `/etc/apt/sources.list.d/*.list`, keys in
`/etc/apt/keyrings/`.

```bash
sudo add-apt-repository ppa:deadsnakes/ppa && sudo apt update
```

⚠️ `apt-key` is deprecated — put the key in `/etc/apt/keyrings/` and reference it with
`signed-by=` in the source entry.

**Fixing a broken state:**

```bash
sudo dpkg --configure -a         # ⭐ finish interrupted installs
sudo apt install -f              # repair dependencies
sudo rm /var/lib/dpkg/lock-frontend    # ⚠️ ONLY if no apt process is running
```

**Other families** (worth naming): RHEL/Fedora `dnf`/`yum` + `rpm`, Arch `pacman`, Alpine
`apk`, plus universal `snap` and `flatpak`.

---

## 3. Building a `.deb`

### Directory layout

```
myapp_1.0_all/                    ← name is arbitrary; the DEBIAN dir is what matters
├── DEBIAN/
│   ├── control                   ⭐ required metadata (no file extension)
│   ├── postinst                  optional: runs AFTER install   (chmod 755)
│   ├── prerm                     optional: runs BEFORE removal  (chmod 755)
│   └── conffiles                 optional: files to preserve on upgrade
└── usr/                          ⭐ mirrors the TARGET filesystem from /
    ├── bin/
    │   └── myapp                 → installs to /usr/bin/myapp
    └── share/
        └── myapp/
            └── assets/
```

⭐ **The tree under the build directory is laid down verbatim at `/`.** Put binaries in
`usr/bin/`, config in `etc/`, unit files in `lib/systemd/system/` — mirroring
[filesystem.md §1](filesystem.md).

### `DEBIAN/control`

```
Package: myapp
Version: 1.0.0
Section: utils
Priority: optional
Architecture: amd64
Depends: python3 (>= 3.10), libssl3
Maintainer: Parvez Hossen <you@mail.com>
Description: Short one-line summary
 Longer description, indented by exactly one space.
 Blank lines must be a single dot on its own line.
```

⚠️ **Three things that silently break the build:**
- `Architecture:` must be `amd64`/`arm64`/`all` (`all` = arch-independent scripts/data).
- The long description must be **indented one space**; an unindented line ends it.
- The file must end with a **newline**.

### Build & install

```bash
dpkg-deb --build myapp_1.0_all           # → myapp_1.0_all.deb
dpkg-deb --build myapp_1.0_all myapp_1.0.0_amd64.deb   # ⭐ explicit output name

sudo dpkg -i myapp_1.0.0_amd64.deb
sudo apt install -f                       # if it complained about dependencies
myapp

dpkg -c myapp_1.0.0_amd64.deb             # ⭐ verify the contents BEFORE installing
lintian myapp_1.0.0_amd64.deb             # ⭐ policy checker — catches real mistakes
sudo dpkg -r myapp                        # remove
sudo dpkg -P myapp                        # purge (config too)
```

⚠️ **Permissions inside the package are preserved** — `chmod +x` your binaries and maintainer
scripts *before* building, or the installed command won't run.

### Maintainer script example

`DEBIAN/postinst` (must be `755`):

```bash
#!/bin/sh
set -e
case "$1" in
  configure)
    systemctl daemon-reload
    systemctl enable --now myapp.service
    ;;
esac
```

⭐ Maintainer scripts must be **idempotent** — they run again on upgrade and reinstall.

---

## 4. Dependencies of a binary

```bash
ldd /usr/bin/myapp            # ⭐ shared libraries it needs
ldd myapp | grep "not found"  # ⭐ the missing ones — the cause of most "won't start"
ldconfig -p | grep ssl        # what the linker knows about
readelf -d myapp | grep NEEDED
file myapp                    # ELF? dynamically or statically linked? which arch?
```

⚠️ **`ldd` on an untrusted binary can execute it.** Prefer `objdump -p` / `readelf -d` for
anything you didn't build.

⭐ **`ldd ... | grep "not found"` is the fastest diagnosis** for a binary that fails with a
cryptic loader error. Then `dpkg -S` the library name to find which package provides it.

---

## 5. Interview points

- **`apt` vs `dpkg`?** apt resolves dependencies from repositories; dpkg installs a single
  local `.deb` and merely reports missing deps.
- **`apt update` vs `apt upgrade`?** Refresh the index vs actually install newer packages.
- **`remove` vs `purge`?** Purge also deletes configuration files.
- **Which package owns `/usr/sbin/nginx`?** `dpkg -S /usr/sbin/nginx`.
- **`/boot` is full — why, and the fix?** Accumulated old kernels; `sudo apt autoremove
  --purge`.
- **Why pin a package?** `apt-mark hold` prevents an unattended upgrade from moving a version
  your application depends on.
- **What's in `DEBIAN/control`?** Package, Version, Architecture, Depends, Maintainer,
  Description — the metadata dpkg uses for dependency resolution.
- **`Architecture: all` vs `amd64`?** Arch-independent content (scripts, data) vs compiled
  binaries for a specific CPU.
- **A binary won't start with a loader error.** `ldd` it and look for `not found`, then
  install the package providing that library.
