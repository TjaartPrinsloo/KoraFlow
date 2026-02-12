# Cloud Audit Logs & Log Sink Configuration

# Enable Data Access Audit Logs for all services
resource "google_project_iam_audit_config" "all_services" {
  project = var.project_id
  service = "allServices"

  audit_log_config {
    log_type = "ADMIN_READ"
  }
  audit_log_config {
    log_type = "DATA_READ"
  }
  audit_log_config {
    log_type = "DATA_WRITE"
  }
}

# Log Sink → Cloud Storage (Long-term retention for compliance)
resource "google_storage_bucket" "audit_logs" {
  name          = "${var.project_id}-${var.environment}-audit-logs"
  location      = var.region
  project       = var.project_id
  force_destroy = false

  uniform_bucket_level_access = true

  versioning {
    enabled = true
  }

  lifecycle_rule {
    condition {
      age = var.log_retention_days
    }
    action {
      type = "Delete"
    }
  }

  retention_policy {
    is_locked        = var.environment == "prod" ? true : false
    retention_period = var.log_retention_days * 86400 # seconds
  }
}

resource "google_logging_project_sink" "audit_sink" {
  name        = "${var.environment}-audit-log-sink"
  project     = var.project_id
  destination = "storage.googleapis.com/${google_storage_bucket.audit_logs.name}"
  filter      = "logName:\"logs/cloudaudit.googleapis.com\""

  unique_writer_identity = true
}

# Grant the sink's service account write access to the bucket
resource "google_storage_bucket_iam_member" "sink_writer" {
  bucket = google_storage_bucket.audit_logs.name
  role   = "roles/storage.objectCreator"
  member = google_logging_project_sink.audit_sink.writer_identity
}
