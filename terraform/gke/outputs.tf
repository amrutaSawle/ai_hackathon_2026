output "cluster_name" {
  description = "Created GKE cluster name."
  value       = google_container_cluster.this.name
}

output "cluster_location" {
  description = "Zone containing the GKE control plane."
  value       = google_container_cluster.this.location
}

output "get_credentials_command" {
  description = "Run this command to configure kubectl for the cluster."
  value       = "gcloud container clusters get-credentials ${google_container_cluster.this.name} --zone ${google_container_cluster.this.location} --project ${var.project_id}"
}

output "artifact_registry_image_prefix" {
  description = "Artifact Registry image prefix for the backend and frontend."
  value       = "${var.region}-docker.pkg.dev/${var.project_id}/${google_artifact_registry_repository.finance_ai.repository_id}"
}
