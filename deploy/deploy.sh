#!/usr/bin/env bash
# Runs on EC2 during each deployment. Called by the CI/CD pipeline via SSH.
# Usage: deploy.sh <ecr_registry> <ecr_repository> <image_tag> <aws_region>
set -euo pipefail

ECR_REGISTRY="$1"
ECR_REPOSITORY="$2"
IMAGE_TAG="$3"
AWS_REGION="$4"
APP_DIR="/home/ubuntu/app"

cd "$APP_DIR"

echo "==> Logging in to ECR"
aws ecr get-login-password --region "$AWS_REGION" \
  | docker login --username AWS --password-stdin "$ECR_REGISTRY"

echo "==> Pulling image ${ECR_REGISTRY}/${ECR_REPOSITORY}:${IMAGE_TAG}"
docker pull "${ECR_REGISTRY}/${ECR_REPOSITORY}:${IMAGE_TAG}"

echo "==> Setting image tag"
export ECR_REGISTRY ECR_REPOSITORY IMAGE_TAG

echo "==> Running migrations"
docker compose -f docker-compose.prod.yml --profile migrate run --rm migration

echo "==> Deploying application"
docker compose -f docker-compose.prod.yml up -d --remove-orphans api

echo "==> Cleaning up old images"
docker image prune -f

echo "==> Deployment complete"
