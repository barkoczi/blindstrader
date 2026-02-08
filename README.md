# BlindStrader

A multi-service Laravel 12 application built with Docker, featuring microservices architecture with shared authentication.

## Architecture

-   **Auth Service** (`auth.blindstrader.test`): User management and authentication with Filament admin panel
-   **Catalog Service** (`catalog.blindstrader.test`): Catalog management with Filament admin panel and API
-   **Shared Redis Sessions**: Cross-service authentication
-   **MySQL 8**: Single database instance with separate schemas
-   **Nginx**: Reverse proxy with subdomain routing

## Features

-   ✅ Docker Compose orchestration
-   ✅ Multi-architecture Docker images (linux/amd64, linux/arm64)
-   ✅ Subdomain-based routing
-   ✅ Shared session management via Redis
-   ✅ Automatic database migrations on startup
-   ✅ Laravel 12 with PHP 8.3
-   ✅ Local development with Valet integration
-   ✅ Comprehensive monitoring stack (Prometheus, Grafana, Loki, Sentry)
-   ✅ Detailed metrics and logging with cardinality management
-   ✅ Pre-configured dashboards and alerting rules

## Quick Start

### Prerequisites

-   Docker & Docker Compose
-   dnsmasq or Laravel Valet (for local development)
-   GitHub Container Registry access (for pulling images)

### Setup

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
    
    -   Auth service: [https://auth.blindstrader.test](https://auth.blindstrader.test)
    -   Catalog service: [https://catalog.blindstrader.test](https://catalog.blindstrader.test)
    -   Root redirect: [https://blindstrader.test](https://blindstrader.test)
    -   Grafana (Insights): [https://insights.blindstrader.test](https://insights.blindstrader.test) (admin/admin)
    -   Prometheus: [https://prometheus.blindstrader.test](https://prometheus.blindstrader.test)

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