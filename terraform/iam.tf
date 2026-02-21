resource "google_service_account" "scanner" {
  account_id   = "${var.service_name}-sa"
  display_name = "Container Scanner Service Account"
  description  = "Service account used by the GCP Container Vulnerability Scanner."
}

resource "google_project_iam_member" "scanner_artifact_registry_reader" {
  project = var.project_id
  role    = "roles/artifactregistry.reader"
  member  = "serviceAccount:${google_service_account.scanner.email}"
}

resource "google_project_iam_member" "scanner_container_analysis_viewer" {
  project = var.project_id
  role    = "roles/containeranalysis.viewer"
  member  = "serviceAccount:${google_service_account.scanner.email}"
}

resource "google_project_iam_member" "scanner_secret_accessor" {
  project = var.project_id
  role    = "roles/secretmanager.secretAccessor"
  member  = "serviceAccount:${google_service_account.scanner.email}"
}

resource "google_project_iam_member" "scheduler_run_invoker" {
  project = var.project_id
  role    = "roles/run.invoker"
  member  = "serviceAccount:${google_service_account.scanner.email}"
}
