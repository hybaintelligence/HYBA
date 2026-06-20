# HYBA CLI - Command-Line Interface

Enterprise-grade CLI for provisioning, managing, and executing HYBA computational intelligence services.

## Installation

```bash
# From PyPI
pip install hyba-cli

# From source (development)
git clone https://github.com/hyba-ai/hyba-cli.git
cd hyba-cli
pip install -e .
```

## Quick Start

```bash
# Authenticate with your API key
hyba login

# Provision a service
hyba provision --name portfolio-optimizer --tier production

# Execute a workload
hyba execute portfolio-optimizer --workload explain --context "Portfolio optimization strategy"

# View service logs
hyba logs portfolio-optimizer --tail 50

# List all services
hyba services list

# Stop a service
hyba services stop portfolio-optimizer
```

## Commands

### Authentication

```bash
# Login with API key
hyba login --api-key hyba_live_...

# Login interactively
hyba login

# Logout
hyba logout

# Show current credentials
hyba auth status
```

### Service Management

```bash
# Provision a new service
hyba provision \
  --name portfolio-optimizer \
  --tier production \
  --connector sql_snowflake \
  --host acme.snowflakecomputing.com \
  --database finance_dw

# List all services
hyba services list

# Show service details
hyba services describe portfolio-optimizer

# Start a service
hyba services start portfolio-optimizer

# Stop a service
hyba services stop portfolio-optimizer

# Delete a service
hyba services delete portfolio-optimizer

# Get service health
hyba services health portfolio-optimizer
```

### Workload Execution

```bash
# Execute a workload
hyba execute portfolio-optimizer \
  --workload explain \
  --context "Portfolio optimization strategy"

# Stream results
hyba results portfolio-optimizer --stream

# Export results
hyba results portfolio-optimizer --output results.json

# Get execution history
hyba history portfolio-optimizer --limit 10
```

### Connector Management

```bash
# List available connectors
hyba connectors list

# Show connector details
hyba connectors describe sql_snowflake

# Test connector connectivity
hyba connectors test \
  --type sql_snowflake \
  --host acme.snowflakecomputing.com \
  --database finance_dw

# Create connector config
hyba connectors configure \
  --name my-snowflake \
  --type sql_snowflake \
  --host acme.snowflakecomputing.com

# List saved connector configs
hyba connectors saved
```

### Logs and Monitoring

```bash
# Stream service logs
hyba logs portfolio-optimizer --tail 100 --follow

# Export logs
hyba logs portfolio-optimizer --output logs.json

# Filter logs by level
hyba logs portfolio-optimizer --level ERROR

# Get service metrics
hyba metrics portfolio-optimizer

# Show usage statistics
hyba usage --format table
```

### Configuration

```bash
# Show current configuration
hyba config show

# Set configuration value
hyba config set api_url https://api.hyba.ai

# Edit configuration file
hyba config edit

# Reset to defaults
hyba config reset

# Show configuration file location
hyba config path
```

### Shell Completion

```bash
# Install bash completion
eval "$(hyba completion bash)"

# Install zsh completion
eval "$(hyba completion zsh)"

# Install fish completion
hyba completion fish | source
```

## Configuration File

Configuration is stored in `~/.hyba/config.yaml`:

```yaml
api_url: https://api.hyba.ai
api_key: hyba_live_...
output_format: table  # table, json, yaml
verbose: false
timeout: 30

# Saved connector configs
connectors:
  my-snowflake:
    type: sql_snowflake
    host: acme.snowflakecomputing.com
    database: finance_dw
  my-kafka:
    type: kafka
    broker: kafka.internal:9092
    topic: market_data
```

## Examples

### Provision and Execute

```bash
# Step 1: Provision service
$ hyba provision --name stock-analyzer --tier production
✓ Provisioned: hyba-ciaas-001 (2m 34s)

# Step 2: Start service
$ hyba services start hyba-ciaas-001
✓ Service started

# Step 3: Execute workload
$ hyba execute hyba-ciaas-001 \
  --workload explain \
  --context "Analyze stock market trends"
✓ Workload executed (12.3s)
Result: {...}

# Step 4: Export results
$ hyba results hyba-ciaas-001 --output analysis.json
✓ Results exported to analysis.json
```

### CI/CD Integration

```bash
# In your GitHub Actions workflow
- name: Run HYBA Analysis
  run: |
    hyba execute portfolio-optimizer \
      --workload explain \
      --context "CI/CD analysis" \
      --output results.json
    
- name: Upload Results
  uses: actions/upload-artifact@v3
  with:
    name: hyba-results
    path: results.json
```

### Scripting

```bash
#!/bin/bash
# Batch execute multiple workloads

SERVICE_ID=$1
CONTEXTS=$2

# Parse contexts (comma-separated)
IFS=',' read -ra CONTEXT_ARRAY <<< "$CONTEXTS"

for context in "${CONTEXT_ARRAY[@]}"; do
  echo "Executing: $context"
  hyba execute "$SERVICE_ID" \
    --workload explain \
    --context "$context" \
    --output "result-${context}.json"
done

echo "✓ All workloads completed"
```

## Error Handling

The CLI provides detailed error messages:

```bash
# Missing required argument
$ hyba execute
Error: Missing argument 'SERVICE_ID'
Usage: hyba execute SERVICE_ID [OPTIONS]

# Invalid service
$ hyba execute invalid-service
Error: Service not found: invalid-service
Tip: Use 'hyba services list' to see available services

# Quota exceeded
$ hyba execute portfolio-optimizer
Error: Quota exceeded (100/100 requests used)
Tip: Upgrade your plan or wait for quota reset

# Connection error
$ hyba services list
Error: Connection failed: Cannot reach api.hyba.ai
Tip: Check your network connection or verify API URL
```

## Troubleshooting

```bash
# Enable debug output
hyba --debug services list

# Verify authentication
hyba auth status

# Test API connectivity
hyba health

# Check configuration
hyba config show

# View logs
cat ~/.hyba/hyba.log
```

## Development

### Running Tests

```bash
cd hyba-cli
pip install -e ".[dev]"
pytest tests/
```

### Building Distribution

```bash
python setup.py sdist bdist_wheel
```

### Publishing to PyPI

```bash
twine upload dist/*
```

## License

Apache License 2.0

## Support

- Documentation: https://docs.hyba.ai/cli
- GitHub Issues: https://github.com/hyba-ai/hyba-cli/issues
- Email: support@hyba.ai
