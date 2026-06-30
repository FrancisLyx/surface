#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ENV_FILE="${ROOT_DIR}/.env.production"
ENV_EXAMPLE="${ROOT_DIR}/.env.production.example"
COMPOSE_FILE="${ROOT_DIR}/deploy/docker-compose.yml"
WEB_DIR="${ROOT_DIR}/web"
DIST_DIR="${WEB_DIR}/dist"
WEB_TARGET_DIR="${SURFACE_WEB_TARGET:-/var/www/finance.liuyixuan.site/current}"
GIT_BRANCH="${1:-${SURFACE_GIT_BRANCH:-master}}"

cd "${ROOT_DIR}"

if ! command -v docker >/dev/null 2>&1; then
  echo "docker is required but was not found" >&2
  exit 1
fi

if ! docker compose version >/dev/null 2>&1; then
  echo "docker compose is required but was not found" >&2
  exit 1
fi

if ! command -v npm >/dev/null 2>&1; then
  echo "npm is required but was not found" >&2
  exit 1
fi

if ! command -v rsync >/dev/null 2>&1; then
  echo "rsync is required but was not found" >&2
  exit 1
fi

if [ ! -f "${ENV_FILE}" ]; then
  cp "${ENV_EXAMPLE}" "${ENV_FILE}"
  echo "Created ${ENV_FILE}. Edit it with the production database URL and JWT secret, then rerun this script." >&2
  exit 1
fi

if git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  git fetch origin "${GIT_BRANCH}"
  git checkout "${GIT_BRANCH}"
  git pull --ff-only origin "${GIT_BRANCH}"
fi

docker compose --env-file "${ENV_FILE}" -f "${COMPOSE_FILE}" build
docker compose --env-file "${ENV_FILE}" -f "${COMPOSE_FILE}" up -d
docker compose --env-file "${ENV_FILE}" -f "${COMPOSE_FILE}" ps

cd "${WEB_DIR}"
npm ci
npm run build

if [ ! -d "${DIST_DIR}" ]; then
  echo "Build output not found: ${DIST_DIR}" >&2
  exit 1
fi

if [ ! -d "${WEB_TARGET_DIR}" ]; then
  sudo mkdir -p "${WEB_TARGET_DIR}"
fi

if [ -w "${WEB_TARGET_DIR}" ]; then
  rsync -av --delete "${DIST_DIR}/" "${WEB_TARGET_DIR}/"
else
  sudo rsync -av --delete "${DIST_DIR}/" "${WEB_TARGET_DIR}/"
fi

echo "Frontend deployed to ${WEB_TARGET_DIR}"
