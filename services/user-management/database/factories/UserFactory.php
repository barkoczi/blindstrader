<?php

namespace Database\Factories;

use Illuminate\Database\Eloquent\Factories\Factory;
use Illuminate\Support\Facades\Hash;
use Illuminate\Support\Str;

/**
 * @extends \Illuminate\Database\Eloquent\Factories\Factory<\App\Models\User>
 */
class UserFactory extends Factory
{
    /**
     * The current password being used by the factory.
     */
    protected static ?string $password;

    /**
     * Define the model's default state.
     *
     * @return array<string, mixed>
     */
    public function definition(): array
    {
        return [
            'first_name' => fake()->firstName(),
            'last_name' => fake()->lastName(),
            'middle_name' => fake()->boolean(30) ? fake()->firstName() : null,
            'email' => fake()->unique()->safeEmail(),
            'locale' => fake()->randomElement(['en', 'hu']),
            'is_admin' => false,
            'avatar_url' => fake()->boolean(50) ? fake()->imageUrl(200, 200, 'people') : null,
            'email_verified_at' => now(),
            'password' => static::$password ??= Hash::make('password'),
            'remember_token' => Str::random(10),
            'settings' => [
                'theme' => fake()->randomElement(['light', 'dark']),
                'notifications' => [
                    'email' => fake()->boolean(80),
                    'push' => fake()->boolean(50),
                ],
                'privacy' => [
                    'profile_visible' => fake()->boolean(90),
                ],
            ],
            'is_registered' => true,
        ];
    }

    /**
     * Indicate that the model's email address should be unverified.
     */
    public function unverified(): static
    {
        return $this->state(fn(array $attributes) => [
            'email_verified_at' => null,
        ]);
    }

    /**
     * Indicate that the user is an administrator.
     */
    public function admin(): static
    {
        return $this->state(fn(array $attributes) => [
            'is_admin' => true,
        ]);
    }

    /**
     * Indicate that the user has not completed registration.
     */
    public function unregistered(): static
    {
        return $this->state(fn(array $attributes) => [
            'is_registered' => false,
            'password' => null,
            'email_verified_at' => null,
        ]);
    }

    /**
     * Indicate that the user prefers Hungarian locale.
     */
    public function hungarian(): static
    {
        return $this->state(function (array $attributes) {
            // Common Hungarian names
            $hungarianFirstNames = ['János', 'István', 'László', 'Zoltán', 'Gábor', 'Péter', 'Katalin', 'Éva', 'Anna', 'Mária'];
            $hungarianLastNames = ['Nagy', 'Kovács', 'Tóth', 'Szabó', 'Horváth', 'Varga', 'Kiss', 'Molnár', 'Németh', 'Farkas'];

            return [
                'first_name' => fake()->randomElement($hungarianFirstNames),
                'last_name' => fake()->randomElement($hungarianLastNames),
                'locale' => 'hu',
            ];
        });
    }

    /**
     * Indicate that the user prefers English locale.
     */
    public function english(): static
    {
        return $this->state(fn(array $attributes) => [
            'locale' => 'en',
        ]);
    }
}
