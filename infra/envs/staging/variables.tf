variable "project_id" {
  description = "GCP Project ID for Staging"
}

variable "region" {
  default = "us-central1"
}

variable "environment" {
  default = "staging"
}

variable "db_password" {
  description = "Initial DB password"
  sensitive   = true
}
