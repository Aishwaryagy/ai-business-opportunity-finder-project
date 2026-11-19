"""
Real-Time Market Intelligence & Evidence Retrieval Service (services/market_data_service.py).
Responsibilities:
  1. Collects real-time market articles and consumer/business signals from:
     a) Configured NewsAPI.org (`MARKET_DATA_API_KEY`) if present, AND/OR
     b) Live public Google News RSS syndication (`https://news.google.com/rss/search`)
        tailored to the selected country, city, and business category.
  2. Preserves source name, source URL, publication date, retrieval timestamp, and
     location/category context for every record.
  3. Deduplicates records, caches results in SQLite (`market_data_cache`), and handles
     network timeouts or offline conditions gracefully.
  4. Never pretends that cached or fallback demo records are live:
     - Live fetch -> "Live data retrieved at [timestamp]"
     - SQLite cache -> "Cached data from [timestamp]"
     - Offline/fallback -> "Demo/sample data"
"""

import html
import re
import urllib.parse
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
import httpx

from config import settings
from database import get_cached_market_data, set_cached_market_data

# Preserve existing hyperlocal demographic context from the original project
LOCALITY_PROFILES: Dict[str, Dict[str, Dict[str, Any]]] = {
    "Shivamogga": {
        "Gandhi Nagar": {
            "type": "Central Commercial & Residential Neighborhood",
            "primary_demographic": "Families, retail traders, civil servants, students, daily commuters",
            "commercial_density": "High",
            "growth_drivers": "Central municipal retail arteries, bus terminal proximity, dense residential blocks",
            "consumer_behavior": "Strong daily demand for fresh milk/dairy, groceries, affordable home-style tiffin, and quick repair services",
            "market_gaps": "Hygienic neighbourhood dairy & grocery mini-marts, affordable daily tiffin subscriptions, water delivery, quick tailoring & laundry",
        },
        "Vinoba Nagar": {
            "type": "Prominent Upper-Middle Residential & Clinic Belt",
            "primary_demographic": "Doctors, teachers, families, school students, senior citizens",
            "commercial_density": "Medium-High",
            "growth_drivers": "Schools, specialty clinics, stable residential apartments",
            "consumer_behavior": "Quality-conscious households seeking fresh produce, pure dairy, tutoring, and reliable home cleaning",
            "market_gaps": "Fresh organic produce & dairy depot, after-school math/science tutoring, organized laundry & steam ironing",
        },
        "Gopi Circle": {
            "type": "High-Footfall Downtown Pedestrian & Commercial Junction",
            "primary_demographic": "Daily commuters, college youth, retail shoppers, office workers",
            "commercial_density": "Extreme",
            "growth_drivers": "Central traffic junction, retail showrooms, banking hub",
            "consumer_behavior": "High impulse purchases of tea, coffee, snacks, mobile accessories, and express repairs",
            "market_gaps": "Hygienic tea/coffee & fresh snack kiosk, express 30-minute mobile screen/battery repair shop",
        },
    },
    "Bangalore": {
        "Whitefield": {
            "type": "High-Density Tech Corridor & Gated Residential Suburb",
            "primary_demographic": "IT families, engineering students, dual-income households",
            "commercial_density": "Very High",
            "growth_drivers": "Metro line connectivity, IT parks, large apartment societies",
            "consumer_behavior": "Time-poor households relying on doorstep daily essentials, home food, laundry, and home cleaning",
            "market_gaps": "Healthy home-cooked tiffin service, doorstep laundry & dry cleaning, apartment deep-cleaning service",
        },
        "Koramangala": {
            "type": "University & Startup Residential Hub",
            "primary_demographic": "College students, young working professionals, long-term residents",
            "commercial_density": "Extreme",
            "growth_drivers": "University campuses, PG accommodations, high pedestrian footfall",
            "consumer_behavior": "High demand for budget-friendly daily meals, late-evening tea/snacks, laundry, and quick gadget repair",
            "market_gaps": "Affordable student tiffin & meal plans, self-service / express laundry studio, specialty tea & bakery counter",
        },
    },
}


def get_locality_context(country: str, state: str, city: str, area: str) -> Dict[str, Any]:
    """Returns demographic and commercial context for the selected location."""
    city_map = LOCALITY_PROFILES.get(city, {})
    profile = city_map.get(area)
    if not profile:
        profile = {
            "type": f"Active Residential & Commercial Micro-Market in {area}, {city}",
            "primary_demographic": f"Local households, working professionals, students, and small shopkeepers in {area} ({city}, {state}, {country})",
            "commercial_density": "Medium-High",
            "growth_drivers": f"Steady residential demand for everyday goods, food, personal care, and reliable local services in {city}",
            "consumer_behavior": "Strong repeat purchasing of daily household necessities, fresh food, repairs, and convenient neighbourhood services",
            "market_gaps": "Consistent quality in everyday essentials, transparent pricing, punctual doorstep delivery, and hygienic local storefronts",
        }
    return {
        "country": country,
        "state": state,
        "city": city,
        "area": area,
        "profile": profile,
        "summary": (
            f"{area} in {city} ({state}, {country}) is an {profile['type'].lower()}. "
            f"Primary customer segments include {profile['primary_demographic'].lower()}. "
            f"Key local pattern: {profile['consumer_behavior']}."
        ),
    }


def _strip_html(raw_text: str) -> str:
    """Removes HTML tags and decodes HTML entities from RSS descriptions."""
    if not raw_text:
        return ""
    clean = re.sub(r"<[^>]+>", " ", raw_text)
    clean = html.unescape(clean)
    clean = re.sub(r"\s+", " ", clean).strip()
    return clean


def _build_search_query(country: str, state: str, city: str, category: str) -> str:
    """Builds a targeted search query for local small business and consumer demand news."""
    cat_keywords = {
        "Daily Needs & Grocery": "grocery retail OR dairy milk shop OR local supermarket demand",
        "Food & Beverage": "food delivery OR tiffin service OR bakery cafe small business",
        "Home & Personal Services": "laundry service OR home cleaning OR salon personal care small business",
        "Repair & Local Retail": "mobile repair OR water delivery OR retail shop small business",
        "Education & Tutoring": "tutoring coaching classes OR skill education center demand",
        "Logistics & Delivery": "local courier delivery service OR hyperlocal logistics",
        "Agri & Fresh Produce": "fresh vegetable produce distribution OR dairy farming market",
        "Sustainability & Recycling": "recycling waste management OR eco refill products small business",
        "Healthcare & Wellness": "pharmacy diagnostics clinic OR home healthcare service",
        "Digital & B2B Services": "small business bookkeeping OR digital retail services",
    }
    kw = cat_keywords.get(category, "small business retail consumer demand local services")
    return f"{country} {state} {kw} when:4y"


def _fetch_from_newsapi(
    query: str, country: str, city: str, category: str, now_iso: str
) -> List[Dict[str, Any]]:
    """Queries NewsAPI.org when MARKET_DATA_API_KEY is configured in .env."""
    if not settings.is_market_api_configured():
        return []
    url = "https://newsapi.org/v2/everything"
    params = {
        "q": query,
        "language": "en",
        "sortBy": "publishedAt",
        "pageSize": 8,
        "apiKey": settings.MARKET_DATA_API_KEY,
    }
    records: List[Dict[str, Any]] = []
    with httpx.Client(timeout=5.0) as client:
        resp = client.get(url, params=params)
        if resp.status_code == 200:
            data = resp.json()
            for art in data.get("articles", []):
                title = (art.get("title") or "").strip()
                desc = _strip_html(art.get("description") or art.get("content") or "")
                link = (art.get("url") or "").strip()
                src_name = (art.get("source", {}).get("name") or "NewsAPI Source").strip()
                pub_date = (art.get("publishedAt") or now_iso)[:19].replace("T", " ")
                if title and link and "[Removed]" not in title:
                    records.append({
                        "title": title,
                        "snippet": desc if desc else title,
                        "source_name": f"{src_name} (via NewsAPI)",
                        "source_url": link,
                        "published_at": pub_date,
                        "retrieved_at": now_iso,
                        "location": f"{city}, {country}",
                        "category": category,
                        "is_live_source": True,
                    })
    return records


def _fetch_from_google_news_rss(
    query: str, country: str, country_code: str, city: str, category: str, now_iso: str
) -> List[Dict[str, Any]]:
    """
    Fetches real, current news articles from Google News Public RSS feed.
    Preserves exact article title, publisher name, article URL, and publication timestamp.
    """
    gl = (country_code or "IN").upper()
    encoded_q = urllib.parse.quote(query)
    rss_url = f"https://news.google.com/rss/search?q={encoded_q}&hl=en-{gl}&gl={gl}&ceid={gl}:en"

    records: List[Dict[str, Any]] = []
    headers = {"User-Agent": "Mozilla/5.0 (compatible; OpportunityIntelligenceBot/2.0)"}

    with httpx.Client(timeout=5.0, follow_redirects=True) as client:
        resp = client.get(rss_url, headers=headers)
        if resp.status_code != 200:
            return []

        root = ET.fromstring(resp.text)
        channel = root.find("channel")
        if channel is None:
            return []

        seen_titles = set()
        for item in channel.findall("item")[:10]:
            raw_title = (item.findtext("title") or "").strip()
            link = (item.findtext("link") or "").strip()
            pub_date = (item.findtext("pubDate") or "").strip()
            desc = _strip_html(item.findtext("description") or "")
            source_elem = item.find("source")
            source_name = (
                source_elem.text.strip()
                if source_elem is not None and source_elem.text
                else "Google News Syndicate"
            )

            if not raw_title or not link:
                continue

            # Deduplicate by normalized title
            norm_title = raw_title.lower()[:80]
            if norm_title in seen_titles:
                continue
            seen_titles.add(norm_title)

            # Clean snippet if it duplicates title
            snippet_text = desc if desc and len(desc) > len(raw_title) + 15 else raw_title

            records.append({
                "title": raw_title,
                "snippet": snippet_text[:320],
                "source_name": source_name,
                "source_url": link,
                "published_at": pub_date[:25] if pub_date else now_iso,
                "retrieved_at": now_iso,
                "location": f"{city}, {country}",
                "category": category,
                "is_live_source": True,
            })

    return records


def _get_fallback_demo_records(
    country: str, state: str, city: str, area: str, category: str, now_iso: str
) -> List[Dict[str, Any]]:
    """
    Provides clearly labelled illustrative sample records ONLY when external APIs
    are unreachable or return zero articles (e.g., offline mode or test mocks).
    Never claims these are live articles.
    """
    return [
        {
            "title": f"[Illustrative Sample] Rising household expenditure on daily essentials and convenient services in {city} ({state})",
            "snippet": (
                f"Residents in {area}, {city} report persistent challenges finding reliable, hygienic daily "
                f"suppliers for fresh groceries, dairy, home-style meals, and punctual household maintenance. "
                f"Price inflation and high delivery platform commissions create a strong gap for direct neighbourhood shops."
            ),
            "source_name": "Built-in Illustrative Market Profile (Offline / Demo Fallback)",
            "source_url": "https://data.worldbank.org/indicator/NE.CON.PRVT.CD",
            "published_at": "2026-10-01 (Baseline Reference)",
            "retrieved_at": now_iso,
            "location": f"{area}, {city}, {country}",
            "category": category,
            "is_live_source": False,
        },
        {
            "title": f"[Illustrative Sample] Small business consumer survey highlights demand for affordable repeat-purchase services in {city}",
            "snippet": (
                f"Consumers complain about inconsistent quality in unorganized local vendors and high markups on "
                f"aggregator apps in {area}. Practical businesses offering transparent pricing, subscription plans, "
                f"and WhatsApp-based local ordering see high repeat retention."
            ),
            "source_name": "Built-in Small Enterprise Reference Dataset (Demo Mode)",
            "source_url": "https://www.oecd.org/cfe/smes/",
            "published_at": "2026-10-01 (Baseline Reference)",
            "retrieved_at": now_iso,
            "location": f"{area}, {city}, {country}",
            "category": category,
            "is_live_source": False,
        },
        {
            "title": f"[Illustrative Sample] Neighbourhood retail and service micro-enterprises show resilient cash flow in {country}",
            "snippet": (
                f"Low-capex everyday businesses such as dairy depots, mini-supermarkets, laundry & ironing studios, "
                f"water delivery, and tutoring centres in {city} benefit from steady daily footfall and fast working-capital turnover."
            ),
            "source_name": "Built-in Sector Viability Reference (Demo Mode)",
            "source_url": "https://www.ifc.org/en/what-we-do/sector-expertise/financial-institutions/msme-finance",
            "published_at": "2026-10-01 (Baseline Reference)",
            "retrieved_at": now_iso,
            "location": f"{area}, {city}, {country}",
            "category": category,
            "is_live_source": False,
        },
    ]


def collect_market_intelligence(
    country: str,
    country_code: str,
    state: str,
    city: str,
    area: str,
    category: str,
    force_refresh: bool = False,
    allow_network: bool = True,
) -> Dict[str, Any]:
    """
    Collects market records for `(country, state, city, area, category)`.
    Returns:
      - `records`: list of article/evidence dicts
      - `data_status_label`: exact honest label ("Live data retrieved at ...", "Cached data from ...", or "Demo/sample data")
      - `source_summary`: human-readable description of sources and coverage limitations
      - `is_live`: bool
      - `is_cached`: bool
      - `locality_context`: demographic and commercial profile
    """
    now_iso = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    cache_key = f"{country_code}_{state}_{city}_{category}".lower().replace(" ", "_")
    locality_context = get_locality_context(country, state, city, area)

    # 1. Check fresh SQLite cache first (unless force_refresh=True)
    if not force_refresh:
        cached = get_cached_market_data(
            cache_key, max_age_minutes=settings.MARKET_DATA_CACHE_TTL_MINUTES
        )
        if cached and cached.get("is_fresh") and cached.get("records"):
            return {
                "records": cached["records"],
                "data_status_label": f"Cached data from {cached['retrieved_at']}",
                "source_name": cached["source_name"],
                "retrieved_at": cached["retrieved_at"],
                "is_live": False,
                "is_cached": True,
                "locality_context": locality_context,
                "coverage_note": (
                    f"Retrieved {len(cached['records'])} cached market articles from {cached['source_name']} "
                    f"(originally fetched at {cached['retrieved_at']}). Covers regional public news for {country}/{state}; "
                    f"hyperlocal street-level conditions in {area} should be verified in person."
                ),
            }

    # 2. Attempt live external retrieval if network is enabled
    query = _build_search_query(country, state, city, category)
    live_records: List[Dict[str, Any]] = []
    active_source_name = ""

    if allow_network:
        # Try NewsAPI first if configured
        if settings.is_market_api_configured():
            try:
                live_records = _fetch_from_newsapi(query, country, city, category, now_iso)
                if live_records:
                    active_source_name = "NewsAPI.org Live Market Feed"
            except Exception:
                live_records = []

        # Try public Google News RSS feed
        if not live_records:
            try:
                live_records = _fetch_from_google_news_rss(
                    query, country, country_code, city, category, now_iso
                )
                if live_records:
                    active_source_name = "Google News Public RSS Syndication"
            except Exception:
                live_records = []

    if live_records:
        set_cached_market_data(
            cache_key=cache_key,
            source_name=active_source_name,
            country=country,
            city=city,
            category=category,
            records=live_records,
            retrieved_at=now_iso,
        )
        return {
            "records": live_records,
            "data_status_label": f"Live data retrieved at {now_iso}",
            "source_name": active_source_name,
            "retrieved_at": now_iso,
            "is_live": True,
            "is_cached": False,
            "locality_context": locality_context,
            "coverage_note": (
                f"Analysed {len(live_records)} live news records retrieved at {now_iso} via {active_source_name} "
                f"for {country} ({state} / {city}). Public news feeds capture macro and regional sector trends, "
                f"not every street-level shop in {area}."
            ),
        }

    # 3. Check if an older expired cache exists before falling back to demo data
    stale_cached = get_cached_market_data(cache_key, max_age_minutes=999999)
    if stale_cached and stale_cached.get("records"):
        return {
            "records": stale_cached["records"],
            "data_status_label": f"Cached data from {stale_cached['retrieved_at']}",
            "source_name": stale_cached["source_name"],
            "retrieved_at": stale_cached["retrieved_at"],
            "is_live": False,
            "is_cached": True,
            "locality_context": locality_context,
            "coverage_note": (
                f"Using {len(stale_cached['records'])} previously cached market records from {stale_cached['retrieved_at']} "
                f"because live external news endpoints were unreachable."
            ),
        }

    # 4. Honest Demo/Sample Fallback
    demo_records = _get_fallback_demo_records(country, state, city, area, category, now_iso)
    return {
        "records": demo_records,
        "data_status_label": "Demo/sample data",
        "source_name": "Built-in Illustrative Market Dataset (Demo Mode)",
        "retrieved_at": now_iso,
        "is_live": False,
        "is_cached": False,
        "locality_context": locality_context,
        "coverage_note": (
            "External news APIs are currently unreachable or unconfigured. Displaying clearly labelled "
            "demo/sample market intelligence records so you can evaluate the full workflow offline."
        ),
    }
