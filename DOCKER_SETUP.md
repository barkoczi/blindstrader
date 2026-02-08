# Docker Compose Setup for BlindStrader

## Overview
This setup provides a multi-container Docker environment for the BlindStrader project with:
- **MySQL 8** on port 3307 (custom port to avoid conflicts)
- **Two Laravel 12 services**: catalog and user-management
- **PHP 8.3 FPM** with Alpine Linux (multi-architecture support: linux/amd64, linux/arm64)
- **Nginx** reverse proxy for request routing
- **Valet** integration for local HTTPS access via `https://blindstrader.test/`

## Services

### Database (MySQL)
- **Host**: `db` (Docker network)
- **Port**: 3307 (mapped to 3306 internally)
- **Root Password**: `root`
- **Username**: `blindstrader`
- **Password**: `blindstrader`
- **Databases**: 
  - `blindstrader_catalog`
  - `blindstrader_user_management`

### Catalog Service
- **Image**: `ghcr.io/barkoczi/blindstrader-catalog:latest`
- **Port**: 8001 (PHP-FPM)
- **Route**: `/` → returns "Hello from catalog"
- **Database**: `blindstrader_catalog`

### User Management Service
- **Image**: `ghcr.io/barkoczi/blindstrader-user-management:latest`
- **Port**: 8002 (PHP-FPM)
- **Route**: `/` → returns "Hello from user management"
- **Database**: `blindstrader_user_management`

### Nginx Reverse Proxy
- **Port**: 80 (HTTP)
- **Routes**:
  - `/` and `/catalog/*` → routes to catalog service
  - `/user/*` → routes to user-management service

## Prerequisites

1. **Docker** with buildx support for multi-architecture builds
2. **Docker Compose** v3.8+
3. **Valet** installed locally for HTTPS routing
4. **GitHub Container Registry (GHCR)** credentials for pulling private images

## Local Setup

### 1. Add hosts entry
Add the following line to `/etc/hosts`:
```
127.0.0.1 blindstrader.test
```

To edit:
```bash
sudo nano /etc/hosts
```

### 2. Configure Valet to proxy Docker Nginx

Create a Valet proxy configuration:
```bash
# First, add blindstrader.test as a Valet site
valet link blindstrader

# Then configure it to proxy to Docker Nginx
valet proxy blindstrader http://127.0.0.1:80
```

Alternatively, if using Valet 4.x, you can directly proxy in your Valet config.

### 3. GitHub Container Registry Authentication (optional for pulling private images)

```bash
# Create a personal access token on GitHub with `read:packages` scope
# Then login to GHCR
echo $CR_PAT | docker login ghcr.io -u barkoczi --password-stdin
```

## Running the Stack

### Start all services:
```bash
cd /Users/barkocziroland/laravel/blindstrader
docker-compose up -d
```

### Verify services are running:
```bash
docker-compose ps
```

### View logs:
```bash
docker-compose logs -f

# Specific service
docker-compose logs -f catalog
docker-compose logs -f user-management
docker-compose logs -f nginx
```

### Stop all services:
```bash
docker-compose down
```

## Testing

### Test via HTTP (direct to Nginx):
```bash
curl http://localhost/
curl http://localhost/catalog/
curl http://localhost/user/
```

### Test via HTTPS (through Valet):
```bash
curl https://blindstrader.test/
curl https://blindstrader.test/catalog/
curl https://blindstrader.test/user/
```

### Open in browser:
```
https://blindstrader.test/
```

## Database Access

### From Docker container:
```bash
docker-compose exec db mysql -u blindstrader -p blindstrader_catalog
# Enter password: blindstrader
```

### From local machine (port 3307):
```bash
mysql -h 127.0.0.1 -P 3307 -u blindstrader -p blindstrader_catalog
# Enter password: blindstrader
```

## Rebuilding Images

### Rebuild locally (single platform):
```bash
docker build -t ghcr.io/barkoczi/blindstrader-catalog:latest ./services/catalog/
docker build -t ghcr.io/barkoczi/blindstrader-user-management:latest ./services/user-management/
```

### Rebuild multi-architecture and push to GHCR:
```bash
# Make sure buildx builder is active
docker buildx use blindstrader

# Catalog service
docker buildx build --platform linux/amd64,linux/arm64 -t ghcr.io/barkoczi/blindstrader-catalog:latest --push ./services/catalog/

# User management service
docker buildx build --platform linux/amd64,linux/arm64 -t ghcr.io/barkoczi/blindstrader-user-management:latest --push ./services/user-management/
```

## Environment Variables

Each service has a `.env` file in its directory:
- `services/catalog/.env`
- `services/user-management/.env`

Key variables:
- `DB_HOST`: Set to `db` (Docker network hostname)
- `DB_PORT`: Set to `3306` (internal Docker port, not 3307)
- `DB_DATABASE`: Service-specific database name
- `DB_USERNAME`: `blindstrader`
- `DB_PASSWORD`: `blindstrader`

## Volumes

- **Database**: `db_data` (persistent MySQL data)
- **Catalog service**: `./services/catalog/` (mounted for hot-reload during development)
- **User-management service**: `./services/user-management/` (mounted for hot-reload during development)
- **Nginx config**: `./nginx/nginx.conf` (read-only)

## Troubleshooting

### Services not starting:
```bash
docker-compose logs -f
```

### Rebuild fresh without cache:
```bash
docker-compose down -v  # Removes volumes too
docker buildx prune     # Clean build cache
docker-compose up --build
```

### MySQL connection errors:
- Wait 10-15 seconds after starting for MySQL to initialize
- Check MySQL logs: `docker-compose logs db`
- Verify `DB_HOST` is set to `db`, not `localhost`

### Valet/HTTPS not working:
- Ensure `blindstrader.test` is in `/etc/hosts` pointing to `127.0.0.1`
- Check Valet is running: `valet status`
- Regenerate Valet certificates: `valet secure blindstrader`
- Verify Nginx is running on port 80: `netstat -an | grep 80`

## Development Workflow

1. **Make code changes** in `services/catalog/` or `services/user-management/`
   - Changes auto-reflect thanks to volume mounts

2. **Install new dependencies**:
   ```bash
   docker-compose exec catalog composer require package/name
   docker-compose exec user-management composer require package/name
   ```

3. **Run migrations** (if needed):
   ```bash
   docker-compose exec catalog php artisan migrate
   docker-compose exec user-management php artisan migrate
   ```

4. **View real-time logs**:
   ```bash
   docker-compose logs -f catalog
   ```

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│ Client HTTPS                                                │
│    ↓                                                         │
│ Valet Proxy (Local macOS)                                   │
│    ↓                                                         │
│ Docker Network: blindstrader                                │
│                                                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────┐  │
│  │   Nginx      │  │  PHP-FPM     │  │   PHP-FPM        │  │
│  │  (Port 80)   │  │  Catalog     │  │ User-Management  │  │
│  │              │  │ (Port 8001)  │  │   (Port 8002)    │  │
│  │  Routes:     │→ │              │→ │                  │  │
│  │  / & /cat*   │  │Laravel 12    │  │ Laravel 12       │  │
│  │  /user/*  ───┼─→│              │  │                  │  │
│  └──────────────┘  └──────────────┘  └──────────────────┘  │
│         ↓                    │                 │             │
│         └────────────────────┴─────────────────┘             │
│                              ↓                              │
│                    ┌──────────────────┐                     │
│                    │    MySQL 8       │                     │
│                    │ (Port 3307 →3306)│                     │
│                    │                  │                     │
│                    │ Two Schemas:     │                     │
│                    │ • catalog        │                     │
│                    │ • user_mgmt      │                     │
│                    └──────────────────┘                     │
└─────────────────────────────────────────────────────────────┘
```

## Docker Image Details

### Multi-Architecture Support
Both service images are built for:
- `linux/amd64` (Intel/AMD 64-bit)
- `linux/arm64` (ARM 64-bit, Apple Silicon, etc.)

This allows seamless deployment across different architectures without requiring separate builds.

### Image Size Optimization
- Uses Alpine Linux base images (minimal footprint)
- Only essential PHP extensions installed (gd, mysqli, pdo_mysql)
- Production builds use `--no-dev --optimize-autoloader`

## Next Steps

1. Test the setup: `curl https://blindstrader.test/`
2. Add more routes to each service as needed
3. Create migrations and models for each microservice
4. Set up CI/CD to automatically rebuild and push images on code changes
