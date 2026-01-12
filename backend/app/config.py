"""
XOR Trading Platform - Configuration
Centralized configuration with environment validation
"""
import os
from functools import lru_cache
from typing import List, Optional

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings with environment variable support"""
    
    # Application
    APP_NAME: str = "XOR Trading Platform"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    ENVIRONMENT: str = Field(default="development", pattern="^(development|staging|production)$")
    
    # API
    API_V1_PREFIX: str = "/api/v1"
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:8000"]
    
    # Security
    SECRET_KEY: str = Field(default="your-super-secret-key-change-in-production")
    JWT_SECRET_KEY: str = Field(default="jwt-secret-key-change-in-production")
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    ENCRYPTION_KEY: str = Field(default="32-byte-encryption-key-here!!")  # 32 bytes for AES-256
    
    # Rate Limiting
    RATE_LIMIT_REQUESTS: int = 100
    RATE_LIMIT_WINDOW_SECONDS: int = 60
    
    # Database
    DATABASE_URL: str = Field(
        default="postgresql+asyncpg://postgres:postgres@localhost:5432/xor_trading"
    )
    DATABASE_POOL_SIZE: int = 20
    DATABASE_MAX_OVERFLOW: int = 10
    DATABASE_ECHO: bool = False
    
    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"
    REDIS_CACHE_TTL: int = 300  # 5 minutes default
    
    # WebSocket
    WS_HEARTBEAT_INTERVAL: int = 30
    WS_MAX_CONNECTIONS_PER_USER: int = 5
    
    # Exchange Settings
    EXCHANGE_REQUEST_TIMEOUT: int = 30
    EXCHANGE_WS_RECONNECT_DELAY: int = 5
    EXCHANGE_MAX_RETRIES: int = 3
    
    # Risk Management Defaults
    DEFAULT_MAX_DRAWDOWN_PERCENT: float = 10.0
    DEFAULT_MAX_POSITION_SIZE_PERCENT: float = 5.0
    DEFAULT_DAILY_LOSS_LIMIT_PERCENT: float = 3.0
    DEFAULT_MAX_LEVERAGE: int = 10
    
    # AI Engine
    AI_ENGINE_URL: str = "http://localhost:8001"
    AI_MODEL_PATH: str = "./ai-engine/saved_models"
    AI_INFERENCE_TIMEOUT: int = 5
    
    # Monitoring
    PROMETHEUS_PORT: int = 9090
    ENABLE_METRICS: bool = True
    
    @field_validator('ENCRYPTION_KEY')
    @classmethod
    def validate_encryption_key(cls, v: str) -> str:
        if len(v) != 32:
            raise ValueError('ENCRYPTION_KEY must be exactly 32 bytes for AES-256')
        return v
    
    @field_validator('SECRET_KEY', 'JWT_SECRET_KEY')
    @classmethod
    def validate_secrets(cls, v: str) -> str:
        if len(v) < 16:
            raise ValueError('Secret keys must be at least 16 characters')
        return v
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True


class DevelopmentSettings(Settings):
    """Development-specific settings"""
    DEBUG: bool = True
    DATABASE_ECHO: bool = True


class StagingSettings(Settings):
    """Staging-specific settings"""
    DEBUG: bool = False
    CORS_ORIGINS: List[str] = ["https://staging.xortrading.com"]


class ProductionSettings(Settings):
    """Production-specific settings"""
    DEBUG: bool = False
    DATABASE_ECHO: bool = False
    
    @field_validator('SECRET_KEY', 'JWT_SECRET_KEY', 'ENCRYPTION_KEY')
    @classmethod
    def validate_production_secrets(cls, v: str, info) -> str:
        if 'change' in v.lower() or 'default' in v.lower():
            raise ValueError(f'{info.field_name} must be properly set in production')
        return v


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings based on environment"""
    env = os.getenv("ENVIRONMENT", "development")
    
    settings_map = {
        "development": DevelopmentSettings,
        "staging": StagingSettings,
        "production": ProductionSettings,
    }
    
    settings_class = settings_map.get(env, DevelopmentSettings)
    return settings_class()


# Global settings instance
settings = get_settings()
