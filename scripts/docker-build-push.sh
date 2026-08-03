#!/usr/bin/env bash
# CI helper: Build Docker image, tag with version, push to GitHub Container Registry.
# Usage: bash scripts/docker-build-push.sh v2.1.0

set -euo pipefail

VERSION="${1:-latest}"
IMAGE="ghcr.io/twomathematicians-code/demand-forecasting"

echo "Building Docker image: ${IMAGE}:${VERSION}"
docker build -t "${IMAGE}:${VERSION}" -t "${IMAGE}:latest" .

echo "Pushing ${IMAGE}:${VERSION}"
docker push "${IMAGE}:${VERSION}"

if [ "${VERSION}" != "latest" ]; then
    docker push "${IMAGE}:latest"
fi

echo "Done: ${IMAGE}:${VERSION}"
