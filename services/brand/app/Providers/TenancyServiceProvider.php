<?php

declare(strict_types=1);

namespace App\Providers;

use Illuminate\Support\ServiceProvider;
use Stancl\Tenancy\Middleware\InitializeTenancyByDomain;
use Stancl\Tenancy\Middleware\PreventAccessFromCentralDomains;

class TenancyServiceProvider extends ServiceProvider
{
    // By default, no central route middleware is needed here —
    // tenancy bootstrapping is handled per-request via InitializeTenancyByDomain.

    public function register(): void
    {
        //
    }

    public function boot(): void
    {
        $this->bootRoutes();
    }

    protected function bootRoutes(): void
    {
        // Add tenant route middleware aliases so routes can use:
        //   ->middleware(['tenant', 'prevent-access-from-central-domains'])
        $router = $this->app['router'];

        $router->aliasMiddleware('tenant', InitializeTenancyByDomain::class);
        $router->aliasMiddleware('prevent-access-from-central-domains', PreventAccessFromCentralDomains::class);
    }
}
