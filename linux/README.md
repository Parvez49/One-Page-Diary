# Linux & Git — Index

Domain knowledge for **senior/staff backend interviews** and day-to-day production work.
Assumes you can already use a shell — the focus is on *why*, on the traps, and on the
questions that separate "I've used Linux" from "I've debugged Linux at 3 AM."

**Conventions:** ⭐ = high interview value · ⚠️ = a trap that causes real incidents ·
every file ends with an **Interview points** section.

---

## Files

| File | Covers | Interview weight |
|---|---|---|
| [git.md](git.md) | Object model & DAG, daily workflow, undo matrix, **merge vs rebase**, stash, worktree, bisect, submodules, large repos | ⭐⭐⭐ |
| [git_interview.md](git_interview.md) | Q&A: **reset vs revert**, merge vs rebase, reflog, detached HEAD, leaked secrets, rapid fire | ⭐⭐⭐ |
| [gitssh.md](gitssh.md) | Key auth flow, `~/.ssh/config`, **multi-account GitHub**, bastions, **port forwarding**, sshd hardening | ⭐⭐ |
| [filesystem.md](filesystem.md) | FHS, `ls -l` anatomy, **inodes & hard vs soft links**, disk usage, mounts, `df` vs `du` | ⭐⭐ |
| [permissions.md](permissions.md) | chmod octal/symbolic, **setuid/setgid/sticky**, umask, ACLs, "permission denied" checklist | ⭐⭐⭐ |
| [users.md](users.md) | UID/GID, `/etc/passwd` & shadow, groups, **sudo vs su**, sudoers, PAM | ⭐⭐ |
| [process.md](process.md) | States (**D & zombie**), **signals & why not `kill -9`**, jobs, nice, **OOM killer**, strace | ⭐⭐⭐ |
| [systemd.md](systemd.md) | Units, **`enable` vs `start`**, `Type=`, journald, timers, cron, troubleshooting | ⭐⭐⭐ |
| [networking.md](networking.md) | **The debugging ladder**, `ss`, TCP states, DNS, curl, firewall, tcpdump | ⭐⭐⭐ |
| [performance.md](performance.md) | **60-second triage**, load average, `free` misreadings, `%wa`/`%st`, iostat, ulimits | ⭐⭐⭐ |
| [text_processing.md](text_processing.md) | Redirection, grep, **find + xargs safety**, awk, sed, real log pipelines | ⭐⭐ |
| [packaging.md](packaging.md) | OS identification, **apt vs dpkg**, repos, **building a .deb**, `ldd` | ⭐ |
| [tmux.md](tmux.md) | Sessions/windows/panes, copy mode, config, **why it beats `nohup`** | ⭐ |

---

## Suggested study order

1. **[process.md](process.md)** + **[performance.md](performance.md)** — "the server is slow"
   is the most common senior screening scenario. Load average and `free` are the two numbers
   candidates misread most.
2. **[networking.md](networking.md)** — the debugging ladder is the highest-leverage thing
   here; refused-vs-timeout alone answers half of connectivity questions.
3. **[permissions.md](permissions.md)** — setuid, sticky, and "you can delete a file you
   can't write" are reliable differentiators.
4. **[systemd.md](systemd.md)** — every service you own runs under it; `enable` vs `start`
   is a real production bug.
5. **[git_interview.md](git_interview.md)** — reset vs revert and merge vs rebase come up in
   nearly every interview.
6. **[filesystem.md](filesystem.md)**, **[users.md](users.md)**,
   **[text_processing.md](text_processing.md)** — supporting depth.
7. **[gitssh.md](gitssh.md)**, **[packaging.md](packaging.md)**, **[tmux.md](tmux.md)** —
   working knowledge; skim before an infra-heavy round.

---

## The senior answers worth memorising

| Question | Short answer |
|---|---|
| Why not `kill -9` first? | SIGKILL is handled by the **kernel** — the app never runs cleanup. TERM → wait → KILL. |
| Load average 8 — bad? | Depends on `nproc`, and it counts **D-state I/O**, not just CPU. |
| `free` shows no free RAM | Read **`available`**; `buff/cache` is reclaimable page cache. |
| Connection refused vs timeout | Refused = nothing listening (RST). **Timeout = firewall dropping.** |
| Works locally, not remotely | Bound to `127.0.0.1` instead of `0.0.0.0` — `ss -tlnp`. |
| Disk full but `df` shows space | Inodes (`df -i`) or a deleted-but-open file (`lsof +L1`). |
| Service dies with no error logged | **OOM killer** — `dmesg -T \| grep -i oom`. |
| Fine until reboot | `systemctl start`ed but never **`enable`d**. |
| Can delete a file you can't write? | **Yes** — deletion needs `w` on the *directory*. Sticky bit fixes it. |
| Undo a pushed commit | **`git revert`**, never `reset` + force-push. |
| Added to a group, still denied | Group list is stamped at **login** — log out and back in. |
| `kill -9` didn't work | Process is in **`D` state** — a storage problem, not a process one. |

---

## Related directories

`../Deploy/` Docker, K8s, nginx · `../CICD/` pipelines · `../Database/` SQL & NoSQL ·
`../CyberSecurity/` security · `../SDLC/` architecture & process · `../Algorithm/` DSA
