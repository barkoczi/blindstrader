#!/usr/bin/env python3
"""Generate boilerplate files for all 8 BlindStrader microservices."""

import os
import json

BASE = "/Users/barkocziroland/laravel/blindstrader/services"

SERVICES = {
    "identity": {
        "port": 8001,
        "db": "blindstrader_identity",
        "subdomain": "identity",
        "app_name": "Identity",
        "kafka": True,
        "tenancy": False,
        "filament": True,
        "stripe": False,
        "sentry_env": "identity",
    },
    "brand": {
        "port": 8002,
        "db": "blindstrader_brand",
        "subdomain": "brand",
        "app_name": "Brand",
        "kafka": True,
        "tenancy": True,
        "filament": True,
        "stripe": False,
        "sentry_env": "brand",
        "tenant_name": "Louvolite",
        "tenant_slug": "louvolite",
    },
    "supplier": {
        "port": 8003,
        "db": "blindstrader_supplier",
        "subdomain": "supplier",
        "app_name": "Supplier",
        "kafka": True,
        "tenancy": True,
        "filament": True,
        "stripe": False,
        "sentry_env": "supplier",
        "tenant_name": "Cassidy",
        "tenant_slug": "cassidy",
    },
    "supply-chain": {
        "port": 8004,
        "db": "blindstrader_supply_chain",
        "subdomain": "sc",
        "app_name": "SupplyChain",
        "kafka": True,
        "tenancy": False,
        "filament": False,
        "stripe": False,
        "sentry_env": "supply-chain",
    },
    "payment": {
        "port": 8005,
        "db": "blindstrader_payment",
        "subdomain": "payment",
        "app_name": "Payment",
        "kafka": True,
        "tenancy": False,
        "filament": False,
        "stripe": True,
        "sentry_env": "payment",
    },
    "retailer": {
        "port": 8006,
        "db": "blindstrader_retailer",
        "subdomain": "retailer",
        "app_name": "Retailer",
        "kafka": True,
        "tenancy": True,
        "filament": False,
        "stripe": False,
        "sentry_env": "retailer",
        "tenant_name": "Newblinds",
        "tenant_slug": "newblinds",
    },
    "platform": {
        "port": 8007,
        "db": "blindstrader_platform",
        "subdomain": "platform",
        "app_name": "Platform",
        "kafka": True,
        "tenancy": False,
        "filament": True,
        "stripe": False,
        "sentry_env": "platform",
    },
    "notification": {
        "port": 8008,
        "db": "blindstrader_notification",
        "subdomain": "notification",
        "app_name": "Notification",
        "kafka": False,
        "tenancy": False,
        "filament": False,
        "stripe": False,
        "sentry_env": "notification",
    },
}


def write(path, content):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        f.write(content)
    print(f"  wrote {path.replace(BASE + '/', '')}")


def bootstrap_app(svc, cfg):
    return """\
<?php

use App\\Http\\Middleware\\CollectPrometheusMetrics;
use Illuminate\\Foundation\\Application;
use Illuminate\\Foundation\\Configuration\\Exceptions;
use Illuminate\\Foundation\\Configuration\\Middleware;
use Illuminate\\Http\\Request;

return Application::configure(basePath: dirname(__DIR__))
    ->withRouting(
        api: __DIR__.'/../routes/api.php',
        commands: __DIR__.'/../routes/console.php',
        health: '/up',
    )
    ->withMiddleware(function (Middleware $middleware): void {
        $middleware->append(CollectPrometheusMetrics::class);
    })
    ->withExceptions(function (Exceptions $exceptions): void {
        $exceptions->shouldRenderJsonWhen(fn (Request $request) => true);
    })->create();
"""


def routes_api(svc, cfg):
    return """\
<?php

use App\\Http\\Controllers\\HealthController;
use App\\Http\\Middleware\\InternalNetworkOnly;
use Illuminate\\Http\\Request;
use Illuminate\\Support\\Facades\\Route;
use Spatie\\Prometheus\\Facades\\Prometheus;

/*
|--------------------------------------------------------------------------
| API Routes
|--------------------------------------------------------------------------
*/

// Public health check
Route::get('/health', HealthController::class)->name('health');

// Internal metrics endpoint (Prometheus scraping)
Route::get('/metrics', function () {
    return response(Prometheus::renderResponse(), 200, [
        'Content-Type' => 'text/plain; version=0.0.4',
    ]);
})->middleware(InternalNetworkOnly::class)->name('metrics');

// Authenticated API v1 routes
Route::prefix('v1')->middleware('auth:sanctum')->group(
    base_path('routes/api_v1.php')
);
"""


def routes_api_v1(svc, cfg):
    name = cfg["app_name"]
    return f"""\
<?php

use Illuminate\\Http\\Request;
use Illuminate\\Support\\Facades\\Route;

/*
|--------------------------------------------------------------------------
| {name} Service — API v1 Routes
|--------------------------------------------------------------------------
*/

Route::get('/user', function (Request $request) {{
    return $request->user();
}});
"""


def health_controller(svc, cfg):
    return """\
<?php

namespace App\\Http\\Controllers;

use Illuminate\\Http\\JsonResponse;

class HealthController extends Controller
{
    public function __invoke(): JsonResponse
    {
        return response()->json([
            'status'  => 'ok',
            'service' => config('app.name'),
        ]);
    }
}
"""


def api_resource(svc, cfg):
    return """\
<?php

namespace App\\Http\\Resources;

use Illuminate\\Http\\Request;
use Illuminate\\Http\\Resources\\Json\\JsonResource;

abstract class ApiResource extends JsonResource
{
    /**
     * Wrap the resource in a consistent envelope.
     */
    public static $wrap = 'data';
}
"""


def api_form_request(svc, cfg):
    return """\
<?php

namespace App\\Http\\Requests;

use Illuminate\\Contracts\\Validation\\Validator;
use Illuminate\\Foundation\\Http\\FormRequest;
use Illuminate\\Http\\Exceptions\\HttpResponseException;

abstract class ApiFormRequest extends FormRequest
{
    /**
     * Always return JSON validation errors.
     */
    protected function failedValidation(Validator $validator): never
    {
        throw new HttpResponseException(
            response()->json([
                'message' => 'The given data was invalid.',
                'errors'  => $validator->errors(),
            ], 422)
        );
    }

    /**
     * Always return JSON authorization errors.
     */
    protected function failedAuthorization(): never
    {
        throw new HttpResponseException(
            response()->json([
                'message' => 'This action is unauthorized.',
            ], 403)
        );
    }
}
"""


def app_service_provider(svc, cfg):
    return """\
<?php

namespace App\\Providers;

use App\\Listeners\\DatabaseQueryMetrics;
use Illuminate\\Database\\Events\\QueryExecuted;
use Illuminate\\Support\\Facades\\Event;
use Illuminate\\Support\\ServiceProvider;

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
"""


def env_example(svc, cfg):
    name = cfg["app_name"]
    db = cfg["db"]
    sentry_env = cfg["sentry_env"]
    subdomain = cfg["subdomain"]

    kafka_block = ""
    if cfg["kafka"]:
        kafka_block = """\

# Kafka
KAFKA_BROKERS=kafka:9092
KAFKA_GROUP_ID={svc}-service
KAFKA_AUTO_CREATE_TOPICS_ENABLE=true
""".format(svc=svc)

    tenancy_block = ""
    if cfg["tenancy"]:
        tenancy_block = """\

# Tenancy (stancl/tenancy)
TENANCY_DB_HOST=db
TENANCY_DB_PORT=3306
TENANCY_DB_USERNAME=blindstrader
TENANCY_DB_PASSWORD=blindstrader
TENANCY_DB_PREFIX=blindstrader_{svc}_
""".format(svc=svc.replace("-", "_"))

    stripe_block = ""
    if cfg["stripe"]:
        stripe_block = """\

# Stripe (raw SDK — custom Connect implementation)
STRIPE_SECRET_KEY=sk_test_your_key_here
STRIPE_WEBHOOK_SECRET=whsec_your_webhook_secret_here
STRIPE_CONNECT_CLIENT_ID=ca_your_connect_client_id_here
"""

    socialite_block = ""
    if svc == "identity":
        socialite_block = """\

# Socialite (OAuth providers)
SOCIALITE_GITHUB_CLIENT_ID=your_github_client_id
SOCIALITE_GITHUB_CLIENT_SECRET=your_github_client_secret
SOCIALITE_GITHUB_REDIRECT_URI=https://identity.blindstrader.com/auth/github/callback
"""

    return f"""\
APP_NAME={name}
APP_ENV=local
APP_KEY=
APP_DEBUG=true
APP_URL=https://{subdomain}.blindstrader.test
APP_PORT={cfg['port']}

LOG_CHANNEL=stack
LOG_DEPRECATIONS_CHANNEL=null
LOG_LEVEL=debug

# Database
DB_CONNECTION=mysql
DB_HOST=db
DB_PORT=3306
DB_DATABASE={db}
DB_USERNAME=blindstrader
DB_PASSWORD=blindstrader

# Redis
REDIS_CLIENT=predis
REDIS_HOST=redis
REDIS_PASSWORD=null
REDIS_PORT=6379
SESSION_DRIVER=redis
CACHE_STORE=redis
QUEUE_CONNECTION=redis

# Session
SESSION_LIFETIME=120
SESSION_DOMAIN=.blindstrader.test
SANCTUM_STATEFUL_DOMAINS=

# Sentry
SENTRY_LARAVEL_DSN=
SENTRY_ENVIRONMENT={sentry_env}
SENTRY_TRACES_SAMPLE_RATE=0.2
SENTRY_SEND_DEFAULT_PII=true

# Inter-service Auth (issued by Identity service)
IDENTITY_SERVICE_URL=http://identity:9000
SERVICE_ACCOUNT_CLIENT_ID=
SERVICE_ACCOUNT_CLIENT_SECRET=
{kafka_block}{tenancy_block}{stripe_block}{socialite_block}
# Mail (for notifications / password resets)
MAIL_MAILER=log
MAIL_HOST=127.0.0.1
MAIL_PORT=2525
MAIL_USERNAME=null
MAIL_PASSWORD=null
MAIL_ENCRYPTION=null
MAIL_FROM_ADDRESS="noreply@blindstrader.com"
MAIL_FROM_NAME="${{APP_NAME}}"
"""


def tenant_seeder(svc, cfg):
    tenant_name = cfg["tenant_name"]
    tenant_slug = cfg["tenant_slug"]
    name = cfg["app_name"]
    return f"""\
<?php

namespace Database\\Seeders;

use Illuminate\\Database\\Seeder;
use Stancl\\Tenancy\\Database\\Models\\Tenant;

class TenantSeeder extends Seeder
{{
    /**
     * Seed a sample {name} tenant for local development.
     *
     * Tenant database (e.g. blindstrader_{svc.replace('-','_')}_{tenant_slug}) is
     * created dynamically by stancl/tenancy at runtime.
     */
    public function run(): void
    {{
        if (Tenant::where('id', '{tenant_slug}')->exists()) {{
            $this->command->info('Tenant "{tenant_name}" already exists, skipping.');
            return;
        }}

        Tenant::create([
            'id'   => '{tenant_slug}',
            'name' => '{tenant_name}',
        ]);

        $this->command->info('Sample tenant "{tenant_name}" created.');
    }}
}}
"""


def service_account_migration():
    return """\
<?php

use Illuminate\\Database\\Migrations\\Migration;
use Illuminate\\Database\\Schema\\Blueprint;
use Illuminate\\Support\\Facades\\Schema;

return new class extends Migration
{
    public function up(): void
    {
        Schema::create('service_accounts', function (Blueprint $table) {
            $table->id();
            $table->string('name')->unique();
            $table->string('client_id')->unique();
            $table->string('client_secret_hash');
            $table->json('permissions')->nullable();
            $table->boolean('is_active')->default(true);
            $table->timestamps();
        });
    }

    public function down(): void
    {
        Schema::dropIfExists('service_accounts');
    }
};
"""


def service_account_model():
    return """\
<?php

namespace App\\Models;

use Illuminate\\Database\\Eloquent\\Model;

class ServiceAccount extends Model
{
    protected $fillable = [
        'name',
        'client_id',
        'client_secret_hash',
        'permissions',
        'is_active',
    ];

    protected $casts = [
        'permissions' => 'array',
        'is_active'   => 'boolean',
    ];

    protected $hidden = ['client_secret_hash'];

    public function verifySecret(string $secret): bool
    {
        return password_verify($secret, $this->client_secret_hash);
    }
}
"""


def service_account_seeder():
    services = ["brand", "supplier", "supply-chain", "payment", "retailer", "platform", "notification"]
    entries = []
    for s in services:
        slug = s.replace("-", "_")
        entries.append(f"""\
        [
            'name'               => '{s}-service',
            'client_id'          => '{slug}_client',
            'client_secret_hash' => password_hash(env('SA_{slug.upper()}_SECRET', '{slug}_secret_change_me'), PASSWORD_BCRYPT),
            'permissions'        => json_encode(['*']),
            'is_active'          => true,
        ],""")

    entries_str = "\n".join(entries)

    return f"""\
<?php

namespace Database\\Seeders;

use App\\Models\\ServiceAccount;
use Illuminate\\Database\\Seeder;

class ServiceAccountSeeder extends Seeder
{{
    /**
     * Pre-create machine credentials for each downstream service.
     * Run automatically via DatabaseSeeder on first boot.
     */
    public function run(): void
    {{
        $accounts = [
{entries_str}
        ];

        foreach ($accounts as $account) {{
            ServiceAccount::firstOrCreate(
                ['client_id' => $account['client_id']],
                $account
            );
        }}

        $this->command->info('Service accounts seeded.');
    }}
}}
"""


def database_seeder_with_service_accounts():
    return """\
<?php

namespace Database\\Seeders;

use Illuminate\\Database\\Seeder;

class DatabaseSeeder extends Seeder
{
    public function run(): void
    {
        $this->call([
            ServiceAccountSeeder::class,
        ]);
    }
}
"""


# ─── Generate files ────────────────────────────────────────────────────────────

for svc, cfg in SERVICES.items():
    svc_path = os.path.join(BASE, svc)
    print(f"\n[{svc}]")

    write(f"{svc_path}/bootstrap/app.php", bootstrap_app(svc, cfg))
    write(f"{svc_path}/routes/api.php", routes_api(svc, cfg))
    write(f"{svc_path}/routes/api_v1.php", routes_api_v1(svc, cfg))
    write(f"{svc_path}/app/Http/Controllers/HealthController.php", health_controller(svc, cfg))
    write(f"{svc_path}/app/Http/Resources/ApiResource.php", api_resource(svc, cfg))
    write(f"{svc_path}/app/Http/Requests/ApiFormRequest.php", api_form_request(svc, cfg))
    write(f"{svc_path}/app/Providers/AppServiceProvider.php", app_service_provider(svc, cfg))
    write(f"{svc_path}/.env.example", env_example(svc, cfg))

    # TenantSeeder for multi-tenant services
    if cfg["tenancy"]:
        write(f"{svc_path}/database/seeders/TenantSeeder.php", tenant_seeder(svc, cfg))

# Identity-specific: service account system
identity_path = os.path.join(BASE, "identity")
print("\n[identity — service account extras]")
write(
    f"{identity_path}/database/migrations/2026_03_05_000001_create_service_accounts_table.php",
    service_account_migration(),
)
write(f"{identity_path}/app/Models/ServiceAccount.php", service_account_model())
write(f"{identity_path}/database/seeders/ServiceAccountSeeder.php", service_account_seeder())
write(f"{identity_path}/database/seeders/DatabaseSeeder.php", database_seeder_with_service_accounts())

print("\n✅ All service files generated.")
