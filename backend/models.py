"""
Domain models, global reference constants, business categories, and practical everyday
business templates for AI Business Opportunity Finder — Global Edition.
"""

from typing import List, Dict, Any

# Supported Business Categories (prioritizing everyday, practical, and scalable small businesses)
BUSINESS_CATEGORIES: List[Dict[str, str]] = [
    {"id": "Daily Needs & Grocery", "label": "Daily Needs, Dairy & Grocery", "icon": "ShoppingBag", "everyday": "true"},
    {"id": "Food & Beverage", "label": "Tiffin, Bakery, Tea/Coffee & Food", "icon": "Utensils", "everyday": "true"},
    {"id": "Home & Personal Services", "label": "Laundry, Cleaning, Tailoring & Salon", "icon": "Scissors", "everyday": "true"},
    {"id": "Repair & Local Retail", "label": "Mobile Repair, Water Delivery & Retail", "icon": "Wrench", "everyday": "true"},
    {"id": "Education & Tutoring", "label": "Tutoring, Coaching & Skill Centers", "icon": "GraduationCap", "everyday": "true"},
    {"id": "Logistics & Delivery", "label": "Local Delivery & Courier Services", "icon": "Truck", "everyday": "true"},
    {"id": "Agri & Fresh Produce", "label": "Small Farming & Produce Distribution", "icon": "Sprout", "everyday": "true"},
    {"id": "Sustainability & Recycling", "label": "Small-Scale Recycling & Refill Products", "icon": "Recycle", "everyday": "true"},
    {"id": "Healthcare & Wellness", "label": "Pharmacy, Diagnostics & Elder Care", "icon": "HeartPulse", "everyday": "false"},
    {"id": "Digital & B2B Services", "label": "Bookkeeping, Digital Agency & IT Support", "icon": "Laptop", "everyday": "false"},
    {"id": "Explore All Categories", "label": "Explore All (Recommend Best Fit)", "icon": "Sparkles", "everyday": "true"},
]

# Legacy domain list kept for backward compatibility with existing endpoints
AVAILABLE_DOMAINS: List[str] = [c["id"] for c in BUSINESS_CATEGORIES] + [
    "Business", "Education", "Finance", "Food", "Healthcare", "Technology", "Retail", "Travel", "Explore for me"
]

# Preferred Business Types
BUSINESS_TYPES: List[str] = [
    "Flexible (Any suitable type)",
    "Shop / Storefront",
    "Home-based",
    "Service-based",
    "Food / Kitchen",
    "Retail / Kiosk",
    "Online / Hybrid",
]

# Experience Levels
EXPERIENCE_LEVELS: List[str] = ["Beginner", "Intermediate", "Experienced"]

# Risk Preferences
RISK_PREFERENCES: List[str] = ["Low", "Medium", "High"]
