"""
Transparent Opportunity Scoring Service (services/scoring_service.py).
Calculates a documented, explainable Opportunity Score out of 100 based on 5 factors:
  1. Customer Need (25% weight) — Urgency and repeat frequency of the customer need.
  2. Market Demand (25% weight) — Addressable local household/commercial footfall and NLP demand signals.
  3. Competition & Gap (15% weight) — Room for a new local entrant (higher score = less saturated / clearer gap).
  4. Growth Potential (15% weight) — Ability to expand via subscriptions, delivery, or repeat referrals.
  5. Feasibility within Budget (20% weight) — Alignment with the user's available startup budget and experience level.

IMPORTANT: This score is an analytical heuristic for comparing small business ideas, NOT a scientifically
validated guarantee of business success.
"""

from typing import Dict, Any, List


def compute_transparent_score(
    base_customer_need: int,
    base_market_demand: int,
    base_competition: int,
    base_growth_potential: int,
    estimated_startup_cost: float,
    user_available_budget: float,
    experience_level: str = "Beginner",
    is_beginner_friendly: bool = True,
    nlp_sentiment_score: float = 0.0,
) -> Dict[str, Any]:
    """
    Computes each of the 5 factor scores (0-100), applies documented weights,
    and returns both the overall score and a transparent breakdown with formulas.
    """
    # 1. Adjust Market Demand slightly using real NLP sentiment signal (-3 to +4 points)
    nlp_adj = int(round(nlp_sentiment_score * 6.0))
    customer_need = max(25, min(98, int(base_customer_need)))
    market_demand = max(25, min(98, int(base_market_demand + nlp_adj)))
    competition = max(20, min(95, int(base_competition)))
    growth_potential = max(25, min(96, int(base_growth_potential)))

    # 2. Compute Feasibility within User's Budget & Experience
    safe_budget = max(user_available_budget, 1.0)
    cost_ratio = estimated_startup_cost / safe_budget

    if cost_ratio <= 0.75:
        budget_feasibility = 94
        feas_reason = (
            f"Estimated initial setup ({cost_ratio*100:.0f}% of your budget) leaves a healthy safety buffer."
        )
    elif cost_ratio <= 1.00:
        budget_feasibility = 86
        feas_reason = (
            f"Estimated initial setup ({cost_ratio*100:.0f}% of your budget) fits comfortably within your available capital."
        )
    elif cost_ratio <= 1.25:
        budget_feasibility = 68
        feas_reason = (
            f"Estimated initial setup is ~{(cost_ratio-1)*100:.0f}% above your target budget; requires phasing optional equipment."
        )
    else:
        budget_feasibility = 48
        feas_reason = (
            f"Full setup exceeds your stated budget ({cost_ratio*100:.0f}% of budget); consider starting smaller or home-based."
        )

    if experience_level.lower() == "beginner" and not is_beginner_friendly:
        budget_feasibility = max(35, budget_feasibility - 10)
        feas_reason += " Adjusted (-10 pts) because this format benefits from prior operational experience."
    elif experience_level.lower() == "beginner" and is_beginner_friendly:
        budget_feasibility = min(98, budget_feasibility + 3)
        feas_reason += " Straightforward operations suitable for first-time founders."

    feasibility = int(budget_feasibility)

    # 3. Documented Weighted Formula:
    # Score = 0.25*CustomerNeed + 0.25*MarketDemand + 0.15*Competition + 0.15*GrowthPotential + 0.20*Feasibility
    w_need = round(customer_need * 0.25, 2)
    w_demand = round(market_demand * 0.25, 2)
    w_comp = round(competition * 0.15, 2)
    w_growth = round(growth_potential * 0.15, 2)
    w_feas = round(feasibility * 0.20, 2)

    total_raw = w_need + w_demand + w_comp + w_growth + w_feas
    overall_score = max(15, min(98, int(round(total_raw))))

    factors: List[Dict[str, Any]] = [
        {
            "name": "Customer Need",
            "key": "customerNeed",
            "score": customer_need,
            "weight_pct": 25,
            "weighted_points": w_need,
            "explanation": "Measures how essential and frequently purchased the product or service is for local residents.",
        },
        {
            "name": "Market Demand",
            "key": "marketDemand",
            "score": market_demand,
            "weight_pct": 25,
            "weighted_points": w_demand,
            "explanation": "Reflects local population density, repeat footfall, and NLP market sentiment signals.",
        },
        {
            "name": "Competition & Market Gap",
            "key": "competition",
            "score": competition,
            "weight_pct": 15,
            "weighted_points": w_comp,
            "explanation": "Higher score means existing local options are fragmented or leave room for better quality/service.",
        },
        {
            "name": "Growth Potential",
            "key": "growthPotential",
            "score": growth_potential,
            "weight_pct": 15,
            "weighted_points": w_growth,
            "explanation": "Potential to grow revenue via monthly subscriptions, home delivery, or B2B bulk orders.",
        },
        {
            "name": "Feasibility within Budget",
            "key": "feasibility",
            "score": feasibility,
            "weight_pct": 20,
            "weighted_points": w_feas,
            "explanation": feas_reason,
        },
    ]

    formula_str = (
        f"Score = (0.25 × {customer_need}) + (0.25 × {market_demand}) + (0.15 × {competition}) "
        f"+ (0.15 × {growth_potential}) + (0.20 × {feasibility}) = {total_raw:.1f} → {overall_score}/100"
    )

    return {
        "overall_score": overall_score,
        "breakdown": {
            "customerNeed": customer_need,
            "marketDemand": market_demand,
            "competition": competition,
            "growthPotential": growth_potential,
            "feasibility": feasibility,
            "formula": formula_str,
            "methodology_note": (
                "This Opportunity Score is a transparent multi-factor planning index designed to compare "
                "practical business ideas against your budget and locality. It is a decision-support heuristic, "
                "not a scientifically validated forecast or profit guarantee."
            ),
            "factors": factors,
        },
    }
