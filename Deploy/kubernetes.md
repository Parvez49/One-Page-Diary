# Kubernetes

> Prerequisite: **[docker.md](docker.md)** · The single-host alternative it replaces:
> **[nginx.md](nginx.md)** + **[process_management.md](process_management.md)**

Kubernetes is an open-source **container orchestration** platform: it schedules containers
across machines, restarts what dies, scales what's loaded, and gives it all stable networking.

⭐ **The honest framing for an interview:** K8s solves problems you only have *above* a certain
scale — many services, many nodes, frequent deploys, a team to operate it. For one app on one
VPS, nginx + gunicorn + systemd is less to run and less to get wrong. Knowing when *not* to
reach for it is the senior signal.

---

## 1. The object hierarchy ⭐

```
container  →  pod  →  node  →  cluster
```

- **Pod** — one or more containers that share a network namespace and storage. ⭐ Containers in
  a pod reach each other on `localhost` and are always scheduled together. The pod, not the
  container, is the smallest deployable unit.
- **Node** — a machine (VM, bare metal, cloud instance) running one or more pods.
- **Cluster** — a control plane (**at least one master node**) plus worker nodes.

⚠️ **Pods are cattle, not pets.** They get a new IP every time they're recreated, and they're
evicted and rescheduled routinely. Never address a pod directly, and never write important
state to its filesystem.

---

## 2. Control plane components ⭐

| Component | Responsibility |
|---|---|
| **kube-apiserver** | ⭐ the front door — every read/write goes through it; the only thing that talks to etcd |
| **etcd** | ⭐ distributed key-value store — **the entire cluster state**. ⚠️ back it up; lose it, lose the cluster |
| **kube-scheduler** | picks a node for each new pod (resources, affinity, taints) |
| **kube-controller-manager** | ⭐ reconciliation loops — node, replication, endpoint, service-account & token controllers |
| **cloud-controller-manager** | cloud-specific loops — node, route, service (load balancers), volume |

On each **worker node**: `kubelet` (starts pods, reports health), `kube-proxy` (service
networking/routing), and a container runtime (containerd).

⭐⭐ **The one idea that explains all of it — the reconciliation loop.** You declare *desired
state*; controllers continuously compare it against *actual state* and act to close the gap.
That's why a deleted pod comes back, why a failed node's pods reappear elsewhere, and why K8s
is declarative rather than imperative. "3 replicas" is a standing instruction, not a command.

---

## 3. Manifest anatomy

Every object has the same four top-level keys:

```yaml
apiVersion: apps/v1     # which API version to use
kind: Deployment        # what type of resource (Deployment, Service, Secret, ConfigMap…)
metadata:               # name, namespace, labels, annotations
  name: web
  labels: {app: web}
spec:                   # the desired state — shape depends on kind
  replicas: 3
  selector:
    matchLabels: {app: web}
  template:                          # the POD template
    metadata:
      labels: {app: web}            # ⚠️ must match selector.matchLabels
    spec:
      containers:
        - name: web
          image: myregistry/web:1.4.2     # ⚠️ pin a tag — never :latest
          ports: [{containerPort: 8000}]
          envFrom:
            - secretRef: {name: web-secrets}
          resources:
            requests: {cpu: 100m, memory: 128Mi}    # ⭐ scheduling
            limits:   {cpu: 500m, memory: 512Mi}    # ⭐ enforcement
          readinessProbe:                            # ⭐⭐ ready for traffic?
            httpGet: {path: /healthz, port: 8000}
          livenessProbe:                             # alive, or restart me?
            httpGet: {path: /healthz, port: 8000}
            initialDelaySeconds: 20
```

⭐ **`requests` vs `limits`:** requests are what the scheduler reserves; limits are the hard
cap. ⚠️ Exceeding a memory limit gets the container **OOM-killed** (exit 137); exceeding a CPU
limit only throttles it. Omitting requests entirely lets the scheduler overcommit a node into
instability.

⭐⭐ **Readiness vs liveness is the most-missed distinction.** *Readiness* failing removes the
pod from the Service's endpoints — no traffic, no restart. *Liveness* failing **restarts the
container**. ⚠️ Pointing liveness at an endpoint that touches the database means a slow
database restarts every pod in the cluster, turning a degradation into an outage.

---

## 4. Core object types ⭐

| Kind | Purpose |
|---|---|
| **Pod** | the unit of scheduling — rarely created directly |
| **Deployment** ⭐ | declarative replicas + **rolling updates & rollback** for stateless apps |
| **StatefulSet** | stable identities and per-pod storage — databases |
| **DaemonSet** | one pod per node — log/metrics agents |
| **Job / CronJob** | run-to-completion / scheduled work (migrations, batch) |
| **Service** ⭐ | ⭐ **stable virtual IP + DNS name** in front of a changing set of pods |
| **Ingress** | HTTP(S) routing by host/path into Services; TLS termination |
| **ConfigMap** | non-secret configuration |
| **Secret** | ⚠️ **base64, not encrypted** — enable encryption-at-rest or use an external manager |
| **PersistentVolumeClaim** | durable storage independent of a pod's lifecycle |
| **Namespace** | logical partition for isolation and quotas |
| **HorizontalPodAutoscaler** | scale replicas on CPU/memory/custom metrics |

⭐ **Service types:** `ClusterIP` (internal only, the default), `NodePort` (a port on every
node), `LoadBalancer` (provisions a cloud LB — ⚠️ one per Service gets expensive fast, which
is exactly why Ingress exists).

⭐ **Why a Service exists at all:** pod IPs change constantly. The Service is a stable name and
IP that load-balances to whichever pods currently match its label selector. Kubernetes' whole
networking model hangs on **labels and selectors** — not on IPs.

---

## 5. Everyday commands

```bash
brew install kubectl                      # or: apt install kubectl

kubectl apply -f deployment.yaml          # ⭐ declarative — the way to do it
kubectl get pods -o wide
kubectl get all -n mynamespace
kubectl describe pod <pod>                # ⭐⭐ events at the bottom explain scheduling failures
kubectl logs -f <pod> [-c container]
kubectl logs --previous <pod>             # ⭐ logs from the CRASHED instance
kubectl exec -it <pod> -- bash
kubectl port-forward svc/web 8000:80      # ⭐ reach an internal service from your laptop
kubectl rollout status deploy/web
kubectl rollout undo deploy/web           # ⭐ roll back
kubectl scale deploy/web --replicas=5
kubectl get events --sort-by=.lastTimestamp
```

⭐ **`describe` before `logs`.** If the pod never started, there are no logs — the *events*
tell you it's `Pending` (unschedulable), `ImagePullBackOff` (bad tag or missing registry
credentials), or `CrashLoopBackOff` (started, then died — *now* read `logs --previous`).

| Status | Meaning |
|---|---|
| `Pending` | ⚠️ no node satisfies the resource requests, or no PV is available |
| `ImagePullBackOff` | ⚠️ wrong tag/registry, or missing `imagePullSecrets` |
| `CrashLoopBackOff` | ⭐ container starts and exits repeatedly — `logs --previous` |
| `OOMKilled` (137) | ⚠️ exceeded the memory limit |
| `Running` but no traffic | ⭐ readiness probe failing, or selector labels don't match |

---

## 6. Learning locally

**Install/bootstrap:** `minikube` (⭐ easiest local cluster), `kind` (clusters in Docker),
`k3s` (lightweight, production-capable), `kubeadm` (build a real cluster by hand).

**Online playgrounds:** Kubernetes Playground, Play with Kubernetes, Katacoda-style classrooms.

---

## 7. Django/web app on K8s — the practical mapping

| Concern | Kubernetes answer |
|---|---|
| gunicorn/daphne processes | Deployment with N replicas ([app_servers.md](app_servers.md)) |
| supervisor/systemd | ⭐ the kubelet — restarts are built in |
| nginx vhost + TLS | Ingress + cert-manager ([tls_certbot.md](tls_certbot.md)) |
| `.env` | ConfigMap + Secret |
| `manage.py migrate` | ⭐ a **Job**, or an initContainer — never in the app's start command with N replicas |
| Celery workers | a separate Deployment (no Service — nothing connects *to* it) |
| Celery beat | ⚠️ exactly **one** replica, or a CronJob |
| static/media | S3 or a PVC — ⚠️ **not** the pod filesystem |

⚠️⚠️ Running migrations from the container's entrypoint means N replicas race to migrate
simultaneously on every deploy. Use a Job (or initContainer) that completes first.

---

## Interview points

- **What problem does K8s solve?** ⭐ Scheduling, self-healing, scaling and stable networking
  for containers across many machines — and it's overkill below that scale.
- **Pod vs container** ⭐ — a pod is the scheduling unit; containers in it share network and
  storage and talk over `localhost`.
- **The reconciliation loop** ⭐⭐ — declared desired state, controllers close the gap
  continuously. This is *the* Kubernetes idea.
- **What's in the control plane?** apiserver (the only path to etcd), etcd (all state),
  scheduler, controller-manager, cloud-controller-manager.
- **What is etcd, and why does it matter?** ⚠️ The complete cluster state — the one thing that
  must be backed up.
- **Why do you need a Service?** ⭐ Pod IPs are ephemeral; a Service is a stable name/IP that
  selects pods **by label**.
- **ClusterIP vs NodePort vs LoadBalancer vs Ingress** ⭐ — internal, node port, one cloud LB
  per Service, HTTP routing for many services behind one LB.
- **Readiness vs liveness** ⭐⭐ — pulled from load balancing vs restarted. ⚠️ A liveness probe
  that hits the database converts a slow DB into a cluster-wide restart storm.
- **`requests` vs `limits`** ⭐ — scheduling reservation vs hard cap; memory overrun =
  OOMKilled, CPU overrun = throttled.
- **Are Secrets encrypted?** ⚠️ Base64-encoded by default — enable encryption at rest.
- **Deployment vs StatefulSet** — interchangeable stateless pods vs stable identity and
  storage.
- **Debugging a pod that won't start** ⭐ — `describe` (events) before `logs`;
  `logs --previous` for a crash loop.
- **When would you *not* use Kubernetes?** ⭐ One app, one team, one server — the operational
  cost exceeds the benefit; a PaaS or a plain VPS wins.
