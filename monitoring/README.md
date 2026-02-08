# BlindStrader Monitoring Stack

Comprehensive observability solution for the BlindStrader microservices platform using Prometheus, Grafana, Loki, Sentry, and supporting tools.

## Architecture Overview

### Components

- **Prometheus** (`:9090`) - Time-series metrics collection and alerting
- **Grafana** (`:8000` → `insights.blindstrader.test`) - Visualization dashboards
- **Loki** (`:3100`) - Log aggregation and querying
- **Promtail** (`:9080`) - Log collector and shipper
- **cAdvisor** (`:8004`) - Container resource metrics
- **Node Exporter** (`:9100`) - Host system metrics
- **MySQL Exporter** (`:9104`) - Database metrics
- **Redis Exporter** (`:9121`) - Cache metrics
- **Sentry** (external) - Error tracking and performance monitoring

### Data Retention

- **Prometheus**: 15 days (configurable via `--storage.tsdb.retention.time=15d`)
- **Loki**: 30 days (720 hours)
- **Grafana**: Persistent dashboards and settings

### Service Instrumentation

Both `catalog` and `user-management` services are instrumented with:
- HTTP request metrics (rate, duration, status codes)
- Database query metrics (duration, count per table/model)
- Structured JSON logging with service context
- Sentry error tracking with 20% transaction sampling

## Access URLs

After adding to `/etc/hosts`:
```
127.0.0.1 insights.blindstrader.test prometheus.blindstrader.test
```

- **Grafana (Insights)**: http://insights.blindstrader.test
  - Username: `admin`
  - Password: `admin` (default, override with `GRAFANA_ADMIN_PASSWORD`)
  - Anonymous access enabled for development

- **Prometheus**: http://prometheus.blindstrader.test
  - Query interface and alert status

- **Direct Access**:
  - Grafana: http://localhost:8000
  - Prometheus: http://localhost:9090
  - cAdvisor: http://localhost:8004

## Quick Start

### 1. Install Dependencies

Install packages in both Laravel services:

```bash
# Catalog service
cd services/catalog
composer require sentry/sentry-laravel:"^4.0" spatie/laravel-prometheus:"^1.0"
php artisan sentry:publish --config

# User-management service
cd services/user-management
composer require sentry/sentry-laravel:"^4.0" spatie/laravel-prometheus:"^1.0"
php artisan sentry:publish --config
```

### 2. Configure Sentry

1. Create a Sentry project at https://sentry.io (or your self-hosted instance)
2. Name it "BlindStrader Platform"
3. Copy the DSN and add to your environment:

```bash
# Create .env file or export
export SENTRY_LARAVEL_DSN="https://your-dsn@sentry.io/project-id"
```

### 3. Update Sentry Config

Edit `services/catalog/config/sentry.php` and `services/user-management/config/sentry.php`:

```php
return [
    'dsn' => env('SENTRY_LARAVEL_DSN'),
    
    'environment' => env('SENTRY_ENVIRONMENT', env('APP_ENV')),
    
    'tags' => [
        'service_name' => env('SENTRY_ENVIRONMENT', 'unknown'),
    ],
    
    'breadcrumbs' => [
        'sql_queries' => true,
        'redis_commands' => true,
    ],
    
    'traces_sample_rate' => (float) env('SENTRY_TRACES_SAMPLE_RATE', 0.0),
    'send_default_pii' => env('SENTRY_SEND_DEFAULT_PII', false),
];
```

### 4. Register Middleware and Listeners

**Catalog Service:**

Edit `services/catalog/bootstrap/app.php`:
```php
->withMiddleware(function (Middleware $middleware) {
    $middleware->append(\App\Http\Middleware\CollectPrometheusMetrics::class);
})
```

Edit `services/catalog/app/Providers/AppServiceProvider.php`:
```php
use Illuminate\Support\Facades\Event;
use Illuminate\Database\Events\QueryExecuted;
use App\Listeners\DatabaseQueryMetrics;

public function boot(): void
{
    Event::listen(QueryExecuted::class, DatabaseQueryMetrics::class);
}
```

**User-Management Service:** Repeat the same steps.

### 5. Add Metrics Routes

Add to `services/catalog/routes/web.php` and `services/user-management/routes/web.php`:

```php
use App\Http\Middleware\InternalNetworkOnly;

Route::get('/metrics', function () {
    return response(app('prometheus')->getMetrics())
        ->header('Content-Type', 'text/plain; version=0.0.4');
})->middleware(InternalNetworkOnly::class);
```

### 6. Start Services

```bash
docker-compose up -d
```

Wait for all services to be healthy (1-2 minutes).

### 7. Verify Setup

```bash
# Check Prometheus targets
curl http://localhost:9090/api/v1/targets

# Check metrics endpoints (from inside containers)
docker-compose exec catalog curl http://localhost:9000/metrics
docker-compose exec user-management curl http://localhost:9000/metrics

# Access Grafana
open http://insights.blindstrader.test
```

## Baseline Monitoring Period

**IMPORTANT**: Before enabling alerting to Slack or PagerDuty, monitor for **1-2 weeks** to establish performance baselines.

### Collecting Baseline Metrics

Use these Prometheus queries to understand your application's normal behavior:

#### 95th Percentile Response Time
```promql
histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m])) by (service_name)
```

#### Error Rate Percentage
```promql
sum(rate(http_requests_total{status=~"5.."}[5m])) by (service_name) 
/ 
sum(rate(http_requests_total[5m])) by (service_name) * 100
```

#### Query Performance (95th percentile)
```promql
histogram_quantile(0.95, rate(db_query_duration_seconds_bucket[5m])) by (service_name, model)
```

#### Top Slowest Queries
```promql
topk(10, 
  avg(rate(db_query_duration_seconds_sum[5m])) by (service_name, model) 
  / 
  avg(rate(db_query_duration_seconds_count[5m])) by (service_name, model)
)
```

### Adjusting Alert Thresholds

After collecting baselines, edit `monitoring/prometheus/alerts.yml`:

1. Update `HighErrorRate` threshold if >5% is normal for your traffic
2. Adjust `SlowResponseTime` if >1s is acceptable for heavy operations
3. Fine-tune `HighQueryLatency` based on your query complexity

## Dashboards

Grafana includes 5 pre-configured dashboards:

### 1. Docker Containers
- CPU usage per container
- Memory usage per container
- Network I/O
- Container restarts

### 2. Laravel Services ⭐
- HTTP request rate by service/endpoint
- Error rate percentage gauge
- Response time percentiles (p50/p95/p99)
- **Top 20 database queries by model** (detailed view)
- Query count per table
- N+1 query detection
- Redis operations

### 3. MySQL Performance
- Active connections
- Queries per second
- Slow query rate

### 4. Redis Operations
- Commands per second
- Cache hit rate percentage
- Memory usage

### 5. Logs Explorer
- Real-time log streaming from all services
- Filter by service, level, or search terms
- Integrated with Loki for fast queries

### Creating Custom Dashboards

1. Open Grafana at http://insights.blindstrader.test
2. Create new dashboard
3. Add panels with Prometheus/Loki queries
4. Save dashboard
5. Export JSON via Share → Export
6. Save to `monitoring/grafana/provisioning/dashboards/json/`
7. Commit to version control

## Alert Rules

Current alerts (monitoring only, no notifications):

### Application Alerts
- **HighErrorRate**: >5% error rate for 5 minutes
- **SlowResponseTime**: p95 >1 second for 5 minutes
- **HighQueryLatency**: p95 query time >500ms
- **HighQueryCount**: >500 queries/sec (potential N+1)

### Infrastructure Alerts
- **ContainerRestarted**: Container restarted in last 5 minutes
- **HighMemoryUsage**: >80% memory usage
- **HighCPUUsage**: >80% CPU usage
- **DatabaseDown**: MySQL exporter cannot connect
- **RedisDown**: Redis exporter cannot connect
- **HighDiskUsage**: <10% disk space remaining

### Observability Alerts
- **HighMetricsCardinality**: >100 unique model labels
- **ScrapeFailed**: Prometheus cannot scrape metrics endpoint

## Adding Slack Notifications

After baseline period, add Alertmanager:

### 1. Add Alertmanager Service

Add to `docker-compose.yml`:

```yaml
  alertmanager:
    image: prom/alertmanager:latest
    container_name: blindstrader-alertmanager
    restart: unless-stopped
    command:
      - '--config.file=/etc/alertmanager/alertmanager.yml'
    ports:
      - "9093:9093"
    volumes:
      - ./monitoring/alertmanager:/etc/alertmanager
    networks:
      - blindstrader
```

### 2. Create Alertmanager Config

Create `monitoring/alertmanager/alertmanager.yml`:

```yaml
global:
  slack_api_url: 'https://hooks.slack.com/services/YOUR/SLACK/WEBHOOK'

route:
  receiver: 'slack-notifications'
  group_by: ['alertname', 'severity']
  group_wait: 10s
  group_interval: 5m
  repeat_interval: 3h

receivers:
  - name: 'slack-notifications'
    slack_configs:
      - channel: '#alerts'
        title: '{{ .GroupLabels.alertname }}'
        text: '{{ range .Alerts }}{{ .Annotations.description }}{{ end }}'
        send_resolved: true
```

### 3. Update Prometheus Config

Add to `monitoring/prometheus/prometheus.yml`:

```yaml
alerting:
  alertmanagers:
    - static_configs:
        - targets: ['blindstrader-alertmanager:9093']
```

## Security Considerations

### Docker Socket Access

**cAdvisor** and **Promtail** require read-only access to:
- `/var/lib/docker/containers` - Container logs
- `/var/run/docker.sock` - Docker API (Promtail only)
- Host filesystem mounts

**Security Implications:**
- Read access to all container logs
- Ability to query Docker API
- Not suitable for untrusted multi-tenant environments

**Mitigation:**
- All mounts are read-only (`:ro`)
- cAdvisor runs in privileged mode (required for cgroups access)
- Promtail uses minimal capabilities
- Network isolation via Docker bridge network

### Metrics Endpoint Security

Laravel `/metrics` endpoints are protected by `InternalNetworkOnly` middleware:

- ✅ Accessible from internal Docker networks (10.x, 172.x, 192.168.x)
- ✅ Accessible from other containers
- ❌ Blocked from external networks
- ❌ Returns 403 Forbidden for public access

**For Production:**
1. Ensure Nginx does NOT proxy `/metrics` endpoints
2. Configure firewall rules to block ports 9000-9121 externally
3. Use VPN or bastion host for external access to monitoring tools

### Future: Admin-Only Authentication

After baseline period, implement admin-only access to Grafana and Prometheus:

1. Create `/api/admin/verify` endpoint in user-management service
2. Update Nginx configs to use `auth_request` directive
3. Check `users.is_admin = 1` and valid session
4. Return 200 for authorized, 403 for denied

Example Nginx config (already prepared with TODO comments):
```nginx
location / {
    auth_request /api/admin/verify;
    auth_request_set $auth_status $upstream_status;
    proxy_pass http://blindstrader-grafana:3000;
}
```

## Adding New Services

When adding payment, order-management, or other services, follow the **Service Onboarding Template**:

📁 See `monitoring/service-template/README.md` for complete step-by-step guide.

**Quick Checklist:**
1. ✅ Install sentry/sentry-laravel and spatie/laravel-prometheus
2. ✅ Copy middleware and listener files
3. ✅ Register middleware globally
4. ✅ Register database event listener
5. ✅ Add `/metrics` route with InternalNetworkOnly
6. ✅ Add environment variables to docker-compose.yml
7. ✅ Add Prometheus scrape job
8. ✅ Publish and configure Sentry
9. ✅ Update logging config with service name
10. ✅ Create Grafana dashboard panels
11. ✅ Test metrics endpoint

## Troubleshooting

### Prometheus Not Scraping Targets

```bash
# Check target status
curl http://localhost:9090/api/v1/targets | jq

# Check if service is exposing metrics
docker-compose exec catalog curl http://localhost:9000/metrics

# Check Prometheus logs
docker-compose logs prometheus
```

**Common Issues:**
- Composer packages not installed (run `composer install`)
- Middleware not registered (check bootstrap/app.php)
- Route not added (check routes/web.php)
- Service not started (check docker-compose ps)

### Grafana Dashboards Not Loading

```bash
# Check Grafana logs
docker-compose logs grafana

# Check provisioning directory
ls -la monitoring/grafana/provisioning/dashboards/json/

# Verify Prometheus datasource
curl http://localhost:8000/api/datasources
```

**Common Issues:**
- JSON syntax errors in dashboard files
- Datasource not configured
- Permissions on mounted volumes

### Loki/Promtail Not Collecting Logs

```bash
# Check Promtail logs
docker-compose logs promtail

# Check Loki status
curl http://localhost:3100/ready

# Verify Docker socket access
docker-compose exec promtail ls -la /var/run/docker.sock
```

**Common Issues:**
- Docker socket not mounted
- Insufficient permissions on /var/lib/docker/containers
- Log format not matching regex in promtail-config.yml

### High Cardinality Warnings

If you see `HighMetricsCardinality` alerts:

1. Check model count in DatabaseQueryMetrics
2. Verify cardinality limiting is working (top 20 models only)
3. Review query patterns - are you querying 100+ different models?
4. Consider adjusting `TOP_MODELS_LIMIT` constant if needed

### Sentry Not Capturing Errors

```bash
# Test Sentry connection
docker-compose exec catalog php artisan tinker
>>> Sentry\captureMessage('Test from catalog');

# Check Sentry DSN
docker-compose exec catalog env | grep SENTRY
```

**Common Issues:**
- SENTRY_LARAVEL_DSN not set or empty
- Sentry config not published
- Service provider not registered (should be automatic)

## Performance Impact

### Metrics Collection Overhead

- HTTP middleware: **~0.1-0.5ms per request**
- Database listener: **~0.01-0.05ms per query**
- Prometheus scrape: **15-second interval**, minimal impact

### Storage Requirements

Estimated storage per day (2 services, moderate traffic):

- Prometheus: **~200-500MB/day** (15-day retention ≈ 3-7.5GB)
- Loki: **~100-300MB/day** (30-day retention ≈ 3-9GB)
- Grafana: **~10MB** (dashboards and settings)

**Total: ~6-16GB** for full retention period

### Resource Usage

Expected resource consumption (8 monitoring services):

- CPU: **~0.5-1.5 cores total**
- Memory: **~1-2GB total**
- Network: **~1-5Mbps** (metrics scraping + log shipping)

## Maintenance

### Regular Tasks

- **Weekly**: Review Grafana dashboards for anomalies
- **Monthly**: Check alert thresholds are still relevant
- **Quarterly**: Review and prune old Prometheus/Loki data if needed

### Backup Strategy

Important files to backup:
- `monitoring/prometheus/prometheus.yml` - Metrics config
- `monitoring/prometheus/alerts.yml` - Alert rules
- `monitoring/grafana/provisioning/` - Dashboards and datasources
- Docker volumes: `prometheus_data`, `grafana_data`, `loki_data`

### Updating Components

```bash
# Pull latest images
docker-compose pull prometheus grafana loki promtail

# Restart services
docker-compose up -d prometheus grafana loki promtail
```

Prometheus and Loki support rolling upgrades without data loss.

## Additional Resources

- [Prometheus Documentation](https://prometheus.io/docs/)
- [Grafana Documentation](https://grafana.com/docs/)
- [Loki Documentation](https://grafana.com/docs/loki/)
- [Sentry Laravel Integration](https://docs.sentry.io/platforms/php/guides/laravel/)
- [Service Onboarding Template](./service-template/README.md)

## Support

For questions or issues with the monitoring stack:

1. Check this README and troubleshooting section
2. Review service logs: `docker-compose logs <service-name>`
3. Consult the service-template for new service integration
4. Refer to main project documentation

---

**Last Updated**: February 8, 2026
**Stack Version**: Prometheus (latest), Grafana (latest), Loki (latest)
**Services Monitored**: catalog, user-management (+ 6 planned)
