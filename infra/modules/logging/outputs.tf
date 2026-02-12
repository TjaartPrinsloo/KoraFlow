output "audit_log_bucket" {
  value = google_storage_bucket.audit_logs.name
}

output "audit_sink_name" {
  value = google_logging_project_sink.audit_sink.name
}
