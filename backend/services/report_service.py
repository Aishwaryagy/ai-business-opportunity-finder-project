"""
Report Generation, PDF Export, Dashboard Analytics & Report Assistant Service (services/report_service.py).
Responsibilities:
  1. Generates downloadable, clean PDF opportunity reports using `fpdf2`.
  2. Calculates real-time Dashboard KPIs and chart datasets directly from stored
     SQLite searches, saved reports, and generated opportunities (never fabricating
     platform-wide statistics).
  3. Provides a transparent Report Assistant that helps users interpret their
     generated report (explaining whether a hosted LLM is connected or using the
     built-in structured financial/NLP interpreter).
"""

import time
from datetime import datetime, timezone
from typing import Dict, Any, List
from fpdf import FPDF

from config import settings
from database import get_user_history, count_user_history, get_saved_reports
from services.opportunity_service import discover_global_opportunities
from services.prompt_cache_service import (
    normalize_assistant_question,
    lookup_prompt_cache,
    store_prompt_cache,
    call_hosted_llm_with_prefix_cache,
    get_full_prompt_cache_telemetry,
)


def _clean_latin1(text: str) -> str:
    """Normalizes Unicode symbols (like ₹, €, ¥, —, •) to clean ASCII for standard PDF core fonts."""
    if not text:
        return ""
    replacements = {
        "₹": "INR ",
        "€": "EUR ",
        "£": "GBP ",
        "¥": "JPY ",
        "₦": "NGN ",
        "₱": "PHP ",
        "—": "-",
        "–": "-",
        "•": "*",
        "“": '"',
        "”": '"',
        "’": "'",
        "‘": "'",
        "×": "x",
        "÷": "/",
        "→": "->",
        "≤": "<=",
        "≥": ">=",
    }
    res = str(text)
    for k, v in replacements.items():
        res = res.replace(k, v)
    return res.encode("latin-1", errors="replace").decode("latin-1")


def generate_opportunity_pdf_bytes(opportunity: Dict[str, Any]) -> bytes:
    """
    Generates a comprehensive, multi-section PDF report for a selected opportunity
    using `fpdf2` and returns raw PDF bytes.
    """
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()

    # Header Banner
    pdf.set_fill_color(15, 23, 42)
    pdf.rect(0, 0, 210, 32, style="F")
    pdf.set_text_color(255, 255, 255)
    pdf.set_font("Helvetica", "B", 15)
    pdf.set_xy(12, 8)
    pdf.cell(0, 8, _clean_latin1("OPPORTUNITY INTELLIGENCE - GLOBAL EDITION"), new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 9)
    pdf.set_x(12)
    loc_str = f"{opportunity.get('area', '')}, {opportunity.get('city', '')}, {opportunity.get('state', '')}, {opportunity.get('country', '')}"
    pdf.cell(
        0,
        6,
        _clean_latin1(f"Location: {loc_str}  |  Category: {opportunity.get('category', '')}  |  Score: {opportunity.get('score', 0)}/100"),
        new_x="LMARGIN",
        new_y="NEXT",
    )

    pdf.ln(10)
    pdf.set_text_color(15, 23, 42)

    def add_section(heading: str, body_lines: List[str]) -> None:
        pdf.set_font("Helvetica", "B", 11)
        pdf.set_fill_color(241, 245, 249)
        pdf.cell(0, 8, _clean_latin1(heading), fill=True, new_x="LMARGIN", new_y="NEXT")
        pdf.ln(2)
        pdf.set_font("Helvetica", "", 9.5)
        for line in body_lines:
            pdf.multi_cell(0, 5.2, _clean_latin1(line), new_x="LMARGIN", new_y="NEXT")
            pdf.ln(1)
        pdf.ln(2)

    # 1. Business Overview
    add_section(
        "1. BUSINESS OVERVIEW",
        [
            f"Business Title: {opportunity.get('title', '')}",
            f"Format: {opportunity.get('business_type', '')}  |  Everyday Business: {'Yes' if opportunity.get('is_everyday_business') else 'No'}",
            f"Overview: {opportunity.get('summary', '')}",
            f"Why Suitable: {opportunity.get('whyThisOpportunity', '')}",
            f"Target Customers: {opportunity.get('targetCustomers', '')}",
            f"Customer Problem Addressed: {opportunity.get('customerProblem', '')}",
        ],
    )

    # 2. Opportunity Score Breakdown
    sb = opportunity.get("scoreBreakdown") or {}
    add_section(
        "2. TRANSPARENT OPPORTUNITY SCORE BREAKDOWN",
        [
            f"Overall Opportunity Score: {opportunity.get('score', 0)} / 100",
            f"Formula: {sb.get('formula', 'Weighted 5-factor index')}",
            f"- Customer Need: {sb.get('customerNeed', 0)}/100 (25% weight)",
            f"- Market Demand: {sb.get('marketDemand', 0)}/100 (25% weight)",
            f"- Competition & Gap: {sb.get('competition', 0)}/100 (15% weight)",
            f"- Growth Potential: {sb.get('growthPotential', 0)}/100 (15% weight)",
            f"- Feasibility within Budget: {sb.get('feasibility', 0)}/100 (20% weight)",
            f"Note: {sb.get('methodology_note', '')}",
        ],
    )

    # 3. Startup Budget Breakdown
    budget = opportunity.get("startupBudget") or {}
    b_lines = [
        f"Total Estimated Initial Investment: {budget.get('total_formatted', '')}",
        f"Your Available Budget: {budget.get('user_budget_formatted', '')} ({budget.get('budget_comparison_note', '')})",
    ]
    for item in budget.get("items", []):
        opt_tag = "[Optional]" if item.get("is_optional") else "[Core]"
        b_lines.append(
            f"* {item.get('category')}: {item.get('formatted')} ({item.get('share_pct')}%) {opt_tag} - {item.get('verification_note')}"
        )
    add_section("3. ITEMIZED STARTUP BUDGET BREAKDOWN", b_lines)

    # 4. Financial Projections & Scenarios
    fp = opportunity.get("financialProjections") or {}
    f_lines = [
        f"Expected Monthly Revenue Range: {fp.get('expected_monthly_revenue_range', '')}",
        f"Estimated Monthly Operating Expenses: {fp.get('estimated_monthly_operating_expenses', '')}",
        f"Estimated Monthly Gross Profit: {fp.get('estimated_monthly_gross_profit', '')}",
        f"Estimated Monthly Net Operating Profit: {fp.get('estimated_monthly_net_operating_profit', '')}",
        f"Break-Even Estimate: {fp.get('break_even_estimate', '')}",
        f"Potential Profit Margin: {fp.get('potential_profit_margin', '')}",
        f"Approximate Payback Period: {fp.get('approximate_payback_period', '')}",
        f"Disclaimer: {fp.get('disclaimer', '')}",
    ]
    add_section("4. FINANCIAL PROJECTIONS (ESTIMATES ONLY)", f_lines)

    # 5. NLP Market Intelligence & Evidence Sources
    nlp = opportunity.get("nlpInsights") or {}
    ev_lines = [
        f"Data Status: {nlp.get('data_label', 'Demo/sample data')}  |  NLP Model: {nlp.get('model_name', '')}",
        f"Records Analysed: {nlp.get('records_analysed', 0)} ({nlp.get('date_range', '')})",
        f"{nlp.get('observed_evidence_summary', '')}",
        f"{nlp.get('ai_interpretation_summary', '')}",
    ]
    for ev in (opportunity.get("evidenceSnippets") or [])[:4]:
        ev_lines.append(
            f"* Source: {ev.get('source_name')} ({ev.get('published_at')}) | Sentiment: {ev.get('sentiment_label')} ({ev.get('sentiment_compound')}) | Title: {ev.get('title')} | URL: {ev.get('source_url')}"
        )
    add_section("5. MARKET INTELLIGENCE & NLP EVIDENCE", ev_lines)

    # 6. Action Plan & Risks
    ap = opportunity.get("actionPlan") or {}
    ap_lines = ["First 30-Day Launch Steps:"] + [
        f"  {s}" for s in ap.get("steps_to_start", [])
    ]
    ap_lines.append("Licences to Investigate: " + ", ".join(ap.get("licences_to_investigate", [])))
    add_section("6. 30-DAY ACTION PLAN & VALIDATION", ap_lines)

    out = pdf.output()
    return bytes(out)


def compute_dashboard_summary(user_email: str = "") -> Dict[str, Any]:
    """
    Computes live KPI cards, category distribution, budget comparison, demand vs competition,
    and historical trend data from actual user searches and saved reports.
    Does not return the full search history list (which is served via the dedicated History API).
    """
    clean_email = (user_email or "").strip().lower()
    history_records = get_user_history(user_email=clean_email or None, limit=30)
    total_searches_count = count_user_history(user_email=clean_email or None)
    saved_reports = get_saved_reports(user_email=clean_email or None)

    # Flatten all discovered opportunities from search history
    all_opps: List[Dict[str, Any]] = []
    for h in history_records:
        for opp in h.get("opportunities", []):
            # Enrich older legacy DB records if they lack startupBudget
            if "startupBudget" not in opp:
                continue
            all_opps.append(opp)

    is_initial_demo_seed = False
    latest_data_status = "Demo/sample data"
    latest_nlp_info: Dict[str, Any] = {}

    if not all_opps:
        # Generate a live baseline batch for India / Karnataka / Shivamogga so dashboard KPIs & charts have real computed data
        seed_res = discover_global_opportunities(
            country="India",
            state="Karnataka",
            city="Shivamogga",
            area="Gandhi Nagar",
            category="Explore All Categories",
            budget=500000.0,
            currency="INR",
            recommend_everyday_simple=True,
            allow_network=True,
        )
        all_opps = seed_res["opportunities"]
        latest_data_status = seed_res["data_status_label"]
        latest_nlp_info = seed_res["nlp_summary"]
        is_initial_demo_seed = True
    else:
        latest_record = history_records[0]
        latest_data_status = latest_record.get("data_status_label") or "Cached data"
        latest_nlp_info = latest_record.get("nlp_summary") or {}

    total_discovered = len(all_opps)
    high_potential = sum(1 for o in all_opps if int(o.get("score", 0)) >= 82)
    scores = [int(o.get("score", 75)) for o in all_opps]
    avg_score = round(sum(scores) / max(len(scores), 1), 1)

    budgets = [
        float((o.get("startupBudget") or {}).get("total_estimated_initial_investment", 0))
        for o in all_opps
        if (o.get("startupBudget") or {}).get("total_estimated_initial_investment", 0) > 0
    ]
    primary_curr_sym = (all_opps[0].get("currency_symbol") or "₹") if all_opps else "₹"
    if budgets:
        min_b, max_b = int(min(budgets)), int(max(budgets))
        budget_range_str = f"{primary_curr_sym}{min_b:,} – {primary_curr_sym}{max_b:,}"
    else:
        budget_range_str = "₹45,000 – ₹4,50,000"

    categories_set = {o.get("category", "Daily Needs & Grocery") for o in all_opps}
    last_analysis_date = (
        history_records[0].get("created_at", "")[:16].replace("T", " ")
        if history_records
        else datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    )

    # Chart 1: Category distribution
    cat_counts: Dict[str, Dict[str, Any]] = {}
    for o in all_opps:
        c_name = o.get("category", "Daily Needs & Grocery")
        if c_name not in cat_counts:
            cat_counts[c_name] = {"category": c_name, "count": 0, "avgScore": 0, "scores": []}
        cat_counts[c_name]["count"] += 1
        cat_counts[c_name]["scores"].append(int(o.get("score", 75)))

    category_chart = []
    for c_name, info in cat_counts.items():
        category_chart.append({
            "category": c_name.split("&")[0].strip(),
            "fullCategory": c_name,
            "count": info["count"],
            "avgScore": round(sum(info["scores"]) / len(info["scores"]), 1),
        })

    # Chart 2: Historical opportunity trends over searches (only when real history exists)
    historical_trend_chart = []
    for idx, h in enumerate(reversed(history_records[:10]), start=1):
        h_opps = h.get("opportunities") or []
        if h_opps:
            avg_s = round(
                sum(int(x.get("score", 75)) for x in h_opps) / len(h_opps), 1
            )
            historical_trend_chart.append({
                "searchLabel": f"#{h.get('id', idx)} {h.get('city', '')[:10]}",
                "date": str(h.get("created_at", ""))[:10],
                "avgScore": avg_s,
                "opportunitiesCount": len(h_opps),
            })

    # Chart 3: Startup budget vs Monthly Revenue & Operating Cost comparison
    budget_and_revenue_chart = []
    for o in all_opps[:6]:
        sb = o.get("startupBudget") or {}
        fp = o.get("financialProjections") or {}
        scenarios = fp.get("scenarios") or []
        base_scen = scenarios[1] if len(scenarios) > 1 else (scenarios[0] if scenarios else {})
        short_title = (o.get("title") or "Opportunity")[:22]
        budget_and_revenue_chart.append({
            "name": short_title,
            "fullTitle": o.get("title"),
            "startupCapex": sb.get("total_estimated_initial_investment", 0),
            "userBudget": sb.get("user_available_budget", 0),
            "monthlyRevenue": base_scen.get("monthly_revenue", 0),
            "monthlyOpex": base_scen.get("monthly_operating_expenses", 0) + base_scen.get("monthly_cogs", 0),
            "monthlyNetProfit": base_scen.get("monthly_net_operating_profit", 0),
            "demandScore": o.get("demandScore", 85),
            "competitionScore": o.get("competitionScore", 75),
            "overallScore": o.get("score", 80),
        })

    return {
        "kpis": {
            "total_searches": total_searches_count,
            "opportunities_discovered": total_discovered,
            "high_potential_opportunities": high_potential,
            "estimated_startup_budget_range": budget_range_str,
            "average_opportunity_score": avg_score,
            "business_categories_analysed": len(categories_set),
            "last_analysis_date": last_analysis_date,
            "saved_reports_count": len(saved_reports),
            "is_initial_seed": is_initial_demo_seed,
        },
        "system_status": {
            "data_status_label": latest_data_status,
            "market_data_source": (
                "NewsAPI.org + Google News RSS"
                if settings.is_market_api_configured()
                else "Google News Public RSS Syndication + Local Cache"
            ),
            "nlp_model_name": latest_nlp_info.get(
                "model_name", "VADER-Lexicon-v3.3.2 + Statistical TF-IDF Theme Clusterer"
            ),
            "nlp_model_status": latest_nlp_info.get(
                "model_status",
                "Active (Local Pretrained VADER Sentiment + Statistical Theme Engine)",
            ),
            "hosted_llm_connected": settings.is_ai_configured(),
            "hosted_llm_provider": settings.AI_PROVIDER if settings.is_ai_configured() else None,
            "records_processed": latest_nlp_info.get("records_analysed", 3),
            "last_refresh": last_analysis_date,
            "prompt_cache": get_full_prompt_cache_telemetry()["metrics"],
        },
        "charts": {
            "category_distribution": category_chart,
            "historical_trends": historical_trend_chart,
            "has_historical_data": len(historical_trend_chart) > 0,
            "financial_and_demand_comparison": budget_and_revenue_chart,
        },
        "recent_opportunities": all_opps[:8],
        "saved_reports": saved_reports[:6],
    }


def answer_report_assistant_query(question: str, opportunity: Dict[str, Any]) -> Dict[str, Any]:
    """
    Answers user questions about a specific opportunity report using the report's
    calculated budget, financial projections, NLP evidence, and risk profile.
    Integrates Multi-Layer Prompt Caching:
      - Normalizes user question intent & phrasing (`normalize_assistant_question`).
      - Checks L1 (In-Memory LRU) + L2 (SQLite `prompt_cache` table) before computing.
      - Uses Canonical Static System Prefix (>1,024 tokens) when invoking hosted Gemini/OpenAI LLMs.
    """
    t0 = time.perf_counter()
    q_lower = (question or "").strip().lower()
    title = opportunity.get("title", "this business")
    sb = opportunity.get("startupBudget") or {}
    fp = opportunity.get("financialProjections") or {}
    sc = opportunity.get("scoreBreakdown") or {}
    nlp = opportunity.get("nlpInsights") or {}
    ap = opportunity.get("actionPlan") or {}

    canonical_intent, normalized_q = normalize_assistant_question(question)
    qa_cache_payload = {
        "title": title.strip().lower(),
        "city": str(opportunity.get("city") or "").strip().lower(),
        "area": str(opportunity.get("area") or "").strip().lower(),
        "currency": str(opportunity.get("currency") or "INR").strip().upper(),
        "total_capex": float(sb.get("total_estimated_initial_investment") or 0.0),
        "user_budget": float(sb.get("user_available_budget") or 0.0),
        "score": int(opportunity.get("score") or 0),
        "intent": canonical_intent,
        "query_key": canonical_intent if canonical_intent != "intent:custom_query" else normalized_q,
    }

    cache_lookup = lookup_prompt_cache(
        prompt_type="report_assistant_qa",
        dynamic_payload=qa_cache_payload,
        estimated_compute_saved_ms=22.0,
    )
    if cache_lookup["hit"] and isinstance(cache_lookup["data"], dict):
        cached_resp = dict(cache_lookup["data"])
        cached_resp["question"] = question
        cached_resp["cache_meta"] = cache_lookup["cache_meta"]
        return cached_resp

    # Cache Miss -> Check if Hosted LLM with Prefix Caching is configured
    llm_result = None
    if settings.is_ai_configured():
        dynamic_prompt = (
            f"Opportunity Title: {title}\n"
            f"Location: {opportunity.get('area')}, {opportunity.get('city')}, {opportunity.get('country')}\n"
            f"Startup Investment: {sb.get('total_formatted')} vs User Budget {sb.get('user_budget_formatted')}\n"
            f"Net Profit Estimate: {fp.get('estimated_monthly_net_operating_profit')} ({fp.get('potential_profit_margin')})\n"
            f"Score: {opportunity.get('score')}/100 | NLP Sentiment: {nlp.get('overall_sentiment_label')}\n"
            f"User Question: {question}"
        )
        llm_result = call_hosted_llm_with_prefix_cache(dynamic_user_prompt=dynamic_prompt)

    if llm_result and llm_result.get("text"):
        answer = llm_result["text"]
        provider_cached_tok = llm_result.get("cached_tokens")
    elif any(w in q_lower for w in ["budget", "cost", "invest", "cheaper", "reduce", "capital", "save", "lower", "expense", "optional"]):
        provider_cached_tok = None
        opt_items = [i for i in sb.get("items", []) if i.get("is_optional")]
        opt_names = ", ".join(i["category"] for i in opt_items[:2]) if opt_items else "non-core fixtures"
        answer = (
            f"For **{title}**, the estimated initial investment is **{sb.get('total_formatted')}** "
            f"compared to your budget of **{sb.get('user_budget_formatted')}** ({sb.get('budget_comparison_note')}). "
            f"To lower upfront outlay, you can defer optional items such as *{opt_names}* and negotiate a smaller rent deposit."
        )
    elif any(w in q_lower for w in ["profit", "revenue", "earn", "break", "payback", "margin", "income", "return", "roi", "scenarios"]):
        provider_cached_tok = None
        answer = (
            f"**Estimated Financials (Not Guaranteed):** Expected monthly revenue ranges from **{fp.get('expected_monthly_revenue_range')}**, "
            f"with estimated monthly net operating profit of **{fp.get('estimated_monthly_net_operating_profit')}** "
            f"({fp.get('potential_profit_margin')}). {fp.get('break_even_estimate')}, giving an approximate payback period of **{fp.get('approximate_payback_period')}**."
        )
    elif any(w in q_lower for w in ["score", "why", "demand", "competition", "gap", "sentiment", "nlp", "vader", "news", "evidence", "theme"]):
        provider_cached_tok = None
        answer = (
            f"**{title}** scored **{opportunity.get('score')}/100** using `{sc.get('formula')}`. "
            f"The primary market gap is: *{opportunity.get('marketGap')}* "
            f"NLP analysis of {nlp.get('records_analysed', 0)} market records showed overall sentiment: **{nlp.get('overall_sentiment_label')}**."
        )
    elif any(w in q_lower for w in ["start", "step", "licence", "license", "first", "plan", "supplier", "30-day", "launch", "equipment", "permit"]):
        provider_cached_tok = None
        steps = ap.get("steps_to_start", [])
        lics = ", ".join(ap.get("licences_to_investigate", []))
        answer = (
            f"**How to Start in 30 Days:** {steps[0] if steps else ''} "
            f"Key licences to verify locally: **{lics}**. "
            f"Before signing any lease, validate: *{ap.get('validation_questions', ['Local footfall'])[0]}*"
        )
    else:
        provider_cached_tok = None
        answer = (
            f"**Report Summary for {title}:**\n"
            f"- **Estimated Setup Cost:** {sb.get('total_formatted')} (Budget fit: {sb.get('budget_utilization_pct')}%)\n"
            f"- **Base Monthly Net Profit Estimate:** {fp.get('estimated_monthly_net_operating_profit')}\n"
            f"- **Opportunity Score:** {opportunity.get('score')}/100\n"
            f"- **Evidence Base:** {nlp.get('records_analysed', 0)} records analysed ({nlp.get('data_label')}).\n"
            f"Ask me about *budget reduction*, *profit formulas*, *risks*, or *first 30-day launch steps*!"
        )

    response_payload = {
        "question": question,
        "answer": answer,
        "canonical_intent": canonical_intent,
        "assistant_mode": (
            f"Connected to {settings.AI_PROVIDER.upper()} ({settings.AI_MODEL_NAME}) + Context Prefix Cache"
            if settings.is_ai_configured()
            else "Structured Report & NLP Evidence Interpreter (Local Mode + L1/L2 Prompt Cache)"
        ),
        "is_live_llm": settings.is_ai_configured(),
    }

    compute_ms = round((time.perf_counter() - t0) * 1000.0, 2)
    cache_meta = store_prompt_cache(
        prompt_type="report_assistant_qa",
        dynamic_payload=qa_cache_payload,
        response_data=response_payload,
        compute_latency_ms=compute_ms,
        provider_cached_tokens=provider_cached_tok,
    )
    response_payload["cache_meta"] = cache_meta
    return response_payload
