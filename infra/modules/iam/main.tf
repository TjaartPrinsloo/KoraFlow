# Frappe Service Account (Backend / System of Record)
resource "google_service_account" "frappe_sa" {
  account_id   = "${var.environment}-frappe-sa"
  display_name = "Frappe Service Account (${var.environment})"
  project      = var.project_id
}

# Antigravity Service Account (Frontend / API)
resource "google_service_account" "app_sa" {
  account_id   = "${var.environment}-app-sa"
  display_name = "Antigravity App Service Account (${var.environment})"
  project      = var.project_id
}

# Roles for Frappe SA
resource "google_project_iam_member" "frappe_cloudsql_client" {
  project = var.project_id
  role    = "roles/cloudsql.client"
  member  = "serviceAccount:${google_service_account.frappe_sa.email}"
}

resource "google_project_iam_member" "frappe_secret_accessor" {
  project = var.project_id
  role    = "roles/secretmanager.secretAccessor"
  member  = "serviceAccount:${google_service_account.frappe_sa.email}"
}

resource "google_project_iam_member" "frappe_log_writer" {
  project = var.project_id
  role    = "roles/logging.logWriter"
  member  = "serviceAccount:${google_service_account.frappe_sa.email}"
}

# Roles for App SA
resource "google_project_iam_member" "app_log_writer" {
  project = var.project_id
  role    = "roles/logging.logWriter"
  member  = "serviceAccount:${google_service_account.app_sa.email}"
}

resource "google_project_iam_member" "app_secret_accessor" {
  project = var.project_id
  role    = "roles/secretmanager.secretAccessor"
  member  = "serviceAccount:${google_service_account.app_sa.email}"
}
