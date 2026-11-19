"""
Financial Estimation & Scenario Projection Service (services/financial_service.py).
Responsibilities:
  1. Generates realistic, itemized Startup Budget Breakdowns in the user's selected currency,
     scaling baseline USD costs by both the country's local purchasing-power / cost index
     AND the currency exchange rate, calibrated appropriately to the user's budget tier.
  2.Adapts expense line items (Rent deposit, Equipment/furniture, Initial inventory/raw materials,
     Licences/registration, Staff/setup, Marketing, Working capital, Emergency reserve) to the
     specific business format (e.g., Home-based vs Storefront vs Service).
  3. Computes Low (Conservative), Base (Expected), and High (Optimistic) monthly financial scenarios:
     - Monthly Revenue
     - Cost of Goods Sold (COGS) & Gross Profit
     - Monthly Operating Expenses (Rent, Utilities, Staff/Helper, Marketing/Misc)
     - Monthly Net Operating Profit (Pre-Tax Operating Income)
     - Net Operating Profit Margin (%)
     - Break-Even Point & Approximate Payback Period (in months)
  4. Documents all formulas and assumptions transparently.
"""

from typing import Dict, Any, List
from services.currency_service import (
    REFERENCE_RATES_VS_USD,
    format_currency,
    get_currency_info,
)


def _round_sensibly(val: float, currency: str) -> float:
    """Rounds monetary values cleanly according to currency magnitude."""
    if val <= 0:
        return 0.0
    if currency in ("JPY", "IDR", "NGN", "KES"):
        return float(round(val, -2))
    if currency == "INR":
        return float(round(val, -2)) if val >= 1000 else float(round(val, -1))
    return float(round(val, -1)) if val >= 200 else float(round(val, 0))


def build_startup_budget_and_financials(
    business_title: str,
    business_type: str,
    base_usd_capex: float,
    cost_index_usd: float,
    currency: str,
    user_available_budget: float,
    gross_margin_pct: float = 0.35,
    monthly_revenue_to_capex_ratio: float = 0.55,
    opex_to_revenue_ratio: float = 0.18,
) -> Dict[str, Any]:
    """
    Calculates both the itemized Startup Budget Breakdown and the Low/Base/High
    Monthly Financial Projections in the selected local currency.
    """
    curr = (currency or "INR").strip().upper()
    curr_info = get_currency_info(curr)
    symbol = curr_info["symbol"]
    fx_rate = REFERENCE_RATES_VS_USD.get(curr, 1.0)

    # Convert baseline USD CapEx into local purchasing-power-adjusted currency
    raw_local_capex = base_usd_capex * cost_index_usd * fx_rate

    # Calibrate modular scale (micro/home vs full shop) toward the user's budget if within realistic bounds
    safe_user_budget = max(user_available_budget, 100.0)
    if safe_user_budget < raw_local_capex * 0.65:
        # Scale down to a Lean / Starter edition (minimum 45% of standard setup)
        target_capex = max(raw_local_capex * 0.45, min(raw_local_capex, safe_user_budget * 0.92))
        scale_note = (
            "Calibrated for a Lean / Starter launch format to stay close to your entered startup budget."
        )
    elif safe_user_budget > raw_local_capex * 1.8:
        # Allow slightly larger initial inventory/working capital up to 1.35x standard
        target_capex = min(raw_local_capex * 1.35, safe_user_budget * 0.85)
        scale_note = (
            "Includes expanded initial inventory and working-capital cushion supported by your budget."
        )
    else:
        target_capex = min(raw_local_capex, safe_user_budget * 0.90)
        scale_note = "Standard neighbourhood business launch configuration."

    is_home_or_online = any(
        k in business_type.lower() for k in ["home", "online", "delivery", "tutoring"]
    )

    # Define allocation weights by business format (sums to 1.00)
    if is_home_or_online:
        allocations = [
            ("Workspace Setup / Minor Utility Deposit", 0.08, True, "Optional if operating from an existing room at home."),
            ("Core Equipment, Appliances & Tools", 0.30, False, "Verify local dealer prices and commercial warranty terms."),
            ("Initial Inventory / Raw Materials & Packaging", 0.22, False, "Confirm wholesale minimum order quantities with local distributors."),
            ("Local Business Registration & Food/Trade Licences", 0.06, False, "Verify municipal trade licence and health/safety registration fees."),
            ("Initial Helper / Onboarding & Setup", 0.08, True, "Optional in Month 1 if founder handles operations directly."),
            ("Neighbourhood Launch Marketing (Pamphlets, Signage, WhatsApp)", 0.06, True, "Can be reduced by relying on local community referrals."),
            ("Working Capital (First 2 Months Operating Buffer)", 0.12, False, "Covers utility bills, transport, and restocking before repeat cash flow stabilizes."),
            ("Emergency Contingency Reserve", 0.08, True, "Recommended safety buffer for unexpected repair or supply price fluctuations."),
        ]
    else:
        allocations = [
            ("Shop Rent Security Deposit & Initial Month Rent", 0.22, False, "Requires local verification: landlord deposits vary widely by street and city."),
            ("Storefront Equipment, Shelving, Counters & Signage", 0.26, False, "Can be lowered by sourcing certified pre-owned commercial fixtures."),
            ("Initial Opening Inventory & Stock Supplies", 0.22, False, "Verify wholesale credit periods with local distributors."),
            ("Municipal Trade Licence, Registration & Permits", 0.05, False, "Check local municipal corporation and tax registration rules."),
            ("Store Fitting, Helper Training & Setup", 0.06, True, "Optional if founder and family manage initial store setup."),
            ("Local Opening Promotion & Banner Signage", 0.04, True, "Optional; focus on walk-in visibility and Google Maps listing."),
            ("Working Capital (2 Months Operating Cushion)", 0.09, False, "Essential for daily restocking, electricity, and helper wages."),
            ("Emergency Contingency Reserve", 0.06, True, "Recommended reserve for equipment maintenance or seasonal slowdowns."),
        ]

    line_items: List[Dict[str, Any]] = []
    total_capex = 0.0
    for cat_name, weight, is_opt, note in allocations:
        amt = _round_sensibly(target_capex * weight, curr)
        total_capex += amt
        line_items.append({
            "category": cat_name,
            "amount": amt,
            "currency": curr,
            "formatted": format_currency(amt, curr),
            "share_pct": round(weight * 100.0, 1),
            "is_optional": is_opt,
            "verification_note": note,
        })

    # Recompute exact share percentages
    for item in line_items:
        item["share_pct"] = round((item["amount"] / max(total_capex, 1.0)) * 100.0, 1)

    within_budget = total_capex <= safe_user_budget
    utilization_pct = round((total_capex / safe_user_budget) * 100.0, 1)

    if within_budget:
        diff = safe_user_budget - total_capex
        comparison_note = (
            f"Fits within your budget of {format_currency(safe_user_budget, curr)} with "
            f"{format_currency(diff, curr)} ({100 - utilization_pct:.1f}%) remaining as extra reserve."
        )
    else:
        over = total_capex - safe_user_budget
        opt_sum = sum(i["amount"] for i in line_items if i["is_optional"])
        comparison_note = (
            f"Estimated full setup ({format_currency(total_capex, curr)}) is {format_currency(over, curr)} above "
            f"your budget ({format_currency(safe_user_budget, curr)}). Deferring optional items "
            f"({format_currency(opt_sum, curr)}) reduces initial outlay to {format_currency(total_capex - opt_sum, curr)}."
        )

    startup_budget = {
        "currency": curr,
        "currency_symbol": symbol,
        "total_estimated_initial_investment": total_capex,
        "total_formatted": format_currency(total_capex, curr),
        "user_available_budget": safe_user_budget,
        "user_budget_formatted": format_currency(safe_user_budget, curr),
        "within_budget": within_budget,
        "budget_utilization_pct": utilization_pct,
        "budget_comparison_note": comparison_note,
        "cost_tier_note": scale_note,
        "items": line_items,
    }

    # --- Monthly Financial Projections (Low, Base, High Scenarios) ---
    base_monthly_rev = _round_sensibly(total_capex * monthly_revenue_to_capex_ratio, curr)
    fixed_opex_base = _round_sensibly(base_monthly_rev * opex_to_revenue_ratio, curr)

    scenario_defs = [
        ("Low (Conservative)", 0.72, 0.92),
        ("Base (Expected)", 1.00, 1.00),
        ("High (Optimistic)", 1.30, 1.10),
    ]

    scenarios: List[Dict[str, Any]] = []
    for s_name, rev_mult, opex_mult in scenario_defs:
        rev = _round_sensibly(base_monthly_rev * rev_mult, curr)
        cogs = _round_sensibly(rev * (1.0 - gross_margin_pct), curr)
        gross_profit = max(0.0, rev - cogs)
        opex = _round_sensibly(fixed_opex_base * opex_mult, curr)
        net_op_profit = gross_profit - opex
        margin_pct = round((net_op_profit / max(rev, 1.0)) * 100.0, 1)

        if net_op_profit > 0:
            be_months = round(total_capex / net_op_profit, 1)
            payback_lbl = f"~{be_months:.1f} months"
        else:
            be_months = None
            payback_lbl = "Not reached at this volume"

        scenarios.append({
            "scenario_name": s_name,
            "monthly_revenue": rev,
            "monthly_revenue_formatted": format_currency(rev, curr),
            "monthly_cogs": cogs,
            "monthly_gross_profit": gross_profit,
            "monthly_operating_expenses": opex,
            "monthly_operating_expenses_formatted": format_currency(opex, curr),
            "monthly_net_operating_profit": net_op_profit,
            "monthly_net_profit_formatted": format_currency(net_op_profit, curr),
            "net_profit_margin_pct": margin_pct,
            "break_even_months": be_months,
            "payback_period_label": payback_lbl,
        })

    low_s, base_s, high_s = scenarios[0], scenarios[1], scenarios[2]

    # Build 6-month ramp-up trajectory for Recharts visualization
    six_month_projection = []
    ramp_factors = [0.55, 0.70, 0.85, 0.95, 1.00, 1.08]
    for idx, rf in enumerate(ramp_factors, start=1):
        m_rev = _round_sensibly(base_s["monthly_revenue"] * rf, curr)
        m_cogs = _round_sensibly(m_rev * (1.0 - gross_margin_pct), curr)
        m_opex = base_s["monthly_operating_expenses"]
        m_total_cost = m_cogs + m_opex
        m_profit = m_rev - m_total_cost
        six_month_projection.append({
            "month": f"Month {idx}",
            "revenue": m_rev,
            "operating_costs": m_total_cost,
            "net_profit": m_profit,
        })

    # Fixed monthly operating cost needed to break even: BreakEvenRev = FixedOpex / GrossMarginPct
    break_even_monthly_rev = _round_sensibly(
        base_s["monthly_operating_expenses"] / max(gross_margin_pct, 0.05), curr
    )

    financial_projections = {
        "currency": curr,
        "currency_symbol": symbol,
        "expected_monthly_revenue_range": (
            f"{low_s['monthly_revenue_formatted']} – {high_s['monthly_revenue_formatted']} "
            f"(Base: {base_s['monthly_revenue_formatted']}/mo)"
        ),
        "estimated_monthly_operating_expenses": (
            f"{base_s['monthly_operating_expenses_formatted']}/mo (Rent, utilities, local helper, transport) "
            f"+ {format_currency(base_s['monthly_cogs'], curr)}/mo inventory/raw material restocking (COGS)"
        ),
        "estimated_monthly_gross_profit": (
            f"{format_currency(base_s['monthly_gross_profit'], curr)}/mo "
            f"({gross_margin_pct*100:.0f}% gross margin before rent & overhead)"
        ),
        "estimated_monthly_net_operating_profit": (
            f"{low_s['monthly_net_profit_formatted']} – {high_s['monthly_net_profit_formatted']} "
            f"(Base: {base_s['monthly_net_profit_formatted']}/mo pre-tax)"
        ),
        "break_even_estimate": (
            f"Monthly Break-Even Sales Volume: {format_currency(break_even_monthly_rev, curr)}/mo "
            f"(Fixed OpEx ÷ {gross_margin_pct*100:.0f}% Gross Margin)"
        ),
        "potential_profit_margin": (
            f"{low_s['net_profit_margin_pct']}% – {high_s['net_profit_margin_pct']}% Net Operating Margin "
            f"(Base: {base_s['net_profit_margin_pct']}%)"
        ),
        "approximate_payback_period": (
            f"{base_s['payback_period_label']} in Base Scenario "
            f"(Range: {high_s['payback_period_label']} to {low_s['payback_period_label']})"
        ),
        "assumptions": [
            f"Gross Margin Assumption: {gross_margin_pct*100:.0f}% on sales (Cost of Goods Sold = {(1-gross_margin_pct)*100:.0f}% of revenue).",
            f"Fixed Operating Overhead (Rent, Electricity, Helper, Local Delivery): { base_s['monthly_operating_expenses_formatted'] }/month in the Base case.",
            f"Location Cost Multiplier: {cost_index_usd:.2f}x relative to US baseline, converted at reference rate 1 USD = {fx_rate} {curr}.",
            "Figures represent pre-tax net operating income assuming cash/equity purchase (excludes commercial loan interest and income taxes, which depend on local tax brackets).",
        ],
        "formulas_used": [
            "Gross Profit = Monthly Revenue − Cost of Goods Sold (COGS)",
            "Net Operating Profit = Gross Profit − Fixed Monthly Operating Expenses",
            "Net Profit Margin (%) = (Net Operating Profit ÷ Monthly Revenue) × 100",
            "Break-Even Monthly Revenue = Fixed Operating Expenses ÷ Gross Margin Ratio",
            "Approximate Payback Period (Months) = Total Initial Investment ÷ Monthly Net Operating Profit",
        ],
        "disclaimer": (
            "IMPORTANT ESTIMATE DISCLAIMER: All revenue, cost, and profit figures are illustrative model estimates "
            "derived from documented unit-economics formulas and regional cost indices. They are NOT guaranteed earnings. "
            "Always verify commercial rent, supplier wholesale margins, and municipal taxes in your exact neighbourhood before investing."
        ),
        "scenarios": scenarios,
        "six_month_projection": six_month_projection,
    }

    return {
        "startup_budget": startup_budget,
        "financial_projections": financial_projections,
    }
