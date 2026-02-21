resource "google_cloud_scheduler_job" "scanner_daily" {
  name             = "${var.service_name}-daily"
  description      = "Daily container vulnerability scan and Confluence report"
  schedule         = var.scan_schedule
  time_zone        = "UTC"
  region           = var.region
  attempt_deadline = "600s"

  retry_config {
    retry_count = 2
  }

  http_target {
    http_method = "POST"
    uri         = "${google_cloud_run_v2_service.scanner.uri}/scan"
    body        = base64encode(jsonencode({ publish = true }))

    headers = {
      "Content-Type" = "application/json"
    }

    oidc_token {
      service_account_email = google_service_account.scanner.email
      audience              = google_cloud_run_v2_service.scanner.uri
    }
  }

  depends_on = [google_project_service.cloudscheduler]
}
