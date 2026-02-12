provider "google" {
  project = var.project_id
  region  = var.region
}

provider "google-beta" {
  project = var.project_id
  region  = var.region
}

terraform {
  backend "gcs" {
    bucket = "koraflow-dev-tfstate" # Bucket must be created manually first
    prefix = "terraform/state"
  }
}
