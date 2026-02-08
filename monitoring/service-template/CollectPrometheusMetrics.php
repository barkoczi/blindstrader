<?php

namespace App\Http\Middleware;

use Closure;
use Illuminate\Http\Request;
use Illuminate\Support\Facades\Log;
use Prometheus\CollectorRegistry;
use Prometheus\Exception\MetricsRegistrationException;
use Symfony\Component\HttpFoundation\Response;

/**
 * Middleware to collect Prometheus metrics for HTTP requests.
 */
class CollectPrometheusMetrics
{
    private CollectorRegistry $registry;
    
    public function __construct(CollectorRegistry $registry)
    {
        $this->registry = $registry;
    }
    
    /**
     * Handle an incoming request.
     */
    public function handle(Request $request, Closure $next): Response
    {
        $startTime = microtime(true);
        
        $response = $next($request);
        
        $duration = microtime(true) - $startTime;
        
        try {
            $this->recordMetrics($request, $response, $duration);
        } catch (\Exception $e) {
            Log::error('Failed to record Prometheus metrics', [
                'error' => $e->getMessage(),
                'trace' => $e->getTraceAsString(),
            ]);
        }
        
        return $response;
    }
    
    /**
     * Record HTTP request metrics.
     */
    private function recordMetrics(Request $request, Response $response, float $duration): void
    {
        $serviceName = config('app.name', 'catalog');
        $method = $request->method();
        $endpoint = $this->normalizeEndpoint($request->path());
        $status = $response->getStatusCode();
        
        // HTTP request duration histogram
        try {
            $histogram = $this->registry->getOrRegisterHistogram(
                $serviceName,
                'http_request_duration_seconds',
                'HTTP request duration in seconds',
                ['service_name', 'method', 'endpoint', 'status'],
                [0.05, 0.1, 0.3, 0.5, 1.0, 3.0, 5.0]
            );
            
            $histogram->observe(
                $duration,
                [$serviceName, $method, $endpoint, (string) $status]
            );
        } catch (MetricsRegistrationException $e) {
            Log::warning('Failed to register histogram metric', ['error' => $e->getMessage()]);
        }
        
        // HTTP request counter
        try {
            $counter = $this->registry->getOrRegisterCounter(
                $serviceName,
                'http_requests_total',
                'Total HTTP requests',
                ['service_name', 'method', 'endpoint', 'status']
            );
            
            $counter->inc([$serviceName, $method, $endpoint, (string) $status]);
        } catch (MetricsRegistrationException $e) {
            Log::warning('Failed to register counter metric', ['error' => $e->getMessage()]);
        }
    }
    
    /**
     * Normalize endpoint path to reduce cardinality.
     * Replace dynamic segments with placeholders.
     */
    private function normalizeEndpoint(string $path): string
    {
        // Remove leading/trailing slashes
        $path = trim($path, '/');
        
        if (empty($path)) {
            return '/';
        }
        
        // Replace UUIDs
        $path = preg_replace(
            '/[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}/i',
            '{uuid}',
            $path
        );
        
        // Replace numeric IDs
        $path = preg_replace('/\/\d+/', '/{id}', $path);
        
        // Replace long alphanumeric strings (likely tokens/hashes)
        $path = preg_replace('/\/[a-zA-Z0-9]{20,}/', '/{token}', $path);
        
        return '/' . $path;
    }
}
