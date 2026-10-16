# ShopAdmin

A small admin panel for an online store. You can add products, edit price and stock, search, filter by
category and see a few numbers on top (total products, low stock, categories, inventory value).

The app itself is kept small on purpose. The point of the project is everything around it: tests, docker,
CI/CD, security scan, terraform, kubernetes, helm, autoscaling and monitoring.

Ashutosh Kumar - 24bcs10111

## Stack

| part | what |
|---|---|
| frontend | React + Vite, plain CSS, served by nginx |
| backend | FastAPI, SQLAlchemy, Alembic |
| database | PostgreSQL 16 |
| tests | pytest (runs on in-memory sqlite) |
| containers | Docker, docker compose |
| CI/CD | GitHub Actions, Trivy, GHCR |
| infra | Terraform (AWS VPC + EKS) |
| cluster | Kubernetes (minikube for now), Helm, ingress-nginx, HPA |
| monitoring | Prometheus + Grafana (kube-prometheus-stack) |

```
browser -> ingress -> /      -> frontend (nginx)
                   -> /api   -> backend (fastapi) -> postgres
prometheus -> backend /metrics -> grafana
```

## Folders

```
backend/          fastapi app, alembic migration, tests, Dockerfile
frontend/         react app, nginx.conf, Dockerfile
docker-compose.yml
.github/workflows/ci.yml
terraform/        vpc + eks
k8s/              namespace
helm/shopadmin/   the helm chart
monitoring/       prometheus/grafana values + dashboard
troubleshooting/  two broken manifests for the demo
```

## API

| method | path | |
|---|---|---|
| GET | /health | liveness, no db |
| GET | /ready | readiness, checks db |
| GET | /metrics | prometheus metrics |
| GET | /api/products?q=&category= | list, search, filter |
| GET | /api/products/stats | numbers for the cards |
| GET | /api/products/{id} | one product |
| POST | /api/products | create |
| PUT | /api/products/{id} | update (only the fields you send) |
| DELETE | /api/products/{id} | delete |

Swagger is at `http://localhost:8000/docs`.

## Run it with docker compose

```bash
docker compose up --build
```

- app: http://localhost:3000
- api docs: http://localhost:8000/docs

`docker compose down -v` stops it and deletes the db volume.

Both images run as non-root. Backend runs as uid 10001, frontend uses `nginx-unprivileged` on port 8080.
The backend container runs `alembic upgrade head` before starting uvicorn.

## Tests

```bash
cd backend
python -m venv .venv
.venv/Scripts/activate        # linux/mac: source .venv/bin/activate
pip install -r requirements-dev.txt
pytest -v
```

9 tests covering health, create, get, validation, duplicate sku, list/filter, update, delete, stats and
metrics. `tests/conftest.py` swaps the db for in-memory sqlite so tests never touch postgres.

## CI/CD

`.github/workflows/ci.yml` runs on every push and PR to `main`:

1. **test** - pytest, then `npm ci && npm run build` for the frontend. If a test fails, nothing else runs.
2. **build** - builds both images tagged with the commit sha, scans them with Trivy, then pushes to
   `ghcr.io/the-ashutosh/shopadmin-backend` and `-frontend` (push only happens on `main`, not on PRs).
3. **deploy** - starts a throwaway k3s cluster on the runner, loads the two images it just pushed,
   runs `helm upgrade --install` with the new sha tag and `--wait`, then curls `/api/products/stats` through the
   frontend. So a green run means the chart and images really come up and talk to postgres. An always-on EKS
   cluster would cost ~$150/month, so it is only brought up with terraform when needed (see below).

Image tags are the git sha, so every image in the registry points back to exactly one commit.

### Trivy

Trivy scans both images (the OS packages and the python/node packages inside) for known CVEs. The job fails
if it finds any HIGH or CRITICAL CVE that has a fix available (`ignore-unfixed`), so a vulnerable image never
gets pushed. When I scanned locally both images were clean: debian 13 slim for the backend and alpine for the
frontend had 0 HIGH/CRITICAL fixable issues.

## Kubernetes on minikube

```bash
minikube start --driver=docker --cpus=4 --memory=6144 --addons=ingress,metrics-server

# monitoring first, so the ServiceMonitor CRD exists when the app chart goes in
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm upgrade --install monitoring prometheus-community/kube-prometheus-stack \
  -n monitoring --create-namespace -f monitoring/prometheus-values.yaml
kubectl apply -f monitoring/dashboard.yaml

# build images straight into minikube
minikube image build -t shopadmin-backend:local ./backend
minikube image build -t shopadmin-frontend:local ./frontend

kubectl apply -f k8s/namespace.yaml
helm upgrade --install shopadmin ./helm/shopadmin -n shopadmin -f helm/shopadmin/values-local.yaml

kubectl get pods,svc,ingress,hpa -n shopadmin
helm list -n shopadmin
```

What the chart creates:

- backend and frontend Deployments, 2 replicas each, with resource limits, readiness probes on both and a liveness probe on the backend
- ClusterIP Services `backend`, `frontend`, `postgres`
- postgres Deployment with a PVC, credentials in a Secret
- Ingress: `/api` goes to the backend, everything else to the frontend
- HPA on the backend: 2 to 5 pods at 60% cpu
- ServiceMonitor so Prometheus scrapes `/metrics` (only if the Prometheus operator is installed)

The backend pods wait for postgres with an init container, and migrations take a postgres lock, so two pods
starting together don't both try to create the table.

The postgres password is random. The chart makes one on first install and reuses it from the `db` Secret on
every upgrade. Pass `--set postgres.password=...` if you want your own.

If a pod is stuck in `ImagePullBackOff` with `network is unreachable` (minikube trying IPv6 to quay.io), pull it
on the host and load it in:

```bash
docker pull <image> && minikube image load <image>
kubectl delete pod -n <ns> <pod>
```

### Open the app through the ingress

On Windows/mac with the docker driver the minikube IP isn't reachable, so run `minikube tunnel` in another
terminal and add `127.0.0.1 shopadmin.local` to the hosts file (`/etc/hosts` on mac,
`C:\Windows\System32\drivers\etc\hosts` on Windows). Then open http://shopadmin.local.

### Autoscaling demo

```bash
kubectl create deployment load -n shopadmin --image=busybox --replicas=4 -- \
  sh -c "while true; do wget -q -O /dev/null http://backend:8000/api/products/stats; done"
kubectl get hpa -n shopadmin -w        # cpu goes way past 60%, replicas go up to 5
kubectl delete deployment load -n shopadmin
```

## Monitoring

```bash
kubectl port-forward -n monitoring svc/monitoring-kube-prometheus-prometheus 9090:9090
kubectl port-forward -n monitoring svc/monitoring-grafana 3001:80
```

- Prometheus: http://localhost:9090/targets - look for `serviceMonitor/shopadmin/backend`, both pods `UP`
- Grafana: http://localhost:3001, user `admin`, password from
  `kubectl get secret -n monitoring monitoring-grafana -o jsonpath="{.data.admin-password}" | base64 -d`
- The **ShopAdmin** dashboard is loaded automatically from `monitoring/dashboard.yaml`: requests per second,
  p95 latency, 5xx rate and number of backend pods up.

## Terraform (AWS)

`terraform/` creates a VPC (2 public + 2 private subnets in 2 AZs, one NAT gateway) and an EKS cluster with one
managed node group (2x t3.small), in `ap-south-1` by default.

```bash
cd terraform
cp terraform.tfvars.example terraform.tfvars    # optional, defaults are fine
aws configure                                   # credentials stay on your machine, never in git
terraform init
terraform plan
terraform apply                                 # ~15 min
aws eks update-kubeconfig --region ap-south-1 --name shopadmin
```

Then on EKS:

```bash
helm upgrade --install ingress-nginx ingress-nginx --repo https://kubernetes.github.io/ingress-nginx \
  -n ingress-nginx --create-namespace
# same monitoring + app install as above, but with values-eks.yaml and the GHCR images
helm upgrade --install shopadmin ./helm/shopadmin -n shopadmin --create-namespace \
  -f helm/shopadmin/values-eks.yaml --set tag=<commit sha>
```

The GHCR packages need to be public (package settings on GitHub) or the cluster needs an imagePullSecret.

**Destroy it when done**, EKS + NAT cost money every hour:

```bash
terraform destroy
```

This was applied once in `ap-south-1` (49 resources, ~12 min), checked in the console and with `kubectl get nodes`,
then destroyed the same day - about 27 minutes of runtime in total. To keep it cheap on a free-plan account the nodes
are t3.small and EKS is on 1.37 (older versions are in extended support, which costs 6x more per hour). The app
itself was not deployed on EKS for that run: the load balancer and the postgres volume would be created by Kubernetes,
not terraform, so `terraform destroy` would not clean them up. The app runs on minikube instead.

## Screenshots

Everything in [screenshots/](screenshots/) was taken from the real running setup (docker compose and minikube on
my laptop, the GitHub Actions run, and the EKS cluster on AWS).

| what | file |
|---|---|
| app through the ingress | [01](screenshots/01-app-ingress.png), [08 phone](screenshots/08-phone.png) |
| add / duplicate sku / edit / delete / search | [02](screenshots/02-add-product-form.png), [03](screenshots/03-product-added.png), [04](screenshots/04-duplicate-sku-error.png), [05](screenshots/05-edited-low-stock.png), [06](screenshots/06-deleted.png), [07](screenshots/07-search-filter.png) |
| docker compose up --build, localhost:3000 | [14 up](screenshots/14-docker-compose-up.png), [14 ps](screenshots/14-docker-compose.png), [09](screenshots/09-docker-compose-localhost-3000.png) |
| swagger | [10](screenshots/10-swagger.png) |
| pytest -v | [13](screenshots/13-pytest.png) |
| trivy in the pipeline | [15 backend](screenshots/15-trivy-ci-backend.png), [15 frontend](screenshots/15-trivy-ci-frontend.png) |
| kubectl get pods / svc / ingress, helm list | [16](screenshots/16-kubectl-helm.png) |
| HPA idle and scaling 2 -> 5 | [17](screenshots/17-hpa-idle.png), [18](screenshots/18-hpa-scaled.png) |
| /metrics, prometheus targets, grafana | [19](screenshots/19-metrics.png), [11](screenshots/11-prometheus-targets.png), [12](screenshots/12-grafana-dashboard.png) |
| terraform init + validate, plan | [20](screenshots/20-terraform-init.png), [22](screenshots/22-terraform-plan.png) |
| EKS up: terraform output, nodes, pods | [23](screenshots/23-eks-cluster.png) |
| AWS console: VPC, subnets, EKS cluster, nodes | [24](screenshots/24-aws-vpc.png), [25](screenshots/25-aws-subnets.png), [26](screenshots/26-aws-eks-cluster.png), [27](screenshots/27-aws-eks-nodes.png) |
| terraform destroy | [28](screenshots/28-terraform-destroy.png) |
| pipeline green incl. deploy, deploy log | [31](screenshots/31-actions-green.png), [32](screenshots/32-actions-deploy.png) |
| GHCR packages with sha tags | [29 backend](screenshots/29-ghcr-backend.png), [30 frontend](screenshots/30-ghcr-frontend.png) |
| git log | [21](screenshots/21-git-log.png) |

## Troubleshooting demo

```bash
kubectl apply -f troubleshooting/broken-image.yaml
kubectl get pods -n shopadmin                 # ErrImagePull / ImagePullBackOff
kubectl describe pod -n shopadmin <pod>       # events show the tag doesn't exist

kubectl apply -f troubleshooting/broken-service.yaml
kubectl get endpointslices -n shopadmin       # broken-service has no endpoints
kubectl get pods -n shopadmin --show-labels   # pods are app=backend, service selects app=backnd

kubectl delete -f troubleshooting/
```
