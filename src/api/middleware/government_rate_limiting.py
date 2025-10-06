# -*- coding: utf-8 -*-
"""
Middleware de rate limiting gubernamental para GRUPO_GAD.
Protección contra DoS y abuso en servicios ciudadanos.
"""

import time
from typing import Dict, Callable
from collections import defaultdict
from datetime import datetime

from fastapi import Request, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware


# Configuration for government rate limits
GOVERNMENT_RATE_LIMITS = {
    "citizen_services": 60,  # requests per minute for citizen APIs
    "general_api": 100,  # requests per minute for general API
    "websocket_handshake": 10,  # WebSocket connections per minute
    "admin_services": 200,  # requests per minute for admin
}


class GovernmentRateLimiter:
    """
    Simple in-memory rate limiter for government services.
    For production with multiple workers, use Redis-backed rate limiting.
    """
    
    def __init__(self):
        self.requests: Dict[str, list] = defaultdict(list)
        self.window_seconds = 60
    
    def is_rate_limited(self, client_id: str, limit: int) -> bool:
        """Check if client has exceeded rate limit."""
        now = time.time()
        window_start = now - self.window_seconds
        
        # Clean old requests
        if client_id in self.requests:
            self.requests[client_id] = [
                req_time for req_time in self.requests[client_id]
                if req_time > window_start
            ]
        
        # Check limit
        request_count = len(self.requests[client_id])
        
        if request_count >= limit:
            return True
        
        # Record this request
        self.requests[client_id].append(now)
        return False
    
    def get_retry_after(self, client_id: str) -> int:
        """Get seconds until rate limit resets."""
        if client_id not in self.requests or not self.requests[client_id]:
            return 0
        
        oldest_request = min(self.requests[client_id])
        window_end = oldest_request + self.window_seconds
        retry_after = int(window_end - time.time())
        
        return max(retry_after, 1)


# Global rate limiter instance
government_rate_limiter = GovernmentRateLimiter()


def get_government_client_id(request: Request) -> str:
    """
    Get unique client identifier for government services.
    Prioritizes real IP behind proxy for accurate tracking.
    """
    # Get IP from headers (behind proxy/load balancer)
    real_ip = (
        request.headers.get("X-Real-IP") or
        request.headers.get("X-Forwarded-For", "").split(",")[0].strip() or
        request.client.host if request.client else "unknown"
    )
    
    # For authenticated users, combine with user ID for better tracking
    if hasattr(request.state, "user") and request.state.user:
        user_id = getattr(request.state.user, "id", "unknown")
        return f"gov_user:{user_id}:{real_ip}"
    
    return f"gov_ip:{real_ip}"


def get_rate_limit_for_path(path: str) -> int:
    """Determine rate limit based on API path."""
    # Citizen services (most restrictive)
    if any(segment in path for segment in ["/servicios", "/ciudadano", "/tramites"]):
        return GOVERNMENT_RATE_LIMITS["citizen_services"]
    
    # WebSocket handshake (very restrictive)
    if "/ws/connect" in path:
        return GOVERNMENT_RATE_LIMITS["websocket_handshake"]
    
    # Admin endpoints (more permissive)
    if "/admin" in path or "/management" in path:
        return GOVERNMENT_RATE_LIMITS["admin_services"]
    
    # General API
    return GOVERNMENT_RATE_LIMITS["general_api"]


class GovernmentRateLimitMiddleware(BaseHTTPMiddleware):
    """
    Middleware for rate limiting government services.
    Applies different limits based on endpoint type and user status.
    """
    
    async def dispatch(self, request: Request, call_next: Callable):
        # Skip rate limiting for health checks and metrics
        if request.url.path in ["/health", "/health/live", "/health/ready", "/metrics"]:
            return await call_next(request)
        
        # Get client identifier
        client_id = get_government_client_id(request)
        
        # Determine rate limit for this path
        rate_limit = get_rate_limit_for_path(request.url.path)
        
        # Check rate limit
        if government_rate_limiter.is_rate_limited(client_id, rate_limit):
            retry_after = government_rate_limiter.get_retry_after(client_id)
            
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={
                    "error": "rate_limit_exceeded",
                    "message": "Ha excedido el límite de solicitudes para servicios gubernamentales.",
                    "details": "Los servicios digitales tienen límites para garantizar disponibilidad equitativa.",
                    "retry_after_seconds": retry_after,
                    "rate_limit": rate_limit,
                    "window_seconds": 60,
                    "government_service": "GRUPO_GAD",
                    "citizen_support": "Para asistencia, contacte soporte ciudadano.",
                    "timestamp": datetime.utcnow().isoformat()
                },
                headers={
                    "Retry-After": str(retry_after),
                    "X-RateLimit-Limit": str(rate_limit),
                    "X-RateLimit-Window": "60",
                    "X-RateLimit-Policy": "government_citizen_protection",
                    "X-Government-Service": "GRUPO_GAD"
                }
            )
        
        # Add rate limit info to response headers
        response = await call_next(request)
        
        # Add informational headers
        response.headers["X-RateLimit-Limit"] = str(rate_limit)
        response.headers["X-RateLimit-Window"] = "60"
        response.headers["X-Government-Service"] = "GRUPO_GAD"
        
        return response


def setup_government_rate_limiting(app):
    """
    Configure rate limiting for FastAPI application.
    Call this during app initialization.
    """
    app.add_middleware(GovernmentRateLimitMiddleware)
    return app
