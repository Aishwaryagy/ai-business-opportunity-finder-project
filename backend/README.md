# Backend Documentation — AI Business Opportunity Finder (Global Edition)

See the root [README.md](../README.md) for the complete architecture diagram, scoring and financial formulas, API reference, and troubleshooting guide.

## Backend Module Summary (`backend/`)
- `main.py` — FastAPI application and REST API endpoints.
- `config.py` — Environment configuration loader (`backend/.env`).
- `database.py` — SQLite connection and parameterized queries for `users`, `search_history`, `saved_reports`, `market_data_cache`, and `fx_rates_cache`.
- `models.py` — Business categories, business types, experience levels, and risk preferences.
- `schemas.py` — Pydantic v2 request/response validation schemas.
- `services/location_service.py` — Global countries, ISO-3166 codes, ISO-4217 currencies, and cascading subdivisions.
- `services/currency_service.py` — Currency formatting, budget presets, and live/cached/dated exchange-rate conversion.
- `services/market_data_service.py` — Real-time public Google News RSS & optional NewsAPI collector with SQLite caching and honest data status labels.
- `services/nlp_analysis_service.py` — Pretrained VADER sentiment analysis and statistical TF-IDF problem theme clustering engine.
- `services/opportunity_service.py` — Practical everyday business recommendation engine.
- `services/scoring_service.py` — Transparent 5-factor weighted Opportunity Score calculator.
- `services/financial_service.py` — Itemized Startup Budget Breakdown and Low/Base/High monthly financial projections.
- `services/report_service.py` — Dashboard analytics aggregator, Report Interpreter Assistant, and `fpdf2` PDF generator.
- `services/email_service.py` — Passwordless 6-digit OTP email sender (SMTP + local demo fallback).
- `tests/test_all.py` — Automated `pytest` test suite covering unit, integration, NLP, financial, currency, and end-to-end user journeys.
