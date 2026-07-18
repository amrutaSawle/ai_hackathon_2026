# Single-click GKE deployment

The repository now supports two deployment paths:

- **Local one command:** run `bash scripts/build-and-deploy-gke.sh`.
- **GitHub one click:** open **Actions → Deploy Finance AI to GKE → Run workflow**.

Both paths provision or update GKE with Terraform, build both Docker images,
push them to Artifact Registry, and deploy the Helm chart. The workflow is the
recommended repeatable option after the one-time setup below.

## One-time Google Cloud bootstrap

Create a GCS bucket for Terraform state. Bucket names are globally unique.

```sh
export PROJECT_ID="your-gcp-project-id"
export TF_STATE_BUCKET="${PROJECT_ID}-finance-ai-tfstate"

gcloud config set project "$PROJECT_ID"
gcloud storage buckets create "gs://${TF_STATE_BUCKET}" \
  --location=us-central1 \
  --uniform-bucket-level-access
gcloud storage buckets update "gs://${TF_STATE_BUCKET}" --versioning
```

Create a Google service account for the GitHub workflow, give it the required
project roles, then configure a GitHub Workload Identity Federation provider.
The service account needs, at minimum, permissions to manage GKE, Artifact
Registry, enabled services, project IAM binding for the node image-pull role,
and the Terraform-state bucket. Keep this bootstrap configuration separate from
the application deployment state.

## GitHub configuration

Create a GitHub Environment named `gke`, then add these **Environment
variables**:

| Variable | Example |
| --- | --- |
| `GCP_PROJECT_ID` | `my-project` |
| `GCP_REGION` | `us-central1` |
| `GCP_ZONE` | `us-central1-a` |
| `GKE_CLUSTER_NAME` | `finance-ai-test` |
| `ARTIFACT_REPOSITORY` | `finance-ai` |
| `TF_STATE_BUCKET` | `my-project-finance-ai-tfstate` |
| `GCP_WORKLOAD_IDENTITY_PROVIDER` | Full provider resource name |
| `GCP_DEPLOYER_SERVICE_ACCOUNT` | Deployer service-account email |

Add these **Environment secrets**:

| Secret | Value |
| --- | --- |
| `DATABASE_PASSWORD` | Output of `openssl rand -hex 24` |
| `APP_SECRET_KEY` | Output of `openssl rand -hex 32` |
| `OPENAI_API_KEY` | Optional OpenAI key |

The workflow expects Workload Identity Federation; do not place a Google service
account JSON key in GitHub Secrets. Restrict the identity provider's attribute
condition to this GitHub repository and grant the deployer only the roles it
needs.

## Local one-command deployment

```sh
cp scripts/deploy-gke.env.example scripts/deploy-gke.env
# Edit the file, then:
gcloud auth login
gcloud auth application-default login # One-time local authentication
source scripts/deploy-gke.env
bash scripts/build-and-deploy-gke.sh
```

The local script uses local Terraform state. For shared or repeat deployments,
initialize Terraform with the same GCS backend used by the GitHub workflow.

## Cost-safe test access

The default GitHub workflow creates a `ClusterIP` frontend service. After the
workflow succeeds, access it without creating a public load balancer:

```sh
kubectl port-forward -n finance-ai service/finance-ai-finance-ai-frontend 8080:80
```

Choose **public_service** when launching the workflow only if you want a public
Google LoadBalancer and accept its additional cost.
