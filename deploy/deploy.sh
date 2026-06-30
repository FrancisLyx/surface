#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ENV_FILE="${ROOT_DIR}/.env.production"
ENV_EXAMPLE="${ROOT_DIR}/.env.production.example"
COMPOSE_FILE="${ROOT_DIR}/deploy/docker-compose.yml"

cd "${ROOT_DIR}"

if ! command -v docker >/dev/null 2>&1; then
  echo "docker is required but was not found" >&2
  exit 1
fi

if ! docker compose version >/dev/null 2>&1; then
  echo "docker compose is required but was not found" >&2
  exit 1
fi

if [ ! -f "${ENV_FILE}" ]; then
  cp "${ENV_EXAMPLE}" "${ENV_FILE}"
  echo "Created ${ENV_FILE}. Edit it with the production database URL and JWT secret, then rerun this script." >&2
  exit 1
fi

if git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  git pull --ff-only
fi

docker compose --env-file "${ENV_FILE}" -f "${COMPOSE_FILE}" build
docker compose --env-file "${ENV_FILE}" -f "${COMPOSE_FILE}" up -d
docker compose --env-file "${ENV_FILE}" -f "${COMPOSE_FILE}" ps
