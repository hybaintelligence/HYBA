variable "hyba_endpoint" {
  description = "The HYBA API endpoint URL"
  type        = string
  sensitive   = true
}

variable "hyba_api_key" {
  description = "The HYBA API key for authentication"
  type        = string
  sensitive   = true
}

variable "service_name" {
  description = "Name of the computational intelligence service"
  type        = string
  default     = "my-ml-service"
}

variable "service_tier" {
  description = "Service tier (developer, production, sovereign)"
  type        = string
  default     = "production"

  validation {
    condition     = contains(["developer", "production", "sovereign"], var.service_tier)
    error_message = "Service tier must be one of: developer, production, sovereign."
  }
}

variable "connector_type" {
  description = "Type of connector to use"
  type        = string
  default     = "tensorflow"

  validation {
    condition = contains([
      "tensorflow",
      "pytorch",
      "qiskit",
      "sql_snowflake",
      "kafka",
      "s3"
    ], var.connector_type)
    error_message = "Connector type not supported."
  }
}

variable "tags" {
  description = "Tags to apply to the service"
  type        = map(string)
  default = {
    managed-by = "terraform"
  }
}
