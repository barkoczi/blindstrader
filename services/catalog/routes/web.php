<?php

use Illuminate\Support\Facades\Route;

Route::get('/', function () {
    return 'Hello from catalog';
});

Route::get('/session/set', function () {
    session(['test_value' => 'set from catalog']);
    return 'Session set in catalog: ' . session('test_value');
});

Route::get('/session/get', function () {
    return 'Session value in catalog: ' . (session('test_value') ?? 'not set');
});

Route::get('/debug', function () {
    return json_encode([
        'session_id' => session()->getId(),
        'session_data' => session()->all(),
        'cookie_name' => config('session.cookie'),
        'driver' => config('session.driver'),
    ]);
});
