#!/usr/bin/env bash
set -euo pipefail
ENVIRONMENT=${1:-}
CLOUD=${2:-}
if [[ ! "$ENVIRONMENT" =~ ^(staging|production)$ ]] || [[ ! "$CLOUD" =~ ^(aws|azure|gcp)$ ]]; then
  echo "Usage: ./scripts/deploy-multi-cloud.sh [staging|production] [aws|azure|gcp]" >&2
  exit 1
fi
ROOT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
echo "Deploying HYBA to ${CLOUD} (${ENVIRONMENT})..."
cd "${ROOT_DIR}/terraform/${CLOUD}"
terraform init
terraform apply -auto-approve -var="environment=${ENVIRONMENT}" -var="node_count=3"
ENDPOINT=$(terraform output -raw backend_endpoint)
echo "Backend deployed: ${ENDPOINT}"
cd "${ROOT_DIR}/helm"
IMAGE_TAG=$(git describe --tags --always)
helm upgrade --install hyba ./hyba-platform \
  --namespace "hyba-${ENVIRONMENT}" \
  --create-namespace \
  --values "values-${ENVIRONMENT}.yaml" \
  --set "image.tag=${IMAGE_TAG}"
echo "✅ Deployment complete on ${CLOUD}"
