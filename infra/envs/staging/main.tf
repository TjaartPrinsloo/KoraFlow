module "vpc" {
  source              = "../../modules/vpc"
  project_id          = var.project_id
  region              = var.region
  environment         = var.environment
  app_subnet_cidr     = "10.1.1.0/24"
  backend_subnet_cidr = "10.1.2.0/24"
  db_subnet_cidr      = "10.1.3.0/24"
}

module "secrets" {
  source      = "../../modules/secrets"
  project_id  = var.project_id
  environment = var.environment
  secrets     = [
    "db-password",
    "frappe-admin-password",
    "encryption-key"
  ]
}

module "iam" {
  source      = "../../modules/iam"
  project_id  = var.project_id
  environment = var.environment
}

module "logging" {
  source      = "../../modules/logging"
  project_id  = var.project_id
  region      = var.region
  environment = var.environment
  log_retention_days = 180 # 6 months for staging
}

module "cloudsql" {
  source              = "../../modules/cloudsql"
  project_id          = var.project_id
  region              = var.region
  environment         = var.environment
  vpc_id              = module.vpc.vpc_id
  db_password         = var.db_password
  deletion_protection = true # Staging data matters
}

module "frappe_cloudrun" {
  source                = "../../modules/cloudrun"
  project_id            = var.project_id
  region                = var.region
  service_name          = "${var.environment}-frappe"
  image                 = "gcr.io/${var.project_id}/frappe:latest"
  service_account_email = module.iam.frappe_sa_email
  vpc_connector_id      = module.vpc.vpc_access_connector_id

  secret_env_vars = [
    {
      name      = "DB_PASSWORD"
      secret_id = "${var.environment}-db-password"
      version   = "latest"
    }
  ]

  env_vars = {
    DB_HOST = module.cloudsql.private_ip_address
    DB_PORT = "3306"
  }
}
