#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
WEB_DIR="${ROOT_DIR}/web"
DIST_DIR="${WEB_DIR}/dist"
TARGET_DIR="${SURFACE_WEB_TARGET:-/var/www/finance.liuyixuan.site/current}"
GIT_BRANCH="${1:-${SURFACE_GIT_BRANCH:-master}}"

cd "${ROOT_DIR}"

if ! command -v npm >/dev/null 2>&1; then
  echo "npm is required but was not found" >&2
  exit 1
fi

if ! command -v rsync >/dev/null 2>&1; then
  echo "rsync is required but was not found" >&2
  exit 1
fi

if git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  git fetch origin "${GIT_BRANCH}"
  git checkout "${GIT_BRANCH}"
  git pull --ff-only origin "${GIT_BRANCH}"
fi

cd "${WEB_DIR}"
npm ci
npm run build

if [ ! -d "${DIST_DIR}" ]; then
  echo "Build output not found: ${DIST_DIR}" >&2
  exit 1
fi

if [ ! -d "${TARGET_DIR}" ]; then
  sudo mkdir -p "${TARGET_DIR}"
fi

if [ -w "${TARGET_DIR}" ]; then
  rsync -av --delete "${DIST_DIR}/" "${TARGET_DIR}/"
else
  sudo rsync -av --delete "${DIST_DIR}/" "${TARGET_DIR}/"
fi

echo "Frontend deployed to ${TARGET_DIR}"
