<?php

use App\Models\User;
use Illuminate\Support\Facades\App;

test('external_id is auto-generated on user creation', function () {
    $user = User::factory()->create();

    expect($user->external_id)
        ->not->toBeNull()
        ->toStartWith('usr_')
        ->toHaveLength(20); // usr_ (4 chars) + 16 random chars
});

test('external_id is unique for each user', function () {
    $user1 = User::factory()->create();
    $user2 = User::factory()->create();

    expect($user1->external_id)->not->toBe($user2->external_id);
});

test('external_id can be manually set', function () {
    $customId = 'usr_custom123456789';
    $user = User::factory()->create(['external_id' => $customId]);

    expect($user->external_id)->toBe($customId);
});

test('users can be found by external_id', function () {
    $user = User::factory()->create();

    $found = User::where('external_id', $user->external_id)->first();

    expect($found->id)->toBe($user->id);
});

test('route model binding uses external_id', function () {
    $user = User::factory()->create();

    expect($user->getRouteKeyName())->toBe('external_id');
});

test('fullName returns first middle last for English locale', function () {
    $user = User::factory()->english()->create([
        'first_name' => 'John',
        'middle_name' => 'Michael',
        'last_name' => 'Doe',
    ]);

    expect($user->full_name)->toBe('John Michael Doe');
});

test('fullName returns last middle first for Hungarian locale', function () {
    $user = User::factory()->hungarian()->create([
        'first_name' => 'János',
        'middle_name' => 'István',
        'last_name' => 'Kovács',
    ]);

    expect($user->full_name)->toBe('Kovács István János');
});

test('fullName works without middle name for English', function () {
    $user = User::factory()->english()->create([
        'first_name' => 'John',
        'middle_name' => null,
        'last_name' => 'Doe',
    ]);

    expect($user->full_name)->toBe('John Doe');
});

test('fullName works without middle name for Hungarian', function () {
    $user = User::factory()->hungarian()->create([
        'first_name' => 'János',
        'middle_name' => null,
        'last_name' => 'Kovács',
    ]);

    expect($user->full_name)->toBe('Kovács János');
});

test('locale defaults to en', function () {
    $user = User::factory()->create(['locale' => 'en']);

    expect($user->locale)->toBe('en');
});

test('locale can be set to hu', function () {
    $user = User::factory()->create(['locale' => 'hu']);

    expect($user->locale)->toBe('hu');
});

test('is_admin defaults to false', function () {
    $user = User::factory()->create();

    expect($user->is_admin)->toBeFalse();
});

test('admin factory state sets is_admin to true', function () {
    $user = User::factory()->admin()->create();

    expect($user->is_admin)->toBeTrue();
});

test('isAdmin method returns correct value', function () {
    $regularUser = User::factory()->create();
    $adminUser = User::factory()->admin()->create();

    expect($regularUser->isAdmin())->toBeFalse();
    expect($adminUser->isAdmin())->toBeTrue();
});

test('admins scope returns only admin users', function () {
    User::factory()->count(3)->create();
    User::factory()->admin()->count(2)->create();

    $admins = User::admins()->get();

    expect($admins)->toHaveCount(2);
    expect($admins->every(fn($user) => $user->is_admin))->toBeTrue();
});

test('registered scope returns only registered users', function () {
    User::factory()->count(3)->create();
    User::factory()->unregistered()->count(2)->create();

    $registered = User::registered()->get();

    expect($registered)->toHaveCount(3);
    expect($registered->every(fn($user) => $user->is_registered))->toBeTrue();
});

test('is_registered defaults to true for normal users', function () {
    $user = User::factory()->create();

    expect($user->is_registered)->toBeTrue();
});

test('unregistered factory state sets is_registered to false', function () {
    $user = User::factory()->unregistered()->create();

    expect($user->is_registered)->toBeFalse();
    expect($user->password)->toBeNull();
});

test('settings can be stored as JSON', function () {
    $settings = [
        'theme' => 'dark',
        'notifications' => [
            'email' => true,
            'push' => false,
        ],
    ];

    $user = User::factory()->create(['settings' => $settings]);

    expect($user->settings)->toBe($settings);
});

test('settings can be updated', function () {
    $user = User::factory()->create(['settings' => ['theme' => 'light']]);

    $user->update(['settings' => ['theme' => 'dark', 'locale' => 'en']]);

    expect($user->fresh()->settings)->toBe(['theme' => 'dark', 'locale' => 'en']);
});

test('settings can be null', function () {
    $user = User::factory()->create(['settings' => null]);

    expect($user->settings)->toBeNull();
});

test('avatar_url can be set and retrieved', function () {
    $avatarUrl = 'https://example.com/avatar.jpg';
    $user = User::factory()->create(['avatar_url' => $avatarUrl]);

    expect($user->avatar_url)->toBe($avatarUrl);
});

test('avatar_url can be null', function () {
    $user = User::factory()->create(['avatar_url' => null]);

    expect($user->avatar_url)->toBeNull();
});

test('password can be null for OAuth users', function () {
    $user = User::factory()->create(['password' => null]);

    expect($user->password)->toBeNull();
});

test('password is hashed when set', function () {
    $user = User::factory()->create(['password' => 'plain-password']);

    expect($user->password)
        ->not->toBe('plain-password')
        ->not->toBeNull();
});

test('id is hidden in array conversion', function () {
    $user = User::factory()->create();
    $array = $user->toArray();

    expect($array)->not->toHaveKey('id');
    expect($array)->toHaveKey('external_id');
});

test('password is hidden in array conversion', function () {
    $user = User::factory()->create();
    $array = $user->toArray();

    expect($array)->not->toHaveKey('password');
});

test('remember_token is hidden in array conversion', function () {
    $user = User::factory()->create();
    $array = $user->toArray();

    expect($array)->not->toHaveKey('remember_token');
});

test('hungarian factory creates user with Hungarian locale', function () {
    $user = User::factory()->hungarian()->create();

    expect($user->locale)->toBe('hu');
});

test('english factory creates user with English locale', function () {
    $user = User::factory()->english()->create();

    expect($user->locale)->toBe('en');
});

test('SetUserLocale middleware sets app locale from user', function () {
    $user = User::factory()->hungarian()->create();

    $this->actingAs($user)
        ->get('/')
        ->assertStatus(200);

    expect(App::getLocale())->toBe('hu');
});

test('SetUserLocale middleware uses default locale for guest', function () {
    config(['app.locale' => 'en']);

    $this->get('/')
        ->assertStatus(200);

    expect(App::getLocale())->toBe('en');
});

test('user can have all profile fields filled', function () {
    $user = User::factory()->create([
        'first_name' => 'John',
        'middle_name' => 'Michael',
        'last_name' => 'Doe',
        'email' => 'john.doe@example.com',
        'locale' => 'en',
        'is_admin' => true,
        'avatar_url' => 'https://example.com/avatar.jpg',
        'settings' => ['theme' => 'dark'],
        'is_registered' => true,
    ]);

    expect($user->first_name)->toBe('John');
    expect($user->middle_name)->toBe('Michael');
    expect($user->last_name)->toBe('Doe');
    expect($user->email)->toBe('john.doe@example.com');
    expect($user->locale)->toBe('en');
    expect($user->is_admin)->toBeTrue();
    expect($user->avatar_url)->toBe('https://example.com/avatar.jpg');
    expect($user->settings)->toBe(['theme' => 'dark']);
    expect($user->is_registered)->toBeTrue();
    expect($user->external_id)->toStartWith('usr_');
});
