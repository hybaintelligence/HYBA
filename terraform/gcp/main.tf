terraform { required_version = ">= 1.6.0" required_providers { google = { source = "hashicorp/google", version = ">= 5.0" } } }
provider "google" { project = var.gcp_project region = var.gcp_region }
variable "gcp_project" { type = string default = "hyba-market-readiness" }
variable "gcp_region" { type = string default = "us-central1" }
variable "environment" { type = string }
variable "node_count" { type = number default = 3 }
resource "google_container_cluster" "hyba" { name = "hyba-${var.environment}" location = var.gcp_region initial_node_count = var.node_count node_config { machine_type = "n2-standard-4" oauth_scopes = ["https://www.googleapis.com/auth/cloud-platform"] } }
resource "google_sql_database_instance" "hyba" { name = "hyba-postgres-${var.environment}" database_version = "POSTGRES_16" region = var.gcp_region settings { tier = "db-custom-4-16384" } deletion_protection = true }
output "backend_endpoint" { value = google_container_cluster.hyba.endpoint }
