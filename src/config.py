"""
Configuration settings for LearnFlow
Uses pydantic-settings for environment variable management
"""
from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, validator


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables
    """
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"
    )

    # Application
    APP_NAME: str = "LearnFlow"
    VERSION: str = "1.0.0"
    DEBUG: bool = False
    ENV: str = "production"  # development, staging, production

    # API
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    CORS_ORIGINS: List[str] = ["*"]
    RATE_LIMIT_PER_MINUTE: int = 100

    # Security
    JWT_SECRET: str = Field(..., min_length=32)
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = 30
    BCRYPT_ROUNDS: int = 12

    # Database
    DATABASE_URL: str = Field(
        ...,
        description="PostgreSQL connection URL"
    )
    DATABASE_POOL_SIZE: int = 10
    DATABASE_MAX_OVERFLOW: int = 20
    DATABASE_POOL_PRE_PING: bool = True

    # Anthropic AI
    ANTHROPIC_API_KEY: str = Field(..., description="Anthropic API key for Claude")
    ANTHROPIC_MODEL_SONNET: str = "claude-sonnet-4-5"
    ANTHROPIC_MODEL_HAIKU: str = "claude-haiku-4"
    ANTHROPIC_MAX_TOKENS: int = 4096
    ANTHROPIC_TIMEOUT_SECONDS: int = 30

    # Dapr
    DAPR_HTTP_PORT: int = 3500
    DAPR_GRPC_PORT: int = 50001
    DAPR_PUBSUB_NAME: str = "kafka-pubsub"
    DAPR_STATE_STORE_NAME: str = "postgres-state"

    # Kafka Topics
    KAFKA_TOPIC_STUDENT_ACTIVITY: str = "student-activity"
    KAFKA_TOPIC_MASTERY_UPDATES: str = "mastery-updates"
    KAFKA_TOPIC_STRUGGLE_ALERTS: str = "struggle-alerts"
    KAFKA_BROKERS: str = "kafka.learnflow.svc:9092"

    # Code Execution Sandbox
    SANDBOX_TIMEOUT_SECONDS: int = 5
    SANDBOX_MEMORY_LIMIT_MB: int = 50
    SANDBOX_CPU_LIMIT: float = 0.5
    SANDBOX_IMAGE: str = "python:3.11-slim"
    SANDBOX_NETWORK_DISABLED: bool = True
    SANDBOX_ALLOWED_MODULES: List[str] = [
        "builtins", "math", "random", "datetime",
        "json", "re", "itertools", "collections"
    ]

    # Mastery Calculation Weights
    MASTERY_WEIGHT_EXERCISE_COMPLETION: float = 0.40
    MASTERY_WEIGHT_QUIZ_SCORE: float = 0.30
    MASTERY_WEIGHT_CODE_QUALITY: float = 0.20
    MASTERY_WEIGHT_CONSISTENCY: float = 0.10

    # Struggle Detection Thresholds
    STRUGGLE_REPEATED_ERROR_COUNT: int = 3
    STRUGGLE_STUCK_MINUTES: int = 10
    STRUGGLE_QUIZ_THRESHOLD_PERCENT: float = 50.0
    STRUGGLE_FAILED_EXECUTIONS: int = 5
    STRUGGLE_CONFUSION_SIGNALS: List[str] = [
        "I don't understand",
        "I'm stuck",
        "I'm confused",
        "This doesn't make sense",
        "Help"
    ]

    # MCP Server
    MCP_SERVER_HOST: str = "0.0.0.0"
    MCP_SERVER_PORT: int = 8765
    MCP_SERVER_ENABLED: bool = True

    # WebSocket
    WEBSOCKET_MAX_CONNECTIONS: int = 1000
    WEBSOCKET_HEARTBEAT_SECONDS: int = 30

    # Monitoring
    PROMETHEUS_ENABLED: bool = True
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "json"  # json or text

    # Redis (Future)
    REDIS_URL: str = "redis://redis.learnflow.svc:6379/0"
    REDIS_ENABLED: bool = False

    @validator("CORS_ORIGINS", pre=True)
    def parse_cors_origins(cls, v):
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",")]
        return v

    @validator("SANDBOX_ALLOWED_MODULES", pre=True)
    def parse_allowed_modules(cls, v):
        if isinstance(v, str):
            return [module.strip() for module in v.split(",")]
        return v

    @validator("STRUGGLE_CONFUSION_SIGNALS", pre=True)
    def parse_confusion_signals(cls, v):
        if isinstance(v, str):
            return [signal.strip() for signal in v.split(",")]
        return v

    @property
    def database_url_async(self) -> str:
        """Convert sync database URL to async (asyncpg)"""
        return self.DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://")

    @property
    def mastery_weights(self) -> dict:
        """Return mastery calculation weights as dict"""
        return {
            "exercise_completion": self.MASTERY_WEIGHT_EXERCISE_COMPLETION,
            "quiz_score": self.MASTERY_WEIGHT_QUIZ_SCORE,
            "code_quality": self.MASTERY_WEIGHT_CODE_QUALITY,
            "consistency": self.MASTERY_WEIGHT_CONSISTENCY
        }

    @property
    def struggle_thresholds(self) -> dict:
        """Return struggle detection thresholds as dict"""
        return {
            "repeated_error_count": self.STRUGGLE_REPEATED_ERROR_COUNT,
            "stuck_minutes": self.STRUGGLE_STUCK_MINUTES,
            "quiz_threshold_percent": self.STRUGGLE_QUIZ_THRESHOLD_PERCENT,
            "failed_executions": self.STRUGGLE_FAILED_EXECUTIONS,
            "confusion_signals": self.STRUGGLE_CONFUSION_SIGNALS
        }


# Create global settings instance
settings = Settings()
