<?php

namespace App\Http\Resources;

use Illuminate\Http\Request;
use Illuminate\Http\Resources\Json\JsonResource;

abstract class ApiResource extends JsonResource
{
    /**
     * Wrap the resource in a consistent envelope.
     */
    public static $wrap = 'data';
}
