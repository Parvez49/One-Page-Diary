# Docker

> Orchestration: **[kubernetes.md](kubernetes.md)** · What runs inside:
> **[app_servers.md](app_servers.md)** · Pipelines: `../CICD/`

---

## 1. Architecture

| Component | Role |
|---|---|
| **Docker client** (`docker`) | CLI; sends commands to the daemon over a REST API |
| **Docker daemon** (`dockerd`) | ⭐ does the work — builds images, runs containers, manages volumes/networks |
| **Registry** | stores images — Docker Hub, ECR, GHCR, GCR |

```
developer → docker CLI → dockerd → registry → container
```

⭐ **Container ≠ VM.** A VM virtualises hardware and boots its own kernel. A container is
**one or more processes on the host kernel**, isolated by namespaces (PID, network, mount,
user) and limited by cgroups (CPU, memory). That's why containers start in milliseconds and a
Linux container can't run on a Windows kernel without a VM underneath.

---

## 2. Image vs container ⭐

| | Image | Container |
|---|---|---|
| Analogy | **class** | **object** — a running instance |
| State | immutable, read-only template | writable layer on top |
| Storage | stacked layers | thin writable layer |
| Lifecycle | build once | run many, throw away |

An image contains code, runtime, libraries, env vars and config — everything needed to run,
except the kernel.

---

## 3. Layers and build caching ⭐⭐

Every instruction creates a layer. Layers are cached and shared between images — and
**invalidating one layer invalidates every layer after it**.

```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .              # ⭐ dependencies FIRST
RUN pip install -r requirements.txt  # ⭐ cached until requirements.txt changes
COPY . .                             # code last — changes constantly
```

⚠️ **`COPY . .` before `pip install` is the classic mistake**: every one-character source edit
busts the cache and reinstalls every dependency. Order instructions from least- to
most-frequently-changing.

⚠️ **Layers are additive — deleting a file doesn't shrink the image, and a secret committed in
an earlier layer is still extractable** even if a later layer removes it. `docker history`
shows every layer's command.

```bash
docker history image_name
```

⭐ **Multi-stage builds** — build in a fat image, ship a thin one:

```dockerfile
FROM node:20 AS build
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build

FROM nginx:alpine                              # ⭐ final image has no node, no npm, no source
COPY --from=build /app/dist /usr/share/nginx/html
```

⚠️ Add a **`.dockerignore`** (`.git`, `node_modules`, `.env`, `venv`). Without it the whole
directory is sent to the daemon as build context — slow builds, bloated images, and ⚠️ `.env`
baked into the image.

---

## 4. Dockerfile instructions

| Instruction | Does |
|---|---|
| `FROM image` | base layer |
| `WORKDIR path` | set (and create) the working directory |
| `COPY src dst` | copy from build context into the image |
| `RUN cmd` | run at **build** time → new layer |
| `ENV k v` | environment variable ⚠️ visible in `docker inspect` — not for secrets |
| `EXPOSE port` | ⚠️ **documentation only** — it publishes nothing; `-p` does |
| `ENTRYPOINT ["x"]` | the executable; `CMD` becomes its arguments |
| `CMD ["x"]` | default command, overridable on `docker run` |

⭐ **`ENTRYPOINT` vs `CMD`:** `ENTRYPOINT` fixes what runs, `CMD` supplies default arguments a
user can override. `ENTRYPOINT ["python", "app.py"]` + `CMD ["--port=8000"]` → running with
`--port=9000` swaps only the argument. Use exec form (JSON array), not shell form — shell form
wraps the process in `/bin/sh`, which ⚠️ swallows SIGTERM so your container takes the full
10-second timeout to stop and never shuts down gracefully.

---

## 5. Lifecycle

```
created  →  running  →  paused  →  stopped  →  deleted
docker create   start     pause      stop        rm
```

```bash
docker build -t image_name .
docker run -d -p 4000:80 --name web image_name      # detached, host:container
docker run -it ubuntu:24.04 /bin/bash               # interactive shell
docker run --rm -it -v $(pwd):/mounted ubuntu bash  # ⭐ --rm: clean up on exit
```

⭐ `-p 4000:80` is **host:container** — that order is asked about constantly.

---

## 6. Networking

| Mode | Behaviour |
|---|---|
| **bridge** (default) | private network; ⭐ on a *user-defined* bridge, containers resolve each other **by name** |
| **host** | shares the host's stack — faster, ⚠️ no isolation, port conflicts, Linux only |
| **none** | no network |
| **overlay** | multi-host (Swarm/K8s) |

```bash
docker network create mynetwork
docker run --network=mynetwork --name api myimage
```

⭐⭐ **The `localhost` trap:** inside a container, `localhost` is *that container*, not the
host and not the database container. Use the service/container name (`postgres:5432`) on a
user-defined network. From a container to a service on the host: `host.docker.internal`
(Docker Desktop) or the gateway IP.

⚠️ The **default** bridge has no DNS between containers — only user-defined networks and
Compose give you name resolution. This is why "it works in Compose but not with plain
`docker run`."

---

## 7. Storage ⭐

Containers are ephemeral: the writable layer dies with the container.

| | Bind mount | Volume |
|---|---|---|
| Location | a host path you choose | ⭐ Docker-managed (`/var/lib/docker/volumes`) |
| Syntax | `-v /host/data:/container/data` | `-v myvolume:/data` |
| Use | ⭐ **development** — live code reload, no rebuild | ⭐ **production** — databases, uploads |
| Trade-off | ⚠️ host-path dependent, permission/ownership mismatches | portable, backup-able, better perf on Mac/Windows |

```bash
docker volume create myvolume
docker volume ls
docker volume inspect myvolume
docker volume rm myvolume
docker volume prune
docker-compose down -v          # ⚠️⚠️ -v DELETES the volumes — i.e. your dev database
```

⚠️ **A database in a container without a volume loses everything on `docker rm`.** Standard
first-week Docker incident.

---

## 8. Compose

Declarative multi-container definition — one file, one command.

```yaml
services:
  web:
    build: .                     # or: context + dockerfile
    ports: ["8000:8000"]
    volumes: [".:/app"]          # dev: live reload
    env_file: .env               # ⭐ not committed
    depends_on:
      db:
        condition: service_healthy   # ⭐ see warning
  db:
    image: postgres:16
    volumes: ["pgdata:/var/lib/postgresql/data"]
    environment:
      POSTGRES_PASSWORD: ${DB_PASSWORD}
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres"]
      interval: 5s
      retries: 5

volumes:
  pgdata:
```

| Key | Meaning |
|---|---|
| `services` | the containers to run — each name is a **DNS hostname** on the shared network ⭐ |
| `build` / `context` | build from a Dockerfile instead of pulling an image |
| `ports` | host:container mapping |
| `volumes` | bind mounts or named volumes |
| `environment` / `env_file` | env vars for the container |
| `depends_on` | ⚠️ start **order** only, not readiness — add a healthcheck |

⚠️⚠️ **`depends_on` does not wait for the service to be ready**, only started. Postgres accepts
connections seconds after the process starts; your app crashes on boot in that gap. Fix with
`condition: service_healthy` plus a healthcheck, or make the app retry its connection — which
it should do anyway, for restarts in production.

⚠️ `version:` at the top of the file is obsolete in Compose v2 and now warns. Drop it.

---

## 9. Debugging & housekeeping

```bash
docker ps                       # running
docker ps -a                    # ⭐ including stopped — where exit codes live
docker logs -f container_id     # ⭐ first stop for a crash
docker exec -it container_id bash    # shell inside a RUNNING container
docker inspect container_id     # config, mounts, networks, env
docker images                   # local images
docker stats                    # live CPU/memory
```

⭐ **A container that exits immediately** — `docker ps -a` for the exit code, then
`docker logs`. Exit 0 usually means the main process finished (a container lives exactly as
long as PID 1); 137 is OOM-kill or SIGKILL; 1 is an application error.
⚠️ `docker exec` needs the container *running* — for one that crashes on boot, override the
entrypoint: `docker run -it --entrypoint sh image`.

```bash
docker system df                # ⭐ disk usage — check this before it bites
docker system prune             # unused containers/networks/dangling images
docker system prune -a --volumes    # ⚠️ everything unused, INCLUDING volumes
docker container prune
docker image prune
```

⚠️ Docker fills disks quietly — build caches, old images, dangling volumes. `system df` first,
and never `prune --volumes` on a host with real data unless you're certain.

---

## 10. Security ⭐

- ⚠️ **Don't run as root inside the container.** The default is root, and with a bind mount
  that root can write host files. Add a user:
  ```dockerfile
  RUN adduser --system --group app
  USER app
  ```
- ⚠️⚠️ **Membership of the `docker` group is root on the host** — anyone in it can mount `/`
  into a privileged container. Convenient locally, a privilege escalation on a shared server.
  ```bash
  sudo usermod -aG docker $USER && newgrp docker
  ```
- ⚠️ **Secrets don't belong in images.** `ENV`/`ARG`/`COPY .env` are all readable via
  `docker history` / `inspect`. Inject at runtime (`--env-file`, orchestrator secrets).
- ⭐ Pin base image tags (`python:3.11-slim`, ideally a digest), use minimal bases, scan with
  `docker scout` / `trivy`, and rebuild for security updates — an image is a frozen OS.

---

## 11. Swarm vs Kubernetes

**Docker Swarm** is Docker's built-in clustering: multiple daemons as one cluster, with load
balancing, scaling and HA.

```bash
docker swarm init
docker service create --name web nginx
docker service scale web=5
```

⭐ Swarm is dramatically simpler than K8s and effectively lost the orchestration war. Choose
it only for a small cluster where you already know Swarm; otherwise **Compose** for a single
host, **Kubernetes** for a real cluster, or a managed platform (ECS, Cloud Run, Fly) to skip
orchestration entirely. → **[kubernetes.md](kubernetes.md)**

---

## References

- <https://dev.to/thedevtimeline/add-mongodb-and-postgresql-in-django-using-docker-55j6>
- <https://dev.to/karanpratapsingh/dockerize-your-react-app-4j2e>
- <https://medium.com/@audretschjames/understanding-docker-as-if-it-were-a-gameboy-96c96392efbf>

---

## Interview points

- **Container vs VM** ⭐ — namespaces + cgroups on the *host kernel* vs virtualised hardware
  with its own kernel.
- **Image vs container** — class vs instance; immutable layers vs a writable layer.
- **Why order Dockerfile instructions carefully?** ⭐⭐ Layer caching — dependencies before
  source, or every edit reinstalls everything.
- **How do you shrink an image?** Multi-stage build, slim base, `.dockerignore`; ⚠️ deleting
  files in a later layer doesn't help.
- **`ENTRYPOINT` vs `CMD`** ⭐ — fixed executable vs overridable default arguments; use exec
  form so signals reach PID 1.
- **`EXPOSE` vs `-p`** ⚠️ — documentation vs actually publishing a port.
- **Volume vs bind mount** ⭐ — Docker-managed and portable (production) vs a host path
  (development live-reload).
- **Why can't my container reach the database on `localhost`?** ⭐⭐ `localhost` is the
  container itself — use the service name on a user-defined network.
- **Does `depends_on` wait for readiness?** ⚠️ No — order only. Healthchecks or app-side retry.
- **Why did my container exit immediately?** It runs exactly as long as PID 1;
  `docker ps -a` + `docker logs`.
- **Why not run as root?** ⚠️ Container root plus a bind mount writes host files; and the
  `docker` group is effectively root on the host.
- **Where do secrets go?** ⚠️ Never in the image — runtime injection only.
