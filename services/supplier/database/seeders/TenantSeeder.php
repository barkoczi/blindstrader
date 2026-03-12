<?php

namespace Database\Seeders;

use Illuminate\Database\Seeder;
use Stancl\Tenancy\Database\Models\Tenant;

class TenantSeeder extends Seeder
{
    /**
     * Seed a sample Supplier tenant for local development.
     *
     * Tenant database (e.g. blindstrader_supplier_cassidy) is
     * created dynamically by stancl/tenancy at runtime.
     */
    public function run(): void
    {
        if (Tenant::where('id', 'cassidy')->exists()) {
            $this->command->info('Tenant "Cassidy" already exists, skipping.');
            return;
        }

        Tenant::create([
            'id'   => 'cassidy',
            'name' => 'Cassidy',
        ]);

        $this->command->info('Sample tenant "Cassidy" created.');
    }
}
