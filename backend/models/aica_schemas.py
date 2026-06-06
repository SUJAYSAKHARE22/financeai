"""
AI_CA Module — Pydantic schemas
These are NEW models only. Existing schemas.py is untouched.
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


# ── Enums ─────────────────────────────────────────────────────────────────────

class AICACategory(str, Enum):
    SALARY = "salary"
    FREELANCE_INCOME = "freelance_income"
    BUSINESS_INCOME = "business_income"
    INTEREST_INCOME = "interest_income"
    CAPITAL_GAINS = "capital_gains"
    FOOD = "food"
    FUEL = "fuel"
    TRAVEL = "travel"
    OFFICE_EXPENSE = "office_expense"
    RENT = "rent"
    ENTERTAINMENT = "entertainment"
    INVESTMENT = "investment"
    TAX_PAYMENT = "tax_payment"
    UTILITIES = "utilities"
    MEDICAL = "medical"
    LOAN_PAYMENT = "loan_payment"
    INSURANCE = "insurance"
    OTHER = "other"


class ReportPeriod(str, Enum):
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    YEARLY = "yearly"


class ReportFormat(str, Enum):
    JSON = "json"
    PDF = "pdf"
    EXCEL = "excel"


class TaxRegime(str, Enum):
    OLD = "old"
    NEW = "new"


# ── Classification ─────────────────────────────────────────────────────────────

class TaxFlags(BaseModel):
    taxable: bool = True
    deductible: bool = False
    gst_applicable: bool = False
    tds_applicable: bool = False
    business_related: bool = False
    tax_category: str = "other"
    section_80c: bool = False      # LIC, PPF, ELSS etc.
    section_80d: bool = False      # Medical insurance
    hra_applicable: bool = False


class ClassifiedTransaction(BaseModel):
    transaction_id: str
    original_title: str
    original_amount: float
    original_category: str
    aica_category: AICACategory
    tax_flags: TaxFlags
    confidence: float = Field(ge=0.0, le=1.0)
    classification_source: str  # "rule_engine" | "ai" | "hybrid"
    notes: Optional[str] = None


class ClassifyRequest(BaseModel):
    transaction_ids: Optional[List[str]] = None   # None = classify all
    use_ai: bool = True


class ClassifyResponse(BaseModel):
    classified: List[ClassifiedTransaction]
    total: int
    ai_classified: int
    rule_classified: int


# ── Ledger ─────────────────────────────────────────────────────────────────────

class LedgerEntry(BaseModel):
    id: Optional[str] = None
    date: datetime
    description: str
    account: str
    debit: float = 0.0
    credit: float = 0.0
    balance: float = 0.0
    transaction_id: Optional[str] = None
    aica_category: str = "other"


class JournalEntry(BaseModel):
    id: Optional[str] = None
    date: datetime
    narration: str
    debit_account: str
    credit_account: str
    amount: float
    transaction_id: Optional[str] = None


# ── Tax Computation ────────────────────────────────────────────────────────────

class TaxSlab(BaseModel):
    min_income: float
    max_income: float  # -1 = no upper limit
    rate: float        # percentage


class DeductionSummary(BaseModel):
    section_80c: float = 0.0      # max 1,50,000
    section_80d: float = 0.0      # max 25,000 / 50,000 senior
    hra_exemption: float = 0.0
    standard_deduction: float = 75000.0   # FY 2024-25 new regime
    other_deductions: float = 0.0
    total_deductions: float = 0.0


class TaxComputationResult(BaseModel):
    financial_year: str
    tax_regime: TaxRegime
    gross_income: float
    total_deductions: float
    taxable_income: float
    deduction_breakdown: DeductionSummary
    tax_before_cess: float
    education_cess: float           # 4%
    total_tax_liability: float
    tds_already_paid: float
    net_tax_payable: float
    effective_tax_rate: float
    slabs_applied: List[Dict[str, Any]]


# ── Financial Statements ───────────────────────────────────────────────────────

class ProfitLossStatement(BaseModel):
    period: str
    period_type: ReportPeriod
    total_income: float
    income_breakdown: Dict[str, float]
    total_expenses: float
    expense_breakdown: Dict[str, float]
    gross_profit: float
    net_profit: float
    profit_margin: float


class CashFlowSummary(BaseModel):
    period: str
    opening_balance: float
    total_inflows: float
    total_outflows: float
    net_cash_flow: float
    closing_balance: float
    inflow_breakdown: Dict[str, float]
    outflow_breakdown: Dict[str, float]


class TaxSummaryReport(BaseModel):
    period: str
    financial_year: str
    total_income: float
    taxable_income: float
    deductible_expenses: float
    tax_paid: float
    estimated_tax_liability: float
    tds_summary: Dict[str, float]
    deduction_summary: DeductionSummary
    recommendations: List[str]


# ── AI Chat ────────────────────────────────────────────────────────────────────

class AICAMessage(BaseModel):
    role: str
    content: str


class AICAhatRequest(BaseModel):
    message: str
    conversation_history: Optional[List[AICAMessage]] = []
    include_tax_context: bool = True


# ── Report Request ─────────────────────────────────────────────────────────────

class ReportRequest(BaseModel):
    report_type: str   # "pl" | "tax" | "cashflow" | "expense" | "full"
    period: ReportPeriod = ReportPeriod.MONTHLY
    month: Optional[int] = None
    year: Optional[int] = None
    quarter: Optional[int] = None   # 1-4
    format: ReportFormat = ReportFormat.JSON
    tax_regime: TaxRegime = TaxRegime.NEW
    financial_year: Optional[str] = None  # e.g. "2024-25"


class TaxpayerProfile(BaseModel):
    first_name: str = "Rajesh"
    middle_name: Optional[str] = ""
    last_name: str = "Kumar"
    pan: str = "ABCDE1234F"
    aadhaar_no: str = "1234 5678 9012"
    dob: str = "1985-08-15"
    email: str = "rajesh.kumar@gmail.com"
    mobile: str = "9876543210"
    address_flat: str = "Flat 402, Building A"
    address_premises: str = "Green Glen Layout"
    address_road: str = "Outer Ring Road"
    address_area: str = "Bellandur"
    address_city: str = "Bengaluru"
    address_state: str = "Karnataka"
    address_pin: str = "560103"
    employer_type: str = "PRIVATE"  # GOVT, PSU, PRIVATE, OTHERS
    bank_name: str = "HDFC Bank"
    bank_account_no: str = "50100412345678"
    bank_ifsc: str = "HDFC0000184"
    bank_refund_eligible: bool = True


class ITRFilingRequest(BaseModel):
    profile: TaxpayerProfile
    tax_regime: TaxRegime = TaxRegime.NEW
    financial_year: str = "2024-25"