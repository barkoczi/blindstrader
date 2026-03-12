<?php

namespace Database\Seeders;

use Illuminate\Database\Seeder;
use Stancl\Tenancy\Database\Models\Tenant;

class TenantSeeder extends Seeder
{
    /**
     * Seed a sample Brand tenant for local development.
     *
     * Tenant database (e.g. blindstrader_brand_louvolite) is
     * created dynamically by stancl/tenancy at runtime.
     */
    public function run(): void
    {
        if (Tenant::where('id', 'louvolite')->exists()) {
            $this->command->info('Tenant "Louvolite" already exists, skipping.');
            return;
        }

        Tenant::create([
            'id'   => 'louvolite',
            'name' => 'Louvolite',
        ]);

        $this->command->info('Sample tenant "Louvolite" created.');
    }
}
