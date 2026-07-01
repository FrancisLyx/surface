# Surface Deployment

This deployment runs:

- `api`: FastAPI on port `8000` inside Docker.
- PostgreSQL stays on your cloud database.
- Nginx is configured manually on the server.

## Server Requirements

- Docker
- Docker Compose v2
- Git

## First Deploy

Clone the repository on the server:

```bash
git clone <your-repo-url> surface
cd surface
```

Create the production env file:

```bash
cp .env.production.example .env.production
vim .env.production
```

Required values:

```bash
DATABASE_URL=postgresql+psycopg://surface_user:your_password@your-db-host:5432/surface
JWT_SECRET_KEY=replace-with-a-long-random-secret
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=1440
USER_REGISTRATION_ENABLED=true
SURFACE_API_BIND=127.0.0.1:8000
LLM_API_KEY=your-deepseek-api-key
LLM_BASE_URL=https://api.deepseek.com
LLM_MODEL=deepseek-chat
LLM_TIMEOUT_SECONDS=60
SURFACE_WEB_TARGET=/var/www/surface/current
```

Start deployment:

```bash
bash deploy/deploy.sh
```

Default branch is `master`. Deploy another branch:

```bash
bash deploy/deploy.sh dev
```

Or:

```bash
SURFACE_GIT_BRANCH=dev bash deploy/deploy.sh
```

This deploys the backend container and frontend static files together.
The frontend build output is synced into:

```bash
/var/www/surface/current
```

Set target directory in `.env.production`:

```bash
SURFACE_WEB_TARGET=/var/www/surface/current
```

Deploy frontend static files:

```bash
bash deploy/deploy-web.sh
```

The frontend-only script also defaults to `master`; pass a branch the same way:

```bash
bash deploy/deploy-web.sh dev
```

The frontend-only script builds `web/dist` and syncs the contents into:

```bash
/var/www/surface/current
```

Set target directory in `.env.production`:

```bash
SURFACE_WEB_TARGET=/var/www/surface/current
```

## Common Commands

View containers:

```bash
docker compose --env-file .env.production -f deploy/docker-compose.yml ps
```

View API logs:

```bash
docker compose --env-file .env.production -f deploy/docker-compose.yml logs -f api
```

Restart:

```bash
docker compose --env-file .env.production -f deploy/docker-compose.yml up -d
```

Stop:

```bash
docker compose --env-file .env.production -f deploy/docker-compose.yml down
```

## Nginx and HTTPS

This compose file exposes the API on `SURFACE_API_BIND`, default `127.0.0.1:8000`.
Keep it bound to `127.0.0.1` when Nginx is on the same server, so the API is not directly exposed to the internet.

Example host Nginx API proxy:

```nginx
location /api/ {
    proxy_pass http://127.0.0.1:8000/api/;
    proxy_http_version 1.1;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
}
```

Frontend build:

```bash
cd web
npm ci
npm run build
```

Upload or copy `web/dist` to your host Nginx static root.

For HTTPS, use either:

- Cloud provider certificate and load balancer.
- Host Nginx with Certbot, proxying API requests to `127.0.0.1:8000`.
