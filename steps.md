# Build, deploy, and host Finance AI on GKE

This runbook deploys Finance AI to a Google Kubernetes Engine (GKE) cluster for
testing. It uses the project's Terraform, Docker, and Helm assets and keeps
PostgreSQL inside the cluster.

For a 20-minute test, use `ClusterIP` access and port-forwarding. This avoids a
public LoadBalancer and keeps cost very low. Destroy the cluster when finished.

## Architecture

```text
Browser
  │
  ├─ Test: kubectl port-forward → localhost:8080
  └─ Public: Google LoadBalancer external IP
                                  │
                                  ▼
                         Angular + Nginx frontend
                                  │ /api/*
                                  ▼
                            FastAPI backend
                                  │
                                  ▼
                         PostgreSQL StatefulSet
```

## 1. Prerequisites

You need a Google Cloud project with billing enabled and these local tools:

```sh
gcloud --version
terraform --version
docker --version
kubectl version --client
helm version
```

You also need permission to create GKE clusters, Artifact Registry repositories,
Cloud Storage buckets, and project IAM bindings.

Use these low-cost test defaults:

```sh
export PROJECT_ID="your-gcp-project-id"
export REGION="us-central1"
export ZONE="us-central1-a"
export CLUSTER_NAME="finance-ai-test"
export ARTIFACT_REPOSITORY="finance-ai"
export IMAGE_TAG="test-$(date +%Y%m%d-%H%M%S)"
export TF_STATE_BUCKET="${PROJECT_ID}-finance-ai-tfstate"
```

Authenticate:

```sh
gcloud auth login
gcloud auth application-default login
gcloud config set project "$PROJECT_ID"
```

## 2. Create the Terraform-state bucket (one time)

Terraform state records the GKE and Artifact Registry resources that it creates.
The bucket name must be globally unique.

```sh
gcloud storage buckets create "gs://${TF_STATE_BUCKET}" \
  --location="$REGION" \
  --uniform-bucket-level-access

gcloud storage buckets update "gs://${TF_STATE_BUCKET}" --versioning
```

For local-only testing, the deployment script uses local Terraform state. Use
the GCS bucket when using the GitHub Actions deployment workflow or when
multiple people manage the infrastructure.

## 3. Configure deployment secrets

Create a local, Git-ignored configuration file:

```sh
cp scripts/deploy-gke.env.example scripts/deploy-gke.env
```

Generate secrets:

```sh
openssl rand -hex 24 # PostgreSQL password
openssl rand -hex 32 # FastAPI application secret
```

Edit `scripts/deploy-gke.env`. At minimum, set these values:

```sh
export PROJECT_ID="your-gcp-project-id"
export REGION="us-central1"
export ZONE="us-central1-a"
export CLUSTER_NAME="finance-ai-test"
export ARTIFACT_REPOSITORY="finance-ai"
export IMAGE_TAG="test-1"
export DATABASE_PASSWORD="generated-hex-password"
export APP_SECRET_KEY="generated-hex-secret"
export OPENAI_API_KEY="" # Optional
export FRONTEND_SERVICE_TYPE="ClusterIP"
export CORS_ORIGINS="http://localhost:8080"
```

Do not commit `scripts/deploy-gke.env` or share its secret values.

## 4. Build and deploy

From the repository root:

```sh
source scripts/deploy-gke.env
bash scripts/build-and-deploy-gke.sh
```

The script automatically:

1. Enables required Google Cloud APIs.
2. Creates or updates Artifact Registry and the zonal GKE cluster with Terraform.
3. Builds backend and frontend Docker images.
4. Pushes images to Artifact Registry.
5. Configures `kubectl` for the GKE cluster.
6. Deploys PostgreSQL, database migrations, FastAPI, and Angular/Nginx using Helm.

## 5. Verify Kubernetes resources

```sh
kubectl get pods,services,pvc,jobs -n finance-ai
```

Expected state:

- Backend, frontend, and PostgreSQL Pods: `Running`
- Migration Job: `Completed`
- PostgreSQL PVC: `Bound`

If something fails:

```sh
kubectl get events -n finance-ai --sort-by=.lastTimestamp
kubectl logs -n finance-ai deployment/finance-ai-finance-ai-backend
kubectl logs -n finance-ai job/finance-ai-finance-ai-migrations
```

## 6. Initialize test data

Migrations create tables only. The UI currently requests data for user ID `1`,
so seed the test user, cards, scoring rules, and transactions once after the
first deploy:

```sh
kubectl exec -n finance-ai deployment/finance-ai-finance-ai-backend -- \
  python -m seeds.seed_all
```

The seed script is idempotent: rerunning it does not duplicate its sample data.
It is intended for testing, not production user data.

## 7. Access the application in a browser

### Option A: private test access (recommended)

With `FRONTEND_SERVICE_TYPE="ClusterIP"`, run:

```sh
kubectl port-forward -n finance-ai \
  service/finance-ai-finance-ai-frontend 8080:80
```

Open <http://localhost:8080>.

Keep the terminal running while testing. Press `Ctrl+C` to stop port-forwarding.

### Option B: public IP hosting

To make the frontend publicly reachable, set this before running the deployment:

```sh
export FRONTEND_SERVICE_TYPE="LoadBalancer"
```

Deploy again:

```sh
source scripts/deploy-gke.env
bash scripts/build-and-deploy-gke.sh
```

Get the external address:

```sh
kubectl get service -n finance-ai finance-ai-finance-ai-frontend
```

Wait for `EXTERNAL-IP`, then browse to:

```text
http://EXTERNAL-IP
```

This is appropriate for short-lived testing. It does not provide a custom domain
or HTTPS certificate. For a production host, add DNS plus an Ingress/Gateway and
managed TLS before exposing real users.

## 8. Update the application

For code changes, use a new image tag and run deployment again:

```sh
export IMAGE_TAG="test-2"
source scripts/deploy-gke.env
bash scripts/build-and-deploy-gke.sh
```

The script updates Terraform resources if needed and Helm performs a rolling
update of the frontend and backend.

## 9. Stop all GCP test costs

First remove the application:

```sh
helm uninstall finance-ai --namespace finance-ai
```

Then destroy the cluster and Artifact Registry created by Terraform:

```sh
terraform -chdir=terraform/gke destroy \
  -var="project_id=${PROJECT_ID}" \
  -var="region=${REGION}" \
  -var="zone=${ZONE}" \
  -var="cluster_name=${CLUSTER_NAME}" \
  -var="artifact_registry_repository=${ARTIFACT_REPOSITORY}"
```

Confirm that no GKE cluster remains:

```sh
gcloud container clusters list
```

Keep the Terraform-state bucket if you plan to deploy again. Delete it only
when the environment is permanently retired.
