<?php

namespace App\Models;

use Illuminate\Database\Eloquent\Model;

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
