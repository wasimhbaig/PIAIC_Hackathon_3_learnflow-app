"""
Custom middleware for authentication, rate limiting, and logging
"""
import time
import structlog
from typing import Callable
from collections import defaultdict
from datetime import datetime, timedelta

from fastapi import Request, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from jose import jwt, JWTError

from src.config import settings

logger = structlog.get_logger()


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """
    Log all incoming requests with structured logging
    """

    async def dispatch(self, request: Request, call_next: Callable):
        start_time = time.time()

        # Log request
        logger.info(
            "Incoming request",
            method=request.method,
            path=request.url.path,
            client_ip=request.client.host if request.client else "unknown"
        )

        # Process request
        response = await call_next(request)

        # Log response
        duration = time.time() - start_time
        logger.info(
            "Request completed",
            method=request.method,
            path=request.url.path,
            status_code=response.status_code,
            duration_seconds=round(duration, 3)
        )

        return response


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Rate limiting middleware to prevent API abuse
    Uses sliding window algorithm
    """

    def __init__(self, app, requests_per_minute: int = 100):
        super().__init__(app)
        self.requests_per_minute = requests_per_minute
        self.requests = defaultdict(list)

    async def dispatch(self, request: Request, call_next: Callable):
        # Get client IP
        client_ip = request.client.host if request.client else "unknown"

        # Skip rate limiting for health checks
        if request.url.path.startswith("/health"):
            return await call_next(request)

        # Check rate limit
        now = datetime.utcnow()
        cutoff = now - timedelta(minutes=1)

        # Remove old requests
        self.requests[client_ip] = [
            req_time for req_time in self.requests[client_ip]
            if req_time > cutoff
        ]

        # Check if rate limit exceeded
        if len(self.requests[client_ip]) >= self.requests_per_minute:
            logger.warning(
                "Rate limit exceeded",
                client_ip=client_ip,
                requests_count=len(self.requests[client_ip])
            )
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={
                    "detail": "Rate limit exceeded. Please try again later.",
                    "retry_after_seconds": 60
                },
                headers={"Retry-After": "60"}
            )

        # Add current request
        self.requests[client_ip].append(now)

        # Process request
        response = await call_next(request)

        # Add rate limit headers
        remaining = self.requests_per_minute - len(self.requests[client_ip])
        response.headers["X-RateLimit-Limit"] = str(self.requests_per_minute)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        response.headers["X-RateLimit-Reset"] = str(int((now + timedelta(minutes=1)).timestamp()))

        return response


class AuthMiddleware(BaseHTTPMiddleware):
    """
    JWT authentication middleware
    Validates JWT tokens and adds user info to request state
    """

    async def dispatch(self, request: Request, call_next: Callable):
        # Skip authentication for public endpoints
        public_paths = [
            "/",
            "/docs",
            "/redoc",
            "/openapi.json",
            "/health",
            "/health/live",
            "/health/ready",
            "/health/startup",
            "/metrics",
            "/api/v1/auth/login",
            "/api/v1/auth/register"
        ]

        if request.url.path in public_paths or request.url.path.startswith("/docs"):
            return await call_next(request)

        # Get authorization header
        auth_header = request.headers.get("Authorization")

        if not auth_header or not auth_header.startswith("Bearer "):
            logger.warning("Missing or invalid authorization header", path=request.url.path)
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={"detail": "Missing or invalid authorization header"},
                headers={"WWW-Authenticate": "Bearer"}
            )

        # Extract token
        token = auth_header.replace("Bearer ", "")

        try:
            # Verify and decode JWT token
            payload = jwt.decode(
                token,
                settings.JWT_SECRET,
                algorithms=[settings.JWT_ALGORITHM]
            )

            # Add user info to request state
            request.state.user_id = payload.get("sub")
            request.state.user_role = payload.get("role")
            request.state.user_email = payload.get("email")

            logger.debug(
                "User authenticated",
                user_id=request.state.user_id,
                role=request.state.user_role
            )

        except JWTError as e:
            logger.warning("Invalid JWT token", error=str(e))
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={"detail": "Invalid authentication token"},
                headers={"WWW-Authenticate": "Bearer"}
            )

        # Process request
        response = await call_next(request)
        return response


def require_role(allowed_roles: list):
    """
    Dependency to check if user has required role
    Usage: dependencies=[Depends(require_role(["student", "teacher"]))]
    """
    async def role_checker(request: Request):
        if not hasattr(request.state, "user_role"):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication required"
            )

        if request.state.user_role not in allowed_roles:
            logger.warning(
                "Insufficient permissions",
                user_role=request.state.user_role,
                required_roles=allowed_roles
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient permissions. Required roles: {', '.join(allowed_roles)}"
            )

        return request.state

    return role_checker
