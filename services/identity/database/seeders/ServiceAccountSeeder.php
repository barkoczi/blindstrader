<?php

namespace Database\Seeders;

use App\Models\ServiceAccount;
use Illuminate\Database\Seeder;

class ServiceAccountSeeder extends Seeder
{
    /**
     * Pre-create machine credentials for each downstream service.
     * Run automatically via DatabaseSeeder on first boot.
     */
    public function run(): void
    {
        $accounts = [
        [
            'name'               => 'brand-service',
            'client_id'          => 'brand_client',
            'client_secret_hash' => password_hash(env('SA_BRAND_SECRET', 'brand_secret_change_me'), PASSWORD_BCRYPT),
            'permissions'        => json_encode(['*']),
            'is_active'          => true,
        ],
        [
            'name'               => 'supplier-service',
            'client_id'          => 'supplier_client',
            'client_secret_hash' => password_hash(env('SA_SUPPLIER_SECRET', 'supplier_secret_change_me'), PASSWORD_BCRYPT),
            'permissions'        => json_encode(['*']),
            'is_active'          => true,
        ],
        [
            'name'               => 'supply-chain-service',
            'client_id'          => 'supply_chain_client',
            'client_secret_hash' => password_hash(env('SA_SUPPLY_CHAIN_SECRET', 'supply_chain_secret_change_me'), PASSWORD_BCRYPT),
            'permissions'        => json_encode(['*']),
            'is_active'          => true,
        ],
        [
            'name'               => 'payment-service',
            'client_id'          => 'payment_client',
            'client_secret_hash' => password_hash(env('SA_PAYMENT_SECRET', 'payment_secret_change_me'), PASSWORD_BCRYPT),
            'permissions'        => json_encode(['*']),
            'is_active'          => true,
        ],
        [
            'name'               => 'retailer-service',
            'client_id'          => 'retailer_client',
            'client_secret_hash' => password_hash(env('SA_RETAILER_SECRET', 'retailer_secret_change_me'), PASSWORD_BCRYPT),
            'permissions'        => json_encode(['*']),
            'is_active'          => true,
        ],
        [
            'name'               => 'platform-service',
            'client_id'          => 'platform_client',
            'client_secret_hash' => password_hash(env('SA_PLATFORM_SECRET', 'platform_secret_change_me'), PASSWORD_BCRYPT),
            'permissions'        => json_encode(['*']),
            'is_active'          => true,
        ],
        [
            'name'               => 'notification-service',
            'client_id'          => 'notification_client',
            'client_secret_hash' => password_hash(env('SA_NOTIFICATION_SECRET', 'notification_secret_change_me'), PASSWORD_BCRYPT),
            'permissions'        => json_encode(['*']),
            'is_active'          => true,
        ],
        ];

        foreach ($accounts as $account) {
            ServiceAccount::firstOrCreate(
                ['client_id' => $account['client_id']],
                $account
            );
        }

        $this->command->info('Service accounts seeded.');
    }
}
