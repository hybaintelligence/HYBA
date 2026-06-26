#!/bin/bash
# HYBA Local Deployment Script
# Based on Gordon's Tier 1 Deployment Strategy
# This script deploys HYBA locally using Docker Compose

set -e

echo "=========================================="
echo "HYBA Local Deployment (Gordon's Tier 1)"
echo "=========================================="
echo ""

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "Error: Docker is not running. Please start Docker and try again."
    exit 1
fi

# Check if docker-compose is available
if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
    echo "Error: docker-compose is not installed. Please install it and try again."
    exit 1
fi

# Create necessary directories
echo "Creating runtime directories..."
mkdir -p runtime/evidence
mkdir -p runtime/memos
mkdir -p config

# Check if .env.local exists
if [ ! -f .env.local ]; then
    echo "Warning: .env.local not found. Creating from template..."
    cp .env.example .env.local
    echo "Please edit .env.local with your local configuration before running this script again."
    exit 1
fi

# Check if prometheus config exists
if [ ! -f config/prometheus.yml ]; then
    echo "Creating default prometheus configuration..."
    cat > config/prometheus.yml << 'EOF'
global:
  scrape_interval: 15s
  evaluation_interval: 15s

scrape_configs:
  - job_name: 'hyba-backend'
    static_configs:
      - targets: ['backend:3000']
  - job_name: 'prometheus'
    static_configs:
      - targets: ['localhost:9090']
EOF
fi

# Check if grafana datasource config exists
if [ ! -f config/grafana-datasources.yml ]; then
    echo "Creating default grafana datasource configuration..."
    cat > config/grafana-datasources.yml << 'EOF'
apiVersion: 1

datasources:
  - name: Prometheus
    type: prometheus
    access: proxy
    url: http://prometheus:9090
    isDefault: true
    editable: true
EOF
fi

echo "Pulling Docker image from Docker Cloud..."
docker-compose -f docker-compose.local.yml pull

echo "Starting services..."
docker-compose -f docker-compose.local.yml up -d

echo ""
echo "=========================================="
echo "Deployment Complete!"
echo "=========================================="
echo ""
echo "Services:"
echo "  Frontend (Bridge):  http://localhost:3000"
echo "  Backend API:       http://localhost:3001"
echo "  PostgreSQL:        localhost:5432"
echo "  Redis:             localhost:6379"
echo "  Prometheus:        http://localhost:9090"
echo "  Grafana:           http://localhost:3002 (admin/admin)"
echo ""
echo "Governance Rail: treasury"
echo "Evidence Storage: ./runtime/evidence (local filesystem)"
echo ""
echo "Useful Commands:"
echo "  View logs:        docker-compose -f docker-compose.local.yml logs -f"
echo "  Stop services:    docker-compose -f docker-compose.local.yml down"
echo "  Restart services:  docker-compose -f docker-compose.local.yml restart"
echo "  Check status:      docker-compose -f docker-compose.local.yml ps"
echo ""
echo "To enable mining, edit .env.local and set:"
echo "  HYBA_ENABLE_MINING_AUTOCONNECT=true"
echo "  HYBA_ENABLE_LIVE_STRATUM=true"
echo ""
