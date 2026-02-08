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
        // Drop user-related tables - user management is centralized
        Schema::dropIfExists('password_reset_tokens');
        Schema::dropIfExists('users');

        // Drop session table - sessions are stored in Redis
        Schema::dropIfExists('sessions');

        // Drop cache tables - cache is stored in Redis
        Schema::dropIfExists('cache');
        Schema::dropIfExists('cache_locks');

        // Drop job tables - jobs are queued in Redis
        Schema::dropIfExists('job_batches');
        Schema::dropIfExists('failed_jobs');
        Schema::dropIfExists('jobs');
    }

    /**
     * Reverse the migrations.
     */
    public function down(): void
    {
        // Not reversible - these tables should not exist in catalog microservice
        // User management is centralized, sessions/cache/jobs are in Redis
    }
};
