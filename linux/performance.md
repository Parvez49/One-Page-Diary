# Performance Triage — "The server is slow"

> Processes & OOM: **[process.md](process.md)** · Logs: **[systemd.md](systemd.md)** ·
> Disk space: **[filesystem.md](filesystem.md)**

---

## 1. The 60-second triage ⭐⭐

Brendan Gregg's checklist. Run these in order *before* forming a theory — the goal is to
narrow to **CPU, memory, disk, or network** in one minute.

```bash
uptime                  # 1. load average trend
dmesg -T | tail -20     # 2. ⭐ OOM kills, disk errors, TCP drops
vmstat 1 5              # 3. r/b queues, swap in/out, CPU split
mpstat -P ALL 1 3       # 4. per-core — is ONE core pinned?
pidstat 1 3             # 5. which process is burning CPU, over time
iostat -xz 1 3          # 6. ⭐ per-disk %util and await
free -h                 # 7. memory + swap
sar -n DEV 1 3          # 8. network throughput
ss -s                   # 9. socket summary
top                     # 10. now confirm the suspect
```

**Then answer one question: which of the four resources is saturated?**

| Signal | Bottleneck |
|---|---|
| High load + high `%us` in `vmstat` | **CPU** |
| High load + high `%wa` + `iostat` `%util` near 100 | **Disk I/O** |
| `si`/`so` non-zero in `vmstat`, low `free` | **Memory** (swapping) |
| Load high but CPU idle *and* disk idle | ⭐ **`D`-state processes** — NFS/storage hang, or lock contention |

---

## 2. Load average — the most misread number

```bash
uptime
# load average: 2.15, 3.40, 5.02      ← 1 min, 5 min, 15 min
```

⭐ **Linux load average is *not* CPU utilisation.** It counts processes in **runnable (R) *and*
uninterruptible-sleep (D)** state. So heavy disk or NFS I/O inflates load while the CPUs sit
idle — Linux differs from other Unixes here, and it's a favourite interview trap.

**Interpretation:** divide by core count (`nproc`).
Load 4 on 4 cores ≈ fully used. Load 16 on 4 cores = 4× oversubscribed.

**Read the trend, not the value:** `2.15, 3.40, 5.02` is **recovering** (1min < 15min).
`5.02, 3.40, 2.15` is **getting worse right now** — that's the one to page on.

---

## 3. CPU

```bash
top                      # then 1 (per-core), P (sort CPU), M (sort mem)
htop                     # ⭐ nicer; F5 tree view
mpstat -P ALL 2          # per-core breakdown
pidstat -u 2             # per-process, sampled over time (better than top's snapshot)
nproc                    # core count — needed to read load average
```

**The CPU columns and what each one accuses:**

| Column | Meaning | High means |
|---|---|---|
| **`us`** | user | your application code |
| **`sy`** | system/kernel | syscall-heavy: I/O, context switches, network |
| **`ni`** | niced user | background/batch jobs |
| **`id`** | idle | — |
| **`wa`** | ⭐ **I/O wait** | CPU idle **waiting on disk** → it's a *storage* problem |
| **`st`** | ⭐ **steal** | **the hypervisor gave your vCPU to another tenant** — noisy neighbour; resize or move |

⭐ **`%wa` high means the CPU is not the problem.** Chasing code optimisation when `wa` is 40%
wastes days — go to §5. **`%st` above a few percent** on a cloud VM means you are being
throttled by the host, which no amount of application tuning will fix.

⚠️ **`top`'s per-process `%CPU` can exceed 100%** — it's per-core, so 400% = 4 cores saturated
by one multithreaded process. Press `1` to see the per-core picture.

---

## 4. Memory ⭐

```bash
free -h
#               total   used   free   shared  buff/cache   available
# Mem:           15Gi   8Gi    1Gi    200Mi       6Gi         6Gi
```

⭐⭐ **Read the `available` column, not `free`.** Linux deliberately uses all spare RAM for the
page cache (`buff/cache`) because unused RAM is wasted RAM. That memory is **instantly
reclaimable**, so a machine showing 1 GiB "free" and 6 GiB "available" is perfectly healthy.
"Linux is eating my RAM" is the classic misdiagnosis.

**Swap is the real signal:**

```bash
vmstat 1 5
#  r  b   swpd   free   buff  cache   si   so    bi    bo
#                                     └─┬──┘
#                        ⭐ si/so = swap IN/OUT per second
```

- `swpd > 0` with `si`/`so` **at zero** → pages were swapped out once, nothing is happening
  now. **Fine.**
- `si`/`so` **continuously non-zero** → ⚠️ **thrashing.** The system is trading RAM for disk
  and everything is orders of magnitude slower. Fix memory, not the app.

```bash
ps aux --sort=-%mem | head              # top memory consumers (RSS)
smem -tk -s pss                         # ⭐ PSS: shared memory counted fairly
cat /proc/meminfo
dmesg -T | grep -i "killed process"     # ⭐ OOM kills — see process.md §6
```

⚠️ **Summing `RSS` double-counts shared libraries** and will overstate total usage; `PSS`
(via `smem`) divides shared pages among users.

⭐ **A process whose RSS grows steadily and never plateaus is a leak.** Sample it:
`while true; do ps -o rss= -p $PID; sleep 60; done`.

---

## 5. Disk I/O

```bash
iostat -xz 1 3
# Device  r/s   w/s   rkB/s   wkB/s  await  aqu-sz  %util
# nvme0n1 120  3400   1200   140000   28.5    12.4   99.8
```

| Column | Read as |
|---|---|
| **`%util`** | % of time the device had I/O in flight. **~100% = saturated** (⚠️ misleading on SSD/NVMe, which handle parallel queues) |
| **`await`** | ⭐ **average ms per I/O — the number users actually feel.** HDD ~10ms normal; **SSD >5ms is bad**, >20ms is a serious problem |
| `aqu-sz` | average queue depth — high = requests piling up |
| `r/s`, `w/s` | IOPS |

⭐ **`await` beats `%util` as a health metric.** On NVMe, `%util` can read 100% while latency
is fine because the device services many requests concurrently. Latency doesn't lie.

```bash
iotop -oPa               # ⭐ which PROCESS is doing the I/O (-o = only active)
pidstat -d 2             # per-process disk stats
df -h && df -i           # ⭐ full disk / exhausted inodes — see filesystem.md
lsof +L1                 # deleted-but-open files holding space
```

⚠️ **"Slow" is often just "the disk is full."** Check `df -h` and `df -i` in the first minute
— a full `/var` degrades logging, databases, and package operations all at once.

---

## 6. Network

Latency and packet loss masquerade as application slowness. Full toolkit in
**[networking.md](networking.md)**; the triage subset:

```bash
sar -n DEV 1 3              # throughput per interface
sar -n TCP,ETCP 1 3         # ⭐ retransmits — retrans > ~1% is a real problem
ss -s                       # socket counts by state
ip -s link show eth0        # errors, drops at the interface
nethogs                     # bandwidth by process
mtr <host>                  # continuous loss/latency per hop
```

⚠️ Many `CLOSE_WAIT` sockets = an application FD leak, not a network fault (`networking.md §3`).

---

## 7. Limits — the invisible ceiling ⭐

An app that fails **under load but works when idle** is usually hitting a limit, not a
resource wall.

```bash
ulimit -a                              # limits of the CURRENT shell
cat /proc/<pid>/limits                 # ⭐ the limits the RUNNING process actually got
ls /proc/<pid>/fd | wc -l              # current FD count
sysctl fs.file-nr                      # system-wide FD usage
```

⚠️ **`Too many open files` is `nofile`, and raising it in your shell does nothing for a
service.** systemd services ignore `/etc/security/limits.conf` — the limit must be in the
unit:

```ini
[Service]
LimitNOFILE=65535
```

Other ceilings worth knowing: `kernel.pid_max`, `net.core.somaxconn` (accept-queue depth —
manifests as connection timeouts under burst), `fs.inotify.max_user_watches` (breaks file
watchers/IDEs), and cgroup memory limits in containers.

⭐ **In a container, `free -h` and `nproc` report the *host's* resources, not your cgroup
limit.** That's why a JVM or worker pool sizes itself far too large and gets OOM-killed.
Read the real limit:

```bash
cat /sys/fs/cgroup/memory.max        # cgroup v2
cat /sys/fs/cgroup/cpu.max
```

---

## 8. Worked example — "the API is slow"

```bash
uptime                   # load 18 on 4 cores → heavily oversubscribed
vmstat 1 5               # %wa 45, si/so = 0 → not CPU-bound, not swapping → DISK
iostat -xz 1 3           # nvme0n1 await 85ms, %util 99 → confirmed: disk saturated
iotop -oPa               # postgres writing 200 MB/s
# → check for a missing index causing sequential scans, an unthrottled backup,
#   or log-level=DEBUG writing synchronously. Not an application-code problem.
```

The value is in the *elimination*: high `wa` with zero swap ruled out CPU and memory in two
commands, so no one wasted a day profiling Python.

---

## 9. Interview points

- **What is load average, exactly?** Runnable **plus uninterruptible (D-state)** processes,
  averaged over 1/5/15 min. **Not CPU %** — I/O inflates it on Linux.
- **Load 8 — is that bad?** Meaningless without core count. Compare to `nproc`, and read the
  trend across the three numbers.
- **`free` shows almost no free memory — is that a problem?** No. Look at **`available`**;
  `buff/cache` is reclaimable page cache.
- **What does `%wa` tell you?** CPU idle while waiting on I/O — the bottleneck is storage,
  not code.
- **What is CPU `steal`?** The hypervisor scheduled another tenant on your vCPU. Nothing you
  can fix inside the VM.
- **Is swap usage bad?** Static `swpd` is fine; sustained `si`/`so` is thrashing.
- **`%util` 100% on NVMe — saturated?** Not necessarily; NVMe parallelises. Judge by
  **`await`** latency.
- **How do you find a memory leak?** Sample RSS over time; if it grows monotonically and never
  plateaus, it's a leak. Use PSS to avoid double-counting shared pages.
- **`Too many open files` — fix?** Raise `nofile`; for a service, `LimitNOFILE=` in the
  systemd unit, since `limits.conf` doesn't apply.
- **Why does my container think it has 64 GB?** `free`/`nproc` read host values; the real
  ceiling is the cgroup (`/sys/fs/cgroup/memory.max`).
