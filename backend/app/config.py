"""Application configuration using Pydantic Settings"""
from typing import List
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings"""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )
    
    # Application
    APP_NAME: str = "FinRack"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = True
    LOG_LEVEL: str = "INFO"
    
    # Database
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/finrack"
    DATABASE_URL_SYNC: str = "postgresql://postgres:postgres@localhost:5432/finrack"
    
    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"
    
    # RabbitMQ
    RABBITMQ_URL: str = "amqp://guest:guest@localhost:5672/"
    
    # MinIO
    MINIO_ENDPOINT: str = "localhost:9000"
    MINIO_ACCESS_KEY: str = "minioadmin"
    MINIO_SECRET_KEY: str = "minioadmin"
    MINIO_BUCKET: str = "finrack-receipts"
    MINIO_SECURE: bool = False
    
    # JWT
    JWT_SECRET: str = "your-super-secret-jwt-key-change-this-in-production"
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    # CORS
    CORS_ORIGINS: str = "http://localhost:3000,http://127.0.0.1:3000"
    
    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def parse_cors_origins(cls, v: str) -> List[str]:
        """Parse CORS origins from comma-separated string"""
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",")]
        return v
    
    # Plaid
    PLAID_CLIENT_ID: str = ""
    PLAID_SECRET: str = ""
    PLAID_ENV: str = "sandbox"
    
    # LLM Providers
    GROQ_API_KEY: str = ""
    ANTHROPIC_API_KEY: str = ""
    OPENROUTER_API_KEY: str = ""
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    
    # Twilio
    TWILIO_ACCOUNT_SID: str = ""
    TWILIO_AUTH_TOKEN: str = ""
    TWILIO_PHONE_NUMBER: str = ""
    
    # SendGrid
    SENDGRID_API_KEY: str = ""
    SENDGRID_FROM_EMAIL: str = "noreply@finrack.com"
    
    # AWS (Optional)
    AWS_ACCESS_KEY_ID: str = ""
    AWS_SECRET_ACCESS_KEY: str = ""
    AWS_REGION: str = "us-east-1"
    
    # Security
    ENCRYPTION_KEY: str = ""
    
    # Pagination
    DEFAULT_PAGE_SIZE: int = 50
    MAX_PAGE_SIZE: int = 100


# Global settings instance
settings = Settings()
