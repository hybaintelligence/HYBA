terraform { required_version = ">= 1.6.0" required_providers { azurerm = { source = "hashicorp/azurerm", version = ">= 3.100" } } }
provider "azurerm" { features {} }
variable "environment" { type = string }
variable "node_count" { type = number default = 3 }
variable "location" { type = string default = "eastus" }
resource "azurerm_resource_group" "hyba" { name = "hyba-${var.environment}" location = var.location }
resource "azurerm_kubernetes_cluster" "hyba" { name = "hyba-${var.environment}" resource_group_name = azurerm_resource_group.hyba.name location = azurerm_resource_group.hyba.location dns_prefix = "hyba-${var.environment}" default_node_pool { name = "default" node_count = var.node_count vm_size = "Standard_D4s_v3" } identity { type = "SystemAssigned" } }
resource "azurerm_postgresql_flexible_server" "hyba" { name = "hyba-postgres-${var.environment}" resource_group_name = azurerm_resource_group.hyba.name location = azurerm_resource_group.hyba.location version = "16" administrator_login = "hyba" administrator_password = var.database_password storage_mb = 131072 sku_name = "B_Standard_B2ms" }
variable "database_password" { type = string sensitive = true default = "change-me-market-readiness" }
output "backend_endpoint" { value = azurerm_kubernetes_cluster.hyba.fqdn }
