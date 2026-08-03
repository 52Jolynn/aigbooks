#!/usr/bin/env bash
set -euo pipefail

IMAGE_NAME="${IMAGE_NAME:-aigbooks}"
IMAGE_TAG="${IMAGE_TAG:-latest}"
PLATFORM="${PLATFORM:-$(docker version --format '{{.Server.Arch}}')}"
FRONTEND_BUNDLE="${FRONTEND_BUNDLE:-frontend-dist.tar.gz}"
SKIP_FRONTEND_BUILD="${SKIP_FRONTEND_BUILD:-0}"
KEEP_FRONTEND_BUNDLE="${KEEP_FRONTEND_BUNDLE:-0}"

case "$PLATFORM" in
  amd64|x86_64) PLATFORM="linux/amd64" ;;
  arm64|aarch64) PLATFORM="linux/arm64" ;;
  linux/amd64|linux/arm64) ;;
  *)
    printf '不支持的架构: %s，使用 PLATFORM=linux/amd64 或 PLATFORM=linux/arm64 覆盖\n' "$PLATFORM" >&2
    exit 1
    ;;
esac

cleanup_frontend_bundle() {
  if [[ "${KEEP_FRONTEND_BUNDLE}" == "1" ]]; then
    printf '保留前端打包文件: %s\n' "$FRONTEND_BUNDLE"
    return
  fi
  if [[ -f "$FRONTEND_BUNDLE" ]]; then
    rm -f "$FRONTEND_BUNDLE"
    printf '已清理前端打包文件: %s\n' "$FRONTEND_BUNDLE"
  fi
}

build_frontend() {
  if [[ "${SKIP_FRONTEND_BUILD}" == "1" ]]; then
    if [[ ! -f "$FRONTEND_BUNDLE" ]]; then
      printf 'SKIP_FRONTEND_BUILD=1 但未找到 %s\n' "$FRONTEND_BUNDLE" >&2
      exit 1
    fi
    printf '跳过前端构建，复用已有 %s\n' "$FRONTEND_BUNDLE"
    return
  fi

  if [[ ! -d frontend ]]; then
    printf '未找到 frontend 目录，无法构建前端\n' >&2
    exit 1
  fi

  if ! command -v pnpm >/dev/null 2>&1; then
    printf '未检测到 pnpm，请安装 Node 22 与 pnpm 9 后重试\n' >&2
    exit 1
  fi

  printf '构建前端...\n'
  (
    cd frontend
    pnpm install --frozen-lockfile
    pnpm build
  )

  if [[ ! -f frontend/dist/index.html ]]; then
    printf '前端构建失败：缺少 frontend/dist/index.html\n' >&2
    exit 1
  fi

  printf '打包前端产物为 %s\n' "$FRONTEND_BUNDLE"
  tar -czf "$FRONTEND_BUNDLE" -C frontend dist

  local bundle_size
  bundle_size=$(du -h "$FRONTEND_BUNDLE" | awk '{print $1}')
  printf '前端打包完成: %s (%s)\n' "$FRONTEND_BUNDLE" "$bundle_size"
}

build_frontend

printf '构建镜像 %s:%s (%s)\n' "$IMAGE_NAME" "$IMAGE_TAG" "$PLATFORM"
trap 'cleanup_frontend_bundle' EXIT
docker build --platform "$PLATFORM" -t "$IMAGE_NAME:$IMAGE_TAG" -f Dockerfile .
