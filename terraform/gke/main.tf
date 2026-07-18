locals {
  required_apis = toset([
    "artifactregistry.googleapis.com",
    "compute.googleapis.com",
    "container.googleapis.com",
    "iam.googleapis.com",
  ])
}

data "google_project" "current" {
  project_id = var.project_id
}

resource "google_project_service" "required" {
  for_each           = local.required_apis
  project            = var.project_id
  service            = each.value
  disable_on_destroy = false
}

resource "google_artifact_registry_repository" "finance_ai" {
  location      = var.region
  repository_id = var.artifact_registry_repository
  description   = "Finance AI container images"
  format        = "DOCKER"

  depends_on = [google_project_service.required]
}

resource "google_container_cluster" "this" {
  name     = var.cluster_name
  location = var.zone

  network    = var.network
  subnetwork = var.subnetwork

  # A separately managed node pool gives the template a predictable, low-cost
  # one-node default and makes node changes independent from control-plane changes.
  remove_default_node_pool = true
  initial_node_count       = 1
  deletion_protection      = false

  workload_identity_config {
    workload_pool = "${var.project_id}.svc.id.goog"
  }

  release_channel {
    channel = "REGULAR"
  }

  depends_on = [google_project_service.required]
}

resource "google_container_node_pool" "primary" {
  name       = "primary"
  location   = var.zone
  cluster    = google_container_cluster.this.name
  node_count = var.node_count

  node_config {
    machine_type = var.node_machine_type
    oauth_scopes = ["https://www.googleapis.com/auth/cloud-platform"]

    workload_metadata_config {
      mode = "GKE_METADATA"
    }

    labels = {
      environment = "test"
      application = "finance-ai"
    }
  }
}

# Lets GKE nodes pull the backend and frontend images from an Artifact Registry
# repository in this project. This does not create a repository.
resource "google_project_iam_member" "node_artifact_registry_reader" {
  project = var.project_id
  role    = "roles/artifactregistry.reader"
  member  = "serviceAccount:${data.google_project.current.number}-compute@developer.gserviceaccount.com"

  depends_on = [google_project_service.required]
}
