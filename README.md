# BlindStrader

A multi-service Laravel 12 application built with Docker, featuring microservices architecture with shared authentication.

## Architecture

- **Auth Service** (`auth.blindstrader.test`): User management and authentication with Filament admin panel
- **Catalog Service** (`catalog.blindstrader.test`): Catalog management with Filament admin panel and API
- **Shared Redis Sessions**: Cross-service authentication
- **MySQL 8**: Single database instance with separate schemas
- **Nginx**: Reverse proxy with subdomain routing

## Features

- ✅ Docker Compose orchestration
- ✅ Multi-architecture Docker images (linux/amd64, linux/arm64)
- ✅ Subdomain-based routing
- ✅ Shared session management via Redis
- ✅ Automatic database migrations on startup
- ✅ Laravel 12 with PHP 8.3
- ✅ Local development with Valet integration

## Quick Start

### Prerequisites

- Docker & Docker Compose
- dnsmasq or Laravel Valet (for local development)
- GitHub Container Registry access (for pulling images)

### Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/barkoczi/blindstrader.git
   cd blindstrader
   ```

2. **Configure environment**
   ```bash
   # Copy example env files
   cp services/catalog/.env.example services/catalog/.env
   cp services/user-management/.env.example services/user-management/.env
   
   # Generate application keys
   docker-compose run --rm catalog php artisan key:generate
   docker-compose run --rm user-management php artisan key:generate
   ```

3. **Start services**
   ```bash
   docker-compose up -d
   ```

4. **Configure local DNS** (macOS with Valet)
   ```bash
   # If using Valet, proxy to nginx
   valet proxy blindstrader http://127.0.0.1:8080
   valet proxy auth.blindstrader http://127.0.0.1:8080
   valet proxy catalog.blindstrader http://127.0.0.1:8080
   ```

5. **Access the application**
   - Auth service: https://auth.blindstrader.test
   - Catalog service: https://catalog.blindstrader.test
   - Root redirect: https://blindstrader.test

## Services

### MySQL
- **Port**: 3307 (host) → 3306 (container)
- **Root Password**: root
- **User**: blindstrader
- **Databases**: 
  - `blindstrader_catalog`
  - `blindstrader_user_management`

### Redis
- **Port**: 6379
- **Purpose**: Session storage, caching

### Nginx
- **Port**: 8080 (HTTP), 8443 (HTTPS)
- **Config**: `nginx/nginx.conf`

### Laravel Services
- **Catalog**: Port 8001 (PHP-FPM)
- **User Management**: Port 8002 (PHP-FPM)

## Development

### Building Images

Images are automatically built for multi-architecture:

```bash
# Build and push catalog service
cd services/catalog
docker buildx build --platform linux/amd64,linux/arm64 \
  -t ghcr.io/barkoczi/blindstrader-catalog:latest --push .

# Build and push user-management service
cd services/user-management
docker buildx build --platform linux/amd64,linux/arm64 \
  -t ghcr.io/barkoczi/blindstrader-user-management:latest --push .
```

### Running Migrations

Migrations run automatically on container startup. To run manually:

```bash
docker-compose exec catalog php artisan migrate
docker-compose exec user-management php artisan migrate
```

### Viewing Logs

```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f catalog
docker-compose logs -f user-management

# Nginx logs
tail -f logs/nginx/access.log
tail -f logs/nginx/error.log
```

## Session Sharing

Both services share sessions via Redis with the following configuration:

- **Session Driver**: redis
- **Session Cookie**: `blindstrader_session`
- **Session Domain**: `.blindstrader.test`
- **Shared APP_KEY**: Both services use the same encryption key

This allows users to authenticate on the auth service and remain authenticated when accessing the catalog service.

## Configuration

### Environment Variables

Key environment variables in `.env` files:

```env
# Application
APP_NAME="BlindStrader"
APP_KEY=base64:...  # MUST be the same for both services
APP_ENV=local

# Database
DB_HOST=db
DB_PORT=3306
DB_DATABASE=blindstrader_catalog  # or blindstrader_user_management
DB_USERNAME=blindstrader
DB_PASSWORD=blindstrader

# Redis
REDIS_HOST=redis
REDIS_PORT=6379

# Session
SESSION_DRIVER=redis
SESSION_COOKIE=blindstrader_session
SESSION_DOMAIN=.blindstrader.test
CACHE_PREFIX=blindstrader_
REDIS_PREFIX=
```

## Troubleshooting

### Services not accessible
```bash
# Check if all containers are running
docker-compose ps

# Check logs
docker-compose logs
```

### Session not sharing between services
- Verify both services have the same `APP_KEY`
- Check `SESSION_COOKIE` and `SESSION_DOMAIN` are identical
- Ensure Redis is running: `docker-compose ps redis`

### Database connection issues
- Ensure MySQL is healthy: `docker-compose ps db`
- Check credentials in `.env` files
- Verify schemas exist: `docker-compose exec db mysql -u root -proot -e "SHOW DATABASES;"`

## Project Structure

```
blindstrader/
├── docker-compose.yml          # Service orchestration
├── nginx/
│   └── nginx.conf             # Nginx configuration
├── docker/
│   └── mysql/
│       └── init.sql           # Database initialization
├── services/
│   ├── catalog/               # Catalog Laravel application
│   │   ├── Dockerfile
│   │   ├── app/
│   │   ├── routes/
│   │   └── ...
│   └── user-management/       # Auth Laravel application
│       ├── Dockerfile
│       ├── app/
│       ├── routes/
│       └── ...
└── logs/
    └── nginx/                 # Nginx logs
```

## License

MIT

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request
