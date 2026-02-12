variable "project_id" {}
variable "region" {
  default = "us-central1"
}
variable "service_name" {}
variable "image" {}
variable "service_account_email" {}
variable "vpc_connector_id" {}

variable "max_instances" {
  default = 10
}

variable "env_vars" {
  type    = map(string)
  default = {}
}

variable "secret_env_vars" {
  type = list(object({
    name      = string
    secret_id = string
    version   = string
  }))
  default = []
}
