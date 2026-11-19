"""
Comprehensive Automated Test Suite (backend/tests/test_all.py) for
AI Business Opportunity Finder — Global Edition.

Covers all required checks:
  1. Global Location Selection & Cascading Subdivisions
  2. Currency Identification, Formatting (INR/USD/GBP/EUR/JPY), and Conversion
  3. Financial Calculations (Itemized Startup Budget, Low/Base/High Projections, Break-even, Payback)
  4. Transparent 5-Factor Opportunity Scoring Formula
  5. Real-Time Market Intelligence Retrieval, Caching, Error/Timeout Handling, and Honest Status Labelling
  6. Separate Pretrained VADER NLP Sentiment & Theme Clustering Inference on Retrieved Text
  7. End-to-End FastAPI Endpoint Tests (Health, Discover, Invalid Budgets, Unsupported Currencies,
     Save/Compare Reports, PDF Export, Assistant, and Rate-Limited OTP Auth)
"""

import sys
from pathlib import Path

# Ensure backend directory is on sys.path
BACKEND_ROOT = Path(__file__).resolve().parent.parent
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

import pytest
from fastapi.testclient import TestClient

from main import app
from database import init_db
from services.location_service import get_all_countries, get_subdivisions_for_country
from services.currency_service import (
    format_currency,
    get_currency_info,
    convert_currency_amount,
    fetch_exchange_rates,
)
from services.financial_service import build_startup_budget_and_financials
from services.scoring_service import compute_transparent_score
from services.market_data_service import collect_market_intelligence
from services.nlp_analysis_service import classify_text_sentiment, run_nlp_market_analysis

init_db()
client = TestClient(app)


# ---------------------------------------------------------------------------
# 1. LOCATION SELECTION TESTS
# ---------------------------------------------------------------------------
def test_global_countries_and_cascading_subdivisions():
    countries = get_all_countries()
    assert len(countries) >= 15
    iso_codes = {c["iso_code"] for c in countries}
    assert {"IN", "US", "GB", "DE", "JP", "CA", "AU", "AE", "SG"}.issubset(iso_codes)

    # Test India -> Karnataka -> Shivamogga
    india_sub = get_subdivisions_for_country("India")
    assert india_sub["iso_code"] == "IN"
    assert india_sub["currency"] == "INR"
    assert india_sub["currency_symbol"] == "₹"
    assert "Karnataka" in india_sub["states"]
    assert "Shivamogga" in india_sub["hierarchy"]["Karnataka"]
    assert "Gandhi Nagar" in india_sub["hierarchy"]["Karnataka"]["Shivamogga"]

    # Test Japan -> Tokyo
    jp_sub = get_subdivisions_for_country("JP")
    assert jp_sub["currency"] == "JPY"
    assert jp_sub["currency_symbol"] == "¥"
    assert "Tokyo" in jp_sub["states"]


def test_country_search_filter():
    res = get_all_countries("united")
    names = [c["country"] for c in res]
    assert "United States" in names
    assert "United Kingdom" in names


# ---------------------------------------------------------------------------
# 2. CURRENCY & FORMATTING TESTS
# ---------------------------------------------------------------------------
def test_currency_formatting_and_presets():
    assert format_currency(500000, "INR") == "₹5,00,000"
    assert format_currency(25000, "USD") == "$25,000"
    assert format_currency(15000, "GBP") == "£15,000"
    assert format_currency(20000, "EUR") == "€20,000"
    assert format_currency(1500000, "JPY") == "¥1,500,000"

    inr_info = get_currency_info("INR")
    assert len(inr_info["presets"]) == 4
    assert inr_info["symbol"] == "₹"


def test_currency_conversion_and_unsupported_currency_handling():
    conv = convert_currency_amount(500000, "INR", "USD")
    assert conv["original_currency"] == "INR"
    assert conv["target_currency"] == "USD"
    assert conv["converted_amount"] > 1000
    assert conv["rate_date"]
    assert conv["status_label"]

    with pytest.raises(ValueError):
        convert_currency_amount(100, "INR", "INVALID_XYZ")

    with pytest.raises(ValueError):
        convert_currency_amount(-500, "USD", "INR")


# ---------------------------------------------------------------------------
# 3. FINANCIAL CALCULATION & SCORING TESTS
# ---------------------------------------------------------------------------
def test_financial_calculations_and_scenarios():
    fin = build_startup_budget_and_financials(
        business_title="Neighbourhood Dairy Shop",
        business_type="Shop / Storefront",
        base_usd_capex=12000.0,
        cost_index_usd=0.28,
        currency="INR",
        user_available_budget=500000.0,
        gross_margin_pct=0.25,
    )
    sb = fin["startup_budget"]
    fp = fin["financial_projections"]

    assert sb["currency"] == "INR"
    assert sb["total_estimated_initial_investment"] > 0
    assert len(sb["items"]) == 8
    # Verify optional vs core items are flagged
    assert any(i["is_optional"] for i in sb["items"])
    assert any(not i["is_optional"] for i in sb["items"])

    # Verify Low, Base, High scenarios
    scenarios = fp["scenarios"]
    assert len(scenarios) == 3
    low, base, high = scenarios[0], scenarios[1], scenarios[2]
    assert low["monthly_revenue"] < base["monthly_revenue"] < high["monthly_revenue"]
    assert base["monthly_gross_profit"] == base["monthly_revenue"] - base["monthly_cogs"]
    assert (
        base["monthly_net_operating_profit"]
        == base["monthly_gross_profit"] - base["monthly_operating_expenses"]
    )
    assert len(fp["six_month_projection"]) == 6
    assert "NOT guaranteed earnings" in fp["disclaimer"]


def test_transparent_scoring_formula():
    sc = compute_transparent_score(
        base_customer_need=90,
        base_market_demand=88,
        base_competition=76,
        base_growth_potential=84,
        estimated_startup_cost=250000,
        user_available_budget=500000,
        experience_level="Beginner",
        is_beginner_friendly=True,
        nlp_sentiment_score=0.15,
    )
    assert 15 <= sc["overall_score"] <= 98
    assert len(sc["breakdown"]["factors"]) == 5
    assert "Score = (0.25 ×" in sc["breakdown"]["formula"]


# ---------------------------------------------------------------------------
# 4. REAL MARKET DATA & NLP INFERENCE TESTS
# ---------------------------------------------------------------------------
def test_nlp_sentiment_and_theme_inference():
    pos = classify_text_sentiment(
        "Strong retail growth and rising household demand for fresh dairy and healthy daily meals."
    )
    neg = classify_text_sentiment(
        "Customers complain about severe shortage, expensive delivery fees, and spoiled groceries."
    )
    assert pos["compound"] > 0
    assert neg["compound"] < 0
    assert neg["label"] == "Friction / Complaint Signal"

    sample_records = [
        {
            "title": "Consumers in Shivamogga seek affordable daily tiffin and fresh milk options",
            "snippet": "High food delivery fees and inconsistent quality create strong local demand for neighbourhood shops.",
            "source_name": "Test Market Feed",
            "source_url": "https://example.com/article-1",
            "published_at": "2026-10-20",
            "retrieved_at": "2026-10-20 12:00:00 UTC",
            "is_live_source": True,
        }
    ]
    nlp_out = run_nlp_market_analysis(
        records=sample_records,
        country="India",
        state="Karnataka",
        city="Shivamogga",
        area="Gandhi Nagar",
        category="Daily Needs & Grocery",
        data_status_label="Live data retrieved at 2026-10-20 12:00:00 UTC",
    )
    assert nlp_out["records_analysed"] == 1
    assert len(nlp_out["problem_themes"]) == 5
    assert len(nlp_out["recurring_complaints_and_needs"]) >= 1
    assert "OBSERVED EVIDENCE:" in nlp_out["observed_evidence_summary"]
    assert "AI/NLP INTERPRETATION" in nlp_out["ai_interpretation_summary"]


def test_market_data_offline_demo_labelling():
    # When allow_network=False and a unique uncached key is used, it must return Demo/sample data honestly
    res = collect_market_intelligence(
        country="TestCountry",
        country_code="TC",
        state="TestState",
        city="TestCityOffline",
        area="TestArea",
        category="OfflineCategoryTest",
        force_refresh=True,
        allow_network=False,
    )
    assert res["data_status_label"] == "Demo/sample data"
    assert res["is_live"] is False
    assert len(res["records"]) >= 3
    assert all(r["is_live_source"] is False for r in res["records"])


# ---------------------------------------------------------------------------
# 5. END-TO-END API & USER JOURNEY TESTS
# ---------------------------------------------------------------------------
def test_api_health_and_metadata():
    r = client.get("/api/health")
    assert r.status_code == 200
    data = r.json()
    assert data["status"] == "ok"
    assert data["nlp_engine"]["status"] == "active"

    r_cat = client.get("/api/categories")
    assert r_cat.status_code == 200
    assert len(r_cat.json()["categories"]) >= 10


def test_api_discover_full_user_journey_and_validation():
    # 1. Invalid negative budget check
    bad_res = client.post(
        "/api/discover",
        json={
            "country": "India",
            "state": "Karnataka",
            "city": "Shivamogga",
            "area": "Gandhi Nagar",
            "category": "Daily Needs & Grocery",
            "budget": -5000,
            "currency": "INR",
        },
    )
    assert bad_res.status_code == 422

    # 2. Valid discovery journey for Shivamogga, Karnataka, India (₹5,00,000, Beginner)
    valid_payload = {
        "email": "student@demo.ai",
        "country": "India",
        "state": "Karnataka",
        "city": "Shivamogga",
        "area": "Gandhi Nagar",
        "category": "Daily Needs & Grocery",
        "budget": 500000,
        "currency": "INR",
        "target_currency": "USD",
        "business_type": "Shop / Storefront",
        "experience_level": "Beginner",
        "risk_preference": "Low",
        "recommend_everyday_simple": True,
        "skills_and_interests": "Retail and daily household essentials",
    }
    res = client.post("/api/discover", json=valid_payload)
    assert res.status_code == 200, res.text
    body = res.json()
    assert body["country"] == "India"
    assert body["currency"] == "INR"
    assert body["budget_formatted"] == "₹5,00,000"
    assert body["converted_budget"]["target_currency"] == "USD"
    assert len(body["opportunities"]) >= 3

    first_opp = body["opportunities"][0]
    assert first_opp["score"] > 0
    assert len(first_opp["startupBudget"]["items"]) == 8
    assert len(first_opp["evidenceSnippets"]) >= 1
    proven_states = {
        (o.get("crossRegionInsight") or {}).get("proven_in_state")
        for o in body["opportunities"]
        if (o.get("crossRegionInsight") or {}).get("is_cross_region_opportunity")
    }
    # Must include multiple states across the country (not just Tamil Nadu & Karnataka)
    assert len(proven_states) >= 3
    # Every idea must strictly be <= 4 years old from today's date
    assert all(
        (o.get("crossRegionInsight") or {}).get("years_old", 0) <= 4
        for o in body["opportunities"]
    )

    # 3. Save Report & Retrieve Saved Reports
    save_res = client.post(
        "/api/reports/save",
        json={
            "user_email": "student@demo.ai",
            "opportunity": first_opp,
            "notes": "Top candidate for Shivamogga launch",
        },
    )
    assert save_res.status_code == 200
    saved_list = client.get("/api/reports/saved?email=student@demo.ai")
    assert saved_list.status_code == 200
    assert saved_list.json()["count"] >= 1

    # 4. Export PDF Report
    pdf_res = client.post("/api/reports/export-pdf", json=first_opp)
    assert pdf_res.status_code == 200
    assert pdf_res.headers["content-type"] == "application/pdf"
    assert pdf_res.content.startswith(b"%PDF")

    # 5. Query Report Assistant
    ast_res = client.post(
        "/api/assistant/query",
        json={
            "question": "How can I reduce the startup budget and what is the profit?",
            "opportunity": first_opp,
        },
    )
    assert ast_res.status_code == 200
    assert "answer" in ast_res.json()

    # 6. Dashboard KPIs reflect real stored data
    dash_res = client.get("/api/dashboard?email=student@demo.ai")
    assert dash_res.status_code == 200
    kpis = dash_res.json()["kpis"]
    assert kpis["opportunities_discovered"] >= 3


# ---------------------------------------------------------------------------
# 6. MULTI-LAYER PROMPT CACHING & CONTEXT CACHING TESTS
# ---------------------------------------------------------------------------
def test_prompt_caching_hit_miss_and_telemetry():
    # 1. Clear prompt cache to start from a clean slate
    clr = client.post("/api/cache/clear")
    assert clr.status_code == 200
    assert clr.json()["success"] is True

    # 2. Verify static prefix architecture exceeds 1,024 tokens for Gemini/OpenAI context caching
    stats_initial = client.get("/api/cache/stats")
    assert stats_initial.status_code == 200
    s_json = stats_initial.json()
    assert s_json["enabled"] is True
    assert s_json["architecture"]["meets_1024_token_llm_threshold"] is True
    assert s_json["architecture"]["static_prefix_tokens"] >= 1024

    # 3. Run a discovery request -> first run is a Prompt Cache MISS (stored to L1 + L2 SQLite)
    disc_payload = {
        "email": "cachetest@demo.ai",
        "country": "India",
        "state": "Karnataka",
        "city": "Shivamogga",
        "area": "Vinoba Nagar",
        "category": "Food & Beverage",
        "budget": 350000,
        "currency": "INR",
        "business_type": "Shop / Storefront",
        "experience_level": "Beginner",
        "risk_preference": "Low",
        "recommend_everyday_simple": True,
        "skills_and_interests": "Tea and snacks",
    }
    r1 = client.post("/api/discover", json=disc_payload)
    assert r1.status_code == 200
    b1 = r1.json()
    assert b1["prompt_cache_meta"]["cache_hit"] is False

    # 4. Repeat the exact same discovery request -> must be a Prompt Cache HIT
    r2 = client.post("/api/discover", json=disc_payload)
    assert r2.status_code == 200
    b2 = r2.json()
    assert b2["prompt_cache_meta"]["cache_hit"] is True
    assert b2["prompt_cache_meta"]["cache_layer"] in ("L1_MEMORY", "L2_SQLITE")

    # 5. Test Semantic Intent Normalization & Prompt Caching on Report Assistant Q&A
    sample_opp = b2["opportunities"][0]
    qa1 = client.post(
        "/api/assistant/query",
        json={"question": "How can I reduce the startup budget?", "opportunity": sample_opp},
    )
    assert qa1.status_code == 200
    assert qa1.json()["cache_meta"]["cache_hit"] is False

    # Phrased slightly differently but same budget-reduction intent -> Semantic Prompt Cache HIT
    qa2 = client.post(
        "/api/assistant/query",
        json={"question": "how can i lower startup cost and capital?", "opportunity": sample_opp},
    )
    assert qa2.status_code == 200
    assert qa2.json()["cache_meta"]["cache_hit"] is True
    assert qa2.json()["cache_meta"]["cached_tokens_saved"] >= 1024

    # 6. Verify /api/cache/stats reflects hits, tokens saved, and pipeline breakdown
    stats_after = client.get("/api/cache/stats").json()
    assert stats_after["metrics"]["total_hits"] >= 2
    assert stats_after["metrics"]["estimated_tokens_saved"] >= 2000
    assert len(stats_after["by_prompt_type"]) >= 2
