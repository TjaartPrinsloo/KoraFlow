variable "project_id" {}
variable "region" {
  default = "us-central1"
}
variable "environment" {}
variable "vpc_id" {}

variable "tier" {
  description = "The machine type to use"
  default     = "db-f1-micro"
}

variable "db_version" {
  default = "MYSQL_8_0" # or POSTGRES_14, Frappe supports MariaDB primarily but MySQL 8 works too (MariaDB on GCP is in beta or older versions sometimes, checking needed. Frappe standard is MariaDB 10.6. GCP supports MySQL 8.0 which is compatible or Postgres 14. Frappe heavily prefers MariaDB. GCP Cloud SQL for MySQL supports MariaDB compatibility modes but official MariaDB engine support is distinct. We will use MYSQL_8_0 for broad compatibility or verify MariaDB support if strict.)
  # Update: Google Cloud SQL supports MySQL, PostgreSQL, and SQL Server. It does NOT support MariaDB as a first-class engine anymore (it was deprecated or never fully equal). Frappe works with MySQL 8.0.
}

variable "deletion_protection" {
  type    = bool
  default = true
}

variable "db_name" {
  default = "frappe"
}

variable "db_user" {
  default = "frappe"
}

variable "db_password" {
  sensitive = true
}
