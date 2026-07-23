# Build and deploy Finance AI to GKE

This guide deploys the existing Helm chart to Google Kubernetes Engine (GKE).
It keeps PostgreSQL inside the cluster using the chart's StatefulSet and
persistent volume claim.

To create the GKE cluster with Terraform instead of the `gcloud` command in
step 4, use the template in [terraform/gke](terraform/gke/README.md), then
continue with step 5.

## Prerequisites

Install and authenticate the following tools on the machine running these
commands:

- Google Cloud CLI (`gcloud`)
- Docker
- `kubectl`
- Helm 3

Authenticate and define deployment variables. Replace the project ID with your
Google Cloud project.

```sh
gcloud auth login
gcloud auth application-default login

export PROJECT_ID="your-gcp-project-id"
export REGION="asia-south1"
export CLUSTER="finance-ai-gke"
export REPOSITORY="finance-ai"
export IMAGE_TAG="1.0.0"

gcloud config set project "$PROJECT_ID"
```

## 1. Enable Google Cloud APIs

```sh
gcloud services enable \
  container.googleapis.com \
  artifactregistry.googleapis.com \
  compute.googleapis.com
```

## 2. Create an Artifact Registry repository

```sh
gcloud artifacts repositories create "$REPOSITORY" \
  --repository-format=docker \
  --location="$REGION" \
  --description="Finance AI container images"

gcloud auth configure-docker "${REGION}-docker.pkg.dev"
```

If the repository has already been created, skip the first command.

## 3. Build and publish the images

Run these commands from the repository root.

```sh
export REGISTRY="${REGION}-docker.pkg.dev/${PROJECT_ID}/${REPOSITORY}"

docker build -t "${REGISTRY}/finance-ai-backend:${IMAGE_TAG}" finance-ai-backend
docker build -t "${REGISTRY}/finance-ai-frontend:${IMAGE_TAG}" finance-ai-frontend

docker push "${REGISTRY}/finance-ai-backend:${IMAGE_TAG}"
docker push "${REGISTRY}/finance-ai-frontend:${IMAGE_TAG}"
```

## 4. Create a GKE cluster

This creates a regional, two-node standard GKE cluster.

```sh
gcloud container clusters create "$CLUSTER" \
  --location="$REGION" \
  --num-nodes=2 \
  --machine-type=e2-standard-2 \
  --workload-pool="${PROJECT_ID}.svc.id.goog"

gcloud container clusters get-credentials "$CLUSTER" \
  --location="$REGION"

kubectl cluster-info
```

## 5. Allow GKE to pull the images

If the application pods show `ImagePullBackOff` because of Artifact Registry
permissions, grant the GKE node service account read access:

```sh
export PROJECT_NUMBER="$(gcloud projects describe "$PROJECT_ID" \
  --format='value(projectNumber)')"

gcloud projects add-iam-policy-binding "$PROJECT_ID" \
  --member="serviceAccount:${PROJECT_NUMBER}-compute@developer.gserviceaccount.com" \
  --role="roles/artifactregistry.reader"
```

## 6. Create private production values

Create `gke-values.yaml` in the repository root. Do **not** commit this file.
Replace the project ID and the generated secrets.

```yaml
backend:
  image:
    repository: asia-south1-docker.pkg.dev/your-gcp-project-id/finance-ai/finance-ai-backend
    tag: "1.0.0"

frontend:
  image:
    repository: asia-south1-docker.pkg.dev/your-gcp-project-id/finance-ai/finance-ai-frontend
    tag: "1.0.0"
  service:
    type: LoadBalancer

database:
  storage: 10Gi
  password: REPLACE_WITH_A_LONG_HEX_PASSWORD

secrets:
  secretKey: REPLACE_WITH_A_LONG_HEX_SECRET
  openaiApiKey: ""
  openaiModel: gpt-4.1-mini

config:
  corsOrigins: "https://your-future-domain.example"

ingress:
  enabled: false
```

Generate the password and application secret with the following commands. Use a
hex database password because the chart builds the database URL from this value.

```sh
openssl rand -hex 24
openssl rand -hex 32
```

## 7. Validate and deploy with Helm

```sh
helm lint helm/finance-ai

helm upgrade --install finance-ai helm/finance-ai \
  --namespace finance-ai \
  --create-namespace \
  --values gke-values.yaml \
  --wait \
  --timeout 10m
```

The deployment creates PostgreSQL, runs the Alembic migration job, and deploys
the backend and frontend. The frontend's LoadBalancer is the public entrypoint;
it proxies `/api` requests to the backend inside the cluster.

## 8. Verify the deployment

```sh
kubectl get pods -n finance-ai
kubectl get jobs -n finance-ai
kubectl get pvc -n finance-ai
kubectl get svc -n finance-ai
```

Wait for the frontend service to receive an `EXTERNAL-IP`, then open:

```text
http://EXTERNAL-IP
```

Use these commands if troubleshooting is needed:

```sh
kubectl get events -n finance-ai --sort-by=.lastTimestamp
kubectl logs -n finance-ai deployment/finance-ai-finance-ai-backend
kubectl logs -n finance-ai job/finance-ai-finance-ai-migrations
```

## Update a deployment

Build and push new images with a new immutable tag, change both image tags in
`gke-values.yaml`, then run the Helm command again:

```sh
helm upgrade finance-ai helm/finance-ai \
  --namespace finance-ai \
  --values gke-values.yaml \
  --wait \
  --timeout 10m
```

## Delete the application

This removes application workloads but deliberately retains the PersistentVolume
Claim so database data is not accidentally deleted.

```sh
helm uninstall finance-ai --namespace finance-ai
```

To delete the cluster when it is no longer needed:

```sh
gcloud container clusters delete "$CLUSTER" --location="$REGION"
```
