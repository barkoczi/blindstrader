<?php

use App\Http\Controllers\HealthController;
use App\Http\Middleware\InternalNetworkOnly;
use Illuminate\Http\Request;
use Illuminate\Support\Facades\Route;
use Spatie\Prometheus\Facades\Prometheus;

/*
|--------------------------------------------------------------------------
| API Routes
|--------------------------------------------------------------------------
*/

// Public health check
Route::get('/health', HealthController::class)->name('health');

// Internal metrics endpoint (Prometheus scraping)
Route::get('/metrics', function () {
    return response(Prometheus::renderCollectors(), 200, [
        'Content-Type' => 'text/plain; version=0.0.4',
    ]);
})->middleware(InternalNetworkOnly::class)->name('metrics');

// Authenticated API v1 routes
Route::prefix('v1')->middleware('auth:sanctum')->group(
    base_path('routes/api_v1.php')
);
