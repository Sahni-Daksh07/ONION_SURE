"""
Backend Application Settings and Configuration
Smart India Hackathon 2026 - Problem Statement PS26031
"""

from typing import Optional
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Application Info
    APP_NAME: str = "ONION_SURE"
    APP_VERSION: str = "1.0.0"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    API_V1_PREFIX: str = "/api/v1"

    # Server Binding
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    # Security
    SECRET_KEY: str = "development-secret-key-replace-in-production-min-32-chars"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    # PostgreSQL Database
    DATABASE_URL: str = "postgresql+psycopg://onion_sure_app:onion_sure_secure_password_2026@localhost:5432/onion_sure"
    DATABASE_TEST_URL: Optional[str] = "sqlite:///./test_onionsure.db"
    DB_POOL_SIZE: int = 10
    DB_MAX_OVERFLOW: int = 20
    DB_POOL_TIMEOUT: int = 30

    # Storage
    STORAGE_TYPE: str = "local"
    STORAGE_LOCAL_DIR: Path = Path("uploads")
    STORAGE_BUCKET: str = "onion-sure-inspections"
    MAX_UPLOAD_SIZE_MB: int = 15

    # Verification
    QR_BASE_URL: str = "https://onionsure.gov.in/verify"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()
