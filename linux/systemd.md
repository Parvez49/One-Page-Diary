# systemd & journald

> Processes & signals: **[process.md](process.md)** · Log triage: **[performance.md](performance.md)**

---

## 1. What systemd is

**PID 1** — the first userspace process, parent of everything, responsible for bringing the
system up and keeping services alive. It replaced SysV init because init scripts were
sequential shell, had no idea whether a service was actually running, and left orphaned
processes behind.

| | **SysV init** | **systemd** |
|---|---|---|
| Startup | sequential shell scripts | **parallel**, dependency-resolved |
| Service state | guessed from a PID file | **tracked via cgroups** — always accurate |
| Crash recovery | none (needed `monit`/`supervisord`) | ⭐ built-in `Restart=` |
| Logs | scattered text files | **journald**, structured & indexed |
| Config | ~100-line shell script | ~15-line declarative unit |

⭐ **The cgroup point is the big one.** systemd puts every service in its own control group, so
"is it running?" is a fact rather than an inference, `systemctl stop` reliably kills the
*entire* process tree (no orphaned children), and you get per-service resource limits for free.

---

## 2. Unit types

| Suffix | What it is |
|---|---|
| **`.service`** | a daemon — the one you write |
| **`.socket`** | a listening socket; **starts the service on first connection** (socket activation) |
| **`.timer`** | ⭐ scheduled activation — the systemd replacement for cron |
| **`.target`** | a grouping/sync point — the replacement for runlevels (`multi-user.target`) |
| `.mount` / `.automount` | filesystem mounts (generated from `/etc/fstab`) |
| `.path` | activate on filesystem changes |

**Where units live — precedence matters:**

```
/usr/lib/systemd/system/    ← shipped by packages.  ⚠️ overwritten on upgrade
/etc/systemd/system/        ← ⭐ YOURS. Wins. Put custom units and overrides here.
/run/systemd/system/        ← runtime, volatile
~/.config/systemd/user/     ← per-user units (systemctl --user)
```

---

## 3. Daily commands

```bash
systemctl status nginx          # ⭐ state + PID + cgroup + last 10 log lines
systemctl start|stop|restart nginx
systemctl reload nginx          # ⭐ re-read config WITHOUT dropping connections
systemctl reload-or-restart nginx

systemctl enable  nginx         # start at boot (creates a symlink)
systemctl disable nginx
systemctl enable --now nginx    # ⭐ enable AND start in one step
systemctl is-active nginx       # scriptable: exit 0 if running
systemctl is-enabled nginx
systemctl mask nginx            # ⚠️ symlink to /dev/null — cannot be started at all
```

⭐⭐ **`enable` ≠ `start`.** `start` runs it now; `enable` makes it run at boot. Starting a
service without enabling it is the reason it "works until the server reboots" — a genuinely
common production incident.

**`restart` vs `reload`:** restart tears the process down and drops in-flight connections;
reload signals the running process (usually `SIGHUP`) to re-read config with zero downtime.
Use reload for nginx/sshd config changes.

### Discovery & debugging

```bash
systemctl list-units --type=service --state=running
systemctl list-units --failed          # ⭐ FIRST COMMAND on a sick box
systemctl list-unit-files --state=enabled
systemctl cat nginx                    # ⭐ the effective unit + all overrides
systemctl show nginx -p Restart        # one resolved property
systemctl list-dependencies nginx
systemd-analyze blame                  # ⭐ what's slowing boot
systemd-analyze critical-chain
```

⚠️ **After editing a unit file you must `sudo systemctl daemon-reload`** — otherwise systemd
keeps running the old definition and your change appears to do nothing.

---

## 4. Writing a unit

`/etc/systemd/system/myapp.service`:

```ini
[Unit]
Description=My Django App
After=network-online.target postgresql.service   # ORDER only
Wants=postgresql.service                         # weak dep: start it, but don't fail if it dies
# Requires=postgresql.service                    # strong: if postgres stops, WE stop

[Service]
Type=simple                       # process stays in the foreground (most apps)
User=appuser                      # ⭐ never root
Group=appuser
WorkingDirectory=/srv/myapp
Environment="DJANGO_SETTINGS_MODULE=myapp.settings"
EnvironmentFile=/etc/myapp/env    # ⭐ secrets: chmod 600, not in the unit
ExecStart=/srv/myapp/venv/bin/gunicorn myapp.wsgi:application --bind 127.0.0.1:8000
ExecReload=/bin/kill -HUP $MAINPID

Restart=on-failure                # ⭐ restart on crash, NOT on clean exit
RestartSec=5
TimeoutStopSec=30                 # SIGTERM, then SIGKILL after 30s

# hardening — cheap and worth it
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ProtectHome=true
ReadWritePaths=/srv/myapp/media

[Install]
WantedBy=multi-user.target        # ⭐ what `enable` hooks into
```

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now myapp
```

**`Type=`** — the field that causes the most "it starts then immediately fails":

| Type | Use when |
|---|---|
| **`simple`** | the process runs in the **foreground** (default; most modern apps) |
| **`forking`** | the process **daemonizes** itself — traditional daemons; needs `PIDFile=` |
| `exec` | like simple, but wait until the binary has actually exec'd |
| `oneshot` | runs and exits — scripts, migrations; pair with `RemainAfterExit=yes` |
| `notify` | the app calls `sd_notify()` when genuinely ready — best for dependencies |

⚠️ **Getting `Type` wrong is the #1 unit bug.** Declare `forking` for a foreground app and
systemd waits forever for a fork that never comes, then declares it failed. Run a daemon that
backgrounds itself as `simple` and systemd thinks it exited instantly and restarts it forever.
**Most apps should run in the foreground under `Type=simple`** — don't daemonize under
systemd.

**`Wants=` vs `Requires=` vs `After=`** — the other classic confusion:
`After=` is **ordering only**, no dependency. `Wants=`/`Requires=` are **dependency, not
order**. You almost always need both — `After=postgresql.service` *and*
`Wants=postgresql.service`.

**Overriding a packaged unit** — never edit files in `/usr/lib`:

```bash
sudo systemctl edit nginx        # ⭐ creates an override.conf drop-in
sudo systemctl edit --full nginx # copy the whole unit to /etc for editing
```

---

## 5. Timers — better than cron ⭐

`backup.timer` + `backup.service`:

```ini
# backup.timer
[Unit]
Description=Nightly backup

[Timer]
OnCalendar=*-*-* 02:30:00
Persistent=true          # ⭐ run on next boot if the machine was off at 02:30
RandomizedDelaySec=300   # spread load across a fleet

[Install]
WantedBy=timers.target
```

```bash
sudo systemctl enable --now backup.timer
systemctl list-timers --all              # ⭐ next & last run for every timer
systemd-analyze calendar "*-*-* 02:30:00"   # verify a schedule expression
```

**Why prefer timers to cron:** logs go to the journal (cron's output vanishes or gets mailed
nowhere), dependency ordering works, `Persistent=` handles missed runs, jobs get resource
limits and a real service identity, and you can `systemctl start backup.service` to test the
job on demand.

---

### cron — still everywhere

```bash
crontab -e            # ⭐ edit YOUR crontab (never edit /var/spool/cron directly)
crontab -l
crontab -r            # ⚠️ deletes it immediately, no confirmation
sudo crontab -u www-data -e
```

```
┌ min (0-59)
│ ┌ hour (0-23)
│ │ ┌ day of month (1-31)
│ │ │ ┌ month (1-12)
│ │ │ │ ┌ day of week (0-7, 0 and 7 = Sunday)
* * * * *  command

*/15 * * * *   every 15 minutes
0 2 * * *      02:00 daily
0 3 * * 0      03:00 Sundays
@reboot        once at boot
```

System-wide files take an extra **user** field: `/etc/crontab`, `/etc/cron.d/*`.

⚠️ **The three things that break cron jobs, in order of frequency:**

1. **`$PATH` is minimal** (`/usr/bin:/bin`) — `python`, `docker`, `aws` are not found.
   ⭐ **Use absolute paths for everything**, or set `PATH=` at the top of the crontab.
2. **No profile is sourced** — none of `~/.bashrc`, virtualenvs, or exported env vars exist.
3. **Output goes nowhere** (or to local mail you never read). Always redirect:
   `0 2 * * * /srv/app/backup.sh >> /var/log/backup.log 2>&1`.

⚠️ **`%` in a cron command means newline** and must be escaped as `\%` — this silently
truncates `date +%F` commands.

⭐ **Prefer a systemd timer for anything new** (§5): journal logging, missed-run handling,
dependencies, and testability. Keep cron knowledge for the systems you inherit.

---

## 6. journald

```bash
journalctl -u nginx                  # one unit
journalctl -u nginx -f               # ⭐ follow (tail -f)
journalctl -u nginx --since "1 hour ago"
journalctl -u nginx --since "2024-01-15 09:00" --until "09:30"
journalctl -p err -b                 # ⭐ errors+ from THIS boot
journalctl -b -1                     # the PREVIOUS boot — for crash investigation
journalctl -k                        # kernel messages (= dmesg)
journalctl -u nginx -n 100 --no-pager
journalctl _PID=1234                 # by structured field
journalctl -u myapp -o json-pretty   # full structured output
journalctl --disk-usage
sudo journalctl --vacuum-time=7d     # ⭐ reclaim space
```

**Priority levels:** `0 emerg · 1 alert · 2 crit · 3 err · 4 warning · 5 notice · 6 info ·
7 debug`. `-p err` shows 0–3.

⭐ **Incident triage sequence:**

```bash
systemctl list-units --failed
journalctl -p err -b --no-pager | tail -50
journalctl -u <suspect> --since "30 min ago"
journalctl -k | grep -i -E "oom|error"        # OOM kills, hardware
```

⚠️ **By default the journal is volatile on some distros** — logs vanish on reboot, which is
exactly when you need them. Make it persistent:

```bash
sudo mkdir -p /var/log/journal && sudo systemd-tmpfiles --create --prefix /var/log/journal
# or Storage=persistent + SystemMaxUse=1G in /etc/systemd/journald.conf
```

**Application logging under systemd:** just write to **stdout/stderr** — journald captures it
automatically with unit, PID and timestamp attached. Don't manage your own log files or
rotation.

---

## 7. Troubleshooting checklist

| Symptom | Cause |
|---|---|
| Change to the unit does nothing | forgot **`daemon-reload`** |
| Works manually, fails as a service | different `$PATH`/env/cwd — set `WorkingDirectory=`, use **absolute paths**, `EnvironmentFile=` |
| Starts then immediately "failed" | wrong **`Type=`** (usually `forking` vs `simple`) |
| Restart-loops forever | app exits at once → check `journalctl -u x`; use `Restart=on-failure`, raise `RestartSec` |
| Fine until reboot | `start`ed but never **`enable`d** |
| `Permission denied` as a service | `User=` lacks access, or `ProtectSystem=strict`/`ProtectHome` is blocking a path → `ReadWritePaths=` |
| Killed with no app error | **OOM** — `journalctl -k | grep -i oom` (see `process.md §6`) |
| Can't start it at all | it's **`mask`ed** → `systemctl unmask` |

```bash
systemd-analyze verify /etc/systemd/system/myapp.service    # ⭐ lint before deploying
```

---

## 8. Interview points

- **`enable` vs `start`?** Boot-time vs now. The "breaks after reboot" bug.
- **`restart` vs `reload`?** Full process replacement (drops connections) vs re-reading config
  in place (zero downtime).
- **Why did systemd replace SysV init?** Parallel dependency-based startup, accurate state via
  cgroups, built-in restart supervision, unified structured logging, declarative units.
- **`Requires=` vs `Wants=` vs `After=`?** Hard dep, soft dep, and **ordering** — ordering is
  separate from dependency, so you usually need `After=` plus one of the others.
- **`Type=simple` vs `forking`?** Whether your process stays in the foreground or daemonizes.
  Under systemd, don't daemonize.
- **How does systemd know a service died?** It's PID 1 and owns the cgroup — it gets the
  child's exit status directly, no PID files or polling.
- **Timers vs cron?** Journal logging, dependencies, `Persistent=` for missed runs, resource
  control, and on-demand testing.
- **Where do you put a custom unit?** `/etc/systemd/system/` — `/usr/lib/systemd/system/` is
  package territory and gets overwritten.
