variable "project_id" {
  description = "The GCP project ID where resources will be deployed."
  type        = string
}

variable "region" {
  description = "The GCP region for resource deployment."
  type        = string
  default     = "us-central1"
}

variable "service_name" {
  description = "The name to use for the Cloud Run service and related resources."
  type        = string
  default     = "container-scanner"
}

variable "image" {
  description = "The container image URI to deploy to Cloud Run (e.g. gcr.io/PROJECT_ID/container-scanner:latest)."
  type        = string
}

variable "artifact_registry_location" {
  description = "The location of the Artifact Registry repository to scan."
  type        = string
  default     = "us-central1"
}

variable "artifact_registry_repository" {
  description = "The name of the Artifact Registry repository to scan."
  type        = string
  default     = "default"
}

variable "confluence_url" {
  description = "The base URL of the Confluence instance (e.g. https://your-domain.atlassian.net)."
  type        = string
}

variable "confluence_username" {
  description = "The Confluence account username (email address)."
  type        = string
}

variable "confluence_api_token" {
  description = "The Confluence API token used for authentication."
  type        = string
  sensitive   = true
}

variable "confluence_space_key" {
  description = "The Confluence space key where vulnerability reports will be published."
  type        = string
}

variable "scan_schedule" {
  description = "The cron expression for the Cloud Scheduler job that triggers automated scans."
  type        = string
  default     = "0 2 * * *"
}

variable "log_level" {
  description = "The application log level (DEBUG, INFO, WARNING, ERROR)."
  type        = string
  default     = "INFO"
}

variable "cloud_run_min_instances" {
  description = "Minimum number of Cloud Run instances."
  type        = number
  default     = 0
}

variable "cloud_run_max_instances" {
  description = "Maximum number of Cloud Run instances."
  type        = number
  default     = 10
}

variable "cloud_run_memory" {
  description = "Memory limit for each Cloud Run instance."
  type        = string
  default     = "1Gi"
}

variable "cloud_run_cpu" {
  description = "CPU limit for each Cloud Run instance."
  type        = string
  default     = "2"
}

variable "cloud_run_timeout_seconds" {
  description = "Request timeout in seconds for Cloud Run."
  type        = number
  default     = 300
}
