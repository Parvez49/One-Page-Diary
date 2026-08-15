# Processes, Signals & Jobs

> Service management: **[systemd.md](systemd.md)** · Diagnosing slowness: **[performance.md](performance.md)**

---

## 1. What a process is

A running program plus its state: PID, parent PID (PPID), UID/GID, working directory, open
file descriptors, environment, and memory maps. All of it is visible under
**`/proc/<pid>/`** — that directory *is* the kernel's view of the process.

**Lifecycle:** a process is created by **`fork()`** (a near-copy of the parent) and usually
immediately **`exec()`**s a new program image over itself. The parent later **`wait()`**s to
collect the child's exit status. Everything traces back to **PID 1** (`systemd`).

### Process states — the `S` column in `ps`

| State | Meaning |
|---|---|
| **R** | running or runnable (on the run queue) |
| **S** | interruptible sleep — **normal idle**, waiting on I/O or an event |
| **D** | ⚠️ **uninterruptible sleep** — stuck in a kernel I/O call. **Cannot be killed, not even `-9`** |
| **T** | stopped (`Ctrl-Z` or `SIGSTOP`) |
| **Z** | **zombie** — exited, but the parent hasn't reaped its status |

⭐ **`D` state is the one to recognise.** Rising `D`-state counts mean the disk or NFS mount is
the bottleneck — they inflate load average without using CPU, and no signal will clear them.
Fix the storage, or reboot.

**Zombie vs orphan** — routinely asked:

- **Zombie (`Z`)** — child exited, parent never called `wait()`. It holds no memory, just a
  PID table entry. **You cannot kill a zombie** (it's already dead); you kill or fix the
  **parent**. If the parent dies, `init` adopts and reaps it. A few are harmless; thousands
  mean a buggy parent that will exhaust the PID table.
- **Orphan** — parent died first; the child is **re-parented to PID 1** and keeps running
  normally. Harmless.

```bash
ps -eo pid,ppid,stat,cmd | awk '$3 ~ /^Z/'    # find zombies and their parents
```

---

## 2. Inspecting

```bash
ps aux                       # ⭐ BSD style: every process, user-oriented
ps -ef                       # ⭐ SysV style: same idea, shows PPID
ps -eo pid,ppid,user,%cpu,%mem,stat,etime,cmd --sort=-%cpu | head
ps -p 1234 -o etime,cmd      # ⭐ how long has THIS process been up
pstree -p                    # process tree with PIDs — shows parentage at a glance

pgrep -a nginx               # PIDs + command line
pgrep -u www-data            # by user
pidof nginx
```

**Reading `ps aux` columns:** `VSZ` = virtual size (address space reserved — almost always
misleadingly huge, ignore it). **`RSS` = resident set size — actual physical RAM**, the number
that matters. ⚠️ Summing RSS across processes double-counts shared libraries.

### Live views

```bash
top          # then: P sort by CPU, M by memory, 1 per-core, k kill, q quit
htop         # ⭐ far better if available: colour, tree view (F5), scrolling
```

### `/proc` — the source of truth

```bash
ls -l /proc/1234/exe        # the actual binary (works even if deleted)
ls -l /proc/1234/cwd        # working directory
cat  /proc/1234/cmdline | tr '\0' ' '    # ⭐ full args, untruncated
cat  /proc/1234/environ | tr '\0' '\n'   # its environment
ls   /proc/1234/fd | wc -l  # open file descriptors — for leak hunting
cat  /proc/1234/status      # threads, memory, UID
```

⭐ **`/proc/<pid>/exe` still resolves after the binary is deleted or upgraded** — that's how
you identify what a mystery process actually is after a package update.

---

## 3. Signals ⭐⭐

A signal is an asynchronous notification to a process. The three that matter:

| Signal | № | Default | Catchable? | Use |
|---|---|---|---|---|
| **SIGTERM** | **15** | terminate | ✅ yes | ⭐ **polite stop — the default for `kill`** |
| **SIGKILL** | **9** | terminate | ❌ **never** | ⚠️ last resort — instant, no cleanup |
| **SIGHUP** | 1 | terminate | ✅ | ⭐ by convention: **reload config** (nginx, sshd) |
| SIGINT | 2 | terminate | ✅ | `Ctrl-C` |
| SIGQUIT | 3 | core dump | ✅ | `Ctrl-\` |
| SIGSTOP | 19 | stop | ❌ never | pause (`Ctrl-Z` sends SIGTSTP, which *is* catchable) |
| SIGCONT | 18 | continue | ✅ | resume |
| SIGUSR1/2 | 10/12 | terminate | ✅ | app-defined (nginx: reopen logs) |

```bash
kill 1234                    # sends SIGTERM (15) — the default
kill -15 1234
kill -9  1234                # ⚠️ SIGKILL
kill -HUP 1234               # reload config
kill -l                      # list all signals

pkill -f "python manage.py"  # ⭐ -f matches the FULL command line
killall nginx                # by exact process name
```

⭐⭐ **`kill -9` should be your last move, not your first.**

> `SIGTERM` is delivered to the application, which can flush buffers, finish the in-flight
> request, commit or roll back its transaction, remove its PID file, and deregister from the
> load balancer. **`SIGKILL` is handled by the kernel — the process never sees it.** No
> cleanup, no flush: corrupted files, orphaned locks, stale PID files, half-written state.
>
> Correct escalation: `SIGTERM` → wait 10–30s → `SIGKILL` if still alive. That's exactly what
> `systemctl stop` does (`TimeoutStopSec`), and what Kubernetes does with
> `terminationGracePeriodSeconds`.

⚠️ **`kill -9` doesn't work?** The process is in **`D` state** (uninterruptible I/O). Signals
aren't delivered until the kernel call returns. It's a storage problem, not a process problem.

---

## 4. Jobs — foreground / background

```bash
./long_task.sh &         # start in background
Ctrl-Z                   # suspend the foreground job (SIGTSTP)
jobs -l                  # list jobs + PIDs
bg %1                    # resume job 1 in background
fg %1                    # bring to foreground
kill %1                  # kill by job number
wait                     # wait for all background jobs
```

⚠️ **Backgrounding with `&` does not survive logout** — the shell sends `SIGHUP` to its jobs.
Three real fixes:

```bash
nohup ./task.sh > out.log 2>&1 &     # immune to HUP, output to file
disown -h %1                          # ⭐ detach a job you already started
setsid ./task.sh                      # new session, fully detached
```

⭐ **For anything that matters, use `tmux`/`screen` (see [tmux.md](tmux.md)) or a systemd
unit** — not `nohup`. A long migration run over SSH that dies with the connection is a
self-inflicted incident.

---

## 5. Priority: nice & ionice

```bash
nice -n 10 ./batch.sh          # start with LOWER priority (nice to others)
renice -n 5 -p 1234            # change a running process
renice -n -5 -p 1234           # ⚠️ raise priority — root only
ionice -c3 -p 1234             # ⭐ idle-class DISK priority — for backups/rsync
```

**Niceness runs −20 (highest priority) → +19 (lowest); default 0.** Only root can go
negative. `nice` affects **CPU** scheduling only — for an I/O-heavy backup starving a
database, `ionice` is the tool that actually helps.

---

## 6. The OOM killer ⭐

When memory is exhausted, the kernel picks a process and kills it with **SIGKILL** rather than
letting the system die.

```bash
dmesg -T | grep -i "killed process"           # ⭐ the smoking gun
journalctl -k | grep -i oom
cat /proc/1234/oom_score                      # current victim score
```

**How the victim is chosen:** roughly the largest `oom_score` — dominated by memory usage,
adjusted by `oom_score_adj` (−1000 to +1000). This is why **your database, the biggest memory
consumer, is the thing that gets killed** when a leaky worker eats RAM.

```bash
echo -1000 | sudo tee /proc/1234/oom_score_adj    # protect a process
# systemd unit equivalent:  OOMScoreAdjust=-1000
```

⭐ **A service that "randomly restarts" with no application error in its logs is the classic
OOM signature** — the app can't log its own SIGKILL. Always check `dmesg -T | grep -i oom`
before hunting through application code.

---

## 7. Tracing a misbehaving process

```bash
strace -p 1234                     # ⭐ live system calls — see exactly where it's stuck
strace -f -e trace=openat ./app    # -f follow forks; filter to file opens
ltrace -p 1234                     # library calls
lsof -p 1234                       # ⭐ every file/socket it has open
lsof -i :8080                      # who is on this port
gdb -p 1234                        # attach a debugger
cat /proc/1234/stack               # kernel stack — why a D-state process is stuck
```

⭐ **`strace` answers "what is it *actually* waiting on?"** in seconds — a hung process
repeatedly showing `connect()` to an unreachable IP tells you it's a network/DNS issue, not a
code bug. It slows the target significantly, so use it briefly on production.

---

## 8. Interview points

- **`kill -9` vs `kill -15`?** 15 is catchable and lets the app clean up; 9 is handled by the
  kernel, unblockable, and skips all cleanup. Escalate, don't lead with 9.
- **How do you kill a zombie?** You don't — it's already dead. Kill or fix the **parent**;
  `init` reaps orphans automatically.
- **Zombie vs orphan?** Zombie = exited, unreaped, holds a PID slot. Orphan = parent died,
  re-parented to PID 1, still running normally.
- **A process won't die even with `-9`.** It's in `D` state, blocked in an uninterruptible
  kernel I/O call — a storage/NFS problem.
- **`fork` vs `exec`?** `fork` duplicates the process; `exec` replaces the program image in
  place. Shells do `fork` then `exec`.
- **VSZ vs RSS?** Virtual address space (reserved, inflated) vs actual physical RAM. Use RSS.
- **What is PID 1 and why does it matter?** `systemd` — it adopts orphans and reaps them. In
  containers, an app running as PID 1 that doesn't reap children accumulates zombies, and one
  that ignores SIGTERM makes `docker stop` take the full 10s timeout.
- **Service restarts with nothing in its logs?** OOM killer — `dmesg -T | grep -i oom`.
- **How do you find what's holding a deleted file / a port?** `lsof +L1`, `lsof -i :PORT`.
