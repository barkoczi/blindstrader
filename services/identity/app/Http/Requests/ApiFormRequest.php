<?php

namespace App\Http\Requests;

use Illuminate\Contracts\Validation\Validator;
use Illuminate\Foundation\Http\FormRequest;
use Illuminate\Http\Exceptions\HttpResponseException;

abstract class ApiFormRequest extends FormRequest
{
    /**
     * Always return JSON validation errors.
     */
    protected function failedValidation(Validator $validator): never
    {
        throw new HttpResponseException(
            response()->json([
                'message' => 'The given data was invalid.',
                'errors'  => $validator->errors(),
            ], 422)
        );
    }

    /**
     * Always return JSON authorization errors.
     */
    protected function failedAuthorization(): never
    {
        throw new HttpResponseException(
            response()->json([
                'message' => 'This action is unauthorized.',
            ], 403)
        );
    }
}
