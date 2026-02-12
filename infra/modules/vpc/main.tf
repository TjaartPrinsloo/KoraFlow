resource "google_compute_network" "vpc_network" {
  name                    = "${var.environment}-vpc"
  auto_create_subnetworks = false
  project                 = var.project_id
}

# Subnets
resource "google_compute_subnetwork" "app_subnet" {
  name          = "${var.environment}-app-subnet"
  ip_cidr_range = var.app_subnet_cidr
  region        = var.region
  network       = google_compute_network.vpc_network.id
  project       = var.project_id

  private_ip_google_access = true
  
  log_config {
    aggregation_interval = "INTERVAL_10_MIN"
    flow_sampling        = 0.5
    metadata             = "INCLUDE_ALL_METADATA"
  }
}

resource "google_compute_subnetwork" "backend_subnet" {
  name          = "${var.environment}-backend-subnet"
  ip_cidr_range = var.backend_subnet_cidr
  region        = var.region
  network       = google_compute_network.vpc_network.id
  project       = var.project_id

  private_ip_google_access = true
}

resource "google_compute_subnetwork" "db_subnet" {
  name          = "${var.environment}-db-subnet"
  ip_cidr_range = var.db_subnet_cidr
  region        = var.region
  network       = google_compute_network.vpc_network.id
  project       = var.project_id

  private_ip_google_access = true
}

# Firewall - Deny All Ingress by Default (Implicit but good to be explicit for auditing)
resource "google_compute_firewall" "deny_all_ingress" {
  name    = "${var.environment}-deny-all-ingress"
  network = google_compute_network.vpc_network.name
  project = var.project_id

  deny {
    protocol = "all"
  }

  source_ranges = ["0.0.0.0/0"]
  priority      = 65534 
}

# Allow Internal Communication
resource "google_compute_firewall" "allow_internal" {
  name    = "${var.environment}-allow-internal"
  network = google_compute_network.vpc_network.name
  project = var.project_id

  allow {
    protocol = "tcp"
  }
  allow {
    protocol = "udp"
  }
  allow {
    protocol = "icmp"
  }

  source_ranges = [
    var.app_subnet_cidr,
    var.backend_subnet_cidr,
    var.db_subnet_cidr
  ]
}

# Cloud Router & NAT for Outbound Internet Access (Required for updates/packages)
resource "google_compute_router" "router" {
  name    = "${var.environment}-router"
  network = google_compute_network.vpc_network.name
  region  = var.region
  project = var.project_id
}

resource "google_compute_router_nat" "nat" {
  name                               = "${var.environment}-nat"
  router                             = google_compute_router.router.name
  region                             = var.region
  project                            = var.project_id
  nat_ip_allocate_option             = "AUTO_ONLY"
  source_subnetwork_ip_ranges_to_nat = "ALL_SUBNETWORKS_ALL_IP_RANGES"

  log_config {
    enable = true
    filter = "ERRORS_ONLY"
  }
}

# Serverless VPC Access Connector
resource "google_vpc_access_connector" "connector" {
  name          = "${var.environment}-vpc-conn"
  region        = var.region
  project       = var.project_id
  subnet {
    name = google_compute_subnetwork.app_subnet.name
  }
  machine_type  = "e2-micro"
  min_instances = 2
  max_instances = 3
}
