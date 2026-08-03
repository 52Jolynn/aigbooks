#!/usr/bin/env bash
set -euo pipefail

IMAGE_NAME="${IMAGE_NAME:-aigbooks}"
NGINX_IMAGE_NAME="${NGINX_IMAGE_NAME:-aigbooks-nginx}"
IMAGE_TAG="${IMAGE_TAG:-latest}"
PLATFORM="${PLATFORM:-$(docker version --format '{{.Server.Arch}}')}"

case "$PLATFORM" in
  amd64|x86_64) PLATFORM="linux/amd64" ;;
  arm64|aarch64) PLATFORM="linux/arm64" ;;
  linux/amd64|linux/arm64) ;;
  *)
    printf '不支持的架构: %s，使用 PLATFORM=linux/amd64 或 PLATFORM=linux/arm64 覆盖\n' "$PLATFORM" >&2
    exit 1
    ;;
esac

printf '构建镜像 %s:%s (%s)\n' "$IMAGE_NAME" "$IMAGE_TAG" "$PLATFORM"
printf '构建应用镜像 %s:%s (%s)\n' "$IMAGE_NAME" "$IMAGE_TAG" "$PLATFORM"
docker build --platform "$PLATFORM" -t "$IMAGE_NAME:$IMAGE_TAG" -f Dockerfile .
printf '构建 Nginx 镜像 %s:%s (%s)\n' "$NGINX_IMAGE_NAME" "$IMAGE_TAG" "$PLATFORM"
docker build --platform "$PLATFORM" -t "$NGINX_IMAGE_NAME:$IMAGE_TAG" -f deploy/docker/Dockerfile.nginx .
