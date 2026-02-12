resource "google_secret_manager_secret" "secrets" {
  for_each  = toset(var.secrets)
  secret_id = "${var.environment}-${each.key}"
  project   = var.project_id

  replication {
    auto {}
  }
}
