"""
Database Layer for AI Business Opportunity Finder — Global Edition.
Supports Supabase PostgreSQL (via SQLAlchemy connection pooling + psycopg2) as the primary
persistent cloud database when `DATABASE_URL` is configured in `backend/.env`, with automatic
pooled fallback to local SQLite (`business_opportunity.db`) if `DATABASE_URL` is not yet set.

Tables managed:
  1. users              (User accounts, PBKDF2-HMAC-SHA256 password hashes, OTP & session tokens)
  2. search_history     (User-specific discovery searches linked via user_id & user_email)
  3. saved_reports      (User-specific bookmarked opportunity reports linked via user_id & user_email)
  4. market_data_cache  (Cached real-time news/articles with source metadata)
  5. fx_rates_cache     (Cached currency exchange rates with retrieval timestamps)
  6. prompt_cache       (L2 persistent SHA-256 prompt & context cache)
"""

import json
import hashlib
import logging
import secrets
import sqlite3
from datetime import datetime, timedelta, timezone
from pathlib import Path
from threading import Lock
from typing import List, Dict, Any, Optional, Tuple

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
from sqlalchemy.exc import SQLAlchemyError

from config import settings

logger = logging.getLogger("opportunity_finder.database")

DB_FILE: Path = settings.DB_FILE

_ENGINE_LOCK = Lock()
_ACTIVE_ENGINE: Optional[Engine] = None
_ACTIVE_BACKEND: str = "uninitialized"  # "supabase_postgresql" | "sqlite_local"
_LAST_DB_ERROR: Optional[str] = None


def get_engine() -> Engine:
    """
    Returns a singleton SQLAlchemy Engine with connection pooling (`QueuePool`, `pool_pre_ping=True`).
    Reuses pooled connections across requests so a new TCP/SSL connection is never opened per query.
    Connects to Supabase PostgreSQL when `DATABASE_URL` is configured; falls back safely to SQLite
    if `DATABASE_URL` is unset or unreachable.
    """
    global _ACTIVE_ENGINE, _ACTIVE_BACKEND, _LAST_DB_ERROR

    if _ACTIVE_ENGINE is not None:
        return _ACTIVE_ENGINE

    with _ENGINE_LOCK:
        if _ACTIVE_ENGINE is not None:
            return _ACTIVE_ENGINE

        if settings.is_supabase_configured():
            pg_url = settings.get_database_url()
            try:
                connect_args: Dict[str, Any] = {"connect_timeout": 10}
                if "supabase.co" in pg_url and "sslmode=" not in pg_url:
                    connect_args["sslmode"] = "require"

                engine = create_engine(
                    pg_url,
                    pool_pre_ping=True,
                    pool_size=max(2, settings.DB_POOL_MIN_CONN),
                    max_overflow=max(5, settings.DB_POOL_MAX_CONN),
                    pool_recycle=300,
                    connect_args=connect_args,
                    future=True,
                )
                # Verify connectivity with a lightweight ping
                with engine.connect() as conn:
                    conn.execute(text("SELECT 1"))
                _ACTIVE_ENGINE = engine
                _ACTIVE_BACKEND = "supabase_postgresql"
                _LAST_DB_ERROR = None
                logger.info("Connected to Supabase PostgreSQL via pooled SQLAlchemy engine.")
                return _ACTIVE_ENGINE
            except Exception as exc:
                _LAST_DB_ERROR = str(exc)
                logger.warning(
                    "Supabase PostgreSQL connection failed (%s). Falling back to local SQLite (%s).",
                    exc,
                    DB_FILE,
                )

        sqlite_url = f"sqlite:///{DB_FILE}"
        _ACTIVE_ENGINE = create_engine(
            sqlite_url,
            pool_pre_ping=True,
            connect_args={"check_same_thread": False, "timeout": 15.0},
            future=True,
        )
        _ACTIVE_BACKEND = "sqlite_local"
        return _ACTIVE_ENGINE


def is_postgres_active() -> bool:
    """Returns True when the active engine is connected to Supabase PostgreSQL."""
    get_engine()
    return _ACTIVE_BACKEND == "supabase_postgresql"


def get_active_database_info() -> Dict[str, Any]:
    """Returns metadata about the active database backend and connection pool for health checks."""
    get_engine()
    if _ACTIVE_BACKEND == "supabase_postgresql":
        return {
            "backend": "Supabase PostgreSQL",
            "label": "Supabase PostgreSQL (Cloud Persistent Pool)",
            "is_supabase": True,
            "supabase_configured": True,
            "connection_pooling": "SQLAlchemy QueuePool (pool_pre_ping=True)",
            "last_error": _LAST_DB_ERROR,
        }
    return {
        "backend": "SQLite",
        "label": (
            f"SQLite ({DB_FILE.name}) — Set DATABASE_URL in backend/.env for Supabase PostgreSQL"
            if not settings.is_supabase_configured()
            else f"SQLite Fallback ({DB_FILE.name}) — Supabase unreachable: {_LAST_DB_ERROR}"
        ),
        "is_supabase": False,
        "supabase_configured": settings.is_supabase_configured(),
        "connection_pooling": "SQLAlchemy Pooled Connection",
        "last_error": _LAST_DB_ERROR,
    }


def get_db_connection() -> sqlite3.Connection:
    """
    Legacy helper returning a direct SQLite connection to `business_opportunity.db`
    (used by migration verification utilities).
    """
    conn = sqlite3.connect(str(DB_FILE), timeout=15.0)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    """
    Initializes all required tables, foreign keys, unique constraints, and indexes
    in Supabase PostgreSQL (or SQLite when running in local fallback mode).
    """
    engine = get_engine()
    is_pg = is_postgres_active()

    with engine.begin() as conn:
        if is_pg:
            # 1. Users Table
            conn.execute(
                text("""
                CREATE TABLE IF NOT EXISTS users (
                    id SERIAL PRIMARY KEY,
                    email TEXT UNIQUE NOT NULL,
                    password_hash TEXT,
                    password_salt TEXT,
                    otp_code TEXT,
                    otp_expires_at TEXT,
                    otp_attempts INTEGER DEFAULT 0,
                    last_otp_sent_at TEXT,
                    session_token TEXT,
                    last_login_at TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                );
                """)
            )
            conn.execute(text("CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);"))
            conn.execute(text("CREATE INDEX IF NOT EXISTS idx_users_session_token ON users(session_token);"))

            # 2. Search History Table
            conn.execute(
                text("""
                CREATE TABLE IF NOT EXISTS search_history (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
                    user_email TEXT NOT NULL,
                    country TEXT DEFAULT 'India',
                    country_code TEXT DEFAULT 'IN',
                    state TEXT DEFAULT 'Karnataka',
                    city TEXT NOT NULL,
                    area TEXT NOT NULL,
                    domain TEXT NOT NULL,
                    currency TEXT DEFAULT 'INR',
                    budget DOUBLE PRECISION DEFAULT 0,
                    experience_level TEXT DEFAULT 'Beginner',
                    risk_preference TEXT DEFAULT 'Low',
                    user_query TEXT DEFAULT '',
                    data_status_label TEXT DEFAULT 'Demo/sample data',
                    nlp_summary TEXT DEFAULT '{}',
                    opportunities TEXT NOT NULL,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                );
                """)
            )
            conn.execute(text("ALTER TABLE search_history ADD COLUMN IF NOT EXISTS user_id INTEGER REFERENCES users(id) ON DELETE SET NULL;"))
            conn.execute(text("CREATE INDEX IF NOT EXISTS idx_search_history_user_id ON search_history(user_id);"))
            conn.execute(text("CREATE INDEX IF NOT EXISTS idx_search_history_user_email ON search_history(user_email);"))
            conn.execute(text("CREATE INDEX IF NOT EXISTS idx_search_history_created_at ON search_history(created_at DESC);"))
            conn.execute(text("CREATE INDEX IF NOT EXISTS idx_search_history_location ON search_history(country, state, city);"))
            conn.execute(text("CREATE INDEX IF NOT EXISTS idx_search_history_domain ON search_history(domain);"))

            # 3. Saved Opportunity Reports Table
            conn.execute(
                text("""
                CREATE TABLE IF NOT EXISTS saved_reports (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
                    opportunity_id TEXT NOT NULL,
                    user_email TEXT NOT NULL,
                    title TEXT NOT NULL,
                    category TEXT NOT NULL,
                    country TEXT NOT NULL,
                    state TEXT NOT NULL,
                    city TEXT NOT NULL,
                    area TEXT NOT NULL,
                    currency TEXT NOT NULL,
                    estimated_budget DOUBLE PRECISION NOT NULL,
                    score INTEGER NOT NULL,
                    report_json TEXT NOT NULL,
                    notes TEXT DEFAULT '',
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    CONSTRAINT uq_saved_reports_user_opp UNIQUE (opportunity_id, user_email)
                );
                """)
            )
            conn.execute(text("ALTER TABLE saved_reports ADD COLUMN IF NOT EXISTS user_id INTEGER REFERENCES users(id) ON DELETE SET NULL;"))
            conn.execute(text("CREATE INDEX IF NOT EXISTS idx_saved_reports_user_id ON saved_reports(user_id);"))
            conn.execute(text("CREATE INDEX IF NOT EXISTS idx_saved_reports_user_email ON saved_reports(user_email);"))
            conn.execute(text("CREATE INDEX IF NOT EXISTS idx_saved_reports_created_at ON saved_reports(created_at DESC);"))
            conn.execute(text("CREATE INDEX IF NOT EXISTS idx_saved_reports_category ON saved_reports(category);"))

            # 4. External Market Data Cache Table
            conn.execute(
                text("""
                CREATE TABLE IF NOT EXISTS market_data_cache (
                    cache_key TEXT PRIMARY KEY,
                    source_name TEXT NOT NULL,
                    country TEXT NOT NULL,
                    city TEXT NOT NULL,
                    category TEXT NOT NULL,
                    records_json TEXT NOT NULL,
                    retrieved_at TEXT NOT NULL
                );
                """)
            )
            conn.execute(text("CREATE INDEX IF NOT EXISTS idx_market_cache_loc_cat ON market_data_cache(country, city, category);"))

            # 5. Currency Exchange Rates Cache Table
            conn.execute(
                text("""
                CREATE TABLE IF NOT EXISTS fx_rates_cache (
                    base_currency TEXT PRIMARY KEY,
                    provider_name TEXT NOT NULL,
                    rate_date TEXT NOT NULL,
                    retrieved_at TEXT NOT NULL,
                    rates_json TEXT NOT NULL
                );
                """)
            )

            # 6. Multi-Layer Prompt & Context Cache Table
            conn.execute(
                text("""
                CREATE TABLE IF NOT EXISTS prompt_cache (
                    cache_key TEXT PRIMARY KEY,
                    prompt_type TEXT NOT NULL,
                    model_name TEXT NOT NULL,
                    prefix_hash TEXT NOT NULL,
                    payload_hash TEXT NOT NULL,
                    normalized_prompt TEXT NOT NULL,
                    response_json TEXT NOT NULL,
                    prompt_tokens_est INTEGER DEFAULT 0,
                    cached_tokens_est INTEGER DEFAULT 0,
                    completion_tokens_est INTEGER DEFAULT 0,
                    hit_count INTEGER DEFAULT 0,
                    latency_saved_ms DOUBLE PRECISION DEFAULT 0.0,
                    created_at TEXT NOT NULL,
                    last_accessed_at TEXT NOT NULL,
                    expires_at TEXT NOT NULL
                );
                """)
            )
            conn.execute(text("CREATE INDEX IF NOT EXISTS idx_prompt_cache_type ON prompt_cache(prompt_type);"))
            conn.execute(text("CREATE INDEX IF NOT EXISTS idx_prompt_cache_expires ON prompt_cache(expires_at);"))

        else:
            # SQLite Schema + Safe Column & Index Migrations
            conn.execute(
                text("""
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    email TEXT UNIQUE NOT NULL,
                    password_hash TEXT,
                    password_salt TEXT,
                    otp_code TEXT,
                    otp_expires_at TIMESTAMP,
                    otp_attempts INTEGER DEFAULT 0,
                    last_otp_sent_at TIMESTAMP,
                    session_token TEXT,
                    last_login_at TIMESTAMP,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
                """)
            )
            user_cols = [r[1] for r in conn.execute(text("PRAGMA table_info(users);")).fetchall()]
            for col_name, col_def in [
                ("password_hash", "TEXT"),
                ("password_salt", "TEXT"),
                ("otp_code", "TEXT"),
                ("otp_expires_at", "TIMESTAMP"),
                ("otp_attempts", "INTEGER DEFAULT 0"),
                ("last_otp_sent_at", "TIMESTAMP"),
                ("session_token", "TEXT"),
                ("last_login_at", "TIMESTAMP"),
            ]:
                if col_name not in user_cols:
                    conn.execute(text(f"ALTER TABLE users ADD COLUMN {col_name} {col_def};"))

            conn.execute(
                text("""
                CREATE TABLE IF NOT EXISTS search_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
                    user_email TEXT NOT NULL,
                    country TEXT DEFAULT 'India',
                    country_code TEXT DEFAULT 'IN',
                    state TEXT DEFAULT 'Karnataka',
                    city TEXT NOT NULL,
                    area TEXT NOT NULL,
                    domain TEXT NOT NULL,
                    currency TEXT DEFAULT 'INR',
                    budget REAL DEFAULT 0,
                    experience_level TEXT DEFAULT 'Beginner',
                    risk_preference TEXT DEFAULT 'Low',
                    user_query TEXT,
                    data_status_label TEXT DEFAULT 'Demo/sample data',
                    nlp_summary TEXT DEFAULT '{}',
                    opportunities TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
                """)
            )
            sh_cols = [r[1] for r in conn.execute(text("PRAGMA table_info(search_history);")).fetchall()]
            for col_name, col_def in [
                ("user_id", "INTEGER"),
                ("country", "TEXT DEFAULT 'India'"),
                ("country_code", "TEXT DEFAULT 'IN'"),
                ("state", "TEXT DEFAULT 'Karnataka'"),
                ("currency", "TEXT DEFAULT 'INR'"),
                ("budget", "REAL DEFAULT 0"),
                ("experience_level", "TEXT DEFAULT 'Beginner'"),
                ("risk_preference", "TEXT DEFAULT 'Low'"),
                ("data_status_label", "TEXT DEFAULT 'Demo/sample data'"),
                ("nlp_summary", "TEXT DEFAULT '{}'"),
            ]:
                if col_name not in sh_cols:
                    conn.execute(text(f"ALTER TABLE search_history ADD COLUMN {col_name} {col_def};"))

            conn.execute(
                text("""
                CREATE TABLE IF NOT EXISTS saved_reports (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
                    opportunity_id TEXT NOT NULL,
                    user_email TEXT NOT NULL,
                    title TEXT NOT NULL,
                    category TEXT NOT NULL,
                    country TEXT NOT NULL,
                    state TEXT NOT NULL,
                    city TEXT NOT NULL,
                    area TEXT NOT NULL,
                    currency TEXT NOT NULL,
                    estimated_budget REAL NOT NULL,
                    score INTEGER NOT NULL,
                    report_json TEXT NOT NULL,
                    notes TEXT DEFAULT '',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
                """)
            )
            sr_cols = [r[1] for r in conn.execute(text("PRAGMA table_info(saved_reports);")).fetchall()]
            if "user_id" not in sr_cols:
                conn.execute(text("ALTER TABLE saved_reports ADD COLUMN user_id INTEGER;"))

            conn.execute(
                text("""
                CREATE TABLE IF NOT EXISTS market_data_cache (
                    cache_key TEXT PRIMARY KEY,
                    source_name TEXT NOT NULL,
                    country TEXT NOT NULL,
                    city TEXT NOT NULL,
                    category TEXT NOT NULL,
                    records_json TEXT NOT NULL,
                    retrieved_at TEXT NOT NULL
                );
                """)
            )

            conn.execute(
                text("""
                CREATE TABLE IF NOT EXISTS fx_rates_cache (
                    base_currency TEXT PRIMARY KEY,
                    provider_name TEXT NOT NULL,
                    rate_date TEXT NOT NULL,
                    retrieved_at TEXT NOT NULL,
                    rates_json TEXT NOT NULL
                );
                """)
            )

            conn.execute(
                text("""
                CREATE TABLE IF NOT EXISTS prompt_cache (
                    cache_key TEXT PRIMARY KEY,
                    prompt_type TEXT NOT NULL,
                    model_name TEXT NOT NULL,
                    prefix_hash TEXT NOT NULL,
                    payload_hash TEXT NOT NULL,
                    normalized_prompt TEXT NOT NULL,
                    response_json TEXT NOT NULL,
                    prompt_tokens_est INTEGER DEFAULT 0,
                    cached_tokens_est INTEGER DEFAULT 0,
                    completion_tokens_est INTEGER DEFAULT 0,
                    hit_count INTEGER DEFAULT 0,
                    latency_saved_ms REAL DEFAULT 0.0,
                    created_at TEXT NOT NULL,
                    last_accessed_at TEXT NOT NULL,
                    expires_at TEXT NOT NULL
                );
                """)
            )

            # Indexes for fast user, date, location, and category queries
            conn.execute(text("CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);"))
            conn.execute(text("CREATE INDEX IF NOT EXISTS idx_search_history_user_id ON search_history(user_id);"))
            conn.execute(text("CREATE INDEX IF NOT EXISTS idx_search_history_user_email ON search_history(user_email);"))
            conn.execute(text("CREATE INDEX IF NOT EXISTS idx_search_history_created_at ON search_history(created_at DESC);"))
            conn.execute(text("CREATE INDEX IF NOT EXISTS idx_search_history_location ON search_history(country, state, city);"))
            conn.execute(text("CREATE INDEX IF NOT EXISTS idx_search_history_domain ON search_history(domain);"))
            conn.execute(text("CREATE INDEX IF NOT EXISTS idx_saved_reports_user_id ON saved_reports(user_id);"))
            conn.execute(text("CREATE INDEX IF NOT EXISTS idx_saved_reports_user_email ON saved_reports(user_email);"))
            conn.execute(text("CREATE INDEX IF NOT EXISTS idx_prompt_cache_type ON prompt_cache(prompt_type);"))
            conn.execute(text("CREATE INDEX IF NOT EXISTS idx_prompt_cache_expires ON prompt_cache(expires_at);"))

            # Backfill missing user_id foreign keys for existing SQLite rows
            conn.execute(
                text("""
                INSERT OR IGNORE INTO users (email, created_at)
                SELECT DISTINCT LOWER(TRIM(user_email)), CURRENT_TIMESTAMP
                FROM search_history
                WHERE user_email IS NOT NULL AND TRIM(user_email) != '';
                """)
            )
            conn.execute(
                text("""
                INSERT OR IGNORE INTO users (email, created_at)
                SELECT DISTINCT LOWER(TRIM(user_email)), CURRENT_TIMESTAMP
                FROM saved_reports
                WHERE user_email IS NOT NULL AND TRIM(user_email) != '';
                """)
            )
            conn.execute(
                text("""
                UPDATE search_history
                SET user_id = (SELECT id FROM users WHERE LOWER(users.email) = LOWER(search_history.user_email))
                WHERE user_id IS NULL;
                """)
            )
            conn.execute(
                text("""
                UPDATE saved_reports
                SET user_id = (SELECT id FROM users WHERE LOWER(users.email) = LOWER(saved_reports.user_email))
                WHERE user_id IS NULL;
                """)
            )


def _get_or_create_user_id(conn, clean_email: str) -> int:
    """
    Ensures a row exists in `users` for `clean_email` and returns its integer `id`.
    Maintains foreign-key integrity (`user_id -> users.id`) across all user tables.
    """
    row = conn.execute(
        text("SELECT id FROM users WHERE email = :email"),
        {"email": clean_email},
    ).mappings().first()
    if row:
        return int(row["id"])

    now_iso = datetime.now(timezone.utc).isoformat()
    if is_postgres_active():
        inserted = conn.execute(
            text("""
            INSERT INTO users (email, created_at)
            VALUES (:email, :created_at)
            ON CONFLICT (email) DO UPDATE SET email = EXCLUDED.email
            RETURNING id
            """),
            {"email": clean_email, "created_at": now_iso},
        ).mappings().first()
        return int(inserted["id"]) if inserted else 0
    else:
        conn.execute(
            text("INSERT OR IGNORE INTO users (email, created_at) VALUES (:email, :created_at)"),
            {"email": clean_email, "created_at": now_iso},
        )
        fetched = conn.execute(
            text("SELECT id FROM users WHERE email = :email"),
            {"email": clean_email},
        ).mappings().first()
        return int(fetched["id"]) if fetched else 0


PBKDF2_ITERATIONS: int = 260_000


def hash_password(password: str, salt_hex: Optional[str] = None) -> Tuple[str, str]:
    """
    Hashes a plain-text password using PBKDF2-HMAC-SHA256 (260,000 iterations)
    with a 128-bit cryptographic salt.
    Returns (formatted_hash_string, salt_hex).
    """
    if not salt_hex:
        salt_hex = secrets.token_hex(16)
    derived_key = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt_hex.encode("utf-8"),
        PBKDF2_ITERATIONS,
    ).hex()
    formatted_hash = f"pbkdf2_sha256${PBKDF2_ITERATIONS}${salt_hex}${derived_key}"
    return formatted_hash, salt_hex


def verify_password_hash(password: str, stored_hash: str, stored_salt: Optional[str] = None) -> bool:
    """
    Verifies a plain-text password against a stored PBKDF2-HMAC-SHA256 hash using
    constant-time `secrets.compare_digest` to prevent timing attacks.
    """
    if not stored_hash:
        return False
    try:
        if stored_hash.startswith("pbkdf2_sha256$"):
            parts = stored_hash.split("$")
            if len(parts) == 4:
                iterations = int(parts[1])
                salt = parts[2]
                expected_hex = parts[3]
                candidate_hex = hashlib.pbkdf2_hmac(
                    "sha256",
                    password.encode("utf-8"),
                    salt.encode("utf-8"),
                    iterations,
                ).hex()
                return secrets.compare_digest(candidate_hex, expected_hex)
        if stored_salt:
            candidate_formatted, _ = hash_password(password, stored_salt)
            return secrets.compare_digest(candidate_formatted, stored_hash)
    except Exception:
        return False
    return False


def authenticate_or_register_user_password(
    email: str, password: str, mode: str = "auto"
) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
    """
    Authenticates an existing user with their PBKDF2-HMAC-SHA256 hashed password
    or registers/sets the hashed password for a new account.
    Modes:
      - 'login': signs in existing user (or sets password if user row has no password yet)
      - 'register': creates new user with hashed password (fails if email already has a password)
      - 'auto': verifies password if account has one, otherwise creates account & hashes password
    """
    clean_email = email.strip().lower()
    if len(password) < 6:
        return False, "Password must be at least 6 characters long.", None

    now_iso = datetime.now(timezone.utc).isoformat()
    session_token = f"biof_{secrets.token_urlsafe(24)}"
    engine = get_engine()

    with engine.begin() as conn:
        row = conn.execute(
            text(
                "SELECT id, email, password_hash, password_salt, created_at, last_login_at "
                "FROM users WHERE email = :email"
            ),
            {"email": clean_email},
        ).mappings().first()

        if row:
            user = dict(row)
            existing_hash = user.get("password_hash")
            existing_salt = user.get("password_salt")

            if existing_hash:
                if mode == "register":
                    return (
                        False,
                        "An account with this email already exists. Please switch to Sign In and enter your password.",
                        None,
                    )

                if not verify_password_hash(password, existing_hash, existing_salt):
                    return False, "Incorrect password for this account. Please try again.", None

                conn.execute(
                    text("""
                    UPDATE users
                    SET last_login_at = :now_iso, session_token = :token,
                        otp_code = NULL, otp_expires_at = NULL
                    WHERE email = :email
                    """),
                    {"now_iso": now_iso, "token": session_token, "email": clean_email},
                )
                updated_row = conn.execute(
                    text(
                        "SELECT id, email, password_hash, session_token, created_at, last_login_at "
                        "FROM users WHERE email = :email"
                    ),
                    {"email": clean_email},
                ).mappings().first()
                return (
                    True,
                    "Signed in successfully (Verified via PBKDF2-HMAC-SHA256 password hash).",
                    dict(updated_row),
                )
            else:
                hashed_pw, salt_hex = hash_password(password)
                conn.execute(
                    text("""
                    UPDATE users
                    SET password_hash = :pw_hash, password_salt = :pw_salt,
                        last_login_at = :now_iso, session_token = :token,
                        otp_code = NULL, otp_expires_at = NULL
                    WHERE email = :email
                    """),
                    {
                        "pw_hash": hashed_pw,
                        "pw_salt": salt_hex,
                        "now_iso": now_iso,
                        "token": session_token,
                        "email": clean_email,
                    },
                )
                updated_row = conn.execute(
                    text(
                        "SELECT id, email, password_hash, session_token, created_at, last_login_at "
                        "FROM users WHERE email = :email"
                    ),
                    {"email": clean_email},
                ).mappings().first()
                return (
                    True,
                    "Password hashed with PBKDF2-HMAC-SHA256 and saved to your account.",
                    dict(updated_row),
                )
        else:
            hashed_pw, salt_hex = hash_password(password)
            conn.execute(
                text("""
                INSERT INTO users (email, password_hash, password_salt, session_token, last_login_at, created_at)
                VALUES (:email, :pw_hash, :pw_salt, :token, :now_iso, :created_at)
                """),
                {
                    "email": clean_email,
                    "pw_hash": hashed_pw,
                    "pw_salt": salt_hex,
                    "token": session_token,
                    "now_iso": now_iso,
                    "created_at": now_iso,
                },
            )
            new_row = conn.execute(
                text(
                    "SELECT id, email, password_hash, session_token, created_at, last_login_at "
                    "FROM users WHERE email = :email"
                ),
                {"email": clean_email},
            ).mappings().first()
            return (
                True,
                "Account created with PBKDF2-HMAC-SHA256 salted password hash.",
                dict(new_row),
            )


def set_user_otp(email: str, otp_code: str, expiry_minutes: int = 10) -> Tuple[bool, str, Dict[str, Any]]:
    """
    Stores a cryptographically random 6-digit OTP in the database with rate-limiting check.
    Returns (allowed, message, user_dict).
    """
    clean_email = email.strip().lower()
    now_utc = datetime.now(timezone.utc)
    expires_at = (now_utc + timedelta(minutes=expiry_minutes)).isoformat()
    engine = get_engine()

    with engine.begin() as conn:
        user = conn.execute(
            text("SELECT id, last_otp_sent_at, otp_attempts FROM users WHERE email = :email"),
            {"email": clean_email},
        ).mappings().first()

        if user and user["last_otp_sent_at"]:
            try:
                last_sent = datetime.fromisoformat(str(user["last_otp_sent_at"]))
                if last_sent.tzinfo is None:
                    last_sent = last_sent.replace(tzinfo=timezone.utc)
                if (now_utc - last_sent).total_seconds() < 5:
                    return False, "Please wait a few seconds before requesting another code.", {}
            except Exception:
                pass

        if user:
            conn.execute(
                text("""
                UPDATE users
                SET otp_code = :otp, otp_expires_at = :exp, otp_attempts = 0, last_otp_sent_at = :sent_at
                WHERE email = :email
                """),
                {
                    "otp": otp_code,
                    "exp": expires_at,
                    "sent_at": now_utc.isoformat(),
                    "email": clean_email,
                },
            )
        else:
            conn.execute(
                text("""
                INSERT INTO users (email, otp_code, otp_expires_at, otp_attempts, last_otp_sent_at, created_at)
                VALUES (:email, :otp, :exp, 0, :sent_at, :created_at)
                """),
                {
                    "email": clean_email,
                    "otp": otp_code,
                    "exp": expires_at,
                    "sent_at": now_utc.isoformat(),
                    "created_at": now_utc.isoformat(),
                },
            )

        updated_user = conn.execute(
            text("SELECT id, email, otp_expires_at, created_at, last_login_at FROM users WHERE email = :email"),
            {"email": clean_email},
        ).mappings().first()
        return True, "Verification code generated.", dict(updated_user)


def verify_user_otp(
    email: str, code: str, allow_dev_fallback: bool = False
) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
    """
    Verifies a user's 6-digit OTP against the database, enforcing expiration and attempt limits.
    Generates a cryptographic session token on success.
    """
    clean_email = email.strip().lower()
    clean_code = code.strip()
    now_utc = datetime.now(timezone.utc)
    engine = get_engine()

    with engine.begin() as conn:
        user_row = conn.execute(
            text(
                "SELECT id, email, otp_code, otp_expires_at, otp_attempts, created_at, last_login_at "
                "FROM users WHERE email = :email"
            ),
            {"email": clean_email},
        ).mappings().first()

        if not user_row:
            return False, "User account not found. Please request a verification code first.", None

        user = dict(user_row)
        attempts = int(user.get("otp_attempts") or 0)
        if attempts >= 5:
            return False, "Too many failed verification attempts. Please request a new code.", None

        stored_otp = user.get("otp_code")
        stored_expiry = user.get("otp_expires_at")

        if not stored_otp or stored_otp != clean_code:
            conn.execute(
                text("UPDATE users SET otp_attempts = COALESCE(otp_attempts, 0) + 1 WHERE email = :email"),
                {"email": clean_email},
            )
            return False, "Invalid verification code. Please check the 6-digit code and try again.", None

        if stored_expiry:
            try:
                exp_dt = datetime.fromisoformat(str(stored_expiry))
                if exp_dt.tzinfo is None:
                    exp_dt = exp_dt.replace(tzinfo=timezone.utc)
                if now_utc > exp_dt:
                    return False, "Verification code has expired. Please request a new code.", None
            except Exception:
                pass

        session_token = f"biof_{secrets.token_urlsafe(24)}"
        now_iso = now_utc.isoformat()
        conn.execute(
            text("""
            UPDATE users
            SET otp_code = NULL, otp_expires_at = NULL, otp_attempts = 0,
                last_login_at = :now_iso, session_token = :token
            WHERE email = :email
            """),
            {"now_iso": now_iso, "token": session_token, "email": clean_email},
        )

        refreshed_user = conn.execute(
            text("SELECT id, email, session_token, created_at, last_login_at FROM users WHERE email = :email"),
            {"email": clean_email},
        ).mappings().first()
        return True, "Authentication successful.", dict(refreshed_user)


def save_search_history(
    user_email: str,
    domain: str,
    city: str,
    area: str,
    user_query: Optional[str],
    opportunities: List[Dict[str, Any]],
    country: str = "India",
    country_code: str = "IN",
    state: str = "Karnataka",
    currency: str = "INR",
    budget: float = 0.0,
    experience_level: str = "Beginner",
    risk_preference: str = "Low",
    data_status_label: str = "Demo/sample data",
    nlp_summary: Optional[Dict[str, Any]] = None,
) -> int:
    """Saves a complete discovery search and its generated opportunities linked to user_id & user_email."""
    clean_email = (user_email or "founder@opportunity.ai").strip().lower()
    opportunities_json = json.dumps(opportunities, ensure_ascii=False)
    nlp_json = json.dumps(nlp_summary or {}, ensure_ascii=False)
    now_iso = datetime.now(timezone.utc).isoformat()
    engine = get_engine()

    with engine.begin() as conn:
        user_id = _get_or_create_user_id(conn, clean_email)
        params = {
            "user_id": user_id,
            "user_email": clean_email,
            "country": country,
            "country_code": country_code,
            "state": state,
            "city": city,
            "area": area,
            "domain": domain,
            "currency": currency,
            "budget": float(budget or 0.0),
            "experience_level": experience_level,
            "risk_preference": risk_preference,
            "user_query": user_query or "",
            "data_status_label": data_status_label,
            "nlp_summary": nlp_json,
            "opportunities": opportunities_json,
            "created_at": now_iso,
        }

        if is_postgres_active():
            row = conn.execute(
                text("""
                INSERT INTO search_history (
                    user_id, user_email, country, country_code, state, city, area, domain,
                    currency, budget, experience_level, risk_preference,
                    user_query, data_status_label, nlp_summary, opportunities, created_at
                )
                VALUES (
                    :user_id, :user_email, :country, :country_code, :state, :city, :area, :domain,
                    :currency, :budget, :experience_level, :risk_preference,
                    :user_query, :data_status_label, :nlp_summary, :opportunities, :created_at
                )
                RETURNING id
                """),
                params,
            ).mappings().first()
            return int(row["id"]) if row else 0
        else:
            res = conn.execute(
                text("""
                INSERT INTO search_history (
                    user_id, user_email, country, country_code, state, city, area, domain,
                    currency, budget, experience_level, risk_preference,
                    user_query, data_status_label, nlp_summary, opportunities, created_at
                )
                VALUES (
                    :user_id, :user_email, :country, :country_code, :state, :city, :area, :domain,
                    :currency, :budget, :experience_level, :risk_preference,
                    :user_query, :data_status_label, :nlp_summary, :opportunities, :created_at
                )
                """),
                params,
            )
            return int(res.lastrowid or 0)


def _hydrate_history_row(row_mapping: Any) -> Dict[str, Any]:
    """Deserializes JSON columns and enriches a search_history row."""
    row_dict = dict(row_mapping)
    try:
        opps = json.loads(row_dict.get("opportunities") or "[]")
        row_dict["opportunities"] = opps if isinstance(opps, list) else []
    except Exception:
        row_dict["opportunities"] = []
    try:
        nlp = json.loads(row_dict.get("nlp_summary") or "{}")
        row_dict["nlp_summary"] = nlp if isinstance(nlp, dict) else {}
    except Exception:
        row_dict["nlp_summary"] = {}
    row_dict["opportunities_count"] = len(row_dict["opportunities"])
    row_dict["created_at"] = str(row_dict.get("created_at") or "")
    return row_dict


def _build_history_where_clause(
    user_email: Optional[str] = None,
    search_query: Optional[str] = None,
    country: Optional[str] = None,
    state: Optional[str] = None,
    city: Optional[str] = None,
    category: Optional[str] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
) -> Tuple[str, Dict[str, Any]]:
    """Builds a parameterized WHERE clause for filtering user search history."""
    conditions: List[str] = []
    params: Dict[str, Any] = {}

    if user_email and user_email.strip():
        conditions.append("LOWER(user_email) = :user_email")
        params["user_email"] = user_email.strip().lower()

    if country and country.strip() and country.strip().lower() != "all":
        conditions.append("LOWER(country) = :country")
        params["country"] = country.strip().lower()

    if state and state.strip() and state.strip().lower() != "all":
        conditions.append("LOWER(state) = :state")
        params["state"] = state.strip().lower()

    if city and city.strip() and city.strip().lower() != "all":
        conditions.append("LOWER(city) LIKE :city")
        params["city"] = f"%{city.strip().lower()}%"

    if category and category.strip() and category.strip().lower() != "all":
        conditions.append("LOWER(domain) = :category")
        params["category"] = category.strip().lower()

    if date_from and date_from.strip():
        conditions.append("SUBSTR(CAST(created_at AS TEXT), 1, 10) >= :date_from")
        params["date_from"] = date_from.strip()[:10]

    if date_to and date_to.strip():
        conditions.append("SUBSTR(CAST(created_at AS TEXT), 1, 10) <= :date_to")
        params["date_to"] = date_to.strip()[:10]

    if search_query and search_query.strip():
        conditions.append(
            "("
            "LOWER(domain) LIKE :q OR "
            "LOWER(city) LIKE :q OR "
            "LOWER(area) LIKE :q OR "
            "LOWER(state) LIKE :q OR "
            "LOWER(country) LIKE :q OR "
            "LOWER(COALESCE(user_query, '')) LIKE :q"
            ")"
        )
        params["q"] = f"%{search_query.strip().lower()}%"

    where_sql = f"WHERE {' AND '.join(conditions)}" if conditions else ""
    return where_sql, params


def get_user_history(
    user_email: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    search_query: Optional[str] = None,
    country: Optional[str] = None,
    state: Optional[str] = None,
    city: Optional[str] = None,
    category: Optional[str] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """
    Retrieves search history in reverse chronological order (newest first),
    isolated to the specified user and optionally filtered by keyword, location, category, and date.
    """
    where_sql, params = _build_history_where_clause(
        user_email=user_email,
        search_query=search_query,
        country=country,
        state=state,
        city=city,
        category=category,
        date_from=date_from,
        date_to=date_to,
    )
    params["limit"] = max(1, int(limit))
    params["offset"] = max(0, int(offset))

    engine = get_engine()
    with engine.connect() as conn:
        rows = conn.execute(
            text(
                f"SELECT * FROM search_history {where_sql} "
                f"ORDER BY created_at DESC, id DESC LIMIT :limit OFFSET :offset"
            ),
            params,
        ).mappings().all()
        return [_hydrate_history_row(r) for r in rows]


def count_user_history(
    user_email: Optional[str] = None,
    search_query: Optional[str] = None,
    country: Optional[str] = None,
    state: Optional[str] = None,
    city: Optional[str] = None,
    category: Optional[str] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
) -> int:
    """Returns the total count of search history records matching the user and filter criteria."""
    where_sql, params = _build_history_where_clause(
        user_email=user_email,
        search_query=search_query,
        country=country,
        state=state,
        city=city,
        category=category,
        date_from=date_from,
        date_to=date_to,
    )
    engine = get_engine()
    with engine.connect() as conn:
        row = conn.execute(
            text(f"SELECT COUNT(*) AS cnt FROM search_history {where_sql}"),
            params,
        ).mappings().first()
        return int(row["cnt"] or 0) if row else 0


def get_history_record_by_id(history_id: int, user_email: str) -> Optional[Dict[str, Any]]:
    """
    Retrieves a single search history record by ID, strictly enforcing user ownership
    so a user cannot access another user's search history.
    """
    clean_email = (user_email or "").strip().lower()
    if not clean_email:
        return None

    engine = get_engine()
    with engine.connect() as conn:
        row = conn.execute(
            text(
                "SELECT * FROM search_history "
                "WHERE id = :id AND LOWER(user_email) = :user_email"
            ),
            {"id": int(history_id), "user_email": clean_email},
        ).mappings().first()
        return _hydrate_history_row(row) if row else None


def delete_search_history_record(history_id: int, user_email: str) -> bool:
    """
    Deletes a single search history record by ID, strictly enforcing user ownership
    so a user can only delete their own search history records.
    """
    clean_email = (user_email or "").strip().lower()
    if not clean_email:
        return False

    engine = get_engine()
    with engine.begin() as conn:
        res = conn.execute(
            text(
                "DELETE FROM search_history "
                "WHERE id = :id AND LOWER(user_email) = :user_email"
            ),
            {"id": int(history_id), "user_email": clean_email},
        )
        return (res.rowcount or 0) > 0


def save_opportunity_report(
    user_email: str, opportunity: Dict[str, Any], notes: str = ""
) -> Dict[str, Any]:
    """Saves or updates a bookmarked opportunity report linked to user_id & user_email."""
    clean_email = (user_email or "founder@opportunity.ai").strip().lower()
    opp_id = str(opportunity.get("id") or f"opp-{secrets.token_hex(4)}")
    title = str(opportunity.get("title") or "Untitled Business Opportunity")
    category = str(opportunity.get("category") or "Daily Needs & Grocery")
    country = str(opportunity.get("country") or "India")
    state = str(opportunity.get("state") or "")
    city = str(opportunity.get("city") or "")
    area = str(opportunity.get("area") or "")
    currency = str(opportunity.get("currency") or "INR")
    budget_obj = opportunity.get("startupBudget") or {}
    estimated_budget = float(budget_obj.get("total_estimated_initial_investment") or 0.0)
    score = int(opportunity.get("score") or 75)
    report_json = json.dumps(opportunity, ensure_ascii=False)
    now_iso = datetime.now(timezone.utc).isoformat()
    engine = get_engine()

    with engine.begin() as conn:
        user_id = _get_or_create_user_id(conn, clean_email)
        existing = conn.execute(
            text(
                "SELECT id FROM saved_reports "
                "WHERE opportunity_id = :opp_id AND LOWER(user_email) = :email"
            ),
            {"opp_id": opp_id, "email": clean_email},
        ).mappings().first()

        if existing:
            report_db_id = int(existing["id"])
            conn.execute(
                text("""
                UPDATE saved_reports
                SET user_id = :user_id, report_json = :report_json, notes = :notes,
                    score = :score, estimated_budget = :estimated_budget
                WHERE id = :id
                """),
                {
                    "user_id": user_id,
                    "report_json": report_json,
                    "notes": notes,
                    "score": score,
                    "estimated_budget": estimated_budget,
                    "id": report_db_id,
                },
            )
        else:
            params = {
                "user_id": user_id,
                "opp_id": opp_id,
                "email": clean_email,
                "title": title,
                "category": category,
                "country": country,
                "state": state,
                "city": city,
                "area": area,
                "currency": currency,
                "estimated_budget": estimated_budget,
                "score": score,
                "report_json": report_json,
                "notes": notes,
                "created_at": now_iso,
            }
            if is_postgres_active():
                ins = conn.execute(
                    text("""
                    INSERT INTO saved_reports (
                        user_id, opportunity_id, user_email, title, category, country, state, city, area,
                        currency, estimated_budget, score, report_json, notes, created_at
                    )
                    VALUES (
                        :user_id, :opp_id, :email, :title, :category, :country, :state, :city, :area,
                        :currency, :estimated_budget, :score, :report_json, :notes, :created_at
                    )
                    RETURNING id
                    """),
                    params,
                ).mappings().first()
                report_db_id = int(ins["id"]) if ins else 0
            else:
                res = conn.execute(
                    text("""
                    INSERT INTO saved_reports (
                        user_id, opportunity_id, user_email, title, category, country, state, city, area,
                        currency, estimated_budget, score, report_json, notes, created_at
                    )
                    VALUES (
                        :user_id, :opp_id, :email, :title, :category, :country, :state, :city, :area,
                        :currency, :estimated_budget, :score, :report_json, :notes, :created_at
                    )
                    """),
                    params,
                )
                report_db_id = int(res.lastrowid or 0)

    return {
        "id": report_db_id,
        "user_id": user_id,
        "opportunity_id": opp_id,
        "user_email": clean_email,
        "title": title,
        "created_at": now_iso,
    }


def get_saved_reports(user_email: Optional[str] = None) -> List[Dict[str, Any]]:
    """Retrieves saved opportunity reports (filtered by user_email when provided)."""
    engine = get_engine()
    with engine.connect() as conn:
        if user_email and user_email.strip():
            rows = conn.execute(
                text(
                    "SELECT * FROM saved_reports "
                    "WHERE LOWER(user_email) = :email ORDER BY id DESC"
                ),
                {"email": user_email.strip().lower()},
            ).mappings().all()
        else:
            rows = conn.execute(
                text("SELECT * FROM saved_reports ORDER BY id DESC")
            ).mappings().all()

        reports = []
        for r in rows:
            item = dict(r)
            try:
                item["opportunity"] = json.loads(item.get("report_json") or "{}")
            except Exception:
                item["opportunity"] = {}
            item["created_at"] = str(item.get("created_at") or "")
            reports.append(item)
        return reports


def delete_saved_report(report_id: int, user_email: Optional[str] = None) -> bool:
    """Deletes a saved report by database ID (enforcing user_email match when provided)."""
    engine = get_engine()
    with engine.begin() as conn:
        if user_email and user_email.strip():
            res = conn.execute(
                text("DELETE FROM saved_reports WHERE id = :id AND LOWER(user_email) = :email"),
                {"id": int(report_id), "email": user_email.strip().lower()},
            )
        else:
            res = conn.execute(
                text("DELETE FROM saved_reports WHERE id = :id"),
                {"id": int(report_id)},
            )
        return (res.rowcount or 0) > 0


def get_cached_market_data(cache_key: str, max_age_minutes: int = 60) -> Optional[Dict[str, Any]]:
    """Retrieves cached external market data if present and within TTL."""
    engine = get_engine()
    with engine.connect() as conn:
        row = conn.execute(
            text("SELECT * FROM market_data_cache WHERE cache_key = :cache_key"),
            {"cache_key": cache_key},
        ).mappings().first()

    if not row:
        return None

    item = dict(row)
    try:
        retrieved_dt = datetime.fromisoformat(str(item["retrieved_at"]))
        if retrieved_dt.tzinfo is None:
            retrieved_dt = retrieved_dt.replace(tzinfo=timezone.utc)
        age_minutes = (datetime.now(timezone.utc) - retrieved_dt).total_seconds() / 60.0
        item["is_fresh"] = age_minutes <= max_age_minutes
        item["records"] = json.loads(item.get("records_json") or "[]")
        return item
    except Exception:
        return None


def set_cached_market_data(
    cache_key: str,
    source_name: str,
    country: str,
    city: str,
    category: str,
    records: List[Dict[str, Any]],
    retrieved_at: str,
) -> None:
    """Stores retrieved market data records in the database cache."""
    engine = get_engine()
    with engine.begin() as conn:
        conn.execute(
            text("""
            INSERT INTO market_data_cache (
                cache_key, source_name, country, city, category, records_json, retrieved_at
            )
            VALUES (
                :cache_key, :source_name, :country, :city, :category, :records_json, :retrieved_at
            )
            ON CONFLICT(cache_key) DO UPDATE SET
                source_name = excluded.source_name,
                records_json = excluded.records_json,
                retrieved_at = excluded.retrieved_at
            """),
            {
                "cache_key": cache_key,
                "source_name": source_name,
                "country": country,
                "city": city,
                "category": category,
                "records_json": json.dumps(records, ensure_ascii=False),
                "retrieved_at": retrieved_at,
            },
        )


def get_cached_fx_rates(base_currency: str) -> Optional[Dict[str, Any]]:
    """Retrieves cached exchange rates for a base currency."""
    engine = get_engine()
    with engine.connect() as conn:
        row = conn.execute(
            text("SELECT * FROM fx_rates_cache WHERE base_currency = :base"),
            {"base": base_currency.upper()},
        ).mappings().first()

    if not row:
        return None
    item = dict(row)
    try:
        item["rates"] = json.loads(item.get("rates_json") or "{}")
        return item
    except Exception:
        return None


def set_cached_fx_rates(
    base_currency: str,
    provider_name: str,
    rate_date: str,
    retrieved_at: str,
    rates: Dict[str, float],
) -> None:
    """Saves exchange rates for a base currency into the database."""
    engine = get_engine()
    with engine.begin() as conn:
        conn.execute(
            text("""
            INSERT INTO fx_rates_cache (
                base_currency, provider_name, rate_date, retrieved_at, rates_json
            )
            VALUES (:base, :provider, :rate_date, :retrieved_at, :rates_json)
            ON CONFLICT(base_currency) DO UPDATE SET
                provider_name = excluded.provider_name,
                rate_date = excluded.rate_date,
                retrieved_at = excluded.retrieved_at,
                rates_json = excluded.rates_json
            """),
            {
                "base": base_currency.upper(),
                "provider": provider_name,
                "rate_date": rate_date,
                "retrieved_at": retrieved_at,
                "rates_json": json.dumps(rates),
            },
        )


def get_prompt_cache_entry(cache_key: str) -> Optional[Dict[str, Any]]:
    """
    Retrieves a cached prompt/response record if present and not expired.
    Does not mutate hit_count directly (use record_prompt_cache_hit for atomic telemetry updates).
    """
    engine = get_engine()
    with engine.connect() as conn:
        row = conn.execute(
            text("SELECT * FROM prompt_cache WHERE cache_key = :cache_key"),
            {"cache_key": cache_key},
        ).mappings().first()

    if not row:
        return None

    item = dict(row)
    try:
        exp_dt = datetime.fromisoformat(str(item["expires_at"]))
        if exp_dt.tzinfo is None:
            exp_dt = exp_dt.replace(tzinfo=timezone.utc)
        if datetime.now(timezone.utc) > exp_dt:
            return None
        item["response"] = json.loads(item.get("response_json") or "{}")
        return item
    except Exception:
        return None


def set_prompt_cache_entry(
    cache_key: str,
    prompt_type: str,
    model_name: str,
    prefix_hash: str,
    payload_hash: str,
    normalized_prompt: str,
    response_data: Any,
    prompt_tokens_est: int,
    cached_tokens_est: int,
    completion_tokens_est: int,
    ttl_minutes: int = 1440,
) -> None:
    """Stores or updates a deterministic prompt cache entry."""
    now_utc = datetime.now(timezone.utc)
    now_iso = now_utc.isoformat()
    expires_iso = (now_utc + timedelta(minutes=max(1, ttl_minutes))).isoformat()
    response_json = json.dumps(response_data, ensure_ascii=False)
    engine = get_engine()

    with engine.begin() as conn:
        conn.execute(
            text("""
            INSERT INTO prompt_cache (
                cache_key, prompt_type, model_name, prefix_hash, payload_hash,
                normalized_prompt, response_json, prompt_tokens_est, cached_tokens_est,
                completion_tokens_est, hit_count, latency_saved_ms,
                created_at, last_accessed_at, expires_at
            )
            VALUES (
                :cache_key, :prompt_type, :model_name, :prefix_hash, :payload_hash,
                :normalized_prompt, :response_json, :prompt_tokens_est, :cached_tokens_est,
                :completion_tokens_est, 0, 0.0, :created_at, :last_accessed_at, :expires_at
            )
            ON CONFLICT(cache_key) DO UPDATE SET
                response_json = excluded.response_json,
                prompt_tokens_est = excluded.prompt_tokens_est,
                cached_tokens_est = excluded.cached_tokens_est,
                completion_tokens_est = excluded.completion_tokens_est,
                last_accessed_at = excluded.last_accessed_at,
                expires_at = excluded.expires_at
            """),
            {
                "cache_key": cache_key,
                "prompt_type": prompt_type,
                "model_name": model_name,
                "prefix_hash": prefix_hash,
                "payload_hash": payload_hash,
                "normalized_prompt": normalized_prompt[:4000],
                "response_json": response_json,
                "prompt_tokens_est": int(prompt_tokens_est),
                "cached_tokens_est": int(cached_tokens_est),
                "completion_tokens_est": int(completion_tokens_est),
                "created_at": now_iso,
                "last_accessed_at": now_iso,
                "expires_at": expires_iso,
            },
        )


def record_prompt_cache_hit(cache_key: str, latency_saved_ms: float = 18.0) -> None:
    """Atomically increments hit_count, adds latency_saved_ms, and updates last_accessed_at."""
    now_iso = datetime.now(timezone.utc).isoformat()
    engine = get_engine()
    with engine.begin() as conn:
        conn.execute(
            text("""
            UPDATE prompt_cache
            SET hit_count = COALESCE(hit_count, 0) + 1,
                latency_saved_ms = COALESCE(latency_saved_ms, 0.0) + :lat,
                last_accessed_at = :now_iso
            WHERE cache_key = :cache_key
            """),
            {"lat": float(latency_saved_ms), "now_iso": now_iso, "cache_key": cache_key},
        )


def get_prompt_cache_db_stats() -> Dict[str, Any]:
    """Aggregates prompt_cache statistics and returns breakdown by prompt_type + recent entries."""
    engine = get_engine()
    with engine.connect() as conn:
        agg_row_map = conn.execute(
            text("""
            SELECT
                COUNT(*) AS total_entries,
                COALESCE(SUM(hit_count), 0) AS total_db_hits,
                COALESCE(SUM(prompt_tokens_est), 0) AS total_prompt_tokens_stored,
                COALESCE(SUM(cached_tokens_est * (hit_count + 1)), 0) AS total_prefix_tokens_reused,
                COALESCE(SUM((prompt_tokens_est + completion_tokens_est) * hit_count), 0) AS total_tokens_saved_by_hits,
                COALESCE(SUM(latency_saved_ms), 0.0) AS total_latency_saved_ms
            FROM prompt_cache
            """)
        ).mappings().first()
        agg_row = dict(agg_row_map or {})

        by_type = [
            dict(r)
            for r in conn.execute(
                text("""
                SELECT
                    prompt_type,
                    COUNT(*) AS entries,
                    COALESCE(SUM(hit_count), 0) AS hits,
                    COALESCE(SUM(cached_tokens_est), 0) AS avg_prefix_tokens,
                    COALESCE(SUM(latency_saved_ms), 0.0) AS latency_saved_ms
                FROM prompt_cache
                GROUP BY prompt_type
                ORDER BY entries DESC
                """)
            ).mappings().all()
        ]

        recent_entries = [
            dict(r)
            for r in conn.execute(
                text("""
                SELECT
                    cache_key, prompt_type, model_name, prefix_hash, payload_hash,
                    prompt_tokens_est, cached_tokens_est, completion_tokens_est,
                    hit_count, latency_saved_ms, created_at, last_accessed_at, expires_at
                FROM prompt_cache
                ORDER BY last_accessed_at DESC
                LIMIT 12
                """)
            ).mappings().all()
        ]

    return {
        "summary": agg_row,
        "by_type": by_type,
        "recent_entries": recent_entries,
    }


def clear_prompt_cache_db(prompt_type: Optional[str] = None) -> int:
    """Deletes prompt cache entries (all or filtered by prompt_type)."""
    engine = get_engine()
    with engine.begin() as conn:
        if prompt_type and prompt_type.strip():
            res = conn.execute(
                text("DELETE FROM prompt_cache WHERE prompt_type = :pt"),
                {"pt": prompt_type.strip()},
            )
        else:
            res = conn.execute(text("DELETE FROM prompt_cache"))
        return int(res.rowcount or 0)
