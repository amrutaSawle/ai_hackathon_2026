# GKE Terraform template

This template creates a zonal Standard GKE cluster for testing Finance AI. It
enables the APIs the cluster needs, creates the Artifact Registry Docker
repository, uses Workload Identity Federation, and gives the default GKE node
service account permission to pull images from Artifact Registry in the same
project.

The defaults intentionally use one `e2-small` node in `us-central1-a` to reduce
test cost. GKE control-plane free-tier credit does not cover node, disk, or
network costs. Destroy the cluster after testing.

## Prerequisites

- Terraform 1.6 or newer
- Google Cloud CLI authenticated with a principal allowed to create GKE clusters,
  enable APIs, and grant project IAM roles
- A Google Cloud project with billing enabled

## Create the cluster

```sh
cd terraform/gke
cp terraform.tfvars.example terraform.tfvars
# Edit terraform.tfvars and set project_id.

gcloud auth application-default login
terraform init
terraform plan
terraform apply
```

Configure `kubectl` with the command Terraform prints:

```sh
terraform output -raw get_credentials_command
# Copy and run the printed command.
kubectl get nodes
```

## Next steps

Use the one-command local deployment script in
[../../scripts/build-and-deploy-gke.sh](../../scripts/build-and-deploy-gke.sh)
or follow [../../build_and_deploy.md](../../build_and_deploy.md). For this test
cluster, use `ClusterIP` and `kubectl port-forward` instead of a public
LoadBalancer.

## Destroy the cluster

Run this as soon as testing is complete to stop node and disk costs:

```sh
terraform destroy
```
