# tmux — Terminal Multiplexer

> Backgrounding processes: **[process.md](process.md)** · SSH sessions: **[gitssh.md](gitssh.md)**

---

## 1. Why it matters

tmux keeps a shell session alive **on the server, independent of your connection**. The
session lives in a daemon; your terminal merely attaches to it.

⭐ **The senior argument:** any long-running operation over SSH — a migration, a `rsync` of
100 GB, a build, a `kubectl` rollout — dies with the connection if you run it bare. Wi-Fi
drop, laptop sleep, VPN reconnect: the process gets `SIGHUP` and your half-applied migration
is now an incident. Start it inside tmux and you can reattach from anywhere and find it
running.

`nohup`/`&` (see [process.md §4](process.md)) also survive logout, but you can't *interact*
with them afterwards — no output, no prompt, no Ctrl-C. tmux gives you the session back.

**Hierarchy:**

```
session            (a workspace — persists on the server)
└── window         (a tab)
    └── pane       (a split — each is its own sh****ell)
```

---

## 2. Sessions

```bash
tmux                                # unnamed session
tmux new -s deploy                  # ⭐ named — do this, "0" tells you nothing
tmux ls                             # list sessions
tmux attach -t deploy               # ⭐ reattach  (tmux a -t deploy)
tmux new -As deploy                 # ⭐ attach if it exists, else create — the safe one-liner
tmux kill-session -t deploy
tmux kill-server                    # ⚠️ everything
tmux rename-session -t old new
tmux has-session -t deploy 2>/dev/null && echo exists    # scriptable guard
```

⭐ **`tmux new -As name`** is the command to muscle-memorise: it never accidentally nests a
second session, and never errors because one already exists.

⚠️ **`command attach-session: unknown flag -s`** — `-s` and `-t` are not interchangeable:

| | flag | meaning |
|---|---|---|
| `tmux new -s deploy` | `-s` | **s**ets the name, at creation only |
| `tmux attach -t deploy` | `-t` | **t**argets an existing session |

Every command that acts on something that already exists takes `-t` (`attach`, `kill-session`,
`rename-session -t old new`, `send-keys -t`, `switch-client -t`). `new -As` reads as `-A -s`,
which is why that one keeps `-s`.

⚠️ **Sessions do not survive a reboot** — the daemon dies with the machine. tmux protects you
from a dropped *connection*, not from a restart. To persist layouts across reboots you need
the `tmux-resurrect` + `tmux-continuum` plugins (via TPM); nothing built in does it.

⚠️ **`sessions should be nested with care` / `no sessions`** — you're already *inside* tmux.
Detach first (`Ctrl-b d`), or use `Ctrl-b s` to switch.

---

## 3. The prefix

**Every tmux keystroke starts with the prefix — `Ctrl-b` by default.** Notation `Ctrl-b d`
means: press `Ctrl-b`, release, then press `d`.

| Key | Action |
|---|---|
| **`Ctrl-b d`** | ⭐ **detach** — the session keeps running |
| `Ctrl-b s` | interactive **session** list |
| `Ctrl-b (` / `)` | previous / next session (no menu) |
| `Ctrl-b $` | rename session |
| `Ctrl-b ?` | list every binding |
| `Ctrl-b :` | command prompt |

### Getting out of the interactive lists ⭐

`Ctrl-b s`, `Ctrl-b w` and `Ctrl-b ?` all open a **mode**, not a screen you're stuck in —
the shell underneath is still alive, it just isn't listening to you yet.

| Key | Action |
|---|---|
| **`q`** or **`Esc`** | ⭐ **close the list**, back to your pane |
| `↑` `↓` | move |
| `Enter` | switch to the highlighted session/window |
| `x` | kill the highlighted entry (asks to confirm) |
| `/` | filter by name |

⚠️ Don't reach for `Ctrl-c` or close the terminal — the first does nothing useful here and
the second just detaches you from a session you were already attached to.

---

## 4. Windows (tabs)

| Key | Action |
|---|---|
| `Ctrl-b c` | **create** window |
| `Ctrl-b ,` | rename window |
| `Ctrl-b n` / `p` | next / previous |
| `Ctrl-b 0…9` | jump to window N |
| `Ctrl-b w` | ⭐ visual window list |
| `Ctrl-b &` | kill window |
| `Ctrl-b l` | last window (toggle) |

---

## 5. Panes (splits)

| Key | Action |
|---|---|
| `Ctrl-b %` | split **vertical** (left/right) |
| `Ctrl-b "` | split **horizontal** (top/bottom) |
| `Ctrl-b ←↑↓→` | move between panes |
| `Ctrl-b o` | cycle panes |
| `Ctrl-b q` | show pane numbers (then press one) |
| `Ctrl-b z` | ⭐ **zoom** — fullscreen this pane, press again to restore |
| `Ctrl-b x` | kill pane |
| `Ctrl-b {` / `}` | swap pane left / right |
| `Ctrl-b space` | cycle layouts |
| `Ctrl-b Ctrl-←↑↓→` | resize |
| `Ctrl-b !` | ⭐ break pane out into its own window |

⭐ **`Ctrl-b z` is the most underused binding** — instant fullscreen for reading a log or
stack trace in a cramped 4-pane layout, no layout surgery needed.

⚠️ **`%` is vertical and `"` is horizontal** — the opposite of most people's intuition
(the symbols depict the *divider*, not the direction of the split).

---

## 6. Copy mode ⭐

Scrolling back requires copy mode — the mouse scrollwheel won't work by default.

| Key | Action |
|---|---|
| `Ctrl-b [` | **enter copy mode** |
| `↑↓` / `PgUp` `PgDn` | scroll |
| `Ctrl-b ]` | paste |
| `q` | exit |
| `/` then text | ⭐ search **forward**, `n` for next |
| `?` then text | search backward |
| `g` / `G` | top / bottom of scrollback |

**Selecting (vi mode):** `space` starts the selection, `Enter` copies.
(emacs mode: `Ctrl-space` then `Alt-w`.)

```bash
tmux capture-pane -pS -10000 > scrollback.log    # ⭐ dump scrollback to a file
```

---

## 7. Configuration — `~/.tmux.conf`

```tmux
# Ctrl-a is far easier to reach than Ctrl-b (matches screen)
unbind C-b
set -g prefix C-a
bind C-a send-prefix

set -g mouse on                 # ⭐ scroll, click panes, drag borders
set -g history-limit 50000      # ⭐ default 2000 is far too small for logs
set -g base-index 1             # windows start at 1 — matches the keyboard
setw -g pane-base-index 1
set -g renumber-windows on
set -sg escape-time 0           # ⭐ removes vim's ESC lag inside tmux
setw -g mode-keys vi

# splits that keep the current directory (and are memorable)
bind | split-window -h -c "#{pane_current_path}"
bind - split-window -v -c "#{pane_current_path}"

# reload config without restarting
bind r source-file ~/.tmux.conf \; display "reloaded"

set -g status-right '#[fg=green]#H #[fg=yellow]%H:%M'
```

```bash
tmux source-file ~/.tmux.conf     # apply without killing sessions
```

⭐ `history-limit` and `escape-time 0` are the two settings that make the biggest daily
difference.

⚠️ **`mouse on` steals text selection** — once tmux owns the mouse, dragging selects into
*tmux's* copy buffer, not your terminal's clipboard. Hold **`Shift`** while dragging to
bypass tmux and use the terminal's own selection (and `Shift`+middle-click to paste).

⚠️ **Nested tmux** (local tmux → `ssh` → remote tmux): the prefix hits the *outer* session
first. Press the prefix **twice** to send it inward — `Ctrl-b Ctrl-b d` detaches the remote
one. Simplest fix is a different prefix on each side (e.g. `Ctrl-a` locally, `Ctrl-b`
remotely) so there's nothing to disambiguate.

---

## 8. Practical patterns

**Long deploy over SSH — the whole point:**

```bash
ssh prod
tmux new -As deploy
./migrate.sh                # now safe: Ctrl-b d, close the laptop, reattach later
```

**Send a command to every pane** (rolling restart across servers):

```bash
tmux setw synchronize-panes on     # ⭐ type once, executes everywhere
tmux setw synchronize-panes off    # ⚠️ REMEMBER to turn it off
```

**Scripted layout:**

```bash
tmux new -s dev -d              # detached
tmux send-keys -t dev 'cd ~/app && ./manage.py runserver' Enter
tmux split-window -t dev
tmux send-keys -t dev 'tail -F logs/app.log' Enter
tmux attach -t dev
```

**tmux vs screen vs nohup:**

| | `nohup`/`&` | `screen` | **`tmux`** |
|---|---|---|---|
| Survives disconnect | ✅ | ✅ | ✅ |
| Reattach & interact | ❌ | ✅ | ✅ |
| Panes/splits | ❌ | limited | ✅ |
| Scriptable | ❌ | limited | ⭐ ✅ |

---

## 9. Interview points

- **Why use tmux on a server?** A dropped SSH connection sends `SIGHUP` and kills the job;
  tmux runs it in a session owned by a daemon, so it survives and stays interactive.
- **tmux vs `nohup`?** Both survive logout, but `nohup` gives up interactivity — no input, no
  live output, no way to intervene.
- **Session vs window vs pane?** Workspace → tab → split, in that order.
- **How do you scroll back?** Copy mode (`Ctrl-b [`), or enable `set -g mouse on`.
- **How do you leave a session running?** Detach with `Ctrl-b d` — *not* `exit`, which kills
  the shell. (A session ends on its own once its last window exits.)
- **Does a tmux session survive a reboot?** No — it's a daemon on that host. It covers dropped
  connections, not restarts; `tmux-resurrect`/`continuum` are what restore layouts after one.
- **How would you script a dev environment?** `new -d` + `send-keys -t` + `split-window`, then
  `attach` — the same commands you'd use interactively, which is why tmux beats `screen` for
  automation.
