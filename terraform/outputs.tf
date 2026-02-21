output "cloud_run_url" {
  description = "The URL of the deployed Cloud Run service."
  value       = google_cloud_run_v2_service.scanner.uri
}

output "service_account_email" {
  description = "The email address of the service account used by the scanner."
  value       = google_service_account.scanner.email
}

output "scheduler_job_name" {
  description = "The name of the Cloud Scheduler job for automated scans."
  value       = google_cloud_scheduler_job.scanner_daily.name
}
