# BlindStrader Project Plan

## Overview
Build a microservice-based software with Docker containers using trunk-based branching strategy. Initial deployment on Debian Linux server with Nginx reverse proxy, monitoring, and admin panels.

## Phase 1: Project Setup

### 1.1 Git Repository & Branching Strategy
- [ ] Initialize monorepo at `/opt/blindstrader`
- [ ] Set up main (trunk) branch
- [ ] Create release/staging and release/production branches
- [ ] Configure branch protection rules
- [ ] Document trunk-based workflow in README.md

### 1.2 Folder Structure
- [ ] Create `services/user-management/` directory
- [ ] Create `services/catalog/` directory
- [ ] Create `shared/` directory for common utilities
- [ ] Create `monitoring/` directory for Prometheus/Grafana configs
- [ ] Create `.github/workflows/` for CI/CD pipelines

### 1.3 Docker & Compose Setup
- [ ] Create root `docker-compose.yml` with both services
- [ ] Create `docker-compose.staging.yml` override
- [ ] Create `docker-compose.production.yml` override
- [ ] Create `.env.example`, `.env.staging`, `.env.production`
- [ ] Add Docker logging configuration

### 1.4 Nginx Configuration
- [ ] Configure Nginx reverse proxy for API routes
- [ ] Set up routing: `/api/users` → user-management service
- [ ] Set up routing: `/api/products` → catalog service
- [ ] Configure admin panel routing: `/admin` paths
- [ ] Add SSL/TLS with Certbot

## Phase 2: Service Development

### 2.1 User Management Service
- [ ] Initialize Laravel project in `services/user-management/`
- [ ] Create Dockerfile for user-management
- [ ] Set up Laravel API routes (users, organizations, authentication)
- [ ] Implement Filament admin panel for user/organization management
- [ ] Configure database migrations
- [ ] Add API authentication (JWT/Sanctum)

### 2.2 Product Catalog Service
- [ ] Initialize Laravel project in `services/catalog/`
- [ ] Create Dockerfile for catalog
- [ ] Set up Laravel API routes (products, categories)
- [ ] Implement Filament admin panel for catalog management
- [ ] Configure database migrations
- [ ] Add API endpoints for product listing/filtering

### 2.3 Shared Resources
- [ ] Create shared interfaces/contracts
- [ ] Set up shared constants and utilities
- [ ] Document service communication patterns

## Phase 3: Deployment & Monitoring

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
- [ ] Configure Docker JSON logging driver
- [ ] Set up log rotation
- [ ] Create shell script for service health checks
- [ ] Add monitoring to crontab
- [ ] Configure CloudWatch integration (optional)

## Phase 4: CI/CD & Testing

### 4.1 GitHub Actions
- [ ] Create workflow to test on PR to main
- [ ] Create workflow to deploy to staging on `release/staging` push
- [ ] Create workflow to deploy to production on `release/production` push
- [ ] Add security scanning

### 4.2 Testing
- [ ] Write unit tests for both services
- [ ] Set up integration tests
- [ ] Add API endpoint tests

## Phase 5: Domain & SSL

### 5.1 Domain Configuration
- [ ] Register/configure custom domain (api.blindstrader.com)
- [ ] Update DNS A records
- [ ] Configure Nginx virtual host

### 5.2 SSL Certificate
- [ ] Generate SSL certificate with Certbot
- [ ] Configure auto-renewal

## Timeline
| Phase | Duration | Status |
|-------|----------|--------|
| Setup | 2-3 days | Pending |
| Service Development | 2-3 weeks | Pending |
| Deployment & Monitoring | 1 week | Pending |
| CI/CD & Testing | 1-2 weeks | Pending |
| Domain & SSL | 2-3 days | Pending |

## Success Criteria
- ✅ Both services running in Docker containers
- ✅ API accessible via custom domain with SSL
- ✅ Filament admin panels functional
- ✅ Real-time monitoring active (Prometheus/Grafana)
- ✅ Logs aggregated and accessible
- ✅ Automated CI/CD pipeline working
- ✅ Trunk-based workflow operational
