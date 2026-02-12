output "frappe_sa_email" {
  value = google_service_account.frappe_sa.email
}

output "app_sa_email" {
  value = google_service_account.app_sa.email
}
