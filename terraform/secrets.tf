resource "google_secret_manager_secret" "confluence_url" {
  secret_id = "confluence-url"

  replication {
    auto {}
  }

  depends_on = [google_project_service.secretmanager]
}

resource "google_secret_manager_secret_version" "confluence_url" {
  secret      = google_secret_manager_secret.confluence_url.id
  secret_data = var.confluence_url
}

resource "google_secret_manager_secret" "confluence_username" {
  secret_id = "confluence-username"

  replication {
    auto {}
  }

  depends_on = [google_project_service.secretmanager]
}

resource "google_secret_manager_secret_version" "confluence_username" {
  secret      = google_secret_manager_secret.confluence_username.id
  secret_data = var.confluence_username
}

resource "google_secret_manager_secret" "confluence_api_token" {
  secret_id = "confluence-api-token"

  replication {
    auto {}
  }

  depends_on = [google_project_service.secretmanager]
}

resource "google_secret_manager_secret_version" "confluence_api_token" {
  secret      = google_secret_manager_secret.confluence_api_token.id
  secret_data = var.confluence_api_token
}

resource "google_secret_manager_secret" "confluence_space_key" {
  secret_id = "confluence-space-key"

  replication {
    auto {}
  }

  depends_on = [google_project_service.secretmanager]
}

resource "google_secret_manager_secret_version" "confluence_space_key" {
  secret      = google_secret_manager_secret.confluence_space_key.id
  secret_data = var.confluence_space_key
}
