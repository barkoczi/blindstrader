<?php

namespace Database\Seeders;

use Illuminate\Database\Seeder;
use Stancl\Tenancy\Database\Models\Tenant;

class TenantSeeder extends Seeder
{
    /**
     * Seed a sample Retailer tenant for local development.
     *
     * Tenant database (e.g. blindstrader_retailer_newblinds) is
     * created dynamically by stancl/tenancy at runtime.
     */
    public function run(): void
    {
        if (Tenant::where('id', 'newblinds')->exists()) {
            $this->command->info('Tenant "Newblinds" already exists, skipping.');
            return;
        }

        Tenant::create([
            'id'   => 'newblinds',
            'name' => 'Newblinds',
        ]);

        $this->command->info('Sample tenant "Newblinds" created.');
    }
}
