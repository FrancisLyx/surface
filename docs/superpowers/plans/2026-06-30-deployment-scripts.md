# Deployment Scripts Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add production deployment scripts for the Surface FastAPI API service.

**Architecture:** Build the FastAPI service into a Python container and use Docker Compose to run the API service. PostgreSQL remains an external cloud database configured through `.env.production`, and host Nginx is configured manually outside Compose.

**Tech Stack:** Docker, Docker Compose v2, Nginx, FastAPI, uv, React, Vite.

---

### Task 1: Backend Container

**Files:**
- Create: `Dockerfile`
- Create: `.dockerignore`

- [x] **Step 1: Create a uv-based Python Dockerfile**

Use `ghcr.io/astral-sh/uv:python3.12-bookworm-slim`, install dependencies from `pyproject.toml` and `uv.lock`, copy `app`, expose `8000`, and start `uvicorn app.main:app`.

- [x] **Step 2: Exclude local files from Docker build context**

Ignore `.env`, virtual environments, caches, frontend dependencies, build output, and editor files.

### Task 2: Nginx Reference

**Files:**
- Create: `deploy/Dockerfile.web`
- Create: `deploy/nginx.conf`

- [x] **Step 1: Build frontend with Node**

Run `npm ci` and `npm run build` from `web`.

- [x] **Step 2: Serve frontend with Nginx**

Copy `web/dist` to `/usr/share/nginx/html`, serve SPA fallback with `try_files`, and proxy `/api/` to `http://api:8000/api/`.

### Task 3: Compose and Deploy Script

**Files:**
- Create: `deploy/docker-compose.yml`
- Create: `deploy/deploy.sh`
- Create: `.env.production.example`
- Create: `deploy/README.md`

- [x] **Step 1: Add Docker Compose services**

Define the `api` service. The API reads `.env.production` and binds `${SURFACE_API_BIND:-127.0.0.1:8000}:8000` for host Nginx proxying.

- [x] **Step 2: Add deployment command**

Create `deploy/deploy.sh` to validate Docker availability, create `.env.production` from the example if missing, pull the latest git changes, build images, start services, and show container status.

- [x] **Step 3: Document server usage**

Document first deployment, common Docker Compose commands, and HTTPS options.
