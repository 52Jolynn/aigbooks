#!/usr/bin/env bash
set -euo pipefail

IMAGE_NAME="${IMAGE_NAME:-aigbooks}"
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
docker build --platform "$PLATFORM" -t "$IMAGE_NAME:$IMAGE_TAG" -f Dockerfile .
