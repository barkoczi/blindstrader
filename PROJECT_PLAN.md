# BlindStrader Project Plan

## Overview
Build a microservice-based software with Docker containers using trunk-based branching strategy. Initial development with local Docker environment, later deployment on server with Nginx reverse proxy, monitoring, and admin panels.

**Current Status:** Development Phase - Local Docker infrastructure complete with shared session authentication

## Phase 1: Project Setup ✅ COMPLETED

### 1.1 Git Repository & Branching Strategy ✅
- [x] Initialize repository on GitHub (https://github.com/barkoczi/blindstrader)
- [x] Set up main (trunk) branch
- [x] Initial commit with complete infrastructure
- [x] Comprehensive README documentation
- [ ] Create release/staging and release/production branches (Future)
- [ ] Configure branch protection rules (Future)

### 1.2 Folder Structure ✅
- [x] Create `services/user-management/` directory
- [x] Create `services/catalog/` directory
- [x] Create `nginx/` directory for reverse proxy configuration
- [x] Create `docker/mysql/` for database initialization
- [x] Create `logs/nginx/` for access and error logs
- [ ] Create `monitoring/` directory for Prometheus/Grafana configs (Future)

### 1.3 Docker & Compose Setup ✅
- [x] Create root `docker-compose.yml` with all services
- [x] MySQL 8.0 with separate schemas for each service
- [x] Redis 7-alpine for session sharing (port 6380 for development)
- [x] phpMyAdmin service for database management
- [x] Configure environment variables via `.env` files
- [x] Docker health checks for MySQL and Redis
- [x] Automatic migrations on container startup
- [ ] Create `docker-compose.staging.yml` override (Future)
- [ ] Create `docker-compose.production.yml` override (Future)

### 1.4 Nginx Configuration ✅
- [x] Configure Nginx reverse proxy with subdomain routing
- [x] Set up routing: `auth.blindstrader.test` → user-management service
- [x] Set up routing: `catalog.blindstrader.test` → catalog service
- [x] Set up routing: `pa.blindstrader.test` → phpMyAdmin
- [x] Configure Valet proxies for local HTTPS development
- [x] Laravel Valet SSL certificates for all subdomains
- [ ] Production SSL/TLS with Certbot (Future)

### 1.5 Docker Image Registry ✅
- [x] Multi-architecture Docker images (linux/amd64, linux/arm64)
- [x] GitHub Container Registry setup (ghcr.io/barkoczi/)
- [x] Published catalog service image
- [x] Published user-management service image
- [x] Docker buildx configuration for multi-platform builds

## Phase 2: Service Development 🚧 IN PROGRESS

### 2.1 User Management Service ✅ Infrastructure Complete
- [x] Initialize Laravel 12 project in `services/user-management/`
- [x] Create Dockerfile with PHP 8.3-fpm-alpine, Redis extension
- [x] Configure database connection (blindstrader_user_management schema)
- [x] Set up Redis session driver with shared authentication
- [x] Basic routes and health check endpoints
- [x] Database migrations (users, cache, jobs tables)
- [ ] Implement Filament admin panel for user/organization management
- [ ] Add API authentication (Sanctum/Passport)
- [ ] Implement user management features
- [ ] Add organization management

### 2.2 Product Catalog Service ✅ Infrastructure Complete
- [x] Initialize Laravel 12 project in `services/catalog/`
- [x] Create Dockerfile with PHP 8.3-fpm-alpine, Redis extension
- [x] Configure database connection (blindstrader_catalog schema)
- [x] Set up Redis session driver with shared authentication
- [x] Basic routes and health check endpoints
- [x] Database migrations (users, cache, jobs tables)
- [ ] Implement Filament admin panel for catalog management
- [ ] Add API endpoints for product listing/filtering
- [ ] Implement catalog features
- [ ] Add category management

### 2.3 Shared Session Authentication ✅
- [x] Redis-based session storage shared between services
- [x] Unified session cookie configuration (`blindstrader_session`)
- [x] Shared session domain (`.blindstrader.test`)
- [x] Identical APP_KEY for session encryption
- [x] Unified cache and Redis prefixes
- [x] Cross-service authentication working

### 2.4 Database Management ✅
- [x] phpMyAdmin accessible at pa.blindstrader.test
- [x] Single MySQL instance with separate schemas
- [x] Database initialization scripts
- [x] Automatic migrations on service startup

## Phase 3: Deployment & Monitoring 📋 PLANNED

### 3.1 EC2 Server Setup
- [ ] Install Docker Engine on Debian
- [ ] Install Docker Compose
- [ ] Install Nginx
- [ ] Configure firewall rules
- [ ] Set up SSH access and security

### 3.2 Monitoring Stack
- [ ] Deploy Prometheus for metrics collection
- [ ] Deploy Grafana for visualization
- [ ] Deploy Node Exporter for system metrics
- [ ] Deploy cAdvisor for container metrics
- [ ] Create monitoring dashboards

### 3.3 Logging & Alerts
- [x] Configure Docker JSON logging driver (development)
- [x] Nginx access and error logs mounted locally
- [ ] Set up log rotation
- [ ] Create shell script for service health checks
- [ ] Add monitoring to crontab
- [ ] Configure CloudWatch integration (optional)

## Phase 4: CI/CD & Testing 📋 PLANNED

### 4.1 GitHub Actions
- [ ] Create workflow to test on PR to main
- [ ] Create workflow to build and push Docker images
- [ ] Create workflow to deploy to staging on `release/staging` push
- [ ] Create workflow to deploy to production on `release/production` push
- [ ] Add security scanning

### 4.2 Testing
- [ ] Write unit tests for both services
- [ ] Set up integration tests
- [ ] Add API endpoint tests

## Phase 5: Domain & SSL 🚧 PARTIAL

### 5.1 Local Development Domain ✅
- [x] Configure local .test domains via dnsmasq/Valet
- [x] Set up subdomain routing
- [x] Valet proxy configuration
- [ ] Production domain setup (Future)

### 5.2 SSL Certificate ✅ (Development)
- [x] Laravel Valet SSL certificates for local development
- [x] HTTPS enabled for all subdomains
- [ ] Production SSL with Certbot (Future)
- [ ] Configure auto-renewal (Future)

## Current Architecture

### Services
```
blindstrader/
├── services/
│   ├── catalog/                    # Catalog microservice
│   │   ├── Dockerfile             # PHP 8.3-fpm-alpine + Redis
│   │   └── ...                    # Laravel 12 application
│   └── user-management/           # Auth microservice
│       ├── Dockerfile             # PHP 8.3-fpm-alpine + Redis
│       └── ...                    # Laravel 12 application
├── nginx/
│   └── nginx.conf                 # Subdomain routing config
├── docker/
│   └── mysql/
│       └── init.sql              # Database schemas
├── docker-compose.yml            # Service orchestration
└── README.md                     # Comprehensive documentation
```

### Infrastructure
- **MySQL 8.0**: Single instance, port 3307, separate schemas
- **Redis 7-alpine**: Session storage, port 6380 (dev), internal 6379
- **Nginx Alpine**: Reverse proxy, port 8080
- **phpMyAdmin**: Database admin, via pa.blindstrader.test
- **Laravel Services**: PHP 8.3-FPM on ports 8001, 8002

### Endpoints
- `https://auth.blindstrader.test` - User management & authentication
- `https://catalog.blindstrader.test` - Product catalog
- `https://pa.blindstrader.test` - phpMyAdmin
- `https://blindstrader.test` - Main site (redirects to auth)

## Timeline
| Phase | Duration | Status |
|-------|----------|--------|
| Setup | 2-3 days | ✅ Completed |
| Service Development | 2-3 weeks | 🚧 In Progress (Infrastructure Done) |
| Deployment & Monitoring | 1 week | 📋 Planned |
| CI/CD & Testing | 1-2 weeks | 📋 Planned |
| Domain & SSL | 2-3 days | 🚧 Partial (Dev Complete) |

## Success Criteria
- ✅ Both services running in Docker containers
- ✅ Services accessible via local HTTPS with Valet
- ✅ Shared authentication working between services
- ✅ phpMyAdmin accessible for database management
- ✅ Multi-architecture Docker images published to GHCR
- ✅ Automatic database migrations
- ✅ Comprehensive documentation
- [ ] Filament admin panels functional (In Progress)
- [ ] API endpoints implemented (In Progress)
- [ ] Real-time monitoring active (Planned)
- [ ] Automated CI/CD pipeline working (Planned)
- [ ] Production deployment (Planned)

## Next Steps

### Immediate (Current Sprint)
1. Install and configure Filament in both services
2. Create admin panels for user and catalog management
3. Implement authentication with Sanctum
4. Build API endpoints for catalog operations
5. Add API key management in auth service

### Short Term
1. Implement business logic for both services
2. Add comprehensive API documentation
3. Write unit and integration tests
4. Set up GitHub Actions for automated testing

### Long Term
1. Production server setup
2. Monitoring stack deployment
3. CI/CD pipeline configuration
4. Production domain and SSL setup
