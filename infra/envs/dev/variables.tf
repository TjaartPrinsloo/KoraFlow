variable "project_id" {
  description = "GCP Project ID for Dev"
}

variable "region" {
  default = "us-central1"
}

variable "environment" {
  default = "dev"
}

variable "db_password" {
  description = "Initial DB password"
  sensitive   = true
}
