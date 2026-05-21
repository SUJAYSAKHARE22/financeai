"""
AI_CA Rule Engine
Deterministic rule-based transaction classifier.
No LLM dependency — fast, reliable, always-on.
"""
from typing import Tuple
from models.aica_schemas import AICACategory, TaxFlags

# ── Keyword maps ───────────────────────────────────────────────────────────────
# Each entry: (aica_category, confidence, tax_flags_overrides)

KEYWORD_RULES: list[tuple] = [
    # INCOME ──────────────────────────────────────────────────────────────────
    (["salary", "payroll", "ctc", "basic pay", "in-hand"], AICACategory.SALARY, 0.95,
     {"taxable": True, "deductible": False, "tds_applicable": True}),

    (["freelance", "consulting fee", "project payment", "client payment", "upwork", "fiverr"],
     AICACategory.FREELANCE_INCOME, 0.90,
     {"taxable": True, "deductible": False, "tds_applicable": True, "business_related": True}),

    (["business revenue", "sales", "invoice", "gst invoice", "b2b", "client"],
     AICACategory.BUSINESS_INCOME, 0.88,
     {"taxable": True, "deductible": False, "gst_applicable": True, "tds_applicable": True, "business_related": True}),

    (["interest", "fd interest", "savings interest", "bank interest", "nsc interest"],
     AICACategory.INTEREST_INCOME, 0.92,
     {"taxable": True, "deductible": False, "tds_applicable": True}),

    (["capital gain", "mutual fund redemption", "stock sale", "shares sold", "equity sale"],
     AICACategory.CAPITAL_GAINS, 0.90,
     {"taxable": True, "deductible": False}),

    # DEDUCTIBLE EXPENSES ─────────────────────────────────────────────────────
    (["lic", "life insurance", "term insurance", "premium", "insurance premium"],
     AICACategory.INSURANCE, 0.93,
     {"deductible": True, "section_80c": True, "section_80d": True}),

    (["ppf", "public provident", "nsc", "elss", "tax saving", "80c"],
     AICACategory.INVESTMENT, 0.95,
     {"deductible": True, "section_80c": True}),

    (["mediclaim", "health insurance", "medical insurance", "star health", "hdfc ergo health"],
     AICACategory.INSURANCE, 0.93,
     {"deductible": True, "section_80d": True}),

    (["rent", "house rent", "pg rent", "apartment rent", "rental", "lease"],
     AICACategory.RENT, 0.92,
     {"deductible": False, "hra_applicable": True}),

    (["home loan emi", "housing loan", "home loan interest"],
     AICACategory.LOAN_PAYMENT, 0.92,
     {"deductible": True, "section_80c": True}),

    # BUSINESS EXPENSES ───────────────────────────────────────────────────────
    (["office", "stationery", "printer", "toner", "coworking", "workspace"],
     AICACategory.OFFICE_EXPENSE, 0.88,
     {"deductible": True, "business_related": True, "gst_applicable": True}),

    (["laptop", "computer", "monitor", "keyboard", "mouse", "software", "saas", "subscription"],
     AICACategory.OFFICE_EXPENSE, 0.82,
     {"deductible": True, "business_related": True, "gst_applicable": True}),

    (["flight", "train", "bus ticket", "cab", "taxi", "auto", "metro", "travel", "uber", "ola",
      "rapido", "toll", "hotel", "accommodation"],
     AICACategory.TRAVEL, 0.85,
     {"deductible": False, "business_related": False}),

    (["fuel", "petrol", "diesel", "cng", "hp petrol", "bharat petroleum", "indian oil"],
     AICACategory.FUEL, 0.95,
     {"deductible": False}),

    # MEDICAL ─────────────────────────────────────────────────────────────────
    (["hospital", "clinic", "doctor", "medicine", "pharmacy", "apollo", "fortis", "max hospital",
      "diagnostic", "lab test", "pathology", "chemist"],
     AICACategory.MEDICAL, 0.90,
     {"deductible": True, "section_80d": True}),

    # TAX PAYMENTS ────────────────────────────────────────────────────────────
    (["income tax", "advance tax", "self assessment tax", "tds payment", "gst payment",
      "gst challan", "tax challan", "nsdl tax"],
     AICACategory.TAX_PAYMENT, 0.97,
     {"taxable": False, "deductible": False}),

    # UTILITIES ───────────────────────────────────────────────────────────────
    (["electricity", "power bill", "bescom", "tata power", "msedcl", "water bill",
      "gas bill", "broadband", "internet", "wifi", "jio fiber", "airtel fiber",
      "mobile recharge", "dth", "tata sky", "dish tv"],
     AICACategory.UTILITIES, 0.90,
     {"deductible": False}),

    # LOAN PAYMENTS ───────────────────────────────────────────────────────────
    (["emi", "loan repayment", "loan emi", "credit card emi", "car loan", "bike loan",
      "personal loan", "hdfc loan", "sbi loan", "icici loan"],
     AICACategory.LOAN_PAYMENT, 0.88,
     {"deductible": False}),

    # FOOD ────────────────────────────────────────────────────────────────────
    (["swiggy", "zomato", "restaurant", "food", "grocery", "supermarket", "bigbasket",
      "blinkit", "zepto", "dunzo", "cafe", "coffee", "tea", "canteen", "mess"],
     AICACategory.FOOD, 0.90,
     {"deductible": False}),

    # ENTERTAINMENT ───────────────────────────────────────────────────────────
    (["netflix", "amazon prime", "hotstar", "disney", "sony liv", "zee5",
      "movie", "pvr", "inox", "game", "steam", "spotify", "youtube premium"],
     AICACategory.ENTERTAINMENT, 0.92,
     {"deductible": False}),

    # INVESTMENT ──────────────────────────────────────────────────────────────
    (["sip", "mutual fund", "zerodha", "groww", "angel broking", "demat",
      "nifty", "sensex", "stock", "equity", "gold bond", "fd", "fixed deposit", "rd"],
     AICACategory.INVESTMENT, 0.90,
     {"deductible": False}),
]


def _build_tax_flags(overrides: dict) -> TaxFlags:
    return TaxFlags(
        taxable=overrides.get("taxable", True),
        deductible=overrides.get("deductible", False),
        gst_applicable=overrides.get("gst_applicable", False),
        tds_applicable=overrides.get("tds_applicable", False),
        business_related=overrides.get("business_related", False),
        section_80c=overrides.get("section_80c", False),
        section_80d=overrides.get("section_80d", False),
        hra_applicable=overrides.get("hra_applicable", False),
        tax_category=overrides.get("tax_category", "general"),
    )


def classify_by_rules(title: str, amount: float, existing_category: str) -> Tuple[AICACategory, TaxFlags, float, str]:
    """
    Returns (aica_category, tax_flags, confidence, source).
    source is always "rule_engine".
    """
    title_lower = title.lower()
    cat_lower = existing_category.lower()
    search_text = f"{title_lower} {cat_lower}"

    best_match = None
    best_confidence = 0.0

    for rule in KEYWORD_RULES:
        keywords, category, confidence, flag_overrides = rule
        for kw in keywords:
            if kw in search_text:
                if confidence > best_confidence:
                    best_confidence = confidence
                    best_match = (category, flag_overrides)
                break

    if best_match:
        category, overrides = best_match
        return category, _build_tax_flags(overrides), best_confidence, "rule_engine"

    # Fallback: map existing category string
    fallback_map = {
        "food & dining": (AICACategory.FOOD, {}, 0.70),
        "transportation": (AICACategory.TRAVEL, {}, 0.70),
        "shopping": (AICACategory.OFFICE_EXPENSE, {"business_related": False}, 0.55),
        "entertainment": (AICACategory.ENTERTAINMENT, {}, 0.70),
        "bills & utilities": (AICACategory.UTILITIES, {}, 0.70),
        "health & medical": (AICACategory.MEDICAL, {"deductible": True, "section_80d": True}, 0.75),
        "education": (AICACategory.OFFICE_EXPENSE, {"deductible": True, "section_80c": True}, 0.65),
        "travel": (AICACategory.TRAVEL, {}, 0.70),
        "income": (AICACategory.SALARY, {"taxable": True, "tds_applicable": True}, 0.65),
        "investment": (AICACategory.INVESTMENT, {}, 0.75),
    }
    for key, (cat, overrides, conf) in fallback_map.items():
        if key in cat_lower:
            return cat, _build_tax_flags(overrides), conf, "rule_engine"

    return AICACategory.OTHER, _build_tax_flags({}), 0.40, "rule_engine"