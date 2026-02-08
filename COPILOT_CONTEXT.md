# BlindStrader Project Context

## Tech Stack
- Framework: Laravel 12, Filamentphp 5, php8.3
- Architecture: Microservices (monorepo)
- Containerization: Docker Compose
- Reverse Proxy: Nginx
- Admin Panel: Filament
- API: RESTful with Laravel Sanctum/JWT
- Monitoring: Prometheus + Grafana
- Branching: Trunk-based (main, release/staging, release/production)
- Deployment: Debian Linux EC2
- the docker images need to be built natively using docker buildx with --platform linux/amd64,linux/arm64 to create multi-architecture images  

## Services
1. **user-management**: User, organization, authentication management
2. **catalog**: Product catalog management

## Key Constraints
- Use Docker containers for all services
- Expose services on ports 8001 (user) and 8002 (catalog)
- Route through Nginx reverse proxy
- Include both API endpoints and Filament admin panels
- Monitor with Prometheus/Grafana

## Directory Structure
```
/services/user-management/
/services/catalog/
/shared/
/monitoring/
docker-compose.yml
```

## Conventions
- API routes: /api/users, /api/products
- Admin routes: /admin paths
- Use environment variables from .env files
- Follow Laravel best practices