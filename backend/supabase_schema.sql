-- ============================================================================
-- Supabase PostgreSQL Schema for AI Business Opportunity Finder — Global Edition
-- ============================================================================
-- Run this script in the Supabase SQL Editor (or let backend/database.py and
-- backend/migrate_sqlite_to_supabase.py initialize it automatically).
-- ============================================================================

-- 1. USERS TABLE
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

CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_users_session_token ON users(session_token);

-- 2. SEARCH HISTORY TABLE (Linked to users via user_id & user_email)
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

CREATE INDEX IF NOT EXISTS idx_search_history_user_id ON search_history(user_id);
CREATE INDEX IF NOT EXISTS idx_search_history_user_email ON search_history(user_email);
CREATE INDEX IF NOT EXISTS idx_search_history_created_at ON search_history(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_search_history_location ON search_history(country, state, city);
CREATE INDEX IF NOT EXISTS idx_search_history_domain ON search_history(domain);

-- 3. SAVED OPPORTUNITY REPORTS TABLE (Linked to users via user_id & user_email)
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

CREATE INDEX IF NOT EXISTS idx_saved_reports_user_id ON saved_reports(user_id);
CREATE INDEX IF NOT EXISTS idx_saved_reports_user_email ON saved_reports(user_email);
CREATE INDEX IF NOT EXISTS idx_saved_reports_created_at ON saved_reports(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_saved_reports_category ON saved_reports(category);

-- 4. EXTERNAL MARKET DATA CACHE TABLE
CREATE TABLE IF NOT EXISTS market_data_cache (
    cache_key TEXT PRIMARY KEY,
    source_name TEXT NOT NULL,
    country TEXT NOT NULL,
    city TEXT NOT NULL,
    category TEXT NOT NULL,
    records_json TEXT NOT NULL,
    retrieved_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_market_cache_loc_cat ON market_data_cache(country, city, category);

-- 5. CURRENCY EXCHANGE RATES CACHE TABLE
CREATE TABLE IF NOT EXISTS fx_rates_cache (
    base_currency TEXT PRIMARY KEY,
    provider_name TEXT NOT NULL,
    rate_date TEXT NOT NULL,
    retrieved_at TEXT NOT NULL,
    rates_json TEXT NOT NULL
);

-- 6. MULTI-LAYER PROMPT & CONTEXT CACHE TABLE
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

CREATE INDEX IF NOT EXISTS idx_prompt_cache_type ON prompt_cache(prompt_type);
CREATE INDEX IF NOT EXISTS idx_prompt_cache_expires ON prompt_cache(expires_at);
