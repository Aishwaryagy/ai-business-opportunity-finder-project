"""
FastAPI REST Application (main.py) for AI Business Opportunity Finder — Global Edition.
Exposes clean, well-documented endpoints for:
  - /api/health                 (System, DB, NLP model, and integration health check)
  - /api/countries              (Global countries with ISO codes, currencies, and subdivisions)
  - /api/locations              (Cascading subdivisions + legacy flat city mapping)
  - /api/currencies             (Supported ISO-4217 currencies and budget presets)
  - /api/currency/convert       (Live / cached / dated-reference currency conversion)
  - /api/categories             (Business categories, types, experience, and risk levels)
  - /api/dashboard              (Real KPI metrics, Recharts datasets, and system status)
  - /api/discover               (Global opportunity discovery with live news + VADER NLP)
  - /api/analyze                (Legacy-compatible discovery endpoint)
  - /api/history                (Saved search history from SQLite)
  - /api/reports/save           (Bookmark a detailed opportunity report)
  - /api/reports/saved          (Retrieve or delete bookmarked reports)
  - /api/reports/export-pdf     (Generate downloadable PDF report via fpdf2)
  - /api/assistant/query        (Interactive Report Interpreter Assistant)
  - /api/auth/start & /verify   (Passwordless email OTP verification with rate limiting)
"""

import secrets
from contextlib import asynccontextmanager
from typing import List, Dict, Any, Optional

from pathlib import Path
from fastapi import FastAPI, HTTPException, status, Query, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response, FileResponse
from fastapi.staticfiles import StaticFiles

from config import settings
from database import (
    init_db,
    get_active_database_info,
    authenticate_or_register_user_password,
    set_user_otp,
    verify_user_otp,
    save_search_history,
    get_user_history,
    count_user_history,
    get_history_record_by_id,
    delete_search_history_record,
    save_opportunity_report,
    get_saved_reports,
    delete_saved_report,
)
from models import (
    BUSINESS_CATEGORIES,
    AVAILABLE_DOMAINS,
    BUSINESS_TYPES,
    EXPERIENCE_LEVELS,
    RISK_PREFERENCES,
)
from schemas import (
    AuthStartRequest,
    AuthStartResponse,
    AuthVerifyRequest,
    AuthVerifyResponse,
    PasswordAuthRequest,
    PasswordAuthResponse,
    DiscoverRequest,
    DiscoverResponse,
    AnalyzeRequest,
    SaveReportRequest,
    AssistantQueryRequest,
)
from services.location_service import (
    get_all_countries,
    get_subdivisions_for_country,
    get_legacy_city_areas_mapping,
)
from services.currency_service import (
    get_all_supported_currencies,
    get_currency_info,
    convert_currency_amount,
    fetch_exchange_rates,
)
from services.opportunity_service import (
    discover_global_opportunities,
    analyze_opportunities,
)
from services.report_service import (
    compute_dashboard_summary,
    generate_opportunity_pdf_bytes,
    answer_report_assistant_query,
)
from services.prompt_cache_service import (
    get_full_prompt_cache_telemetry,
    clear_all_prompt_caches,
)
from services.email_service import send_otp_email, is_smtp_configured


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(
    title=settings.APP_NAME,
    description="Global Business Intelligence & Practical Opportunity Discovery Platform powered by FastAPI, VADER NLP, and SQLite.",
    version=settings.APP_VERSION,
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health")
def health_check() -> Dict[str, Any]:
    """Returns backend health, database status (Supabase PostgreSQL / SQLite), NLP engine readiness, Prompt Cache telemetry, and integration status."""
    cache_telemetry = get_full_prompt_cache_telemetry()
    db_info = get_active_database_info()
    return {
        "status": "ok",
        "service": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "database": db_info["label"],
        "database_info": db_info,
        "nlp_engine": {
            "name": "VADER-Lexicon-v3.3.2 + Statistical TF-IDF Theme Clusterer",
            "status": "active",
            "hosted_llm_configured": settings.is_ai_configured(),
        },
        "prompt_cache": {
            "enabled": cache_telemetry["enabled"],
            "ttl_minutes": cache_telemetry["ttl_minutes"],
            "static_prefix_hash": cache_telemetry["architecture"]["static_prefix_hash_short"],
            "static_prefix_tokens": cache_telemetry["architecture"]["static_prefix_tokens"],
            "meets_1024_token_threshold": cache_telemetry["architecture"]["meets_1024_token_llm_threshold"],
            **cache_telemetry["metrics"],
        },
        "integrations": {
            "supabase_configured": db_info["supabase_configured"],
            "supabase_connected": db_info["is_supabase"],
            "smtp_configured": is_smtp_configured(),
            "market_data_api_configured": settings.is_market_api_configured(),
            "public_news_rss_enabled": True,
            "exchange_rate_api_key_configured": settings.is_fx_api_key_configured(),
            "public_fx_api_enabled": True,
        },
    }


@app.get("/api/cache/stats")
def get_prompt_cache_stats_endpoint() -> Dict[str, Any]:
    """Returns detailed L1 In-Memory LRU + L2 SQLite Prompt Cache & Static Prefix telemetry."""
    return get_full_prompt_cache_telemetry()


@app.post("/api/cache/clear")
def clear_prompt_cache_endpoint(
    prompt_type: Optional[str] = Query(
        default=None,
        description="Optional filter: 'opportunity_discovery', 'nlp_corpus_analysis', or 'report_assistant_qa'",
    )
) -> Dict[str, Any]:
    """Purges L1 In-Memory LRU and L2 SQLite prompt cache entries."""
    return clear_all_prompt_caches(prompt_type=prompt_type)


@app.get("/api/categories")
def get_categories() -> Dict[str, Any]:
    """Returns business categories, business types, experience levels, and risk options."""
    return {
        "categories": BUSINESS_CATEGORIES,
        "business_types": BUSINESS_TYPES,
        "experience_levels": EXPERIENCE_LEVELS,
        "risk_preferences": RISK_PREFERENCES,
    }


@app.get("/api/domains")
def get_domains() -> Dict[str, List[str]]:
    """Returns domain list (backward compatible)."""
    return {"domains": AVAILABLE_DOMAINS}


@app.get("/api/countries")
def list_countries(q: Optional[str] = Query(default=None, description="Optional search filter")) -> Dict[str, Any]:
    """Returns supported global countries, ISO codes, currencies, and cascading subdivisions."""
    countries = get_all_countries(q)
    return {
        "count": len(countries),
        "countries": countries,
    }


@app.get("/api/locations")
def get_locations(country: Optional[str] = Query(default=None)) -> Dict[str, Any]:
    """
    Returns cascading subdivisions for a specific country if `country` query param is given,
    plus the flat `cities` map for backward compatibility.
    """
    if country:
        sub = get_subdivisions_for_country(country)
        return {
            **sub,
            "cities": get_legacy_city_areas_mapping(),
        }
    return {
        "countries": get_all_countries(),
        "cities": get_legacy_city_areas_mapping(),
    }


@app.get("/api/currencies")
def list_currencies(code: Optional[str] = Query(default=None)) -> Dict[str, Any]:
    """Returns currency metadata, symbols, and budget presets."""
    if code:
        return {"currency": get_currency_info(code)}
    return {"currencies": get_all_supported_currencies()}


@app.get("/api/currency/convert")
def convert_currency(
    amount: float = Query(..., gt=0, description="Amount to convert"),
    from_currency: str = Query(..., min_length=3, max_length=3),
    to_currency: str = Query(..., min_length=3, max_length=3),
) -> Dict[str, Any]:
    """Converts an amount between two ISO-4217 currencies with clear rate date and source."""
    try:
        return convert_currency_amount(amount, from_currency, to_currency)
    except ValueError as ve:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(ve))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Currency conversion error: {str(e)}",
        )


@app.get("/api/currency/rates")
def get_exchange_rates(base: str = Query(default="USD", min_length=3, max_length=3)) -> Dict[str, Any]:
    """Fetches current or cached/dated exchange rates for a base currency."""
    try:
        return fetch_exchange_rates(base)
    except ValueError as ve:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(ve))


@app.get("/api/dashboard")
def get_dashboard(email: Optional[str] = Query(default="")) -> Dict[str, Any]:
    """Returns real computed KPI metrics, Recharts datasets, and system status for the home dashboard."""
    return compute_dashboard_summary(email or "")


@app.post("/api/discover", response_model=DiscoverResponse)
def discover_opportunities_endpoint(payload: DiscoverRequest):
    """
    Primary Global Opportunity Discovery endpoint.
    Fetches real-time or cached/demo market records, runs pretrained VADER NLP sentiment
    and theme clustering, generates practical business ideas, computes itemized local-currency
    budgets and Low/Base/High financial projections, and persists the search to SQLite.
    """
    try:
        result = discover_global_opportunities(
            country=payload.country,
            state=payload.state,
            city=payload.city,
            area=payload.area or "Central Area",
            category=payload.category,
            budget=payload.budget,
            currency=payload.currency,
            target_currency=payload.target_currency,
            business_type=payload.business_type,
            experience_level=payload.experience_level,
            risk_preference=payload.risk_preference,
            recommend_everyday_simple=payload.recommend_everyday_simple,
            skills_and_interests=payload.skills_and_interests or "",
        )

        search_id = save_search_history(
            user_email=payload.email or "guest@opportunity.ai",
            domain=payload.category,
            city=result["city"],
            area=result["area"],
            user_query=payload.skills_and_interests or "",
            opportunities=result["opportunities"],
            country=result["country"],
            country_code=result["country_code"],
            state=result["state"],
            currency=result["currency"],
            budget=result["budget"],
            experience_level=payload.experience_level,
            risk_preference=payload.risk_preference,
            data_status_label=result["data_status_label"],
            nlp_summary=result["nlp_summary"],
        )
        result["search_id"] = search_id
        return result
    except ValueError as ve:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(ve))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to discover opportunities: {str(e)}",
        )


@app.post("/api/analyze")
def analyze_legacy_endpoint(payload: AnalyzeRequest):
    """Backward-compatible endpoint for `/api/analyze`."""
    if not payload.email or "@" not in payload.email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Valid user email is required for analysis.",
        )
    if not payload.domain or not payload.city or not payload.area:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Domain, city, and area are required.",
        )

    res = analyze_opportunities(
        domain=payload.domain,
        city=payload.city,
        area=payload.area,
        description=payload.description,
        user_email=payload.email,
        country=payload.country or "India",
        state=payload.state or "Karnataka",
        budget=payload.budget or 300000.0,
        currency=payload.currency or "INR",
    )
    record_id = save_search_history(
        user_email=payload.email,
        domain=payload.domain,
        city=payload.city,
        area=payload.area,
        user_query=payload.description,
        opportunities=res["opportunities"],
        country=res["country"],
        state=res["state"],
        currency=res["currency"],
        budget=res["budget"],
        data_status_label=res["data_status_label"],
        nlp_summary=res["nlp_summary"],
    )
    res["id"] = record_id
    return res


@app.get("/api/history")
def get_history(
    email: Optional[str] = Query(default=None, description="Authenticated user's email"),
    q: Optional[str] = Query(default=None, description="Search keyword filter"),
    country: Optional[str] = Query(default=None, description="Country filter"),
    state: Optional[str] = Query(default=None, description="State/province filter"),
    city: Optional[str] = Query(default=None, description="City/area filter"),
    category: Optional[str] = Query(default=None, description="Business category filter"),
    date_from: Optional[str] = Query(default=None, description="Start date YYYY-MM-DD"),
    date_to: Optional[str] = Query(default=None, description="End date YYYY-MM-DD"),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    include_meta: bool = Query(default=False, description="Return pagination envelope when true"),
    x_user_email: Optional[str] = Header(default=None, alias="X-User-Email"),
) -> Any:
    """
    Retrieves user-specific search history in reverse chronological order (newest first)
    with optional keyword, location, category, and date filtering.
    Enforces user-level access so one user's history is never exposed to another user.
    """
    effective_email = (email or x_user_email or "").strip().lower()
    if not effective_email:
        # Return empty list when no user identity is supplied so private history is never leaked
        return {"total": 0, "limit": limit, "offset": offset, "has_more": False, "items": []} if include_meta else []

    items = get_user_history(
        user_email=effective_email,
        limit=limit,
        offset=offset,
        search_query=q,
        country=country,
        state=state,
        city=city,
        category=category,
        date_from=date_from,
        date_to=date_to,
    )
    if include_meta:
        total = count_user_history(
            user_email=effective_email,
            search_query=q,
            country=country,
            state=state,
            city=city,
            category=category,
            date_from=date_from,
            date_to=date_to,
        )
        return {
            "total": total,
            "limit": limit,
            "offset": offset,
            "has_more": (offset + len(items)) < total,
            "items": items,
        }
    return items


@app.get("/api/history/{history_id}")
def get_single_history_record(
    history_id: int,
    email: Optional[str] = Query(default=None, description="Authenticated user's email"),
    x_user_email: Optional[str] = Header(default=None, alias="X-User-Email"),
) -> Dict[str, Any]:
    """Retrieves a specific historical search and its stored opportunity results for the current user."""
    effective_email = (email or x_user_email or "").strip().lower()
    if not effective_email:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User authentication email is required to view a history record.",
        )
    record = get_history_record_by_id(history_id=history_id, user_email=effective_email)
    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Search history record not found or access denied.",
        )
    return record


@app.delete("/api/history/{history_id}")
def delete_single_history_record(
    history_id: int,
    email: Optional[str] = Query(default=None, description="Authenticated user's email"),
    x_user_email: Optional[str] = Header(default=None, alias="X-User-Email"),
) -> Dict[str, Any]:
    """Deletes an individual search history record owned by the authenticated user."""
    effective_email = (email or x_user_email or "").strip().lower()
    if not effective_email:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User authentication email is required to delete a history record.",
        )
    deleted = delete_search_history_record(history_id=history_id, user_email=effective_email)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Search history record not found or access denied.",
        )
    return {"success": True, "deleted_id": history_id}


@app.post("/api/reports/save")
def save_report_endpoint(payload: SaveReportRequest) -> Dict[str, Any]:
    """Saves a detailed opportunity report for future review and comparison."""
    saved = save_opportunity_report(
        user_email=payload.user_email,
        opportunity=payload.opportunity,
        notes=payload.notes or "",
    )
    return {"success": True, "report": saved}


@app.get("/api/reports/saved")
def list_saved_reports(
    email: Optional[str] = Query(default=None),
    x_user_email: Optional[str] = Header(default=None, alias="X-User-Email"),
) -> Dict[str, Any]:
    """Returns bookmarked opportunity reports for the current user."""
    effective_email = (email or x_user_email or "").strip().lower()
    items = get_saved_reports(effective_email or None)
    return {"count": len(items), "reports": items}


@app.delete("/api/reports/saved/{report_id}")
def remove_saved_report(
    report_id: int,
    email: Optional[str] = Query(default=None),
    x_user_email: Optional[str] = Header(default=None, alias="X-User-Email"),
) -> Dict[str, Any]:
    """Deletes a saved opportunity report by ID."""
    effective_email = (email or x_user_email or "").strip().lower()
    deleted = delete_saved_report(report_id, user_email=effective_email or None)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Saved report not found.")
    return {"success": True, "deleted_id": report_id}


@app.post("/api/reports/export-pdf")
def export_pdf_endpoint(opportunity: Dict[str, Any]):
    """Generates a downloadable PDF file for the given opportunity object."""
    if not opportunity or not opportunity.get("title"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Valid opportunity data with a title is required for PDF export.",
        )
    pdf_bytes = generate_opportunity_pdf_bytes(opportunity)
    safe_name = "".join(
        c if c.isalnum() else "_" for c in str(opportunity.get("title", "opportunity"))[:35]
    )
    headers = {
        "Content-Disposition": f'attachment; filename="Opportunity_Report_{safe_name}.pdf"'
    }
    return Response(content=pdf_bytes, media_type="application/pdf", headers=headers)


@app.post("/api/assistant/query")
def assistant_query_endpoint(payload: AssistantQueryRequest) -> Dict[str, Any]:
    """Answers user questions about the active opportunity report."""
    return answer_report_assistant_query(payload.question, payload.opportunity)


@app.post("/api/auth/login", response_model=PasswordAuthResponse)
def login_with_password_endpoint(payload: PasswordAuthRequest):
    """
    Authenticates or creates a user account using PBKDF2-HMAC-SHA256 (260,000 iterations)
    salted password hashing stored in SQLite. No OTP required.
    """
    email = payload.email.strip().lower()
    password = payload.password
    mode = (payload.mode or "auto").strip().lower()

    ok, msg, user_record = authenticate_or_register_user_password(
        email=email, password=password, mode=mode
    )
    if not ok or not user_record:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=msg)

    return PasswordAuthResponse(
        success=True,
        message=msg,
        hash_algorithm="PBKDF2-HMAC-SHA256 (260,000 iterations + 128-bit salt)",
        user={
            "id": user_record["id"],
            "email": user_record["email"],
            "created_at": str(user_record.get("created_at", "")),
            "last_login_at": str(user_record.get("last_login_at", "")),
        },
        token=str(user_record.get("session_token") or f"biof_{secrets.token_urlsafe(16)}"),
    )


@app.post("/api/auth/register", response_model=PasswordAuthResponse)
def register_with_password_endpoint(payload: PasswordAuthRequest):
    """Creates a new user account with a PBKDF2-HMAC-SHA256 salted password hash."""
    payload.mode = "register"
    return login_with_password_endpoint(payload)


@app.post("/api/auth/start", response_model=AuthStartResponse)
def start_auth(payload: AuthStartRequest):
    """
    Generates a cryptographically secure 6-digit OTP using Python's `secrets` module,
    stores it with a 10-minute expiration and rate-limit tracking in SQLite,
    and sends via SMTP if configured. Never exposes OTPs in server logs.
    """
    email = payload.email.strip().lower()
    generated_code = f"{100000 + secrets.randbelow(900000)}"

    allowed, msg, _ = set_user_otp(email=email, otp_code=generated_code, expiry_minutes=10)
    if not allowed:
        raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail=msg)

    sent_successfully, delivery_msg = send_otp_email(recipient_email=email, otp_code=generated_code)
    if sent_successfully:
        return AuthStartResponse(
            success=True,
            message=delivery_msg,
            is_smtp_sent=True,
            expires_in_minutes=10,
            demo_mode_notice=None,
            dev_code=None,
        )
    else:
        return AuthStartResponse(
            success=True,
            message="SMTP is not configured in backend/.env. Running in Local Verification Demo Mode.",
            is_smtp_sent=False,
            expires_in_minutes=10,
            demo_mode_notice=(
                f"Demo Mode Verification Code: {generated_code} (Valid for 10 minutes; "
                f"configure SMTP_USER and SMTP_PASSWORD in backend/.env for live email delivery)."
            ),
            dev_code=generated_code,
        )


@app.post("/api/auth/verify", response_model=AuthVerifyResponse)
def verify_auth(payload: AuthVerifyRequest):
    """Verifies the 6-digit OTP against SQLite, enforcing expiry and rate limits."""
    email = payload.email.strip().lower()
    code = payload.code.strip()

    is_valid, msg, user_record = verify_user_otp(email=email, code=code)
    if not is_valid or not user_record:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=msg)

    return AuthVerifyResponse(
        success=True,
        message=msg,
        user={
            "id": user_record["id"],
            "email": user_record["email"],
            "created_at": str(user_record.get("created_at", "")),
            "last_login_at": str(user_record.get("last_login_at", "")),
        },
        token=str(user_record.get("session_token") or f"biof_{secrets.token_urlsafe(16)}"),
    )


# Serve the built React frontend (frontend/dist) on "/" so opening http://127.0.0.1:8000
# directly from the VS Code terminal loads the full application UI instead of {"detail": "Not Found"}.
FRONTEND_DIST_DIR = Path(__file__).resolve().parent.parent / "frontend" / "dist"
if (FRONTEND_DIST_DIR / "assets").is_dir():
    app.mount(
        "/assets",
        StaticFiles(directory=str(FRONTEND_DIST_DIR / "assets")),
        name="frontend_assets",
    )


@app.get("/", include_in_schema=False)
def serve_root():
    """Serves the React application UI on http://127.0.0.1:8000/ (or API status if dist is not built)."""
    index_file = FRONTEND_DIST_DIR / "index.html"
    if index_file.is_file():
        return FileResponse(str(index_file))
    return {
        "status": "ok",
        "service": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "frontend_dev_url": "http://127.0.0.1:5173",
        "swagger_docs_url": "http://127.0.0.1:8000/docs",
        "health_check_url": "http://127.0.0.1:8000/api/health",
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host=settings.HOST, port=settings.PORT, reload=True)
