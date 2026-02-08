<?php

namespace App\Models;

// use Illuminate\Contracts\Auth\MustVerifyEmail;
use Illuminate\Database\Eloquent\Casts\Attribute;
use Illuminate\Database\Eloquent\Factories\HasFactory;
use Illuminate\Foundation\Auth\User as Authenticatable;
use Illuminate\Notifications\Notifiable;
use Illuminate\Support\Str;

class User extends Authenticatable
{
    /** @use HasFactory<\Database\Factories\UserFactory> */
    use HasFactory, Notifiable;

    /**
     * The attributes that are mass assignable.
     *
     * @var list<string>
     */
    protected $fillable = [
        'external_id',
        'first_name',
        'last_name',
        'middle_name',
        'email',
        'locale',
        'is_admin',
        'avatar_url',
        'password',
        'settings',
        'is_registered',
    ];

    /**
     * The attributes that should be hidden for serialization.
     *
     * @var list<string>
     */
    protected $hidden = [
        'id',
        'password',
        'remember_token',
    ];

    /**
     * Get the attributes that should be cast.
     *
     * @return array<string, string>
     */
    protected function casts(): array
    {
        return [
            'email_verified_at' => 'datetime',
            'password' => 'hashed',
            'settings' => 'array',
            'is_admin' => 'boolean',
            'is_registered' => 'boolean',
        ];
    }

    /**
     * Get the route key name for Laravel.
     */
    public function getRouteKeyName(): string
    {
        return 'external_id';
    }

    /**
     * Boot the model.
     */
    protected static function boot(): void
    {
        parent::boot();

        // Auto-generate external_id on creation
        static::creating(function ($user) {
            if (empty($user->external_id)) {
                $user->external_id = 'usr_' . Str::random(16);
            }
        });
    }

    /**
     * Get the user's full name formatted according to their locale.
     * English (en): First Middle Last
     * Hungarian (hu): Last Middle First
     */
    protected function fullName(): Attribute
    {
        return Attribute::make(
            get: function () {
                $parts = array_filter([
                    $this->locale === 'hu' ? $this->last_name : $this->first_name,
                    $this->middle_name,
                    $this->locale === 'hu' ? $this->first_name : $this->last_name,
                ]);

                return implode(' ', $parts);
            }
        );
    }

    /**
     * Check if the user is an admin.
     */
    public function isAdmin(): bool
    {
        return $this->is_admin;
    }

    /**
     * Scope a query to only include admin users.
     */
    public function scopeAdmins($query)
    {
        return $query->where('is_admin', true);
    }

    /**
     * Scope a query to only include registered users.
     */
    public function scopeRegistered($query)
    {
        return $query->where('is_registered', true);
    }
}
