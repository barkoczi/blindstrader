<?php

use Illuminate\Database\Migrations\Migration;
use Illuminate\Database\Schema\Blueprint;
use Illuminate\Support\Facades\Schema;

return new class extends Migration
{
    /**
     * Run the migrations.
     */
    public function up(): void
    {
        Schema::table('users', function (Blueprint $table) {
            // Add external ID for public-facing URLs (Stripe-style: usr_xxxxx)
            $table->string('external_id', 20)->unique()->after('id');
            $table->index('external_id');

            // Split name into components
            $table->string('first_name')->after('external_id');
            $table->string('last_name')->after('first_name');
            $table->string('middle_name')->nullable()->after('last_name');

            // Remove old name column
            $table->dropColumn('name');

            // Add locale for internationalization (en = English, hu = Hungarian)
            $table->enum('locale', ['en', 'hu'])->default('en')->after('email');

            // Add admin flag
            $table->boolean('is_admin')->default(false)->after('locale');

            // Add avatar URL
            $table->string('avatar_url')->nullable()->after('is_admin');

            // Make password nullable for OAuth users
            $table->string('password')->nullable()->change();

            // Add settings as JSON for flexible user preferences
            $table->json('settings')->nullable()->after('remember_token');

            // Add registration flag
            $table->boolean('is_registered')->default(false)->after('settings');
        });
    }

    /**
     * Reverse the migrations.
     */
    public function down(): void
    {
        Schema::table('users', function (Blueprint $table) {
            // Add back old name column
            $table->string('name')->after('id');

            // Remove new columns
            $table->dropIndex(['external_id']);
            $table->dropColumn([
                'external_id',
                'first_name',
                'last_name',
                'middle_name',
                'locale',
                'is_admin',
                'avatar_url',
                'settings',
                'is_registered',
            ]);

            // Make password required again
            $table->string('password')->nullable(false)->change();
        });
    }
};
