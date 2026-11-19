"""
Pydantic v2 request and response validation schemas for AI Business Opportunity Finder — Global Edition.
"""

import re
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, field_validator


def validate_email_format(v: str) -> str:
    cleaned = (v or "").strip().lower()
    if not cleaned or not re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", cleaned):
        raise ValueError("Invalid email address format.")
    return cleaned


class AuthStartRequest(BaseModel):
    email: str = Field(..., description="User email address")

    @field_validator("email")
    @classmethod
    def check_email(cls, v: str) -> str:
        return validate_email_format(v)


class AuthStartResponse(BaseModel):
    success: bool
    message: str
    is_smtp_sent: bool = False
    expires_in_minutes: int = 10
    demo_mode_notice: Optional[str] = None
    dev_code: Optional[str] = None


class AuthVerifyRequest(BaseModel):
    email: str = Field(..., description="User email address")
    code: str = Field(..., min_length=6, max_length=6, description="6-digit verification code")

    @field_validator("email")
    @classmethod
    def check_email(cls, v: str) -> str:
        return validate_email_format(v)


class UserProfile(BaseModel):
    id: int
    email: str
    created_at: Optional[str] = None
    last_login_at: Optional[str] = None


class AuthVerifyResponse(BaseModel):
    success: bool
    message: str
    user: UserProfile
    token: str


class PasswordAuthRequest(BaseModel):
    email: str = Field(..., description="User email address")
    password: str = Field(..., min_length=6, max_length=128, description="User account password")
    mode: Optional[str] = Field(default="auto", description="'login', 'register', or 'auto'")

    @field_validator("email")
    @classmethod
    def check_email(cls, v: str) -> str:
        return validate_email_format(v)


class PasswordAuthResponse(BaseModel):
    success: bool
    message: str
    hash_algorithm: str = "PBKDF2-HMAC-SHA256 (260,000 iterations + 128-bit salt)"
    user: UserProfile
    token: str


class ScoreFactorDetail(BaseModel):
    name: str
    key: str
    score: int = Field(..., ge=0, le=100)
    weight_pct: int
    weighted_points: float
    explanation: str


class ScoreBreakdown(BaseModel):
    customerNeed: int = Field(..., ge=0, le=100)
    marketDemand: int = Field(..., ge=0, le=100)
    competition: int = Field(..., ge=0, le=100)
    growthPotential: int = Field(..., ge=0, le=100)
    feasibility: int = Field(..., ge=0, le=100)
    formula: Optional[str] = None
    methodology_note: Optional[str] = None
    factors: Optional[List[ScoreFactorDetail]] = None


class BudgetLineItem(BaseModel):
    category: str
    amount: float
    currency: str
    formatted: str
    share_pct: float
    is_optional: bool = False
    verification_note: str


class StartupBudgetBreakdown(BaseModel):
    currency: str
    currency_symbol: str
    total_estimated_initial_investment: float
    total_formatted: str
    user_available_budget: float
    user_budget_formatted: str
    within_budget: bool
    budget_utilization_pct: float
    budget_comparison_note: str
    cost_tier_note: str
    items: List[BudgetLineItem]


class ScenarioProjection(BaseModel):
    scenario_name: str  # "Low (Conservative)", "Base (Expected)", "High (Optimistic)"
    monthly_revenue: float
    monthly_revenue_formatted: str
    monthly_cogs: float
    monthly_gross_profit: float
    monthly_operating_expenses: float
    monthly_operating_expenses_formatted: str
    monthly_net_operating_profit: float
    monthly_net_profit_formatted: str
    net_profit_margin_pct: float
    break_even_months: Optional[float] = None
    payback_period_label: str


class FinancialProjections(BaseModel):
    currency: str
    currency_symbol: str
    expected_monthly_revenue_range: str
    estimated_monthly_operating_expenses: str
    estimated_monthly_gross_profit: str
    estimated_monthly_net_operating_profit: str
    break_even_estimate: str
    potential_profit_margin: str
    approximate_payback_period: str
    assumptions: List[str]
    formulas_used: List[str]
    disclaimer: str
    scenarios: List[ScenarioProjection]
    six_month_projection: List[Dict[str, Any]]


class EvidenceSnippet(BaseModel):
    title: str
    snippet: str
    source_name: str
    source_url: str
    published_at: str
    retrieved_at: str
    sentiment_label: str
    sentiment_compound: float
    is_live_source: bool


class NlpAnalysisSummary(BaseModel):
    model_name: str
    model_type: str
    model_status: str  # "Active (Local Pretrained VADER + Statistical Theme Engine)" | "Active (+ Hosted LLM)"
    data_label: str  # "Live data retrieved at ..." | "Cached data from ..." | "Demo/sample data"
    records_analysed: int
    date_range: str
    overall_sentiment_label: str
    overall_sentiment_score: float
    sentiment_distribution: Dict[str, int]
    recurring_complaints_and_needs: List[str]
    problem_themes: List[Dict[str, Any]]
    observed_evidence_summary: str
    ai_interpretation_summary: str
    prompt_cache_meta: Optional[Dict[str, Any]] = None


class RiskItem(BaseModel):
    category: str
    severity: str  # "Low", "Medium", "High"
    description: str
    mitigation: str


class ActionPlanData(BaseModel):
    steps_to_start: List[str]
    basic_equipment_and_resources: List[str]
    potential_suppliers_or_sourcing: List[str]
    licences_to_investigate: List[str]
    first_30_day_plan: List[Dict[str, str]]
    validation_questions: List[str]


class OpportunityItem(BaseModel):
    id: str
    title: str
    category: str
    business_type: str
    is_everyday_business: bool = True
    beginner_friendly: bool = True
    summary: str
    country: str
    country_code: str
    state: str
    city: str
    area: str
    currency: str
    currency_symbol: str
    whyThisOpportunity: str
    targetCustomers: str
    customerProblem: str
    estimatedDemand: str
    demandScore: int
    competitionScore: int
    marketTrendEvidence: str
    localCustomerNeeds: str
    marketGap: str
    competitorContext: str
    competitors_verified: List[Dict[str, str]] = []
    competitiveAdvantages: List[str] = []
    competitiveDisadvantages: List[str] = []
    differentiationStrategies: List[str] = []
    pricingAndServiceStrategy: str = ""
    businessModel: str
    revenueStreams: List[str] = []
    score: int = Field(..., ge=0, le=100)
    scoreBreakdown: ScoreBreakdown
    startupBudget: StartupBudgetBreakdown
    financialProjections: FinancialProjections
    riskAssessment: List[RiskItem]
    actionPlan: ActionPlanData
    evidenceSnippets: List[EvidenceSnippet]
    nlpInsights: NlpAnalysisSummary
    dataSourceMetadata: Dict[str, Any]
    confidenceLevel: str
    crossRegionInsight: Optional[Dict[str, Any]] = None


class DiscoverRequest(BaseModel):
    email: Optional[str] = Field(default="guest@opportunity.ai")
    country: str = Field(..., min_length=2, description="Country name or ISO code")
    state: str = Field(..., min_length=1, description="State, province, or region")
    city: str = Field(..., min_length=1, description="City or town")
    area: Optional[str] = Field(default="Central District", description="Neighbourhood or local area")
    category: str = Field(default="Daily Needs & Grocery", description="Preferred business category")
    budget: float = Field(..., gt=0, description="Available startup budget in selected currency")
    budget_min: Optional[float] = Field(default=None, ge=0)
    budget_max: Optional[float] = Field(default=None, ge=0)
    currency: str = Field(default="INR", min_length=3, max_length=3)
    target_currency: Optional[str] = Field(default=None)
    business_type: str = Field(default="Flexible (Any suitable type)")
    experience_level: str = Field(default="Beginner")
    risk_preference: str = Field(default="Low")
    recommend_everyday_simple: bool = Field(default=True)
    skills_and_interests: Optional[str] = Field(default="")

    @field_validator("budget")
    @classmethod
    def check_budget(cls, v: float) -> float:
        if v <= 0:
            raise ValueError("Startup budget must be greater than zero.")
        if v > 1e12:
            raise ValueError("Startup budget exceeds realistic small-business range.")
        return v


class DiscoverResponse(BaseModel):
    search_id: int
    country: str
    country_code: str
    state: str
    city: str
    area: str
    category: str
    currency: str
    currency_symbol: str
    budget: float
    budget_formatted: str
    converted_budget: Optional[Dict[str, Any]] = None
    recommend_everyday_simple: bool
    experience_level: str
    risk_preference: str
    data_status_label: str
    market_context_summary: str
    nlp_summary: NlpAnalysisSummary
    opportunities: List[OpportunityItem]
    created_at: str
    prompt_cache_meta: Optional[Dict[str, Any]] = None


# Legacy AnalyzeRequest support so existing tests or calls continue to work
class AnalyzeRequest(BaseModel):
    email: str = "test@gmail.com"
    domain: str
    city: str
    area: str
    country: Optional[str] = "India"
    state: Optional[str] = "Karnataka"
    budget: Optional[float] = 300000.0
    currency: Optional[str] = "INR"
    description: Optional[str] = ""


class SaveReportRequest(BaseModel):
    user_email: str
    opportunity: Dict[str, Any]
    notes: Optional[str] = ""


class AssistantQueryRequest(BaseModel):
    question: str
    opportunity: Dict[str, Any]
