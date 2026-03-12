<?php

declare(strict_types=1);

use Stancl\Tenancy\Database\Drivers\MySQLDatabaseManager;
use Stancl\Tenancy\Bootstrappers\DatabaseTenancyBootstrapper;

return [
    'tenant_model' => \Stancl\Tenancy\Database\Models\Tenant::class,

    'id_generator' => \Stancl\Tenancy\UUIDGenerator::class,

    'central_domains' => [],

    'bootstrappers' => [
        DatabaseTenancyBootstrapper::class,
    ],

    'database' => [
        // Must match the central (landlord) DB connection.
        'central_connection' => env('DB_CONNECTION', 'mysql'),

        'template_tenant_connection' => null,

        // Tenant DB names: blindstrader_retailer_{id}
        'prefix' => env('TENANCY_DB_PREFIX', 'blindstrader_retailer_'),
        'suffix' => '',

        'managers' => [
            'mysql'  => MySQLDatabaseManager::class,
            'sqlite' => \Stancl\Tenancy\Database\Drivers\SQLiteDatabaseManager::class,
        ],
    ],

    'features' => [],

    'storage_to_config_map' => [],
    'storage_drivers'       => [],

    'cache' => [
        'store' => 'redis',
        'ttl'   => 3600,
    ],

    'filesystem' => [
        'suffix_base'      => 'tenant',
        'disks'            => [],
        'root_override'    => [],
        'override_storage' => false,
    ],

    'redis' => [
        'prefix_base'          => 'tenant',
        'prefixed_connections' => [],
    ],

    'queue_contains_tenant_id' => true,
];
