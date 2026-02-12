variable "project_id" {
  description = "The ID of the project where this VPC will be created"
  type        = string
}

variable "region" {
  description = "The region for the VPC and subnets"
  type        = string
  default     = "us-central1"
}

variable "environment" {
  description = "The environment name (e.g., dev, staging, prod)"
  type        = string
}

variable "app_subnet_cidr" {
  description = "CIDR range for the app subnet"
  type        = string
}

variable "backend_subnet_cidr" {
  description = "CIDR range for the backend subnet"
  type        = string
}

variable "db_subnet_cidr" {
  description = "CIDR range for the database subnet"
  type        = string
}
