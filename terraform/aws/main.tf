terraform {
  required_version = ">= 1.6.0"
  required_providers { aws = { source = "hashicorp/aws", version = ">= 5.0" } }
}
provider "aws" { region = var.aws_region }
variable "aws_region" { type = string default = "us-east-1" }
variable "environment" { type = string }
variable "node_count" { type = number default = 3 }
resource "aws_eks_cluster" "hyba" { name = "hyba-${var.environment}" role_arn = var.eks_role_arn vpc_config { subnet_ids = var.subnet_ids } }
variable "eks_role_arn" { type = string default = "arn:aws:iam::000000000000:role/hyba-eks-placeholder" }
variable "subnet_ids" { type = list(string) default = ["subnet-placeholder-a", "subnet-placeholder-b"] }
resource "aws_db_instance" "hyba" { allocated_storage = 100 engine = "postgres" engine_version = "16" instance_class = "db.t3.medium" username = "hyba" password = var.database_password skip_final_snapshot = true }
variable "database_password" { type = string sensitive = true default = "change-me-market-readiness" }
resource "aws_elasticache_cluster" "hyba" { cluster_id = "hyba-${var.environment}" engine = "redis" node_type = "cache.t3.medium" num_cache_nodes = 1 }
output "backend_endpoint" { value = aws_eks_cluster.hyba.endpoint }
