<?php

namespace Database\Seeders;

use App\Models\User;
use Illuminate\Database\Seeder;

class DatabaseSeeder extends Seeder
{
    /**
     * Seed the application's database.
     */
    public function run(): void
    {
        // Create admin user
        User::factory()->admin()->english()->create([
            'first_name' => 'Admin',
            'last_name' => 'User',
            'email' => 'admin@example.com',
        ]);

        // Create regular test user
        User::factory()->english()->create([
            'first_name' => 'Test',
            'last_name' => 'User',
            'email' => 'test@example.com',
        ]);

        // Create Hungarian test user
        User::factory()->hungarian()->create([
            'first_name' => 'János',
            'last_name' => 'Kovács',
            'email' => 'janos.kovacs@example.com',
        ]);

        // Create Hungarian admin
        User::factory()->hungarian()->admin()->create([
            'first_name' => 'Katalin',
            'last_name' => 'Nagy',
            'email' => 'katalin.nagy@example.com',
        ]);

        // Create unregistered user (OAuth flow not completed)
        User::factory()->unregistered()->create([
            'first_name' => 'Pending',
            'last_name' => 'Registration',
            'email' => 'pending@example.com',
        ]);

        // Create random users (5 English, 5 Hungarian)
        User::factory(5)->english()->create();
        User::factory(5)->hungarian()->create();

        // Create some unverified users
        User::factory(2)->unverified()->create();
    }
}
