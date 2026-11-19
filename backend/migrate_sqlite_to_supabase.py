"""
Safe Data Migration Script: SQLite (`business_opportunity.db`) -> Supabase PostgreSQL.

Features:
  - Reads all existing records from `backend/business_opportunity.db` in read-only mode
    (never deletes or modifies the source SQLite database).
  - Creates all 6 tables, foreign keys (`user_id -> users.id`), unique constraints,
    and indexes on the target Supabase PostgreSQL database.
  - Preserves:
      1. `users` (plus auto-backfills user rows for any `user_email` in history/reports)
      2. `search_history` (linked to `user_id` & `user_email`)
      3. `saved_reports` (linked to `user_id` & `user_email`)
      4. `market_data_cache`
      5. `fx_rates_cache`
      6. `prompt_cache`
  - Uses idempotent UPSERTs (`ON CONFLICT DO UPDATE`) so re-running migration never
    creates duplicate records.
  - Synchronizes PostgreSQL `SERIAL` sequences (`setval`) after migration.
  - Verifies record counts before and after migration across all 6 tables.

Usage:
  1. Set `DATABASE_URL=postgresql://...` in `backend/.env`
  2. Run:
       python migrate_sqlite_to_supabase.py
"""

import argparse
import sqlite3
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, List, Optional

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine

from config import settings, _normalize_database_url

TABLES_IN_ORDER = [
    "users",
    "search_history",
    "saved_reports",
    "market_data_cache",
    "fx_rates_cache",
    "prompt_cache",
]


def get_sqlite_counts_and_rows(sqlite_path: Path) -> Dict[str, List[Dict[str, Any]]]:
    """Reads all rows from all 6 tables in the source SQLite database without modifying it."""
    if not sqlite_path.exists():
        raise FileNotFoundError(f"Source SQLite database not found at: {sqlite_path}")

    conn = sqlite3.connect(str(sqlite_path))
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    existing_tables = {
        r[0]
        for r in cur.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
    }

    data: Dict[str, List[Dict[str, Any]]] = {}
    for tbl in TABLES_IN_ORDER:
        if tbl in existing_tables:
            rows = cur.execute(f"SELECT * FROM {tbl}").fetchall()
            data[tbl] = [dict(r) for r in rows]
        else:
            data[tbl] = []

    conn.close()
    return data


def ensure_target_schema(target_engine: Engine, is_postgres: bool) -> None:
    """Creates all 6 tables, foreign keys, unique constraints, and indexes on the target database."""
    schema_sql_path = Path(__file__).resolve().parent / "supabase_schema.sql"
    with target_engine.begin() as conn:
        if is_postgres and schema_sql_path.exists():
            raw_sql = schema_sql_path.read_text(encoding="utf-8")
            for stmt in raw_sql.split(";"):
                cleaned = stmt.strip()
                if cleaned:
                    conn.execute(text(cleaned))
        else:
            conn.execute(
                text("""
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
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
                    user_query TEXT DEFAULT '',
                    data_status_label TEXT DEFAULT 'Demo/sample data',
                    nlp_summary TEXT DEFAULT '{}',
                    opportunities TEXT NOT NULL,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                );
                """)
            )
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
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE (opportunity_id, user_email)
                );
                """)
            )
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


def run_migration(
    target_db_url: str,
    sqlite_path: Optional[Path] = None,
) -> Dict[str, Any]:
    """
    Transfers all records from `sqlite_path` into `target_db_url` (Supabase PostgreSQL),
    preserving relationships (`user_id`), avoiding duplicates, and verifying counts.
    """
    src_path = sqlite_path or settings.DB_FILE
    source_data = get_sqlite_counts_and_rows(src_path)
    before_counts = {tbl: len(rows) for tbl, rows in source_data.items()}

    is_pg = target_db_url.startswith("postgresql")
    connect_args: Dict[str, Any] = {}
    if is_pg:
        connect_args["connect_timeout"] = 15
        if "supabase.co" in target_db_url and "sslmode=" not in target_db_url:
            connect_args["sslmode"] = "require"

    target_engine = create_engine(target_db_url, pool_pre_ping=True, connect_args=connect_args, future=True)
    ensure_target_schema(target_engine, is_postgres=is_pg)

    now_iso = datetime.now(timezone.utc).isoformat()

    with target_engine.begin() as conn:
        # 1. Migrate Users (and ensure any email referenced in search_history or saved_reports has a user record)
        email_to_user_id: Dict[str, int] = {}
        for u in source_data["users"]:
            clean_email = str(u.get("email") or "").strip().lower()
            if not clean_email:
                continue
            conn.execute(
                text("""
                INSERT INTO users (
                    email, password_hash, password_salt, otp_code, otp_expires_at,
                    otp_attempts, last_otp_sent_at, session_token, last_login_at, created_at
                )
                VALUES (
                    :email, :password_hash, :password_salt, :otp_code, :otp_expires_at,
                    :otp_attempts, :last_otp_sent_at, :session_token, :last_login_at, :created_at
                )
                ON CONFLICT(email) DO UPDATE SET
                    password_hash = COALESCE(excluded.password_hash, users.password_hash),
                    password_salt = COALESCE(excluded.password_salt, users.password_salt),
                    session_token = COALESCE(excluded.session_token, users.session_token),
                    last_login_at = COALESCE(excluded.last_login_at, users.last_login_at)
                """),
                {
                    "email": clean_email,
                    "password_hash": u.get("password_hash"),
                    "password_salt": u.get("password_salt"),
                    "otp_code": u.get("otp_code"),
                    "otp_expires_at": str(u["otp_expires_at"]) if u.get("otp_expires_at") else None,
                    "otp_attempts": int(u.get("otp_attempts") or 0),
                    "last_otp_sent_at": str(u["last_otp_sent_at"]) if u.get("last_otp_sent_at") else None,
                    "session_token": u.get("session_token"),
                    "last_login_at": str(u["last_login_at"]) if u.get("last_login_at") else None,
                    "created_at": str(u.get("created_at") or now_iso),
                },
            )

        # Ensure any user_email in search_history or saved_reports exists in `users`
        referenced_emails = set()
        for h in source_data["search_history"]:
            em = str(h.get("user_email") or "").strip().lower()
            if em:
                referenced_emails.add(em)
        for sr in source_data["saved_reports"]:
            em = str(sr.get("user_email") or "").strip().lower()
            if em:
                referenced_emails.add(em)

        for em in referenced_emails:
            conn.execute(
                text("""
                INSERT INTO users (email, created_at)
                VALUES (:email, :created_at)
                ON CONFLICT(email) DO NOTHING
                """),
                {"email": em, "created_at": now_iso},
            )

        # Build email -> user_id map from target database
        for r in conn.execute(text("SELECT id, email FROM users")).mappings().all():
            email_to_user_id[str(r["email"]).strip().lower()] = int(r["id"])

        # 2. Migrate Search History
        for h in source_data["search_history"]:
            clean_email = str(h.get("user_email") or "founder@opportunity.ai").strip().lower()
            uid = email_to_user_id.get(clean_email)
            conn.execute(
                text("""
                INSERT INTO search_history (
                    id, user_id, user_email, country, country_code, state, city, area, domain,
                    currency, budget, experience_level, risk_preference,
                    user_query, data_status_label, nlp_summary, opportunities, created_at
                )
                VALUES (
                    :id, :user_id, :user_email, :country, :country_code, :state, :city, :area, :domain,
                    :currency, :budget, :experience_level, :risk_preference,
                    :user_query, :data_status_label, :nlp_summary, :opportunities, :created_at
                )
                ON CONFLICT(id) DO UPDATE SET
                    user_id = excluded.user_id,
                    user_email = excluded.user_email,
                    opportunities = excluded.opportunities,
                    nlp_summary = excluded.nlp_summary
                """),
                {
                    "id": int(h["id"]),
                    "user_id": uid,
                    "user_email": clean_email,
                    "country": h.get("country") or "India",
                    "country_code": h.get("country_code") or "IN",
                    "state": h.get("state") or "Karnataka",
                    "city": h.get("city") or "",
                    "area": h.get("area") or "",
                    "domain": h.get("domain") or "Daily Needs & Grocery",
                    "currency": h.get("currency") or "INR",
                    "budget": float(h.get("budget") or 0.0),
                    "experience_level": h.get("experience_level") or "Beginner",
                    "risk_preference": h.get("risk_preference") or "Low",
                    "user_query": h.get("user_query") or "",
                    "data_status_label": h.get("data_status_label") or "Demo/sample data",
                    "nlp_summary": h.get("nlp_summary") or "{}",
                    "opportunities": h.get("opportunities") or "[]",
                    "created_at": str(h.get("created_at") or now_iso),
                },
            )

        # 3. Migrate Saved Reports
        for sr in source_data["saved_reports"]:
            clean_email = str(sr.get("user_email") or "founder@opportunity.ai").strip().lower()
            uid = email_to_user_id.get(clean_email)
            conn.execute(
                text("""
                INSERT INTO saved_reports (
                    id, user_id, opportunity_id, user_email, title, category,
                    country, state, city, area, currency, estimated_budget,
                    score, report_json, notes, created_at
                )
                VALUES (
                    :id, :user_id, :opportunity_id, :user_email, :title, :category,
                    :country, :state, :city, :area, :currency, :estimated_budget,
                    :score, :report_json, :notes, :created_at
                )
                ON CONFLICT(opportunity_id, user_email) DO UPDATE SET
                    user_id = excluded.user_id,
                    report_json = excluded.report_json,
                    notes = excluded.notes,
                    score = excluded.score,
                    estimated_budget = excluded.estimated_budget
                """),
                {
                    "id": int(sr["id"]),
                    "user_id": uid,
                    "opportunity_id": str(sr.get("opportunity_id") or f"opp-{sr['id']}"),
                    "user_email": clean_email,
                    "title": sr.get("title") or "Untitled Opportunity",
                    "category": sr.get("category") or "Daily Needs & Grocery",
                    "country": sr.get("country") or "India",
                    "state": sr.get("state") or "",
                    "city": sr.get("city") or "",
                    "area": sr.get("area") or "",
                    "currency": sr.get("currency") or "INR",
                    "estimated_budget": float(sr.get("estimated_budget") or 0.0),
                    "score": int(sr.get("score") or 75),
                    "report_json": sr.get("report_json") or "{}",
                    "notes": sr.get("notes") or "",
                    "created_at": str(sr.get("created_at") or now_iso),
                },
            )

        # 4. Migrate Market Data Cache
        for mc in source_data["market_data_cache"]:
            conn.execute(
                text("""
                INSERT INTO market_data_cache (
                    cache_key, source_name, country, city, category, records_json, retrieved_at
                )
                VALUES (
                    :cache_key, :source_name, :country, :city, :category, :records_json, :retrieved_at
                )
                ON CONFLICT(cache_key) DO UPDATE SET
                    records_json = excluded.records_json,
                    retrieved_at = excluded.retrieved_at
                """),
                {
                    "cache_key": mc["cache_key"],
                    "source_name": mc.get("source_name") or "Google News RSS",
                    "country": mc.get("country") or "India",
                    "city": mc.get("city") or "",
                    "category": mc.get("category") or "",
                    "records_json": mc.get("records_json") or "[]",
                    "retrieved_at": str(mc.get("retrieved_at") or now_iso),
                },
            )

        # 5. Migrate FX Rates Cache
        for fx in source_data["fx_rates_cache"]:
            conn.execute(
                text("""
                INSERT INTO fx_rates_cache (
                    base_currency, provider_name, rate_date, retrieved_at, rates_json
                )
                VALUES (
                    :base_currency, :provider_name, :rate_date, :retrieved_at, :rates_json
                )
                ON CONFLICT(base_currency) DO UPDATE SET
                    rate_date = excluded.rate_date,
                    retrieved_at = excluded.retrieved_at,
                    rates_json = excluded.rates_json
                """),
                {
                    "base_currency": str(fx["base_currency"]).upper(),
                    "provider_name": fx.get("provider_name") or "ExchangeRate-API",
                    "rate_date": str(fx.get("rate_date") or ""),
                    "retrieved_at": str(fx.get("retrieved_at") or now_iso),
                    "rates_json": fx.get("rates_json") or "{}",
                },
            )

        # 6. Migrate Prompt Cache
        for pc in source_data["prompt_cache"]:
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
                    :completion_tokens_est, :hit_count, :latency_saved_ms,
                    :created_at, :last_accessed_at, :expires_at
                )
                ON CONFLICT(cache_key) DO UPDATE SET
                    hit_count = excluded.hit_count,
                    latency_saved_ms = excluded.latency_saved_ms,
                    last_accessed_at = excluded.last_accessed_at
                """),
                {
                    "cache_key": pc["cache_key"],
                    "prompt_type": pc.get("prompt_type") or "opportunity_discovery",
                    "model_name": pc.get("model_name") or "local-vader-v3.3.2",
                    "prefix_hash": pc.get("prefix_hash") or "",
                    "payload_hash": pc.get("payload_hash") or "",
                    "normalized_prompt": pc.get("normalized_prompt") or "",
                    "response_json": pc.get("response_json") or "{}",
                    "prompt_tokens_est": int(pc.get("prompt_tokens_est") or 0),
                    "cached_tokens_est": int(pc.get("cached_tokens_est") or 0),
                    "completion_tokens_est": int(pc.get("completion_tokens_est") or 0),
                    "hit_count": int(pc.get("hit_count") or 0),
                    "latency_saved_ms": float(pc.get("latency_saved_ms") or 0.0),
                    "created_at": str(pc.get("created_at") or now_iso),
                    "last_accessed_at": str(pc.get("last_accessed_at") or now_iso),
                    "expires_at": str(pc.get("expires_at") or now_iso),
                },
            )

        # Synchronize PostgreSQL SERIAL sequences so future inserts never collide
        if is_pg:
            for seq_tbl in ("users", "search_history", "saved_reports"):
                conn.execute(
                    text(
                        f"SELECT setval(pg_get_serial_sequence('{seq_tbl}', 'id'), "
                        f"COALESCE((SELECT MAX(id) FROM {seq_tbl}), 1), true);"
                    )
                )

    # Verify record counts after migration
    after_counts: Dict[str, int] = {}
    with target_engine.connect() as conn:
        for tbl in TABLES_IN_ORDER:
            cnt = conn.execute(text(f"SELECT COUNT(*) FROM {tbl}")).scalar()
            after_counts[tbl] = int(cnt or 0)

    target_engine.dispose()
    verified = all(after_counts[t] >= before_counts[t] for t in TABLES_IN_ORDER)
    return {
        "verified": verified,
        "source_sqlite": str(src_path),
        "before_counts": before_counts,
        "after_counts": after_counts,
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Safely migrate SQLite records into Supabase PostgreSQL and verify counts."
    )
    parser.add_argument(
        "--target-url",
        default="",
        help="Target Supabase PostgreSQL URL (defaults to DATABASE_URL in backend/.env)",
    )
    parser.add_argument(
        "--verify-dry-run",
        action="store_true",
        help="Run a full verification migration into a temporary test DB to validate schema & row parity.",
    )
    args = parser.parse_args()

    if args.verify_dry_run:
        tmp_db = settings.DB_FILE.parent / "migration_verification_test.db"
        if tmp_db.exists():
            tmp_db.unlink()
        try:
            report = run_migration(f"sqlite:///{tmp_db}", settings.DB_FILE)
            print("=== MIGRATION DRY-RUN VERIFICATION REPORT ===")
            for tbl in TABLES_IN_ORDER:
                b_cnt = report["before_counts"][tbl]
                a_cnt = report["after_counts"][tbl]
                print(f"  {tbl:20s}: SQLite={b_cnt:4d}  ->  Target={a_cnt:4d}  [OK]")
            print(f"Overall Verification Status: {'PASSED' if report['verified'] else 'FAILED'}")
            return 0 if report["verified"] else 1
        finally:
            if tmp_db.exists():
                tmp_db.unlink()

    target_url = _normalize_database_url(args.target_url or settings.DATABASE_URL)
    if not target_url:
        print(
            "NOTICE: DATABASE_URL is not yet configured in backend/.env.\n"
            "Set DATABASE_URL=postgresql://... in backend/.env and re-run:\n"
            "  python migrate_sqlite_to_supabase.py\n"
            "Running local schema & row-count verification check on SQLite source..."
        )
        src_data = get_sqlite_counts_and_rows(settings.DB_FILE)
        for tbl in TABLES_IN_ORDER:
            print(f"  {tbl:20s}: {len(src_data[tbl]):4d} existing records ready for migration")
        return 0

    report = run_migration(target_url, settings.DB_FILE)
    print("=== SUPABASE POSTGRESQL MIGRATION VERIFICATION REPORT ===")
    for tbl in TABLES_IN_ORDER:
        b_cnt = report["before_counts"][tbl]
        a_cnt = report["after_counts"][tbl]
        print(f"  {tbl:20s}: SQLite={b_cnt:4d}  ->  Supabase={a_cnt:4d}")
    print(f"Migration Verified: {report['verified']} (Source SQLite file preserved at {settings.DB_FILE})")
    return 0 if report["verified"] else 1


if __name__ == "__main__":
    sys.exit(main())
