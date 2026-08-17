# Process management — Supervisor & systemd

> What you're supervising: **[app_servers.md](app_servers.md)** · Celery semantics:
> `../Web/Django/async_tasks.md`

---

## 1. The problem ⭐

A process started in a shell dies with the shell, doesn't come back after a crash, doesn't
start on boot, and writes its output nowhere useful. A process supervisor fixes all four:

- ⭐ **auto-restart on crash** — the whole point
- start on boot, in dependency/priority order
- start/stop/restart as a unit or a group
- capture stdout/stderr to log files
- run as a specific unprivileged user

| | systemd | Supervisor |
|---|---|---|
| Available | ⭐ already on every modern Linux | `apt install supervisor` |
| Config | `/etc/systemd/system/*.service` | `/etc/supervisor/conf.d/*.conf` |
| Boot ordering | ⭐ real dependency graph (`After=`, `Requires=`) | `priority=` numbers only |
| Sockets | ⭐ socket activation | `fcgi-program` |
| Many similar workers | one unit + templates | ⭐ `numprocs`, `[group:...]` |
| Logs | ⭐ `journalctl` | plain files you rotate yourself |

⭐ **Recommendation:** systemd for anything new — it's already running, it has real
dependencies, and journald handles the logs. Supervisor is worth it when you're managing a
*fleet* of similar processes (`numprocs=8` workers, grouped restarts) or inherited a box that
already uses it.

---

## 2. Supervisor

```bash
sudo apt install supervisor           # configs live in /etc/supervisor/conf.d/
```

### Control commands ⭐

```bash
sudo supervisorctl reread             # ⭐ detect NEW/changed .conf files
sudo supervisorctl update             # ⭐ apply them (starts/stops what changed)
sudo supervisorctl status             # everything, with PIDs and uptime
sudo supervisorctl restart celery     # one program
sudo supervisorctl restart app:*      # ⭐ a whole group
sudo supervisorctl tail -f celery     # follow its stdout
```

⚠️ **`reread` alone does nothing.** It only reports what changed; `update` applies it. Editing
a config and running `restart` restarts the *old* definition — the most common Supervisor
confusion.

⚠️ `restart` does **not** re-read config. New config = `reread && update`.

### Real config — ASGI + Celery worker + beat

`/etc/supervisor/conf.d/data_collector.conf`:

```ini
[fcgi-program:data_collector_asgi]
socket=tcp://localhost:8000
command=/opt/DataCollector-Backend/venv/bin/daphne -u /run/daphne/daphne%(process_num)d.sock
        --fd 0 --access-log - --proxy-headers config.asgi:application
process_name=asgi_%(process_num)d
numprocs=1
directory=/opt/DataCollector-Backend
priority=999
autostart=true
autorestart=true
user=www-data
redirect_stderr=true
stdout_logfile=/var/log/DataCollector-Backend/asgi.log
environment=DJANGO_SETTINGS_MODULE=config.settings.production

[program:data_collector_celery_worker]
command=/opt/DataCollector-Backend/venv/bin/celery -A config.celery worker --loglevel=INFO --concurrency=1
process_name=celery_worker_%(process_num)d
numprocs=1
directory=/opt/DataCollector-Backend
priority=997
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=/var/log/DataCollector-Backend/celery_worker.log
environment=DJANGO_SETTINGS_MODULE=config.settings.production

[program:data_collector_celery_beat]
command=/opt/DataCollector-Backend/venv/bin/celery -A config.celery beat --loglevel=INFO
        --scheduler django_celery_beat.schedulers:DatabaseScheduler
process_name=celery_beat_%(process_num)d
numprocs=1
directory=/opt/DataCollector-Backend
priority=998
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=/var/log/DataCollector-Backend/celery_beat.log
environment=DJANGO_SETTINGS_MODULE=config.settings.production

[group:data_collector_celery]
programs=data_collector_celery_worker,data_collector_celery_beat
```

### Reading that config ⭐

| Key | Meaning |
|---|---|
| `command` | ⚠️ **absolute path into the venv** — no shell, so no `source activate`, no `$PATH`, no `&&` |
| `directory` | working directory (relative imports, `.env` discovery) |
| `autostart` | start when supervisord starts (i.e. at boot) |
| `autorestart` | ⭐ restart on exit — `true`, or `unexpected` for exit codes outside `exitcodes` |
| `priority` | lower starts first / stops last |
| `numprocs` + `%(process_num)d` | ⭐ N identical processes, each with a unique name/socket |
| `user` | drop privileges — ⚠️ must be able to write the log dir and the socket dir |
| `redirect_stderr` | fold stderr into stdout, one log file |
| `environment` | ⚠️ the *only* env the process gets |
| `[group:...]` | restart related programs together (`restart data_collector_celery:*`) |

⚠️ **`command` runs without a shell.** Pipes, `&&`, globs, and `~` don't work. If you need
them, wrap in `bash -c "..."`.

⚠️ **`environment=` is the whole environment.** Secrets that live in your shell profile or a
`.env` sourced by hand are absent. Symptom: works when you run it manually, dies under
supervisor. Load config from a file the app reads itself, or list the vars explicitly. And
⚠️ anything in `environment=` is world-readable in the config file — point at a `.env` with
`0600` permissions instead of pasting secrets inline.

⚠️ **A crash-looping process is worse than a dead one** — `autorestart=true` will restart it
forever, filling logs and burning CPU. Supervisor gives up after `startretries` (default 3) in
`startsecs`; check `supervisorctl status` for `FATAL`.

⭐ **`celery beat` must be exactly one process.** `numprocs=2` on beat means every periodic
task fires twice. Note the priorities above: worker (997) before beat (998) before ASGI (999).

⚠️ Log files here are plain files — **add logrotate** or they fill the disk, which is the
actual cause of a surprising number of "the server went down" incidents.

### FastCGI

`[fcgi-program]` has Supervisor bind the socket and pass it to the process as file descriptor
0 (hence `--fd 0`). That lets `numprocs=4` share one listening socket, with the kernel
load-balancing across them — and restarts don't drop connections, because the socket outlives
the processes. FastCGI itself is the binary protocol between a web server and a backend app.

---

## 3. systemd equivalent ⭐

`/etc/systemd/system/gunicorn.service`:

```ini
[Unit]
Description=gunicorn daemon for myapp
Requires=gunicorn.socket
After=network.target postgresql.service

[Service]
User=www-data
Group=www-data
WorkingDirectory=/opt/myapp
EnvironmentFile=/opt/myapp/.env                 # ⭐ secrets stay in a 0600 file
ExecStart=/opt/myapp/venv/bin/gunicorn myproject.wsgi:application -c gunicorn_config.py
ExecReload=/bin/kill -s HUP $MAINPID            # ⭐ graceful worker reload
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl daemon-reload          # ⚠️ required after ANY unit file edit
sudo systemctl enable --now gunicorn  # start now + on boot
sudo systemctl status gunicorn
sudo systemctl reload gunicorn        # graceful (uses ExecReload)
journalctl -u gunicorn -f             # ⭐ live logs
journalctl -u gunicorn --since "10 min ago" -p err
```

⚠️ `daemon-reload` after editing a unit file — the systemd analogue of `reread && update`.
⚠️ `enable` ≠ `start`. `enable` is boot-time only; `--now` does both.

---

## Interview points

- **Why a process supervisor?** ⭐ Auto-restart on crash, start on boot, log capture, run as
  an unprivileged user.
- **systemd vs Supervisor** — systemd is already there and has real dependency ordering;
  Supervisor is nicer for fleets of identical workers and grouped restarts.
- **`reread` vs `update` vs `restart`** ⚠️ — detect, apply, bounce. `restart` alone never picks
  up config changes.
- **Why does it work manually but not under the supervisor?** ⚠️ Environment and `PATH` —
  the supervised process gets no shell, no profile, only `environment=`/`EnvironmentFile=`.
- **Why absolute venv paths?** No shell, so no activated virtualenv.
- **How many `celery beat` processes?** ⭐ Exactly one, or every scheduled task double-fires.
- **What does `autorestart` not fix?** ⚠️ A crash loop — it hides a broken deploy behind
  restarts. Check for `FATAL` and read the logs.
- **Where do supervised logs go, and what breaks?** Plain files → ⚠️ disk full without
  logrotate. journald handles this for systemd.
