<?php

use Illuminate\Support\Facades\Route;

Route::get('/', function () {
    return 'Hello from user management';
});

Route::get('/session/set', function () {
    session(['test_value' => 'set from auth']);
    return 'Session set in auth: ' . session('test_value');
});

Route::get('/session/get', function () {
    return 'Session value in auth: ' . (session('test_value') ?? 'not set');
});

Route::get('/debug', function () {
    return json_encode([
        'session_id' => session()->getId(),
        'session_data' => session()->all(),
        'cookie_name' => config('session.cookie'),
        'driver' => config('session.driver'),
    ]);
});
