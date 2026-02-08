<?php

namespace App\Listeners;

use Illuminate\Database\Events\QueryExecuted;
use Illuminate\Support\Facades\Log;
use Prometheus\CollectorRegistry;
use Prometheus\Exception\MetricsRegistrationException;

/**
 * Listener to collect database query metrics for Prometheus.
 * Implements cardinality limiting to prevent metrics explosion.
 */
class DatabaseQueryMetrics
{
    private CollectorRegistry $registry;
    
    /**
     * Top N models to track individually.
     * Rest will be aggregated as "other".
     */
    private const TOP_MODELS_LIMIT = 20;
    
    /**
     * In-memory cache of model query counts for cardinality limiting.
     * Reset periodically to adapt to changing query patterns.
     */
    private static array $modelQueryCounts = [];
    private static int $lastResetTime = 0;
    private const RESET_INTERVAL = 3600; // Reset every hour
    
    public function __construct(CollectorRegistry $registry)
    {
        $this->registry = $registry;
    }
    
    /**
     * Handle the event.
     */
    public function handle(QueryExecuted $event): void
    {
        try {
            $this->recordQueryMetrics($event);
        } catch (\Exception $e) {
            Log::error('Failed to record database query metrics', [
                'error' => $e->getMessage(),
                'sql' => $event->sql,
            ]);
        }
    }
    
    /**
     * Record database query metrics.
     */
    private function recordQueryMetrics(QueryExecuted $event): void
    {
        $serviceName = config('app.name', 'catalog');
        $duration = $event->time / 1000; // Convert ms to seconds
        $table = $this->extractTable($event->sql);
        $model = $this->extractModelFromBacktrace();
        $operation = $this->extractOperation($event->sql);
        
        // Update model query count for cardinality limiting
        $this->updateModelCount($model);
        
        // Apply cardinality limiting
        $limitedModel = $this->limitCardinality($model);
        
        // Record query duration histogram
        try {
            $histogram = $this->registry->getOrRegisterHistogram(
                $serviceName,
                'db_query_duration_seconds',
                'Database query duration in seconds',
                ['service_name', 'model', 'operation'],
                [0.001, 0.005, 0.01, 0.05, 0.1, 0.5, 1.0, 5.0]
            );
            
            $histogram->observe($duration, [$serviceName, $limitedModel, $operation]);
        } catch (MetricsRegistrationException $e) {
            Log::debug('Histogram registration failed', ['error' => $e->getMessage()]);
        }
        
        // Record query count counter
        try {
            $counter = $this->registry->getOrRegisterCounter(
                $serviceName,
                'db_queries_total',
                'Total database queries',
                ['service_name', 'table', 'operation']
            );
            
            $counter->inc([$serviceName, $table, $operation]);
        } catch (MetricsRegistrationException $e) {
            Log::debug('Counter registration failed', ['error' => $e->getMessage()]);
        }
    }
    
    /**
     * Extract table name from SQL query.
     */
    private function extractTable(string $sql): string
    {
        // Match common patterns: FROM/INTO/UPDATE table_name
        if (preg_match('/(?:from|into|update)\s+`?(\w+)`?/i', $sql, $matches)) {
            return $matches[1];
        }
        
        return 'unknown';
    }
    
    /**
     * Extract model class name from backtrace.
     */
    private function extractModelFromBacktrace(): string
    {
        $backtrace = debug_backtrace(DEBUG_BACKTRACE_IGNORE_ARGS, 20);
        
        foreach ($backtrace as $trace) {
            if (isset($trace['class'])) {
                // Check if it's an Eloquent model
                if (str_ends_with($trace['class'], 'Model') || 
                    str_contains($trace['class'], '\\Models\\')) {
                    $parts = explode('\\', $trace['class']);
                    return end($parts);
                }
            }
        }
        
        return 'unknown';
    }
    
    /**
     * Extract SQL operation type.
     */
    private function extractOperation(string $sql): string
    {
        $sql = strtoupper(trim($sql));
        
        if (str_starts_with($sql, 'SELECT')) return 'select';
        if (str_starts_with($sql, 'INSERT')) return 'insert';
        if (str_starts_with($sql, 'UPDATE')) return 'update';
        if (str_starts_with($sql, 'DELETE')) return 'delete';
        
        return 'other';
    }
    
    /**
     * Update model query count for cardinality tracking.
     */
    private function updateModelCount(string $model): void
    {
        // Reset counts periodically
        if (time() - self::$lastResetTime > self::RESET_INTERVAL) {
            self::$modelQueryCounts = [];
            self::$lastResetTime = time();
        }
        
        if (!isset(self::$modelQueryCounts[$model])) {
            self::$modelQueryCounts[$model] = 0;
        }
        
        self::$modelQueryCounts[$model]++;
    }
    
    /**
     * Limit cardinality by aggregating low-frequency models as "other".
     */
    private function limitCardinality(string $model): string
    {
        if ($model === 'unknown') {
            return 'unknown';
        }
        
        // Sort models by query count descending
        arsort(self::$modelQueryCounts);
        
        // Get top N models
        $topModels = array_slice(array_keys(self::$modelQueryCounts), 0, self::TOP_MODELS_LIMIT, true);
        
        // If model is in top N, use it; otherwise aggregate as "other"
        return in_array($model, $topModels) ? $model : 'other';
    }
}
