#!/usr/bin/env bash
set -euo pipefail

required_commands=(docker gcloud helm kubectl terraform)
for command in "${required_commands[@]}"; do
  command -v "$command" >/dev/null 2>&1 || {
    echo "Required command not found: $command" >&2
    exit 1
  }
done

required_variables=(PROJECT_ID REGION ZONE CLUSTER_NAME ARTIFACT_REPOSITORY IMAGE_TAG DATABASE_PASSWORD APP_SECRET_KEY)
for variable in "${required_variables[@]}"; do
  [[ -n "${!variable:-}" ]] || {
    echo "Required environment variable is not set: $variable" >&2
    exit 1
  }
done

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
terraform_dir="$repo_root/terraform/gke"
registry="${REGION}-docker.pkg.dev/${PROJECT_ID}/${ARTIFACT_REPOSITORY}"
image_tag="${IMAGE_TAG}"
namespace="finance-ai"
release="finance-ai"
values_file="$(mktemp)"

cleanup() {
  rm -f "$values_file"
}
trap cleanup EXIT

echo "Configuring Google Cloud project: $PROJECT_ID"
gcloud config set project "$PROJECT_ID"
gcloud auth application-default print-access-token >/dev/null 2>&1 || {
  echo "Application Default Credentials are required. Run: gcloud auth application-default login" >&2
  exit 1
}

echo "Creating or updating GKE infrastructure with Terraform"
terraform -chdir="$terraform_dir" init
terraform -chdir="$terraform_dir" apply -auto-approve \
  -var="project_id=${PROJECT_ID}" \
  -var="region=${REGION}" \
  -var="zone=${ZONE}" \
  -var="cluster_name=${CLUSTER_NAME}" \
  -var="artifact_registry_repository=${ARTIFACT_REPOSITORY}"

echo "Configuring Docker and building images"
gcloud auth configure-docker "${REGION}-docker.pkg.dev" --quiet
docker build -t "${registry}/finance-ai-backend:${image_tag}" "$repo_root/finance-ai-backend"
docker build -t "${registry}/finance-ai-frontend:${image_tag}" "$repo_root/finance-ai-frontend"
docker push "${registry}/finance-ai-backend:${image_tag}"
docker push "${registry}/finance-ai-frontend:${image_tag}"

echo "Configuring kubectl"
gcloud container clusters get-credentials "$CLUSTER_NAME" \
  --zone="$ZONE" \
  --project="$PROJECT_ID"

cat >"$values_file" <<EOF
backend:
  image:
    repository: ${registry}/finance-ai-backend
    tag: "${image_tag}"
  replicaCount: 1
frontend:
  image:
    repository: ${registry}/finance-ai-frontend
    tag: "${image_tag}"
  replicaCount: 1
  service:
    type: ${FRONTEND_SERVICE_TYPE:-ClusterIP}
database:
  storage: 2Gi
  password: "${DATABASE_PASSWORD}"
secrets:
  secretKey: "${APP_SECRET_KEY}"
  openaiApiKey: "${OPENAI_API_KEY:-}"
  openaiModel: "${OPENAI_MODEL:-gpt-4.1-mini}"
config:
  corsOrigins: "${CORS_ORIGINS:-http://localhost:8080}"
ingress:
  enabled: false
EOF

echo "Deploying Finance AI with Helm"
helm upgrade --install "$release" "$repo_root/helm/finance-ai" \
  --namespace="$namespace" \
  --create-namespace \
  --values="$values_file" \
  --wait \
  --timeout=10m

echo "Deployment complete."
kubectl get pods,svc,pvc -n "$namespace"
if [[ "${FRONTEND_SERVICE_TYPE:-ClusterIP}" == "ClusterIP" ]]; then
  echo "Open the application with:"
  echo "kubectl port-forward -n $namespace service/${release}-finance-ai-frontend 8080:80"
fi
