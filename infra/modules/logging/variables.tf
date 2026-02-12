variable "project_id" {}
variable "environment" {}

variable "region" {
  default = "us-central1"
}

variable "log_retention_days" {
  description = "Number of days to retain audit logs"
  type        = number
  default     = 365 # 1 year minimum for prod (SAHPRA)
}
