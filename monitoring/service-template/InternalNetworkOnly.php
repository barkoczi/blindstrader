<?php

namespace App\Http\Middleware;

use Closure;
use Illuminate\Http\Request;
use Symfony\Component\HttpFoundation\Response;

/**
 * Middleware to restrict access to internal network only.
 * Used for /metrics endpoint to prevent external access.
 */
class InternalNetworkOnly
{
    /**
     * Handle an incoming request.
     */
    public function handle(Request $request, Closure $next): Response
    {
        $remoteAddr = $request->server('REMOTE_ADDR');
        
        // Allow requests from internal Docker networks
        if ($this->isInternalIP($remoteAddr)) {
            return $next($request);
        }
        
        // Allow if no X-Forwarded-For header (direct container access)
        if (!$request->header('X-Forwarded-For')) {
            return $next($request);
        }
        
        // Deny all other requests
        abort(403, 'Access denied: Metrics endpoint is internal only');
    }
    
    /**
     * Check if IP is from internal network.
     */
    private function isInternalIP(string $ip): bool
    {
        // Docker internal networks
        $internalRanges = [
            '10.0.0.0/8',
            '172.16.0.0/12',
            '192.168.0.0/16',
            '127.0.0.0/8',
            '::1/128',
        ];
        
        foreach ($internalRanges as $range) {
            if ($this->ipInRange($ip, $range)) {
                return true;
            }
        }
        
        return false;
    }
    
    /**
     * Check if IP is in CIDR range.
     */
    private function ipInRange(string $ip, string $range): bool
    {
        if (strpos($range, '/') === false) {
            return $ip === $range;
        }
        
        [$subnet, $mask] = explode('/', $range);
        
        // IPv6
        if (strpos($ip, ':') !== false) {
            return $this->ipv6InRange($ip, $subnet, (int) $mask);
        }
        
        // IPv4
        $ipLong = ip2long($ip);
        $subnetLong = ip2long($subnet);
        $maskLong = -1 << (32 - (int) $mask);
        
        return ($ipLong & $maskLong) === ($subnetLong & $maskLong);
    }
    
    /**
     * Check if IPv6 is in range.
     */
    private function ipv6InRange(string $ip, string $subnet, int $mask): bool
    {
        $ipBin = inet_pton($ip);
        $subnetBin = inet_pton($subnet);
        
        if ($ipBin === false || $subnetBin === false) {
            return false;
        }
        
        $ipBits = unpack('C*', $ipBin);
        $subnetBits = unpack('C*', $subnetBin);
        
        for ($i = 1; $i <= 16; $i++) {
            $bits = min($mask, 8);
            $maskByte = (0xFF << (8 - $bits)) & 0xFF;
            
            if (($ipBits[$i] & $maskByte) !== ($subnetBits[$i] & $maskByte)) {
                return false;
            }
            
            $mask -= 8;
            if ($mask <= 0) {
                break;
            }
        }
        
        return true;
    }
}
