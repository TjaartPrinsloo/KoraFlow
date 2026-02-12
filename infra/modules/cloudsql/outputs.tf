output "instance_name" {
  value = google_sql_database_instance.master.name
}

output "private_ip_address" {
  value = google_sql_database_instance.master.private_ip_address
}

output "connection_name" {
  value = google_sql_database_instance.master.connection_name
}
