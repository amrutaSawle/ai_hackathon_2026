variable "project_id" {
  description = "Google Cloud project ID where the cluster is created."
  type        = string
}

variable "region" {
  description = "Region containing the selected zone."
  type        = string
  default     = "us-central1"
}

variable "zone" {
  description = "Zone for the cost-conscious, single-zone GKE cluster."
  type        = string
  default     = "us-central1-a"
}

variable "cluster_name" {
  description = "Name of the GKE cluster."
  type        = string
  default     = "finance-ai-test"
}

variable "artifact_registry_repository" {
  description = "Artifact Registry Docker repository used for Finance AI images."
  type        = string
  default     = "finance-ai"
}

variable "node_machine_type" {
  description = "Compute Engine machine type for GKE worker nodes."
  type        = string
  default     = "e2-small"
}

variable "node_count" {
  description = "Number of worker nodes. Keep this at 1 for low-cost testing."
  type        = number
  default     = 1

  validation {
    condition     = var.node_count >= 1
    error_message = "node_count must be at least 1."
  }
}

variable "network" {
  description = "VPC network for the cluster. Use default for a simple test deployment."
  type        = string
  default     = "default"
}

variable "subnetwork" {
  description = "Optional subnetwork name. Leave null to use the network default."
  type        = string
  default     = null
  nullable    = true
}
