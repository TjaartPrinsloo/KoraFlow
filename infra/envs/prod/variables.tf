variable "project_id" {
  description = "GCP Project ID for Production"
}

variable "region" {
  default = "us-central1"
}

variable "environment" {
  default = "prod"
}

variable "db_password" {
  description = "Initial DB password"
  sensitive   = true
}
