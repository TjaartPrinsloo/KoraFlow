output "vpc_id" {
  value = google_compute_network.vpc_network.id
}

output "vpc_name" {
  value = google_compute_network.vpc_network.name
}

output "app_subnet_id" {
  value = google_compute_subnetwork.app_subnet.id
}

output "backend_subnet_id" {
  value = google_compute_subnetwork.backend_subnet.id
}

output "db_subnet_id" {
  value = google_compute_subnetwork.db_subnet.id
}

output "vpc_access_connector_id" {
  value = google_vpc_access_connector.connector.id
}
