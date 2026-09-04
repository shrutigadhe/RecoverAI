import os
from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    PROJECT_NAME: str = "RecoverAI — AI Revenue Recovery Agent"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api"

    # Database
    DATABASE_URL: str = "sqlite:///./recoverai.db"  # Fallback SQLite default, overridden by ENV for Postgres

    # Demo Mode flag
    DEMO_MODE: bool = True

    # Razorpay Test Mode Credentials
    RAZORPAY_KEY_ID: Optional[str] = "rzp_test_mock_key_id"
    RAZORPAY_KEY_SECRET: Optional[str] = "mock_secret"
    RAZORPAY_WEBHOOK_SECRET: Optional[str] = "mock_webhook_secret"

    # LLM Settings
    LLM_PROVIDER: str = "gemini"
    LLM_API_KEY: Optional[str] = None

    # Policy / Guardrails Engine Settings
    MAX_AUTO_RETRY: int = 1
    MAX_AUTO_RECOVERY_AMOUNT: float = 5000.0
    MIN_AI_CONFIDENCE: float = 0.80

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )


settings = Settings()
