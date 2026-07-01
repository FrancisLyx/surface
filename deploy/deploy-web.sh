#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PRODUCTION_ENV_FILE="${ROOT_DIR}/.env.production"
WEB_DIR="${ROOT_DIR}/web"
DIST_DIR="${WEB_DIR}/dist"
DEFAULT_TARGET_DIR="/var/www/surface/current"
GIT_BRANCH="${1:-${SURFACE_GIT_BRANCH:-master}}"

cd "${ROOT_DIR}"

read_env_value() {
  local file="$1"
  local key="$2"
  local line

  if [ ! -f "${file}" ]; then
    return 1
  fi

  line="$(grep -E "^${key}=" "${file}" | tail -n 1 || true)"
  if [ -z "${line}" ]; then
    return 1
  fi

  local value="${line#*=}"
  value="${value%\"}"
  value="${value#\"}"
  value="${value%\'}"
  value="${value#\'}"
  printf '%s' "${value}"
}

CONFIG_TARGET_DIR="$(read_env_value "${PRODUCTION_ENV_FILE}" "SURFACE_WEB_TARGET" || true)"
TARGET_DIR="${CONFIG_TARGET_DIR:-${DEFAULT_TARGET_DIR}}"

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
