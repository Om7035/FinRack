"""Application configuration using Pydantic Settings"""

from typing import List, Optional
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
import json


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )

    # Application
    APP_NAME: str = "FinRack"
    APP_VERSION: str = "1.0.0"
    APP_ENV: str = "development"
    DEBUG: bool = True
    LOG_LEVEL: str = "INFO"

    # Database
    DATABASE_URL: str = Field(
        default="postgresql://postgres:postgres@localhost:5432/finrack"
    )
    DATABASE_POOL_SIZE: int = 20
    DATABASE_MAX_OVERFLOW: int = 0

    # Redis
    REDIS_URL: str = "redis://localhost:6379"
    REDIS_MAX_CONNECTIONS: int = 50

    # RabbitMQ & Celery
    RABBITMQ_URL: str = "amqp://admin:admin@localhost:5672/"
    CELERY_BROKER_URL: str = "amqp://admin:admin@localhost:5672/"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/0"

    # MinIO/S3
    MINIO_ENDPOINT: str = "localhost:9000"
    MINIO_ACCESS_KEY: str = "minioadmin"
    MINIO_SECRET_KEY: str = "minioadmin"
    MINIO_BUCKET_NAME: str = "finrack-receipts"
    MINIO_SECURE: bool = False

    # JWT
    JWT_SECRET_KEY: str = Field(
        default="your-super-secret-jwt-key-change-this-in-production"
    )
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # Security
    SECRET_KEY: str = Field(
        default="your-super-secret-key-change-this-in-production"
    )
    BACKEND_CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:8000"
    ]

    @field_validator("BACKEND_CORS_ORIGINS", mode="before")
    @classmethod
    def parse_cors_origins(cls, v):
        if isinstance(v, str):
            return json.loads(v)
        return v

    # Plaid
    PLAID_CLIENT_ID: Optional[str] = None
    PLAID_SECRET: Optional[str] = None
    PLAID_ENV: str = "sandbox"
    PLAID_PRODUCTS: str = "transactions,auth,balance,identity"
    PLAID_COUNTRY_CODES: str = "US,CA,GB,FR,ES,NL,IE"

    # LLM Providers
    # Ollama
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "llama3.3"

    # Groq
    GROQ_API_KEY: Optional[str] = None
    GROQ_MODEL: str = "llama-3.3-70b-versatile"

    # Anthropic
    ANTHROPIC_API_KEY: Optional[str] = None
    ANTHROPIC_MODEL: str = "claude-3-5-sonnet-20241022"

    # OpenRouter
    OPENROUTER_API_KEY: Optional[str] = None

    # Email (SendGrid)
    SENDGRID_API_KEY: Optional[str] = None
    SENDGRID_FROM_EMAIL: str = "noreply@finrack.com"
    SENDGRID_FROM_NAME: str = "FinRack"

    # SMS (Twilio)
    TWILIO_ACCOUNT_SID: Optional[str] = None
    TWILIO_AUTH_TOKEN: Optional[str] = None
    TWILIO_PHONE_NUMBER: Optional[str] = None

    # Push Notifications
    FCM_SERVER_KEY: Optional[str] = None

    # External APIs
    ALPHA_VANTAGE_API_KEY: Optional[str] = None

    # AWS (for Textract)
    AWS_ACCESS_KEY_ID: Optional[str] = None
    AWS_SECRET_ACCESS_KEY: Optional[str] = None
    AWS_REGION: str = "us-east-1"

    # Rate Limiting
    RATE_LIMIT_PER_MINUTE: int = 100
    RATE_LIMIT_PER_HOUR: int = 1000

    # Monitoring
    SENTRY_DSN: Optional[str] = None
    SENTRY_ENVIRONMENT: str = "development"

    @property
    def async_database_url(self) -> str:
        """Convert sync database URL to async"""
        return self.DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://")


# Global settings instance
settings = Settings()
