<?php

namespace App\Providers;

use App\Listeners\DatabaseQueryMetrics;
use Illuminate\Database\Events\QueryExecuted;
use Illuminate\Support\Facades\Event;
use Illuminate\Support\ServiceProvider;

class AppServiceProvider extends ServiceProvider
{
    public function register(): void
    {
        //
    }

    public function boot(): void
    {
        Event::listen(QueryExecuted::class, DatabaseQueryMetrics::class);
    }
}
