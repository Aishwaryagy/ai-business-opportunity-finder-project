"""
Currency & Budget Conversion Service (services/currency_service.py).
Responsibilities:
  1. Maps ISO-4217 currency codes to symbols, names, decimal precision, and localized budget presets.
  2. Formats currency amounts accurately (e.g., Indian numbering system for INR, standard grouping for USD/EUR/GBP/JPY).
  3. Performs currency conversion using:
     a) Configured ExchangeRate-API (`EXCHANGE_RATE_API_KEY`) if present, OR
     b) Documented public unauthenticated ExchangeRate API (`open.er-api.com` / `api.frankfurter.dev`), OR
     c) SQLite cached rates, OR
     d) Clearly dated reference fallback rates (never pretending fallback rates are live).
"""

from datetime import datetime, timezone
from typing import Dict, Any, Optional, List
import httpx

from config import settings
from database import get_cached_fx_rates, set_cached_fx_rates

# Reference Baseline Exchange Rates relative to 1 USD (Dated Reference Fallback)
REFERENCE_FX_DATE = "2026-10-01"
REFERENCE_RATES_VS_USD: Dict[str, float] = {
    "USD": 1.0,
    "INR": 84.10,
    "GBP": 0.77,
    "EUR": 0.92,
    "JPY": 149.50,
    "CAD": 1.38,
    "AUD": 1.49,
    "AED": 3.6725,
    "SGD": 1.32,
    "NGN": 1600.0,
    "KES": 129.0,
    "ZAR": 17.60,
    "BRL": 5.45,
    "MXN": 19.35,
    "IDR": 15500.0,
    "PHP": 56.80,
}

CURRENCY_METADATA: Dict[str, Dict[str, Any]] = {
    "INR": {
        "code": "INR",
        "name": "Indian Rupee",
        "symbol": "₹",
        "decimals": 0,
        "presets": [
            {"id": "very_low", "label": "Very Low (Micro / Home-based)", "min": 25000, "max": 100000, "default": 50000},
            {"id": "low", "label": "Low (Kiosk / Small Service)", "min": 100000, "max": 350000, "default": 200000},
            {"id": "medium", "label": "Medium (Neighbourhood Shop)", "min": 350000, "max": 1000000, "default": 500000},
            {"id": "high", "label": "Higher Investment (Mini-Supermarket / Full Setup)", "min": 1000000, "max": 3500000, "default": 1500000},
        ],
    },
    "USD": {
        "code": "USD",
        "name": "United States Dollar",
        "symbol": "$",
        "decimals": 0,
        "presets": [
            {"id": "very_low", "label": "Very Low (Home / Mobile Service)", "min": 1000, "max": 5000, "default": 3000},
            {"id": "low", "label": "Low (Local Service / Kiosk)", "min": 5000, "max": 15000, "default": 10000},
            {"id": "medium", "label": "Medium (Small Storefront / Food Prep)", "min": 15000, "max": 50000, "default": 28000},
            {"id": "high", "label": "Higher Investment (Retail / Full Cafe)", "min": 50000, "max": 150000, "default": 75000},
        ],
    },
    "GBP": {
        "code": "GBP",
        "name": "British Pound Sterling",
        "symbol": "£",
        "decimals": 0,
        "presets": [
            {"id": "very_low", "label": "Very Low (Home / Sole Trader)", "min": 800, "max": 4000, "default": 2500},
            {"id": "low", "label": "Low (Local Service / Market Stall)", "min": 4000, "max": 12000, "default": 8000},
            {"id": "medium", "label": "Medium (High-Street Shop / Catering)", "min": 12000, "max": 40000, "default": 22000},
            {"id": "high", "label": "Higher Investment (Convenience Store / Salon)", "min": 40000, "max": 120000, "default": 60000},
        ],
    },
    "EUR": {
        "code": "EUR",
        "name": "Euro",
        "symbol": "€",
        "decimals": 0,
        "presets": [
            {"id": "very_low", "label": "Very Low (Home / Micro-Service)", "min": 1000, "max": 4500, "default": 2800},
            {"id": "low", "label": "Low (Kiosk / Local Service)", "min": 4500, "max": 15000, "default": 9500},
            {"id": "medium", "label": "Medium (Neighbourhood Store)", "min": 15000, "max": 45000, "default": 25000},
            {"id": "high", "label": "Higher Investment (Full Shop / Bakery)", "min": 45000, "max": 130000, "default": 65000},
        ],
    },
    "JPY": {
        "code": "JPY",
        "name": "Japanese Yen",
        "symbol": "¥",
        "decimals": 0,
        "presets": [
            {"id": "very_low", "label": "Very Low (Home / Tutoring / Service)", "min": 150000, "max": 700000, "default": 400000},
            {"id": "low", "label": "Low (Bento Stand / Repair Kiosk)", "min": 700000, "max": 2200000, "default": 1500000},
            {"id": "medium", "label": "Medium (Neighbourhood Shop / Cafe)", "min": 2200000, "max": 6500000, "default": 3800000},
            {"id": "high", "label": "Higher Investment (Mini-Mart / Full Store)", "min": 6500000, "max": 18000000, "default": 9500000},
        ],
    },
}


def get_currency_info(currency_code: str) -> Dict[str, Any]:
    """Returns metadata and tailored budget presets for an ISO-4217 currency code."""
    code = (currency_code or "INR").strip().upper()
    if code in CURRENCY_METADATA:
        return CURRENCY_METADATA[code]

    # Dynamically scale presets from USD using reference FX rate
    rate = REFERENCE_RATES_VS_USD.get(code, 1.0)
    symbol_map = {
        "CAD": "CA$",
        "AUD": "A$",
        "AED": "AED ",
        "SGD": "S$",
        "NGN": "₦",
        "KES": "KSh ",
        "ZAR": "R",
        "BRL": "R$",
        "MXN": "MX$",
        "IDR": "Rp",
        "PHP": "₱",
    }
    symbol = symbol_map.get(code, f"{code} ")
    usd_presets = CURRENCY_METADATA["USD"]["presets"]
    scaled_presets = []
    for p in usd_presets:
        scaled_presets.append({
            "id": p["id"],
            "label": p["label"],
            "min": round(p["min"] * rate, -2 if rate > 10 else 0),
            "max": round(p["max"] * rate, -2 if rate > 10 else 0),
            "default": round(p["default"] * rate, -2 if rate > 10 else 0),
        })

    return {
        "code": code,
        "name": f"{code} Currency",
        "symbol": symbol,
        "decimals": 0,
        "presets": scaled_presets,
    }


def format_indian_Grouping(n: int) -> str:
    """Formats an integer using the Indian numbering system (e.g., 5,00,000)."""
    s = str(abs(n))
    if len(s) <= 3:
        result = s
    else:
        last3 = s[-3:]
        rest = s[:-3]
        parts = []
        while len(rest) > 2:
            parts.append(rest[-2:])
            rest = rest[:-2]
        if rest:
            parts.append(rest)
        parts.reverse()
        result = ",".join(parts) + "," + last3
    return f"-{result}" if n < 0 else result


def format_currency(amount: float, currency_code: str = "INR") -> str:
    """
    Formats a numeric amount with the appropriate currency symbol and digit grouping.
    """
    code = (currency_code or "INR").strip().upper()
    info = get_currency_info(code)
    symbol = info["symbol"]
    rounded = int(round(amount))

    if code == "INR":
        return f"{symbol}{format_indian_Grouping(rounded)}"
    return f"{symbol}{rounded:,}"


def fetch_exchange_rates(base_currency: str = "USD", force_refresh: bool = False) -> Dict[str, Any]:
    """
    Fetches exchange rates for `base_currency`.
    Order of precedence:
      1. Fresh SQLite cache (unless force_refresh=True)
      2. Live ExchangeRate-API / Open ER API (`https://open.er-api.com/v6/latest/{base}`)
      3. Live Frankfurter ECB API (`https://api.frankfurter.dev/v1/latest?base={base}`)
      4. Cached SQLite record (labelled as Cached)
      5. Reference fallback table (clearly labelled with reference date)
    """
    base = (base_currency or "USD").strip().upper()
    if base not in REFERENCE_RATES_VS_USD and len(base) != 3:
        raise ValueError(f"Unsupported currency code: {base}")

    now_iso = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")

    # 1. Check SQLite Cache first if not forcing refresh
    if not force_refresh:
        cached = get_cached_fx_rates(base)
        if cached and cached.get("rates"):
            return {
                "base_currency": base,
                "provider": cached["provider_name"],
                "rate_date": cached["rate_date"],
                "retrieved_at": cached["retrieved_at"],
                "status_label": f"Cached exchange rates from {cached['retrieved_at']} (Rate Date: {cached['rate_date']})",
                "is_live": False,
                "is_cached": True,
                "rates": cached["rates"],
            }

    # 2. Try Live Exchange Rate API
    urls_to_try = []
    if settings.is_fx_api_key_configured():
        urls_to_try.append(
            (
                "ExchangeRate-API (Authenticated)",
                f"https://v6.exchangerate-api.com/v6/{settings.EXCHANGE_RATE_API_KEY}/latest/{base}",
            )
        )
    urls_to_try.extend([
        ("Open ExchangeRate-API (Live Public)", f"https://open.er-api.com/v6/latest/{base}"),
        ("Frankfurter ECB FX API (Live Public)", f"https://api.frankfurter.dev/v1/latest?base={base}"),
    ])

    for provider_name, url in urls_to_try:
        try:
            with httpx.Client(timeout=4.5) as client:
                resp = client.get(url)
                if resp.status_code == 200:
                    data = resp.json()
                    rates = data.get("rates") or data.get("conversion_rates")
                    if rates and isinstance(rates, dict):
                        rates[base] = 1.0
                        rate_date = (
                            data.get("date")
                            or data.get("time_last_update_utc", "")[:16]
                            or datetime.now(timezone.utc).strftime("%Y-%m-%d")
                        )
                        set_cached_fx_rates(
                            base_currency=base,
                            provider_name=provider_name,
                            rate_date=str(rate_date),
                            retrieved_at=now_iso,
                            rates=rates,
                        )
                        return {
                            "base_currency": base,
                            "provider": provider_name,
                            "rate_date": str(rate_date),
                            "retrieved_at": now_iso,
                            "status_label": f"Live data retrieved at {now_iso} (Rate date: {rate_date})",
                            "is_live": True,
                            "is_cached": False,
                            "rates": rates,
                        }
        except Exception:
            continue

    # 3. Check if we have any older cached record
    cached = get_cached_fx_rates(base)
    if cached and cached.get("rates"):
        return {
            "base_currency": base,
            "provider": cached["provider_name"],
            "rate_date": cached["rate_date"],
            "retrieved_at": cached["retrieved_at"],
            "status_label": f"Cached data from {cached['retrieved_at']} (Rate date: {cached['rate_date']})",
            "is_live": False,
            "is_cached": True,
            "rates": cached["rates"],
        }

    # 4. Compute from Reference Fallback Table (never claiming it is live)
    base_vs_usd = REFERENCE_RATES_VS_USD.get(base, 1.0)
    computed_rates = {
        code: round(rate_vs_usd / base_vs_usd, 6)
        for code, rate_vs_usd in REFERENCE_RATES_VS_USD.items()
    }
    return {
        "base_currency": base,
        "provider": f"Stored Reference Fallback Dataset (Dated {REFERENCE_FX_DATE})",
        "rate_date": REFERENCE_FX_DATE,
        "retrieved_at": now_iso,
        "status_label": f"Demo/sample reference rates dated {REFERENCE_FX_DATE} (Live FX API unreachable)",
        "is_live": False,
        "is_cached": False,
        "rates": computed_rates,
    }


def convert_currency_amount(
    amount: float, from_currency: str, to_currency: str
) -> Dict[str, Any]:
    """
    Converts `amount` from `from_currency` to `to_currency` and returns a transparent
    conversion breakdown with exchange-rate date and source label.
    """
    src = (from_currency or "INR").strip().upper()
    dst = (to_currency or "USD").strip().upper()
    if amount < 0:
        raise ValueError("Amount to convert cannot be negative.")

    fx_data = fetch_exchange_rates(src)
    rates = fx_data["rates"]

    if dst not in rates:
        # Try bridging via USD reference if missing in ECB response
        if src in REFERENCE_RATES_VS_USD and dst in REFERENCE_RATES_VS_USD:
            rate = REFERENCE_RATES_VS_USD[dst] / REFERENCE_RATES_VS_USD[src]
            rate_source = f"Reference Fallback Rate dated {REFERENCE_FX_DATE}"
            rate_date = REFERENCE_FX_DATE
            is_live = False
        else:
            raise ValueError(f"Unsupported target currency code: {dst}")
    else:
        rate = float(rates[dst])
        rate_source = fx_data["provider"]
        rate_date = fx_data["rate_date"]
        is_live = fx_data["is_live"]

    converted_val = round(amount * rate, 2)
    return {
        "original_amount": amount,
        "original_currency": src,
        "original_formatted": format_currency(amount, src),
        "target_currency": dst,
        "converted_amount": converted_val,
        "converted_formatted": format_currency(converted_val, dst),
        "exchange_rate": round(rate, 6),
        "rate_date": rate_date,
        "retrieved_at": fx_data["retrieved_at"],
        "provider": rate_source,
        "status_label": fx_data["status_label"],
        "is_live": is_live,
        "explanation": (
            f"Converted {format_currency(amount, src)} to {format_currency(converted_val, dst)} "
            f"at 1 {src} = {rate:.4f} {dst} (Source: {rate_source}, Rate Date: {rate_date})."
        ),
    }


def get_all_supported_currencies() -> List[Dict[str, Any]]:
    """Returns all supported currencies and their metadata."""
    return [get_currency_info(code) for code in REFERENCE_RATES_VS_USD.keys()]
