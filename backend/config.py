"""
Centralized configuration module for AI Business Opportunity Finder — Global Edition.
Loads environment variables safely from backend/.env without exposing secrets to the frontend.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Resolve backend root directory and load .env if present
BACKEND_DIR = Path(__file__).resolve().parent
ENV_FILE_PATH = BACKEND_DIR / ".env"
load_dotenv(ENV_FILE_PATH)


def _normalize_database_url(raw_url: str) -> str:
    """
    Normalizes a PostgreSQL / Supabase connection URI:
      - Ignores empty or placeholder strings (e.g. 'your_supabase_postgresql_connection_string')
      - Converts legacy 'postgres://' scheme to 'postgresql://' for SQLAlchemy & psycopg2
    """
    cleaned = (raw_url or "").strip()
    if not cleaned or cleaned.startswith("your_") or "your-password" in cleaned or "[your-" in cleaned:
        return ""
    if cleaned.startswith("postgres://"):
        cleaned = "postgresql://" + cleaned[len("postgres://") :]
    return cleaned


class Settings:
    """Application settings loaded from environment variables with safe defaults."""

    APP_NAME: str = "AI Business Opportunity Finder — Global Edition"
    APP_VERSION: str = "2.0.0"
    APP_ENV: str = os.getenv("APP_ENV", "development").strip()
    HOST: str = os.getenv("HOST", "127.0.0.1").strip()
    PORT: int = int(os.getenv("PORT", "8000").strip() or 8000)

    # Database configuration: Supabase PostgreSQL (primary when DATABASE_URL is set) + SQLite local file
    DB_FILE: Path = BACKEND_DIR / "business_opportunity.db"
    DATABASE_URL: str = _normalize_database_url(os.getenv("DATABASE_URL", ""))
    DB_POOL_MIN_CONN: int = int(os.getenv("DB_POOL_MIN_CONN", "1").strip() or 1)
    DB_POOL_MAX_CONN: int = int(os.getenv("DB_POOL_MAX_CONN", "10").strip() or 10)

    # Optional Hosted AI / LLM Configuration
    AI_PROVIDER: str = os.getenv("AI_PROVIDER", "gemini").strip().lower()
    AI_API_KEY: str = os.getenv("AI_API_KEY", "").strip()
    AI_MODEL_NAME: str = os.getenv("AI_MODEL_NAME", "gemini-2.5-flash").strip()

    # Multi-Layer Prompt Caching & Context Caching Configuration
    PROMPT_CACHE_ENABLED: bool = (
        os.getenv("PROMPT_CACHE_ENABLED", "true").strip().lower() in ("true", "1", "yes")
    )
    PROMPT_CACHE_TTL_MINUTES: int = int(
        os.getenv("PROMPT_CACHE_TTL_MINUTES", "1440").strip() or 1440
    )
    PROMPT_CACHE_MAX_MEM_ITEMS: int = int(
        os.getenv("PROMPT_CACHE_MAX_MEM_ITEMS", "256").strip() or 256
    )
    GEMINI_CONTEXT_CACHE_TTL_SECONDS: int = int(
        os.getenv("GEMINI_CONTEXT_CACHE_TTL_SECONDS", "3600").strip() or 3600
    )

    # Optional External Market-Data API Configuration
    MARKET_DATA_API_KEY: str = os.getenv("MARKET_DATA_API_KEY", "").strip()
    MARKET_DATA_CACHE_TTL_MINUTES: int = int(
        os.getenv("MARKET_DATA_CACHE_TTL_MINUTES", "60").strip() or 60
    )

    # Optional Exchange-Rate API Configuration
    EXCHANGE_RATE_API_KEY: str = os.getenv("EXCHANGE_RATE_API_KEY", "").strip()
    FX_CACHE_TTL_MINUTES: int = int(
        os.getenv("FX_CACHE_TTL_MINUTES", "360").strip() or 360
    )

    # Optional SMTP Email Configuration
    SMTP_HOST: str = os.getenv("SMTP_HOST", "smtp.gmail.com").strip()
    SMTP_PORT: int = int(os.getenv("SMTP_PORT", "587").strip() or 587)
    SMTP_USER: str = os.getenv("SMTP_USER", "").strip()
    SMTP_PASSWORD: str = os.getenv("SMTP_PASSWORD", "").strip()
    SMTP_FROM_NAME: str = os.getenv(
        "SMTP_FROM_NAME", "Opportunity Intelligence Global"
    ).strip()

    @classmethod
    def is_supabase_configured(cls) -> bool:
        """Returns True if a real Supabase PostgreSQL DATABASE_URL is configured."""
        url = _normalize_database_url(os.getenv("DATABASE_URL", "") or cls.DATABASE_URL)
        return bool(url and url.startswith(("postgresql://", "postgresql+psycopg2://")))

    @classmethod
    def get_database_url(cls) -> str:
        """Returns the normalized DATABASE_URL if configured, else SQLite URL."""
        url = _normalize_database_url(os.getenv("DATABASE_URL", "") or cls.DATABASE_URL)
        if url:
            return url
        return f"sqlite:///{cls.DB_FILE}"

    @classmethod
    def is_ai_configured(cls) -> bool:
        """Returns True only if a real non-placeholder AI API key is configured."""
        key = cls.AI_API_KEY
        return bool(key and not key.startswith("your_") and len(key) > 10)

    @classmethod
    def is_market_api_configured(cls) -> bool:
        """Returns True if a paid/keyed Market Data API key (e.g. NewsAPI) is configured."""
        key = cls.MARKET_DATA_API_KEY
        return bool(key and not key.startswith("your_") and len(key) > 8)

    @classmethod
    def is_fx_api_key_configured(cls) -> bool:
        """Returns True if a keyed Exchange-Rate API key is configured."""
        key = cls.EXCHANGE_RATE_API_KEY
        return bool(key and not key.startswith("your_") and len(key) > 8)

    @classmethod
    def is_smtp_configured(cls) -> bool:
        """Returns True if SMTP credentials are provided."""
        return bool(cls.SMTP_USER and cls.SMTP_PASSWORD)


settings = Settings()
