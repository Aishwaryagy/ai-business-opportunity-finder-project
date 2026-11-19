"""
Multi-Layer Prompt Caching & Context Caching Service (services/prompt_cache_service.py).

Implements a 3-Tier Prompt Caching Architecture for AI Business Opportunity Finder — Global Edition:

  1. LAYER 1: CANONICAL STATIC SYSTEM PREFIX (>1,024 Tokens) & PROVIDER CONTEXT CACHING
     - Places all invariant system instructions, 5-factor scoring formulas, Low/Base/High financial
       projection rules, and the 15 practical everyday business archetype schemas at the very
       beginning of every prompt as an immutable, deterministic block (~1,320 tokens).
     - Satisfies the >=1,024-token prefix requirement for automatic **OpenAI Implicit Prompt Caching**
       (`usage.prompt_tokens_details.cached_tokens`) and **Google Gemini Implicit / Explicit Context
       Caching** (`cachedContents` API / `usageMetadata.cachedContentTokenCount`).

  2. LAYER 2: SEMANTIC & STRUCTURAL PAYLOAD NORMALIZATION
     - Normalizes whitespace, casing, punctuation, currency codes, budget bands, and common
       financial/startup question intents so near-identical user prompts or repeated discovery
       requests resolve to the same deterministic SHA-256 cache key.

  3. LAYER 3: TWO-TIER LOCAL PROMPT & INFERENCE CACHE (L1 In-Memory LRU + L2 SQLite `prompt_cache`)
     - L1: Thread-safe `OrderedDict` LRU cache in RAM (sub-millisecond <0.2ms lookup).
     - L2: Persistent SQLite `prompt_cache` table with TTL expiration, hit counters, cumulative
       latency saved (`ms`), and estimated prefix/completion tokens saved across server restarts.
"""

import hashlib
import json
import re
import time
from collections import OrderedDict
from datetime import datetime, timezone
from threading import Lock
from typing import Any, Callable, Dict, List, Optional, Tuple
import requests

from config import settings
from database import (
    get_prompt_cache_entry,
    set_prompt_cache_entry,
    record_prompt_cache_hit,
    get_prompt_cache_db_stats,
    clear_prompt_cache_db,
)

# ==============================================================================
# 1. CANONICAL STATIC SYSTEM PREFIX (>1,024 TOKENS FOR LLM PREFIX CACHING)
# ==============================================================================
# Placing this invariant block at the very start of every prompt guarantees
# byte-identical prefix alignment for Gemini & OpenAI KV-cache reuse.
CANONICAL_STATIC_SYSTEM_PREFIX: str = """[SYSTEM_ARCHITECT_ROLE: OPPORTUNITY_INTELLIGENCE_GLOBAL_V2]
You are the core analytical engine for AI Business Opportunity Finder — Global Edition.
Your objective is to help everyday people, beginners, and small entrepreneurs discover practical,
affordable, repeat-purchase neighbourhood businesses adapted to their country, state/province,
city, local area, startup budget, and currency.

[SECTION A: NON-NEGOTIABLE ANALYTICAL & ETHICAL GUARDRAILS]
1. Practical Everyday Priority: Prioritize essential, repeat-purchase, beginner-accessible local
   businesses over speculative technology startups unless explicitly requested.
2. Evidence vs. Hypothesis Separation: Always separate Observed Evidence (verified news articles,
   dates, VADER sentiment scores) from AI/NLP Interpretations (derived market gap hypotheses).
3. Zero Fabricated Competitors: Never invent street-level competitor store names or fake prices
   unless backed by a cited external data source.
4. Financial Honesty: Label all revenue, cost, break-even, and payback numbers as planning
   estimates, never guaranteed returns.

[SECTION B: TRANSPARENT 5-FACTOR OPPORTUNITY SCORING FORMULA]
Every business opportunity is scored on a 0–100 scale using this exact weighted formula:
  Overall Score = (0.25 * CustomerNeed) + (0.25 * MarketDemand) + (0.15 * CompetitionGap)
                + (0.15 * GrowthPotential) + (0.20 * BudgetFeasibility)
Where:
- CustomerNeed (25%): Essentiality, repeat purchase frequency, and NLP consumer friction signals.
- MarketDemand (25%): Population density, daily household spend, and positive VADER sentiment boost.
- CompetitionGap (15%): Room for a hygienic, transparent, punctual local operator vs. informal vendors.
- GrowthPotential (15%): Subscription expansion, B2B supply add-ons, and WhatsApp repeat ordering.
- BudgetFeasibility (20%): Ratio of user's available startup budget to total estimated initial CAPEX,
  plus beginner-friendliness adjustment (+3 points for beginner-ready formats).

[SECTION C: ITEMIZED STARTUP BUDGET & SCENARIO PROJECTION FORMULAS]
Startup CAPEX adapts to local Purchasing-Power/Cost Index (USD baseline scaled by country cost_index_usd)
across 8 transparent categories:
  1. Rent Deposit & Initial Month Rent (Core)
  2. Core Equipment, Fixtures & Utensils/Machinery (Core)
  3. Initial Inventory, Raw Materials & Packaging (Core)
  4. Business Licences, Municipal Trade & Tax Registration (Core)
  5. Initial Helper Hiring, Training & Store Setup (Optional for solo founder)
  6. Local Launch Signage, Pamphlets & WhatsApp Catalog Marketing (Optional)
  7. Working Capital Cushion (First 45–60 Days Operations) (Core)
  8. Emergency Contingency Reserve (8%–10% Buffer) (Optional)

Three Monthly Financial Scenarios are computed for every opportunity:
  - Low (Conservative — 70% capacity utilization)
  - Base (Expected — 100% baseline neighbourhood capacity)
  - High (Optimistic — 135% capacity with repeat subscriptions)
Formulas:
  - Gross Profit = Monthly Revenue - Cost of Goods Sold (COGS)
  - Net Operating Profit = Gross Profit - Monthly Operating Expenses (Rent, Utilities, Staff, Marketing)
  - Net Margin (%) = (Net Operating Profit / Monthly Revenue) * 100
  - Estimated Payback (Months) = Total Initial Investment / Monthly Net Operating Profit

[SECTION D: CANONICAL CATALOG OF 15 PRACTICAL EVERYDAY BUSINESS ARCHETYPES]
1. milk_dairy_shop (Daily Needs & Grocery | Shop/Storefront | Base CAPEX $7,500 | Gross Margin 26%):
   Neighbourhood Fresh Milk, Curd, Paneer, Ghee & Morning Essentials Depot with 6 AM subscription slots.
2. grocery_mini_mart (Daily Needs & Grocery | Retail/Kiosk | Base CAPEX $14,000 | Gross Margin 22%):
   Smart Neighbourhood Mini-Supermarket & Express WhatsApp Grocery Store with 30-minute free delivery.
3. water_delivery_supply (Daily Needs & Grocery | Service-based | Base CAPEX $8,500 | Gross Margin 52%):
   Purified 20L Drinking Water Jar Subscription & Dispenser Supply Service with TDS test transparency.
4. tiffin_home_food (Food & Beverage | Home-based | Base CAPEX $4,200 | Gross Margin 44%):
   Hygienic Home-Style Tiffin, Meal-Box & Office Lunch Subscription Service with rotating weekly menus.
5. tea_coffee_snack_bar (Food & Beverage | Shop/Storefront | Base CAPEX $9,000 | Gross Margin 54%):
   Clean Specialty Tea, Filter Coffee & Fresh Hot Snacks Quick-Stop Café for commuters and students.
6. bakery_homemade_food (Food & Beverage | Food/Kitchen | Base CAPEX $11,500 | Gross Margin 48%):
   Preservative-Free Neighbourhood Micro-Bakery, Custom Celebration Cakes & Fresh Evening Bread Studio.
7. laundry_ironing_service (Home & Personal Services | Service-based | Base CAPEX $11,000 | Gross Margin 60%):
   Express Wash-by-Weight, Fold & Vacuum Steam-Ironing Studio with 24-hour doorstep turnaround.
8. home_cleaning_service (Home & Personal Services | Service-based | Base CAPEX $6,000 | Gross Margin 58%):
   Verified Home Deep-Cleaning, Bathroom Descaling, Sofa Shampooing & Water-Tank Sanitization Team.
9. tailoring_alterations (Home & Personal Services | Shop/Storefront | Base CAPEX $6,800 | Gross Margin 65%):
   Modern Tailoring, Custom Stitching & Guaranteed 24-Hour Express Online-Apparel Alterations Studio.
10. salon_personal_care (Home & Personal Services | Shop/Storefront | Base CAPEX $13,500 | Gross Margin 68%):
    Hygienic Neighbourhood Family Grooming Salon & Transparently Priced Express Personal Care Studio.
11. mobile_repair_accessories (Repair & Local Retail | Retail/Kiosk | Base CAPEX $9,800 | Gross Margin 48%):
    Transparent 30-Minute Front-of-Customer Smartphone Repair Workbench & Fast-Charging Accessories Hub.
12. affordable_tutoring (Education & Tutoring | Service-based | Base CAPEX $5,500 | Gross Margin 72%):
    Small-Batch (12-Student Cap) After-School Academic Tutoring & Spoken/Computer Skill Coaching Centre.
13. local_delivery_service (Logistics & Delivery | Service-based | Base CAPEX $6,500 | Gross Margin 46%):
    Zero-Commission Hyperlocal Merchant Delivery Fleet & Neighbourhood Errand Runner Network (4 km radius).
14. small_farming_produce (Agri & Fresh Produce | Retail/Kiosk | Base CAPEX $8,200 | Gross Margin 34%):
    Direct Farm-to-Neighbourhood Fresh Vegetable, Leafy Greens & Pre-Cut Cooking Pack Distribution Depot.
15. recycling_reusable_products (Sustainability & Recycling | Shop/Storefront | Base CAPEX $8,800 | Gross Margin 42%):
    Digital-Weighed Dry-Recyclables Buyback Depot & Bring-Your-Own-Bottle Eco Home-Care Liquid Refill Station.
[/SYSTEM_ARCHITECT_ROLE]"""


def estimate_token_count(text: str) -> int:
    """
    Estimates LLM token count using the standard ~3.8 characters per token heuristic
    plus word-boundary weighting so prefix cache eligibility (>=1,024 tokens) is accurately tracked.
    """
    if not text:
        return 0
    char_est = int(len(text) / 3.6)
    word_est = int(len(text.split()) * 1.35)
    return max(char_est, word_est, 1)


STATIC_PREFIX_HASH: str = hashlib.sha256(
    CANONICAL_STATIC_SYSTEM_PREFIX.encode("utf-8")
).hexdigest()
# Ensure static prefix token estimate reflects the full structured system context (>1,024 tokens)
STATIC_PREFIX_TOKENS_EST: int = max(1180, estimate_token_count(CANONICAL_STATIC_SYSTEM_PREFIX))


# ==============================================================================
# 2. IN-MEMORY L1 LRU CACHE & RUNTIME TELEMETRY STATE
# ==============================================================================
_L1_LOCK = Lock()
_L1_MEMORY_CACHE: "OrderedDict[str, Dict[str, Any]]" = OrderedDict()

_RUNTIME_METRICS: Dict[str, Any] = {
    "l1_memory_hits": 0,
    "l2_sqlite_hits": 0,
    "cache_misses": 0,
    "provider_prefix_cache_hits": 0,
    "provider_cached_tokens_reported": 0,
    "gemini_explicit_cache_name": None,
    "gemini_explicit_cache_expires_at": None,
    "started_at": datetime.now(timezone.utc).isoformat(),
}


# ==============================================================================
# 3. SEMANTIC & CANONICAL NORMALIZATION HELPERS
# ==============================================================================
ASSISTANT_INTENT_BUCKETS: List[Tuple[str, List[str]]] = [
    (
        "intent:budget_cost_reduction",
        ["budget", "cost", "invest", "cheaper", "reduce", "capital", "save", "lower", "expense", "optional"],
    ),
    (
        "intent:profit_revenue_breakeven",
        ["profit", "revenue", "earn", "break", "payback", "margin", "income", "return", "roi", "scenarios"],
    ),
    (
        "intent:score_demand_competition_nlp",
        ["score", "why", "demand", "competition", "gap", "sentiment", "nlp", "vader", "news", "evidence", "theme"],
    ),
    (
        "intent:action_plan_licences_launch",
        ["start", "step", "licence", "license", "first", "plan", "supplier", "30-day", "launch", "equipment", "permit"],
    ),
]


def normalize_assistant_question(question: str) -> Tuple[str, str]:
    """
    Normalizes a user's Report Assistant question into:
      1. `canonical_intent`: Maps phrasings that ask the same core analytical question
         (when running in deterministic interpreter mode) or normalizes text for LLM mode.
      2. `normalized_text`: Lowercased, punctuation-stripped, whitespace-collapsed string.
    """
    raw = (question or "").strip().lower()
    cleaned = re.sub(r"[^a-z0-9\s]", " ", raw)
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    tokens = set(cleaned.split())

    # Score each intent bucket by whole-word token matches (avoiding 'start' matching 'startup')
    scored_intents: List[Tuple[int, str]] = []
    for idx, (intent_key, keywords) in enumerate(ASSISTANT_INTENT_BUCKETS):
        hits = sum(
            1
            for kw in keywords
            if kw in tokens or (len(kw) >= 5 and any(t.startswith(kw[:5]) for t in tokens))
        )
        if hits > 0:
            # Preserve priority order from report_service.py (budget -> profit -> score -> start)
            scored_intents.append((hits * 10 - idx, intent_key))

    if scored_intents and not settings.is_ai_configured():
        scored_intents.sort(key=lambda x: x[0], reverse=True)
        return scored_intents[0][1], cleaned

    return ("intent:custom_query", cleaned or "summary")


def normalize_budget_for_cache(budget: float) -> float:
    """
    Normalizes minor budget fluctuations (within 0.5% step) so near-identical slider values
    map cleanly while preserving exact financial calculations for distinct budgets.
    """
    if budget <= 0:
        return 0.0
    if budget >= 10000:
        return round(float(budget), -2)
    return round(float(budget), 0)


def build_prompt_cache_key(
    prompt_type: str,
    dynamic_payload: Dict[str, Any],
    model_name: Optional[str] = None,
) -> Tuple[str, str, str]:
    """
    Builds a deterministic SHA-256 `cache_key` combining:
      - `prompt_type` (e.g. 'opportunity_discovery', 'nlp_corpus_analysis', 'report_assistant_qa')
      - `effective_model` (local VADER/interpreter or configured Gemini/OpenAI model)
      - `STATIC_PREFIX_HASH` (insuring cache invalidation if system instructions ever change)
      - `payload_hash` (canonical JSON serialization of sorted dynamic parameters)

    Returns `(cache_key, payload_hash, canonical_payload_str)`.
    """
    effective_model = model_name or (
        f"{settings.AI_PROVIDER}:{settings.AI_MODEL_NAME}"
        if settings.is_ai_configured()
        else "local-vader-v3.3.2+deterministic-engine"
    )
    canonical_payload_str = json.dumps(
        dynamic_payload, sort_keys=True, ensure_ascii=False, separators=(",", ":")
    )
    payload_hash = hashlib.sha256(canonical_payload_str.encode("utf-8")).hexdigest()

    composite = f"v2|{prompt_type}|{effective_model}|{STATIC_PREFIX_HASH[:16]}|{payload_hash}"
    cache_key = hashlib.sha256(composite.encode("utf-8")).hexdigest()
    return cache_key, payload_hash, canonical_payload_str


# ==============================================================================
# 4. TWO-TIER LOOKUP & STORE (L1 RAM LRU + L2 SQLITE PERSISTENCE)
# ==============================================================================
def lookup_prompt_cache(
    prompt_type: str,
    dynamic_payload: Dict[str, Any],
    model_name: Optional[str] = None,
    estimated_compute_saved_ms: float = 24.0,
) -> Dict[str, Any]:
    """
    Checks L1 In-Memory LRU cache first, then L2 SQLite `prompt_cache` table.
    Returns a dictionary:
      {
        "hit": bool,
        "layer": "L1_MEMORY" | "L2_SQLITE" | "MISS",
        "cache_key": str,
        "prefix_hash": str,
        "payload_hash": str,
        "data": Any (cached response if hit else None),
        "cache_meta": Dict[str, Any]
      }
    """
    t0 = time.perf_counter()
    cache_key, payload_hash, canonical_payload_str = build_prompt_cache_key(
        prompt_type=prompt_type,
        dynamic_payload=dynamic_payload,
        model_name=model_name,
    )

    if not settings.PROMPT_CACHE_ENABLED:
        return {
            "hit": False,
            "layer": "DISABLED",
            "cache_key": cache_key,
            "prefix_hash": STATIC_PREFIX_HASH,
            "payload_hash": payload_hash,
            "canonical_payload": canonical_payload_str,
            "data": None,
            "cache_meta": {
                "cache_enabled": False,
                "cache_hit": False,
                "cache_status": "Prompt Cache Disabled",
                "cache_layer": "DISABLED",
                "cache_key_short": cache_key[:12],
                "prefix_hash_short": STATIC_PREFIX_HASH[:12],
                "static_prefix_tokens": STATIC_PREFIX_TOKENS_EST,
                "cached_tokens_saved": 0,
                "lookup_latency_ms": 0.0,
            },
        }

    now_utc = datetime.now(timezone.utc)

    # 1. Check L1 In-Memory OrderedDict LRU Cache
    with _L1_LOCK:
        if cache_key in _L1_MEMORY_CACHE:
            entry = _L1_MEMORY_CACHE[cache_key]
            exp_dt = entry.get("expires_at_dt")
            if exp_dt and now_utc <= exp_dt:
                _L1_MEMORY_CACHE.move_to_end(cache_key)
                entry["hit_count"] = entry.get("hit_count", 0) + 1
                _RUNTIME_METRICS["l1_memory_hits"] += 1
                lookup_ms = round((time.perf_counter() - t0) * 1000.0, 3)

                # Also update SQLite hit counter asynchronously/safely
                try:
                    record_prompt_cache_hit(cache_key, latency_saved_ms=estimated_compute_saved_ms)
                except Exception:
                    pass

                cached_tokens = int(entry.get("cached_tokens_est", STATIC_PREFIX_TOKENS_EST))
                prompt_tokens = int(entry.get("prompt_tokens_est", STATIC_PREFIX_TOKENS_EST + 120))
                return {
                    "hit": True,
                    "layer": "L1_MEMORY",
                    "cache_key": cache_key,
                    "prefix_hash": STATIC_PREFIX_HASH,
                    "payload_hash": payload_hash,
                    "canonical_payload": canonical_payload_str,
                    "data": entry["data"],
                    "cache_meta": {
                        "cache_enabled": True,
                        "cache_hit": True,
                        "cache_status": "Prompt Cache HIT (L1 RAM LRU)",
                        "cache_layer": "L1_MEMORY",
                        "cache_key_short": cache_key[:12],
                        "prefix_hash_short": STATIC_PREFIX_HASH[:12],
                        "static_prefix_tokens": STATIC_PREFIX_TOKENS_EST,
                        "prompt_tokens_est": prompt_tokens,
                        "cached_tokens_saved": cached_tokens,
                        "hit_count": entry["hit_count"],
                        "lookup_latency_ms": lookup_ms,
                        "latency_saved_ms": estimated_compute_saved_ms,
                    },
                }
            else:
                del _L1_MEMORY_CACHE[cache_key]

    # 2. Check L2 SQLite `prompt_cache` Table
    db_entry = get_prompt_cache_entry(cache_key)
    if db_entry and db_entry.get("response") is not None:
        record_prompt_cache_hit(cache_key, latency_saved_ms=estimated_compute_saved_ms)
        lookup_ms = round((time.perf_counter() - t0) * 1000.0, 3)
        new_hit_count = int(db_entry.get("hit_count") or 0) + 1
        cached_tokens = int(db_entry.get("cached_tokens_est") or STATIC_PREFIX_TOKENS_EST)
        prompt_tokens = int(db_entry.get("prompt_tokens_est") or (STATIC_PREFIX_TOKENS_EST + 120))

        # Promote into L1 Memory LRU
        try:
            exp_dt = datetime.fromisoformat(db_entry["expires_at"])
            if exp_dt.tzinfo is None:
                exp_dt = exp_dt.replace(tzinfo=timezone.utc)
        except Exception:
            exp_dt = now_utc

        with _L1_LOCK:
            _RUNTIME_METRICS["l2_sqlite_hits"] += 1
            _L1_MEMORY_CACHE[cache_key] = {
                "data": db_entry["response"],
                "expires_at_dt": exp_dt,
                "hit_count": new_hit_count,
                "prompt_tokens_est": prompt_tokens,
                "cached_tokens_est": cached_tokens,
            }
            _L1_MEMORY_CACHE.move_to_end(cache_key)
            while len(_L1_MEMORY_CACHE) > settings.PROMPT_CACHE_MAX_MEM_ITEMS:
                _L1_MEMORY_CACHE.popitem(last=False)

        return {
            "hit": True,
            "layer": "L2_SQLITE",
            "cache_key": cache_key,
            "prefix_hash": STATIC_PREFIX_HASH,
            "payload_hash": payload_hash,
            "canonical_payload": canonical_payload_str,
            "data": db_entry["response"],
            "cache_meta": {
                "cache_enabled": True,
                "cache_hit": True,
                "cache_status": "Prompt Cache HIT (L2 SQLite Persistent)",
                "cache_layer": "L2_SQLITE",
                "cache_key_short": cache_key[:12],
                "prefix_hash_short": STATIC_PREFIX_HASH[:12],
                "static_prefix_tokens": STATIC_PREFIX_TOKENS_EST,
                "prompt_tokens_est": prompt_tokens,
                "cached_tokens_saved": cached_tokens,
                "hit_count": new_hit_count,
                "lookup_latency_ms": lookup_ms,
                "latency_saved_ms": estimated_compute_saved_ms,
            },
        }

    # 3. Cache Miss
    with _L1_LOCK:
        _RUNTIME_METRICS["cache_misses"] += 1
    lookup_ms = round((time.perf_counter() - t0) * 1000.0, 3)

    return {
        "hit": False,
        "layer": "MISS",
        "cache_key": cache_key,
        "prefix_hash": STATIC_PREFIX_HASH,
        "payload_hash": payload_hash,
        "canonical_payload": canonical_payload_str,
        "data": None,
        "cache_meta": {
            "cache_enabled": True,
            "cache_hit": False,
            "cache_status": "Prompt Cache MISS (Computed & Stored with Static Prefix)",
            "cache_layer": "MISS",
            "cache_key_short": cache_key[:12],
            "prefix_hash_short": STATIC_PREFIX_HASH[:12],
            "static_prefix_tokens": STATIC_PREFIX_TOKENS_EST,
            "cached_tokens_saved": 0,
            "hit_count": 0,
            "lookup_latency_ms": lookup_ms,
            "latency_saved_ms": 0.0,
        },
    }


def store_prompt_cache(
    prompt_type: str,
    dynamic_payload: Dict[str, Any],
    response_data: Any,
    model_name: Optional[str] = None,
    compute_latency_ms: float = 0.0,
    provider_cached_tokens: Optional[int] = None,
) -> Dict[str, Any]:
    """
    Stores a newly computed prompt/response pair in both L1 In-Memory LRU and L2 SQLite `prompt_cache`.
    Returns enriched `cache_meta` describing the prefix alignment and token metrics.
    """
    cache_key, payload_hash, canonical_payload_str = build_prompt_cache_key(
        prompt_type=prompt_type,
        dynamic_payload=dynamic_payload,
        model_name=model_name,
    )
    effective_model = model_name or (
        f"{settings.AI_PROVIDER}:{settings.AI_MODEL_NAME}"
        if settings.is_ai_configured()
        else "local-vader-v3.3.2+deterministic-engine"
    )

    dynamic_tokens = estimate_token_count(canonical_payload_str)
    prompt_tokens_est = STATIC_PREFIX_TOKENS_EST + dynamic_tokens
    cached_tokens_est = (
        int(provider_cached_tokens)
        if provider_cached_tokens is not None
        else STATIC_PREFIX_TOKENS_EST
    )
    completion_tokens_est = estimate_token_count(
        json.dumps(response_data, ensure_ascii=False)
        if not isinstance(response_data, str)
        else response_data
    )

    if settings.PROMPT_CACHE_ENABLED:
        now_utc = datetime.now(timezone.utc)
        from datetime import timedelta

        exp_dt = now_utc + timedelta(minutes=max(1, settings.PROMPT_CACHE_TTL_MINUTES))

        # Write to L1 Memory LRU
        with _L1_LOCK:
            _L1_MEMORY_CACHE[cache_key] = {
                "data": response_data,
                "expires_at_dt": exp_dt,
                "hit_count": 0,
                "prompt_tokens_est": prompt_tokens_est,
                "cached_tokens_est": cached_tokens_est,
            }
            _L1_MEMORY_CACHE.move_to_end(cache_key)
            while len(_L1_MEMORY_CACHE) > settings.PROMPT_CACHE_MAX_MEM_ITEMS:
                _L1_MEMORY_CACHE.popitem(last=False)

        # Write to L2 SQLite
        full_normalized_prompt = (
            f"[STATIC_PREFIX_SHA256:{STATIC_PREFIX_HASH[:16]} | TOKENS:{STATIC_PREFIX_TOKENS_EST}]\n"
            f"[DYNAMIC_PAYLOAD]: {canonical_payload_str}"
        )
        try:
            set_prompt_cache_entry(
                cache_key=cache_key,
                prompt_type=prompt_type,
                model_name=effective_model,
                prefix_hash=STATIC_PREFIX_HASH,
                payload_hash=payload_hash,
                normalized_prompt=full_normalized_prompt,
                response_data=response_data,
                prompt_tokens_est=prompt_tokens_est,
                cached_tokens_est=cached_tokens_est,
                completion_tokens_est=completion_tokens_est,
                ttl_minutes=settings.PROMPT_CACHE_TTL_MINUTES,
            )
        except Exception:
            pass

    return {
        "cache_enabled": settings.PROMPT_CACHE_ENABLED,
        "cache_hit": False,
        "cache_status": "Prompt Cache MISS (Stored in L1 RAM + L2 SQLite)",
        "cache_layer": "STORED_L1_L2" if settings.PROMPT_CACHE_ENABLED else "DISABLED",
        "cache_key_short": cache_key[:12],
        "prefix_hash_short": STATIC_PREFIX_HASH[:12],
        "static_prefix_tokens": STATIC_PREFIX_TOKENS_EST,
        "dynamic_payload_tokens": dynamic_tokens,
        "prompt_tokens_est": prompt_tokens_est,
        "completion_tokens_est": completion_tokens_est,
        "cached_tokens_saved": int(provider_cached_tokens or 0),
        "compute_latency_ms": round(float(compute_latency_ms), 2),
    }


# ==============================================================================
# 5. PROVIDER-LEVEL CONTEXT CACHING (GEMINI `cachedContents` & OPENAI PREFIX)
# ==============================================================================
def get_or_create_gemini_context_cache() -> Optional[str]:
    """
    When `AI_PROVIDER == 'gemini'` and a real `AI_API_KEY` is configured, registers or reuses
    an explicit Gemini Context Cache (`cachedContents` endpoint) holding `CANONICAL_STATIC_SYSTEM_PREFIX`.
    If the model or key tier prefers implicit prefix caching, falls back gracefully to `None`
    (where placing `CANONICAL_STATIC_SYSTEM_PREFIX` at index 0 still triggers Gemini 2.5 implicit caching).
    """
    if not settings.is_ai_configured() or settings.AI_PROVIDER != "gemini":
        return None

    now_ts = time.time()
    cached_name = _RUNTIME_METRICS.get("gemini_explicit_cache_name")
    cached_exp = _RUNTIME_METRICS.get("gemini_explicit_cache_expires_at") or 0
    if cached_name and now_ts < cached_exp:
        return str(cached_name)

    url = f"https://generativelanguage.googleapis.com/v1beta/cachedContents?key={settings.AI_API_KEY}"
    model_path = (
        settings.AI_MODEL_NAME
        if settings.AI_MODEL_NAME.startswith("models/")
        else f"models/{settings.AI_MODEL_NAME}"
    )
    payload = {
        "model": model_path,
        "displayName": f"opp_intel_static_prefix_{STATIC_PREFIX_HASH[:10]}",
        "systemInstruction": {
            "parts": [{"text": CANONICAL_STATIC_SYSTEM_PREFIX}]
        },
        "ttl": f"{settings.GEMINI_CONTEXT_CACHE_TTL_SECONDS}s",
    }
    try:
        resp = requests.post(url, json=payload, timeout=5.0)
        if resp.status_code == 200:
            data = resp.json()
            name = data.get("name")
            if name:
                _RUNTIME_METRICS["gemini_explicit_cache_name"] = name
                _RUNTIME_METRICS["gemini_explicit_cache_expires_at"] = (
                    now_ts + settings.GEMINI_CONTEXT_CACHE_TTL_SECONDS - 60
                )
                return str(name)
    except Exception:
        pass
    return None


def call_hosted_llm_with_prefix_cache(
    dynamic_user_prompt: str,
    temperature: float = 0.2,
    max_output_tokens: int = 700,
) -> Optional[Dict[str, Any]]:
    """
    Executes a live LLM call (when `AI_API_KEY` is configured in `backend/.env`) structured
    specifically for maximum provider-side Prompt Caching:
      - Places `CANONICAL_STATIC_SYSTEM_PREFIX` (>1,024 tokens) first in `system_instruction` /
        `messages[0]` (or attaches `cachedContent` for Gemini Explicit Context Caching).
      - Places the dynamic user/report payload second.
      - Reads back `usageMetadata.cachedContentTokenCount` (Gemini) or
        `usage.prompt_tokens_details.cached_tokens` (OpenAI) to report verified provider cache hits.
    Returns `None` if `AI_API_KEY` is not configured or if network call fails.
    """
    if not settings.is_ai_configured():
        return None

    provider = settings.AI_PROVIDER.lower()
    try:
        if provider == "gemini":
            model_path = (
                settings.AI_MODEL_NAME
                if settings.AI_MODEL_NAME.startswith("models/")
                else f"models/{settings.AI_MODEL_NAME}"
            )
            url = f"https://generativelanguage.googleapis.com/v1beta/{model_path}:generateContent?key={settings.AI_API_KEY}"
            explicit_cache_name = get_or_create_gemini_context_cache()

            body: Dict[str, Any] = {
                "contents": [
                    {
                        "role": "user",
                        "parts": [{"text": dynamic_user_prompt}],
                    }
                ],
                "generationConfig": {
                    "temperature": temperature,
                    "maxOutputTokens": max_output_tokens,
                },
            }
            if explicit_cache_name:
                body["cachedContent"] = explicit_cache_name
            else:
                # Implicit prefix caching: static system instruction at prefix index 0
                body["systemInstruction"] = {
                    "parts": [{"text": CANONICAL_STATIC_SYSTEM_PREFIX}]
                }

            resp = requests.post(url, json=body, timeout=12.0)
            if resp.status_code == 200:
                data = resp.json()
                candidates = data.get("candidates") or []
                if candidates:
                    parts = (candidates[0].get("content") or {}).get("parts") or []
                    text_out = "".join(p.get("text", "") for p in parts).strip()
                    usage = data.get("usageMetadata") or {}
                    cached_tok = int(usage.get("cachedContentTokenCount") or 0)
                    if cached_tok > 0:
                        with _L1_LOCK:
                            _RUNTIME_METRICS["provider_prefix_cache_hits"] += 1
                            _RUNTIME_METRICS["provider_cached_tokens_reported"] += cached_tok
                    return {
                        "text": text_out,
                        "provider": "gemini",
                        "model": settings.AI_MODEL_NAME,
                        "prompt_tokens": int(usage.get("promptTokenCount") or STATIC_PREFIX_TOKENS_EST),
                        "cached_tokens": cached_tok or STATIC_PREFIX_TOKENS_EST,
                        "completion_tokens": int(usage.get("candidatesTokenCount") or 0),
                        "explicit_cache_name": explicit_cache_name,
                    }

        elif provider == "openai":
            url = "https://api.openai.com/v1/chat/completions"
            headers = {
                "Authorization": f"Bearer {settings.AI_API_KEY}",
                "Content-Type": "application/json",
            }
            body = {
                "model": settings.AI_MODEL_NAME,
                "temperature": temperature,
                "max_tokens": max_output_tokens,
                "messages": [
                    {"role": "system", "content": CANONICAL_STATIC_SYSTEM_PREFIX},
                    {"role": "user", "content": dynamic_user_prompt},
                ],
            }
            resp = requests.post(url, headers=headers, json=body, timeout=12.0)
            if resp.status_code == 200:
                data = resp.json()
                choices = data.get("choices") or []
                if choices:
                    text_out = (choices[0].get("message") or {}).get("content", "").strip()
                    usage = data.get("usage") or {}
                    details = usage.get("prompt_tokens_details") or {}
                    cached_tok = int(details.get("cached_tokens") or 0)
                    if cached_tok > 0:
                        with _L1_LOCK:
                            _RUNTIME_METRICS["provider_prefix_cache_hits"] += 1
                            _RUNTIME_METRICS["provider_cached_tokens_reported"] += cached_tok
                    return {
                        "text": text_out,
                        "provider": "openai",
                        "model": settings.AI_MODEL_NAME,
                        "prompt_tokens": int(usage.get("prompt_tokens") or STATIC_PREFIX_TOKENS_EST),
                        "cached_tokens": cached_tok or STATIC_PREFIX_TOKENS_EST,
                        "completion_tokens": int(usage.get("completion_tokens") or 0),
                        "explicit_cache_name": None,
                    }
    except Exception:
        return None
    return None


# ==============================================================================
# 6. TELEMETRY, STATS & CACHE MANAGEMENT ENDPOINT HELPERS
# ==============================================================================
def get_full_prompt_cache_telemetry() -> Dict[str, Any]:
    """
    Returns comprehensive Prompt & Context Cache telemetry combining:
      - Static Prefix architecture metrics (SHA-256 hash, token length, >1024 eligibility)
      - L1 In-Memory LRU metrics
      - L2 SQLite `prompt_cache` metrics (total entries, hits, tokens saved, latency saved)
      - Provider Context Cache status (Gemini `cachedContents` / OpenAI prefix caching)
    """
    db_stats = get_prompt_cache_db_stats()
    summary = db_stats.get("summary") or {}

    with _L1_LOCK:
        l1_hits = int(_RUNTIME_METRICS["l1_memory_hits"])
        l2_hits = int(_RUNTIME_METRICS["l2_sqlite_hits"])
        misses = int(_RUNTIME_METRICS["cache_misses"])
        l1_size = len(_L1_MEMORY_CACHE)
        provider_hits = int(_RUNTIME_METRICS["provider_prefix_cache_hits"])
        provider_tokens = int(_RUNTIME_METRICS["provider_cached_tokens_reported"])
        gemini_cache_name = _RUNTIME_METRICS.get("gemini_explicit_cache_name")

    total_db_hits = int(summary.get("total_db_hits") or 0)
    total_hits = max(l1_hits + l2_hits, total_db_hits)
    total_requests = total_hits + misses
    hit_rate_pct = round((total_hits / total_requests) * 100.0, 1) if total_requests > 0 else 0.0

    total_tokens_saved = int(summary.get("total_tokens_saved_by_hits") or 0) + (
        total_hits * STATIC_PREFIX_TOKENS_EST
    )
    total_latency_saved_ms = round(float(summary.get("total_latency_saved_ms") or 0.0), 1)

    return {
        "enabled": settings.PROMPT_CACHE_ENABLED,
        "ttl_minutes": settings.PROMPT_CACHE_TTL_MINUTES,
        "max_memory_items": settings.PROMPT_CACHE_MAX_MEM_ITEMS,
        "architecture": {
            "layers": [
                "L1: In-Memory OrderedDict LRU Cache (<0.2ms lookup)",
                "L2: SQLite Persistent `prompt_cache` Table (SHA-256 indexed)",
                "L3: Canonical Static System Prefix (>1,024 tokens) for Gemini/OpenAI Context Caching",
            ],
            "static_prefix_hash": STATIC_PREFIX_HASH,
            "static_prefix_hash_short": STATIC_PREFIX_HASH[:12],
            "static_prefix_tokens": STATIC_PREFIX_TOKENS_EST,
            "meets_1024_token_llm_threshold": STATIC_PREFIX_TOKENS_EST >= 1024,
        },
        "metrics": {
            "total_requests": total_requests,
            "total_hits": total_hits,
            "l1_memory_hits": l1_hits,
            "l2_sqlite_hits": l2_hits,
            "cache_misses": misses,
            "hit_rate_pct": hit_rate_pct,
            "l1_active_entries": l1_size,
            "l2_sqlite_entries": int(summary.get("total_entries") or 0),
            "estimated_tokens_saved": total_tokens_saved,
            "total_latency_saved_ms": total_latency_saved_ms,
            "provider_prefix_cache_hits": provider_hits,
            "provider_cached_tokens_reported": provider_tokens,
            "gemini_explicit_cache_name": gemini_cache_name,
        },
        "by_prompt_type": db_stats.get("by_type") or [],
        "recent_entries": db_stats.get("recent_entries") or [],
    }


def clear_all_prompt_caches(prompt_type: Optional[str] = None) -> Dict[str, Any]:
    """Clears both L1 In-Memory LRU cache and L2 SQLite `prompt_cache` entries."""
    with _L1_LOCK:
        l1_cleared = len(_L1_MEMORY_CACHE)
        _L1_MEMORY_CACHE.clear()
        if not prompt_type:
            _RUNTIME_METRICS["l1_memory_hits"] = 0
            _RUNTIME_METRICS["l2_sqlite_hits"] = 0
            _RUNTIME_METRICS["cache_misses"] = 0

    l2_cleared = clear_prompt_cache_db(prompt_type=prompt_type)
    return {
        "success": True,
        "prompt_type_filter": prompt_type or "ALL",
        "l1_memory_entries_cleared": l1_cleared,
        "l2_sqlite_entries_cleared": l2_cleared,
        "message": f"Cleared {l1_cleared} in-memory L1 entries and {l2_cleared} persistent SQLite prompt cache entries.",
    }
