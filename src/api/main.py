"""
LearnFlow API Gateway
Main FastAPI application with WebSocket support, Dapr integration, and AI agents
"""
import logging
import structlog
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse
from prometheus_client import make_asgi_app, Counter, Histogram
import uvicorn

from src.api.routers import auth, students, teachers, chat, code, exercises, quizzes, progress
from src.api.middleware import AuthMiddleware, RateLimitMiddleware, RequestLoggingMiddleware
from src.api.dependencies import get_db, get_dapr_client
from src.models.database import engine, Base
from src.config import settings

# Configure structured logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer()
    ],
    wrapper_class=structlog.stdlib.BoundLogger,
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger()

# Prometheus metrics
REQUEST_COUNT = Counter(
    'learnflow_api_requests_total',
    'Total API requests',
    ['method', 'endpoint', 'status']
)

REQUEST_DURATION = Histogram(
    'learnflow_api_request_duration_seconds',
    'API request duration',
    ['method', 'endpoint']
)

WEBSOCKET_CONNECTIONS = Counter(
    'learnflow_websocket_connections_total',
    'Total WebSocket connections',
    ['status']
)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator:
    """
    Application lifespan events
    """
    # Startup
    logger.info("Starting LearnFlow API Gateway", version=settings.VERSION)

    # Create database tables (in production, use migrations)
    # Base.metadata.create_all(bind=engine)

    # Initialize Dapr client
    logger.info("Initializing Dapr client",
                pubsub_name=settings.DAPR_PUBSUB_NAME,
                state_store=settings.DAPR_STATE_STORE_NAME)

    # Verify Anthropic API key
    try:
        import anthropic
        client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)
        logger.info("Anthropic client initialized successfully")
    except Exception as e:
        logger.error("Failed to initialize Anthropic client", error=str(e))
        raise

    logger.info("LearnFlow API Gateway started successfully")

    yield

    # Shutdown
    logger.info("Shutting down LearnFlow API Gateway")
    # Close database connections
    # await database.disconnect()


# Create FastAPI application
app = FastAPI(
    title="LearnFlow API",
    description="AI-powered Python tutoring platform with multi-agent architecture",
    version=settings.VERSION,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan
)

# Add middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(GZipMiddleware, minimum_size=1000)
app.add_middleware(RequestLoggingMiddleware)
app.add_middleware(RateLimitMiddleware, requests_per_minute=settings.RATE_LIMIT_PER_MINUTE)
# AuthMiddleware should be added to specific routers that need authentication

# Include routers
app.include_router(auth.router, prefix="/api/v1/auth", tags=["Authentication"])
app.include_router(students.router, prefix="/api/v1/students", tags=["Students"])
app.include_router(teachers.router, prefix="/api/v1/teachers", tags=["Teachers"])
app.include_router(chat.router, prefix="/api/v1/chat", tags=["Chat"])
app.include_router(code.router, prefix="/api/v1/code", tags=["Code Execution"])
app.include_router(exercises.router, prefix="/api/v1/exercises", tags=["Exercises"])
app.include_router(quizzes.router, prefix="/api/v1/quizzes", tags=["Quizzes"])
app.include_router(progress.router, prefix="/api/v1/progress", tags=["Progress"])

# Mount Prometheus metrics
metrics_app = make_asgi_app()
app.mount("/metrics", metrics_app)


@app.get("/", tags=["Root"])
async def root():
    """Root endpoint"""
    return {
        "service": "LearnFlow API Gateway",
        "version": settings.VERSION,
        "status": "running",
        "docs": "/docs",
        "health": "/health"
    }


@app.get("/health", tags=["Health"])
async def health_check():
    """
    Health check endpoint for Kubernetes probes
    """
    return {
        "status": "healthy",
        "service": "learnflow-api",
        "version": settings.VERSION
    }


@app.get("/health/live", tags=["Health"])
async def liveness():
    """
    Liveness probe - checks if application is running
    """
    return {"status": "alive"}


@app.get("/health/ready", tags=["Health"])
async def readiness():
    """
    Readiness probe - checks if application is ready to serve traffic
    """
    # Check database connection
    try:
        from src.models.database import SessionLocal
        db = SessionLocal()
        db.execute("SELECT 1")
        db.close()
        db_status = "connected"
    except Exception as e:
        logger.error("Database connection failed", error=str(e))
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={"status": "not_ready", "reason": "database_unavailable"}
        )

    # Check Dapr sidecar
    try:
        import httpx
        response = httpx.get(f"http://localhost:{settings.DAPR_HTTP_PORT}/v1.0/healthz", timeout=2.0)
        dapr_status = "ready" if response.status_code == 200 else "not_ready"
    except Exception as e:
        logger.error("Dapr sidecar not responding", error=str(e))
        dapr_status = "not_ready"

    if dapr_status != "ready":
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={"status": "not_ready", "reason": "dapr_unavailable"}
        )

    return {
        "status": "ready",
        "database": db_status,
        "dapr": dapr_status
    }


@app.get("/health/startup", tags=["Health"])
async def startup():
    """
    Startup probe - checks if application has finished starting
    """
    # In production, this would check if all initialization is complete
    return {"status": "started"}


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """
    Global exception handler
    """
    logger.error(
        "Unhandled exception",
        path=request.url.path,
        method=request.method,
        error=str(exc),
        exc_info=True
    )

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "detail": "Internal server error",
            "error_id": "See logs for details"
        }
    )


@app.middleware("http")
async def add_correlation_id(request: Request, call_next):
    """
    Add correlation ID to all requests for distributed tracing
    """
    import uuid
    correlation_id = request.headers.get("X-Correlation-ID", str(uuid.uuid4()))

    # Add to structlog context
    structlog.contextvars.bind_contextvars(correlation_id=correlation_id)

    response = await call_next(request)
    response.headers["X-Correlation-ID"] = correlation_id

    return response


@app.middleware("http")
async def metrics_middleware(request: Request, call_next):
    """
    Record Prometheus metrics for all requests
    """
    import time

    method = request.method
    path = request.url.path

    # Record request duration
    start_time = time.time()
    response = await call_next(request)
    duration = time.time() - start_time

    # Update metrics
    REQUEST_COUNT.labels(method=method, endpoint=path, status=response.status_code).inc()
    REQUEST_DURATION.labels(method=method, endpoint=path).observe(duration)

    return response


if __name__ == "__main__":
    # For local development
    uvicorn.run(
        "src.api.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
