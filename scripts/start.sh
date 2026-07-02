#!/usr/bin/env bash
set -euo pipefail

uv run uvicorn app.main:app --host "${HOST:-0.0.0.0}" --port "${PORT:-8000}"
