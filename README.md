# BlindStrader

A multi-service Laravel application with microservices architecture, Docker containerization, and automated CI/CD pipeline.

## 🏗️ Architecture

### Services
-   **Auth Service** (`auth.blindstrader.com`): User management and authentication
-   **Catalog Service** (`catalog.blindstrader.com`): Catalog management and API
-   **Monitoring** (`insights.blindstrader.com`): Grafana dashboards
-   **Metrics** (`prometheus.blindstrader.com`): Prometheus metrics

### Infrastructure
-   **Cloud**: AWS (EC2, S3, Route53, Secrets Manager)
-   **Infrastructure as Code**: Terraform
-   **Configuration Management**: Ansible
-   **CI/CD**: GitHub Actions
-   **Containerization**: Docker, Docker Compose
-   **Web Server**: Nginx with Let's Encrypt SSL
-   **Databases**: MySQL 8, Redis 7
-   **Monitoring**: Prometheus, Grafana, Loki, Promtail

## ✨ Features

### Development
-   ✅ Docker Compose orchestration
-   ✅ Hot-reload for local development
-   ✅ Shared Redis sessions across services
-   ✅ Automatic database migrations
-   ✅ Laravel 12 with PHP 8.2

### Infrastructure
-   ✅ Automated AWS provisioning via Terraform
-   ✅ Configuration management with Ansible
-   ✅ Separate production and staging environments
-   ✅ Auto-shutdown scheduling for staging (50-70% cost savings)
-   ✅ Automated backups with GPG encryption to S3

### CI/CD Pipeline
-   ✅ Automated testing on every push/PR
-   ✅ Docker image building and pushing to ghcr.io
-   ✅ Automated deployments to staging (on develop push)
-   ✅ Tagged deployments to production (with approval)
-   ✅ Automatic rollback on deployment failures
-   ✅ Health checks and verification

### Monitoring & Observability
-   ✅ Prometheus metrics collection
-   ✅ Grafana dashboards
-   ✅ Loki log aggregation
-   ✅ Application performance monitoring
-   ✅ Alert rules and notifications

## 🚀 Quick Start

### Local Development

### Prerequisites

-   Docker & Docker Compose
-   For production deployment: AWS account, Terraform, Ansible

### Local Development Setup

1.  **Clone the repository**
    
    ```bash
    git clone https://github.com/barkoczi/blindstrader.gitcd blindstrader
    ```
    
2.  **Configure environment**
    
    ```bash
    # Copy example env filescp services/catalog/.env.example services/catalog/.envcp services/user-management/.env.example services/user-management/.env# Generate application keysdocker-compose run --rm catalog php artisan key:generatedocker-compose run --rm user-management php artisan key:generate
    ```
    
3.  **Start services**
    
    ```bash
    docker-compose up -d
    ```
    
4.  **Configure local DNS** (macOS with Valet)
    
    ```bash
    # If using Valet, proxy to nginxvalet proxy blindstrader http://127.0.0.1:8080valet proxy auth.blindstrader http://127.0.0.1:8080valet proxy catalog.blindstrader http://127.0.0.1:8080# Proxy monitoring servicesvalet proxy insights.blindstrader http://127.0.0.1:8000valet proxy prometheus.blindstrader http://127.0.0.1:9090
    ```
    
5.  **Access the application**
    
    -   Auth service: http://localhost:8080 (or via Valet)
    -   Catalog service: http://localhost:8080 (or via Valet)
    -   Grafana: http://localhost:3000 (admin/admin)
    -   Prometheus: http://localhost:9090

### Production Deployment

See comprehensive guides in the `docs/` directory:

1. **[PRE_DEPLOYMENT.md](docs/PRE_DEPLOYMENT.md)** - Prerequisites and preparation
2. **[DEPLOYMENT.md](docs/DEPLOYMENT.md)** - Infrastructure deployment with Terraform
3. **[ANSIBLE_DEPLOYMENT.md](docs/ANSIBLE_DEPLOYMENT.md)** - Configuration with Ansible
4. **[GITHUB_ACTIONS.md](docs/GITHUB_ACTIONS.md)** - CI/CD pipeline setup
5. **[COMPLETE_WORKFLOW.md](docs/COMPLETE_WORKFLOW.md)** - End-to-end workflow

**Quick overview**:
```bash
# 1. Provision infrastructure
cd terraform/environments/prod
terraform init && terraform apply

# 2. Configure server
cd ../../ansible
ansible-playbook -i inventory/prod.yml playbooks/site.yml

# 3. Obtain SSL certificates
ansible-playbook -i inventory/prod.yml playbooks/ssl.yml

# 4. Deploy application (via GitHub Actions or manually)
ansible-playbook -i inventory/prod.yml playbooks/deploy-app.yml
```

## 📚 Documentation

### Infrastructure & Deployment
- [PRE_DEPLOYMENT.md](docs/PRE_DEPLOYMENT.md) - Prerequisites, AWS setup, secrets configuration
- [DEPLOYMENT.md](docs/DEPLOYMENT.md) - Terraform infrastructure deployment
- [ANSIBLE_DEPLOYMENT.md](docs/ANSIBLE_DEPLOYMENT.md) - Ansible configuration management
- [GITHUB_ACTIONS.md](docs/GITHUB_ACTIONS.md) - CI/CD pipeline with GitHub Actions
- [COMPLETE_WORKFLOW.md](docs/COMPLETE_WORKFLOW.md) - Complete development to production workflow
- [DISASTER_RECOVERY.md](docs/DISASTER_RECOVERY.md) - Backup restoration procedures
- [GIT_WORKFLOW.md](docs/GIT_WORKFLOW.md) - Git branching and versioning strategy

### Quick References
- [ansible/README.md](ansible/README.md) - Ansible quick start
- [ANSIBLE_IMPLEMENTATION_SUMMARY.md](ANSIBLE_IMPLEMENTATION_SUMMARY.md) - Implementation overview

### Infrastructure Specs
- **Environments**: Production and Staging on AWS
- **Instance Types**: t3a.medium (prod), t3a.small (stage)
- **Regions**: eu-west-2 (London)
- **Estimated Cost**: $50-66/month for both environments
- **Backup**: Nightly encrypted backups to S3 (production only)

## Services

### MySQL

-   **Port**: 3307 (host) → 3306 (container)
-   **Root Password**: root
-   **User**: blindstrader
-   **Databases**:
    -   `blindstrader_catalog`
    -   `blindstrader_user_management`

### Redis

-   **Port**: 6379
-   **Purpose**: Session storage, caching

### Nginx

-   **Port**: 8080 (HTTP), 8443 (HTTPS)
-   **Config**: `nginx/nginx.conf`

### Laravel Services

-   **Catalog**: Port 8001 (PHP-FPM)
-   **User Management**: Port 8002 (PHP-FPM)

### Monitoring Services

-   **Prometheus**: Port 9090 - Metrics collection with 15-day retention
-   **Grafana**: Port 8000 → - Dashboards and visualization
-   **Loki**: Port 3100 - Log aggregation with 30-day retention
-   **Promtail**: Port 9080 - Log shipping and collection
-   **cAdvisor**: Port 8004 - Container resource metrics
-   **Node Exporter**: Port 9100 - Host system metrics
-   **MySQL Exporter**: Port 9104 - Database performance metrics
-   **Redis Exporter**: Port 9121 - Cache metrics

## Monitoring & Observability

### Quick Access

Add to `/etc/hosts`:

```
127.0.0.1 insights.blindstrader.test prometheus.blindstrader.test
```

Access points:

-   **Grafana**: [http://insights.blindstrader.test](http://insights.blindstrader.test) (admin/admin)
-   **Prometheus**: [http://prometheus.blindstrader.test](http://prometheus.blindstrader.test)

### Features

-   **HTTP Metrics**: Request rate, latency (p50/p95/p99), error rates by service/endpoint
-   **Database Metrics**: Query duration and count per model/table with N+1 detection
-   **Infrastructure Metrics**: CPU, memory, network I/O per container
-   **Centralized Logging**: JSON-formatted logs from all services with filtering
-   **Error Tracking**: Sentry integration with 20% transaction sampling
-   **5 Pre-built Dashboards**: Docker containers, Laravel services, MySQL, Redis, logs explorer
-   **Smart Alerting**: 11 alert rules for errors, performance, and infrastructure

### Setup Monitoring

1.  **Install dependencies** in both Laravel services:
    
    ```bash
    cd services/catalogcomposer require sentry/sentry-laravel spatie/laravel-prometheusphp artisan sentry:publish --configcd ../user-managementcomposer require sentry/sentry-laravel spatie/laravel-prometheusphp artisan sentry:publish --config
    ```
    
2.  **Register middleware** in `bootstrap/app.php` for both services:
    
    ```php
    ->withMiddleware(function (Middleware $middleware) {    $middleware->append(AppHttpMiddlewareCollectPrometheusMetrics::class);})
    ```
    
3.  **Register event listener** in `app/Providers/AppServiceProvider.php`:
    
    ```php
    use IlluminateSupportFacadesEvent;use IlluminateDatabaseEventsQueryExecuted;use AppListenersDatabaseQueryMetrics;public function boot(): void{    Event::listen(QueryExecuted::class, DatabaseQueryMetrics::class);}
    ```
    
4.  **Add metrics route** in `routes/web.php`:
    
    ```php
    Route::get('/metrics', function () {    return response(app('prometheus')->getMetrics())        ->header('Content-Type', 'text/plain; version=0.0.4');})->middleware(AppHttpMiddlewareInternalNetworkOnly::class);
    ```
    
5.  **Configure Sentry** (optional):
    
    -   Create project at sentry.io
    -   Set `SENTRY_LARAVEL_DSN` environment variable
    -   Update `config/sentry.php` with service tags
6.  **Start monitoring stack**:
    
    ```bash
    docker-compose up -d
    ```
    

For detailed setup instructions, baseline monitoring, and troubleshooting, see [monitoring/README.md](monitoring/README.md).

### Adding Monitoring to New Services

When adding new microservices (payment, order-management, etc.), follow the comprehensive template in [monitoring/service-template/README.md](monitoring/service-template/README.md).

## Development

### Building Images

Images are automatically built for multi-architecture:

```bash
# Build and push catalog servicecd services/catalogdocker buildx build --platform linux/amd64,linux/arm64   -t ghcr.io/barkoczi/blindstrader-catalog:latest --push .# Build and push user-management servicecd services/user-managementdocker buildx build --platform linux/amd64,linux/arm64   -t ghcr.io/barkoczi/blindstrader-user-management:latest --push .
```

### Running Migrations

Migrations run automatically on container startup. To run manually:

```bash
docker-compose exec catalog php artisan migratedocker-compose exec user-management php artisan migrate
```

### Viewing Logs

```bash
# All servicesdocker-compose logs -f# Specific servicedocker-compose logs -f catalogdocker-compose logs -f user-management# Nginx logstail -f logs/nginx/access.logtail -f logs/nginx/error.log
```

## Session Sharing

Both services share sessions via Redis with the following configuration:

-   **Session Driver**: redis
-   **Session Cookie**: `blindstrader_session`
-   **Session Domain**: `.blindstrader.test`
-   **Shared APP_KEY**: Both services use the same encryption key

This allows users to authenticate on the auth service and remain authenticated when accessing the catalog service.

## Configuration

### Environment Variables

Key environment variables in `.env` files:

```env
# ApplicationAPP_NAME="BlindStrader"APP_KEY=base64:...  # MUST be the same for both servicesAPP_ENV=local# DatabaseDB_HOST=dbDB_PORT=3306DB_DATABASE=blindstrader_catalog  # or blindstrader_user_managementDB_USERNAME=blindstraderDB_PASSWORD=blindstrader# RedisREDIS_HOST=redisREDIS_PORT=6379# SessionSESSION_DRIVER=redisSESSION_COOKIE=blindstrader_sessionSESSION_DOMAIN=.blindstrader.testCACHE_PREFIX=blindstrader_REDIS_PREFIX=
```

## Troubleshooting

### Services not accessible

```bash
# Check if all containers are runningdocker-compose ps# Check logsdocker-compose logs
```

### Session not sharing between services

-   Verify both services have the same `APP_KEY`
-   Check `SESSION_COOKIE` and `SESSION_DOMAIN` are identical
-   Ensure Redis is running: `docker-compose ps redis`

### Database connection issues

-   Ensure MySQL is healthy: `docker-compose ps db`
-   Check credentials in `.env` files
-   Verify schemas exist: `docker-compose exec db mysql -u root -proot -e "SHOW DATABASES;"`

### Monitoring not collecting metrics

-   Install composer packages in both services
-   Verify middleware is registered in `bootstrap/app.php`
-   Check metrics endpoint: `docker-compose exec catalog curl http://localhost:9000/metrics`
-   See detailed troubleshooting in [monitoring/README.md](monitoring/README.md)

## Project Structure

```
blindstrader/├── docker-compose.yml          # Service orchestration├── nginx/│   ├── nginx.conf             # Nginx configuration│   └── conf.d/                # Subdomain routing configs├── docker/│   └── mysql/│       └── init.sql           # Database initialization├── monitoring/│   ├── README.md              # Comprehensive monitoring guide│   ├── prometheus/            # Metrics collection config│   ├── grafana/               # Dashboards and provisioning│   ├── loki/                  # Log aggregation config│   ├── promtail/              # Log shipping config│   └── service-template/      # Template for new services├── services/│   ├── catalog/               # Catalog Laravel application│   │   ├── Dockerfile│   │   ├── app/│   │   │   ├── Http/Middleware/  # Metrics collection│   │   │   └── Listeners/        # Query metrics│   │   ├── routes/│   │   └── ...│   └── user-management/       # Auth Laravel application│       ├── Dockerfile│       ├── app/│       ├── routes/│       └── ...└── logs/    └── nginx/                 # Nginx logs
```

## License

MIT

## Contributing

1.  Fork the repository
2.  Create your feature branch (`git checkout -b feature/amazing-feature`)
3.  Commit your changes (`git commit -m 'Add amazing feature'`)
4.  Push to the branch (`git push origin feature/amazing-feature`)
5.  Open a Pull Request