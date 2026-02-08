# Service Onboarding Template

This directory contains template files and documentation for adding monitoring to new BlindStrader services (e.g., payment, order-management, etc.).

## Quick Start Checklist

When adding a new service to the platform, follow these steps to enable full observability:

### 1. Install Required Packages

```bash
cd services/your-service-name
composer require sentry/sentry-laravel:"^4.0" spatie/laravel-prometheus:"^1.0"
```

### 2. Copy Middleware Files

Copy the following middleware to `app/Http/Middleware/`:
- `CollectPrometheusMetrics.php` - Collects HTTP request metrics
- `InternalNetworkOnly.php` - Protects /metrics endpoint

Files are available in this template directory.

### 3. Copy Listener File

Copy `DatabaseQueryMetrics.php` to `app/Listeners/` for database query metrics collection with cardinality limiting.

### 4. Register Middleware

Update `bootstrap/app.php` to register the metrics collection middleware globally:

```php
->withMiddleware(function (Middleware $middleware) {
    $middleware->append(\App\Http\Middleware\CollectPrometheusMetrics::class);
})
```

### 5. Register Event Listener

In `app/Providers/AppServiceProvider.php`, register the database query listener in the `boot()` method:

```php
use Illuminate\Support\Facades\Event;
use Illuminate\Database\Events\QueryExecuted;
use App\Listeners\DatabaseQueryMetrics;

public function boot(): void
{
    Event::listen(QueryExecuted::class, DatabaseQueryMetrics::class);
}
```

### 6. Add /metrics Route

In `routes/web.php`, add the metrics endpoint:

```php
use App\Http\Middleware\InternalNetworkOnly;
use Illuminate\Support\Facades\Route;

Route::get('/metrics', function () {
    return response(app('prometheus')->getMetrics())
        ->header('Content-Type', 'text/plain; version=0.0.4');
})->middleware(InternalNetworkOnly::class);
```

### 7. Update docker-compose.yml

Add environment variables to your service definition (see `docker-compose-environment.yml` template):

```yaml
environment:
  # ... existing vars ...
  SENTRY_LARAVEL_DSN: ${SENTRY_LARAVEL_DSN:-}
  SENTRY_ENVIRONMENT: your-service-name
  SENTRY_TRACES_SAMPLE_RATE: 0.2
  SENTRY_SEND_DEFAULT_PII: "true"
```

Update service name in logging config (`config/logging.php`):
```php
$record['extra']['service_name'] = 'your-service-name';
```

### 8. Add Prometheus Scrape Job

Add your service to `monitoring/prometheus/prometheus.yml` (see `prometheus-scrape-job.yml` template):

```yaml
  - job_name: 'your-service-metrics'
    metrics_path: '/metrics'
    static_configs:
      - targets: ['blindstrader-your-service:9000']
        labels:
          service: 'your-service'
          service_type: 'laravel'
```

### 9. Publish Sentry Configuration

After deploying/rebuilding containers:

```bash
docker-compose exec your-service php artisan sentry:publish --config
```

Then update `config/sentry.php`:
```php
'tags' => [
    'service_name' => env('SENTRY_ENVIRONMENT', 'unknown'),
],
'breadcrumbs' => [
    'sql_queries' => true,
    'redis_commands' => true,
],
```

### 10. Create Grafana Dashboard Panel

Add a new panel to `monitoring/grafana/provisioning/dashboards/json/laravel-services.json` (see `grafana-panel-example.json`) or create a new dashboard for your service.

### 11. Test Metrics Endpoint

```bash
# From inside the container (internal access)
docker-compose exec your-service curl http://localhost:9000/metrics

# From Prometheus container (should work)
docker-compose exec prometheus curl http://blindstrader-your-service:9000/metrics

# From outside (should be blocked)
curl http://localhost:8XXX/metrics  # Should return 403
```

## Important Notes

### Service Naming Convention
- Service name in docker-compose: `your-service` (lowercase, hyphenated)
- Container name: `blindstrader-your-service`
- SENTRY_ENVIRONMENT: `your-service` (matches service name)
- Logging service_name: `your-service`

### Cardinality Management
The `DatabaseQueryMetrics` listener automatically limits cardinality by:
- Tracking only the top 20 most-queried models
- Aggregating others as "other"
- Resetting counts hourly to adapt to changing patterns

### Security
- `/metrics` endpoint is protected by `InternalNetworkOnly` middleware
- Only accessible from Docker internal networks
- External access returns 403 Forbidden

### Sentry Project
All services share a single Sentry project ("BlindStrader Platform") but are differentiated by the `SENTRY_ENVIRONMENT` tag and custom `service_name` tag.

## Files in This Template

- `README.md` - This file
- `CollectPrometheusMetrics.php` - HTTP metrics middleware
- `InternalNetworkOnly.php` - Security middleware
- `DatabaseQueryMetrics.php` - Query metrics listener
- `composer-packages.txt` - Required package versions
- `docker-compose-environment.yml` - Environment variable template
- `prometheus-scrape-job.yml` - Prometheus config snippet
- `grafana-panel-example.json` - Dashboard panel example

## Support

For questions or issues, refer to `monitoring/README.md` or the main project documentation.
