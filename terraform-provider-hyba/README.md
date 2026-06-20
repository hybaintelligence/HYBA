# Terraform Provider for HYBA

This is a Terraform provider for managing HYBA Computational Intelligence Services (CIaaS) infrastructure.

## Features

- Create, read, update, and delete computational intelligence services
- Manage connectors and output configurations
- Support for multiple service tiers (developer, production, sovereign)
- Complete state management and lifecycle control
- Evidence sealing and claim boundary documentation
- Full Terraform SDK integration

## Requirements

- Terraform >= 1.0
- Go >= 1.21 (for building from source)
- HYBA API credentials (endpoint and API key)

## Installation

### From Terraform Registry (Recommended)

Add the provider to your Terraform configuration:

```hcl
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
```

### Building from Source

1. Clone the repository:
```bash
git clone https://github.com/hyba-ai/terraform-provider-hyba.git
cd terraform-provider-hyba
```

2. Build the provider:
```bash
go build -o terraform-provider-hyba_v1.0.0
```

3. Install locally:
```bash
mkdir -p ~/.terraform.d/plugins/registry.terraform.io/hyba-ai/hyba/1.0.0/linux_amd64
mv terraform-provider-hyba_v1.0.0 ~/.terraform.d/plugins/registry.terraform.io/hyba-ai/hyba/1.0.0/linux_amd64/
chmod +x ~/.terraform.d/plugins/registry.terraform.io/hyba-ai/hyba/1.0.0/linux_amd64/terraform-provider-hyba_v1.0.0
```

## Configuration

### Provider Configuration

```hcl
provider "hyba" {
  endpoint = "https://api.hyba.ai"  # or set HYBA_ENDPOINT env var
  api_key  = "your-api-key"         # or set HYBA_API_KEY env var
}
```

### Environment Variables

- `HYBA_ENDPOINT`: The API endpoint URL
- `HYBA_API_KEY`: The API key for authentication

## Usage

### Create a Service

```hcl
resource "hyba_ciaas_service" "example" {
  name  = "My ML Service"
  tier  = "production"

  connector_type = "tensorflow"
  connector_config = {
    model   = "resnet50"
    version = "2.0"
  }

  output_type = "http"
  output_config = {
    format = "json"
  }

  tags = {
    environment = "production"
    team        = "ml-ops"
  }
}
```

### Read Service Data

```hcl
data "hyba_ciaas_service" "existing" {
  id = "service-id-123"
}
```

### List Available Connectors

```hcl
data "hyba_connectors" "available" {}

output "connectors" {
  value = data.hyba_connectors.available.connectors
}
```

### Update a Service

```hcl
resource "hyba_ciaas_service" "example" {
  name = "Updated Service Name"
  tier = "sovereign"

  # ... other configuration
}
```

### Delete a Service

Services are automatically deleted when destroyed:

```bash
terraform destroy
```

## Resource: hyba_ciaas_service

### Arguments

- `name` (Required) - Name of the service
- `tier` (Required) - Service tier: `developer`, `production`, or `sovereign`
- `connector_type` (Optional) - Type of connector
- `connector_config` (Optional) - Configuration map for the connector
- `output_type` (Optional) - Type of output
- `output_config` (Optional) - Configuration map for output
- `tags` (Optional) - Map of tags

### Attributes

- `id` - Service ID
- `state` - Current service state
- `tenancy` - Tenancy mode
- `created_at` - Creation timestamp
- `updated_at` - Last update timestamp

## Data Source: hyba_ciaas_service

Fetch details of a specific service.

### Arguments

- `id` (Required) - Service ID

### Attributes

- `name` - Service name
- `tier` - Service tier
- `state` - Current state
- `tenancy` - Tenancy mode
- `owner` - Service owner
- `created_at` - Creation timestamp
- `updated_at` - Last update timestamp
- `evidence_seal` - Cryptographic evidence seal
- `claim_boundary` - Claim boundary documentation

## Data Source: hyba_connectors

List all available connectors.

### Attributes

- `connectors` - Map of available connectors

## Supported Connectors

- **tensorflow** - TensorFlow ML framework
- **pytorch** - PyTorch ML framework
- **qiskit** - IBM Qiskit quantum computing
- **sql_snowflake** - Snowflake SQL connector
- **kafka** - Apache Kafka streaming
- **s3** - Amazon S3 storage

## Examples

### Complete Example

See `examples/main.tf` for a complete working example.

### Run Terraform

```bash
cd examples
cp terraform.tfvars.example terraform.tfvars
# Edit terraform.tfvars with your credentials
terraform init
terraform plan
terraform apply
```

## Development

### Testing

Run tests with:

```bash
go test -v ./...
```

### Building Documentation

Generate provider documentation:

```bash
go generate ./...
```

## Troubleshooting

### Authentication Errors

Ensure your API key is valid:
```bash
export HYBA_API_KEY="your-api-key"
export HYBA_ENDPOINT="https://api.hyba.ai"
```

### Service Not Found

Verify the service ID exists:
```bash
terraform state show hyba_ciaas_service.example
```

### Import Errors

Import an existing service:
```bash
terraform import hyba_ciaas_service.existing service-id-123
```

## Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## License

Copyright (c) 2026 HYBA Inc. All rights reserved.

## Support

- Documentation: https://docs.hyba.ai
- Issues: https://github.com/hyba-ai/terraform-provider-hyba/issues
- Email: support@hyba.ai
