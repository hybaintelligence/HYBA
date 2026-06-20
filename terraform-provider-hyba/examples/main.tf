terraform {
  required_providers {
    hyba = {
      source  = "hyba-ai/hyba"
      version = "~> 1.0"
    }
  }
}

provider "hyba" {
  endpoint = var.hyba_endpoint
  api_key  = var.hyba_api_key
}

# Create a Computational Intelligence Service
resource "hyba_ciaas_service" "ml_inference" {
  name  = "ML Inference Service"
  tier  = "production"

  connector_type   = "tensorflow"
  connector_config = {
    model     = "resnet50"
    version   = "2.0"
    framework = "tensorflow"
  }

  output_type = "http"
  output_config = {
    format      = "json"
    compression = "gzip"
  }

  tags = {
    environment = "production"
    team        = "ml-ops"
    cost-center = "eng-001"
  }
}

# Data source to fetch a service
data "hyba_ciaas_service" "example" {
  id = hyba_ciaas_service.ml_inference.id
}

# Get available connectors
data "hyba_connectors" "available" {}

# Output the service details
output "service_id" {
  value = hyba_ciaas_service.ml_inference.id
}

output "service_state" {
  value = hyba_ciaas_service.ml_inference.state
}

output "available_connectors" {
  value = data.hyba_connectors.available.connectors
}
