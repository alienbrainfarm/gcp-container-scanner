resource "google_cloud_run_v2_service" "scanner" {
  name     = var.service_name
  location = var.region

  template {
    service_account = google_service_account.scanner.email

    scaling {
      min_instance_count = var.cloud_run_min_instances
      max_instance_count = var.cloud_run_max_instances
    }

    timeout = "${var.cloud_run_timeout_seconds}s"

    containers {
      image = var.image

      resources {
        limits = {
          cpu    = var.cloud_run_cpu
          memory = var.cloud_run_memory
        }
      }

      ports {
        name           = "http1"
        container_port = 8080
      }

      env {
        name  = "GCP_PROJECT_ID"
        value = var.project_id
      }

      env {
        name  = "ARTIFACT_REGISTRY_LOCATION"
        value = var.artifact_registry_location
      }

      env {
        name  = "ARTIFACT_REGISTRY_REPOSITORY"
        value = var.artifact_registry_repository
      }

      env {
        name  = "LOG_LEVEL"
        value = var.log_level
      }

      env {
        name = "CONFLUENCE_URL"
        value_source {
          secret_key_ref {
            secret  = google_secret_manager_secret.confluence_url.secret_id
            version = "latest"
          }
        }
      }

      env {
        name = "CONFLUENCE_USERNAME"
        value_source {
          secret_key_ref {
            secret  = google_secret_manager_secret.confluence_username.secret_id
            version = "latest"
          }
        }
      }

      env {
        name = "CONFLUENCE_API_TOKEN"
        value_source {
          secret_key_ref {
            secret  = google_secret_manager_secret.confluence_api_token.secret_id
            version = "latest"
          }
        }
      }

      env {
        name = "CONFLUENCE_SPACE_KEY"
        value_source {
          secret_key_ref {
            secret  = google_secret_manager_secret.confluence_space_key.secret_id
            version = "latest"
          }
        }
      }

      liveness_probe {
        http_get {
          path = "/health"
          port = 8080
        }
        initial_delay_seconds = 10
        period_seconds        = 30
        timeout_seconds       = 5
        failure_threshold     = 3
      }
    }
  }

  depends_on = [
    google_project_service.run,
    google_project_iam_member.scanner_secret_accessor,
  ]
}
