"""
AI_CA Tax Computation Engine
Indian Income Tax — FY 2024-25 (AY 2025-26)
Supports both Old and New Tax Regime.
Pure deterministic logic — no LLM dependency.
"""
from typing import List, Dict, Any
from models.aica_schemas import (
    TaxComputationResult, DeductionSummary, TaxRegime, TaxSlab, AICACategory
)

# ── Tax Slabs ──────────────────────────────────────────────────────────────────

NEW_REGIME_SLABS: List[TaxSlab] = [
    TaxSlab(min_income=0,        max_income=300000,   rate=0.0),
    TaxSlab(min_income=300000,   max_income=700000,   rate=5.0),
    TaxSlab(min_income=700000,   max_income=1000000,  rate=10.0),
    TaxSlab(min_income=1000000,  max_income=1200000,  rate=15.0),
    TaxSlab(min_income=1200000,  max_income=1500000,  rate=20.0),
    TaxSlab(min_income=1500000,  max_income=-1,       rate=30.0),
]

OLD_REGIME_SLABS: List[TaxSlab] = [
    TaxSlab(min_income=0,        max_income=250000,   rate=0.0),
    TaxSlab(min_income=250000,   max_income=500000,   rate=5.0),
    TaxSlab(min_income=500000,   max_income=1000000,  rate=20.0),
    TaxSlab(min_income=1000000,  max_income=-1,       rate=30.0),
]

# Section 80C limit
SEC_80C_LIMIT = 150000.0
# Section 80D limit (non-senior)
SEC_80D_LIMIT = 25000.0
# Standard deduction (New regime FY24-25)
STANDARD_DEDUCTION_NEW = 75000.0
# Standard deduction (Old regime)
STANDARD_DEDUCTION_OLD = 50000.0
# Rebate u/s 87A (New regime — income ≤ 7L → zero tax)
REBATE_87A_NEW = 7_00_000.0
# Education + Health cess
CESS_RATE = 0.04


def _apply_slabs(taxable_income: float, slabs: List[TaxSlab]) -> tuple[float, List[Dict[str, Any]]]:
    """Returns (tax_amount, slab_breakdown_list)."""
    tax = 0.0
    breakdown = []
    for slab in slabs:
        if taxable_income <= slab.min_income:
            break
        upper = slab.max_income if slab.max_income != -1 else taxable_income
        taxable_in_slab = min(taxable_income, upper) - slab.min_income
        if taxable_in_slab <= 0:
            continue
        slab_tax = taxable_in_slab * slab.rate / 100
        tax += slab_tax
        breakdown.append({
            "slab": f"₹{slab.min_income:,.0f} – {'above' if slab.max_income == -1 else f'₹{slab.max_income:,.0f}'}",
            "rate": f"{slab.rate}%",
            "income_in_slab": round(taxable_in_slab, 2),
            "tax": round(slab_tax, 2),
        })
    return tax, breakdown


def compute_tax(
    classified_transactions: list,
    regime: TaxRegime,
    financial_year: str = "2024-25",
    existing_tds: float = 0.0,
) -> TaxComputationResult:
    """
    Core tax computation function.
    classified_transactions: list of ClassifiedTransaction objects.
    """
    # ── Step 1: Aggregate incomes and deductions ──────────────────────────────
    income_categories = {
        AICACategory.SALARY, AICACategory.FREELANCE_INCOME,
        AICACategory.BUSINESS_INCOME, AICACategory.INTEREST_INCOME,
        AICACategory.CAPITAL_GAINS,
    }

    gross_income = 0.0
    sec_80c_total = 0.0
    sec_80d_total = 0.0
    tds_paid = existing_tds
    hra_deductible = 0.0

    for ct in classified_transactions:
        if ct.aica_category in income_categories:
            gross_income += ct.original_amount
        if ct.tax_flags.tds_applicable:
            tds_paid += ct.original_amount * 0.10   # rough 10% TDS estimate
        if ct.tax_flags.section_80c and ct.tax_flags.deductible:
            sec_80c_total += ct.original_amount
        if ct.tax_flags.section_80d and ct.tax_flags.deductible:
            sec_80d_total += ct.original_amount
        if ct.tax_flags.hra_applicable:
            hra_deductible += ct.original_amount * 0.40  # 40% of rent as HRA estimate

    # ── Step 2: Apply limits ──────────────────────────────────────────────────
    sec_80c_allowed = min(sec_80c_total, SEC_80C_LIMIT)
    sec_80d_allowed = min(sec_80d_total, SEC_80D_LIMIT)

    if regime == TaxRegime.NEW:
        standard_deduction = STANDARD_DEDUCTION_NEW
        # New regime: only standard deduction allowed
        total_deductions = standard_deduction
    else:
        standard_deduction = STANDARD_DEDUCTION_OLD
        total_deductions = standard_deduction + sec_80c_allowed + sec_80d_allowed + hra_deductible

    deduction_summary = DeductionSummary(
        section_80c=round(sec_80c_allowed, 2),
        section_80d=round(sec_80d_allowed, 2),
        hra_exemption=round(hra_deductible, 2) if regime == TaxRegime.OLD else 0.0,
        standard_deduction=round(standard_deduction, 2),
        other_deductions=0.0,
        total_deductions=round(total_deductions, 2),
    )

    taxable_income = max(gross_income - total_deductions, 0.0)

    # ── Step 3: Compute tax ───────────────────────────────────────────────────
    slabs = NEW_REGIME_SLABS if regime == TaxRegime.NEW else OLD_REGIME_SLABS
    tax_before_cess, slabs_applied = _apply_slabs(taxable_income, slabs)

    # Rebate u/s 87A — new regime: full rebate if taxable ≤ 7L
    if regime == TaxRegime.NEW and taxable_income <= REBATE_87A_NEW:
        tax_before_cess = 0.0
        slabs_applied = [{"note": "Full rebate u/s 87A — taxable income ≤ ₹7,00,000"}]

    education_cess = tax_before_cess * CESS_RATE
    total_tax = tax_before_cess + education_cess
    net_tax_payable = max(total_tax - tds_paid, 0.0)
    effective_rate = (total_tax / gross_income * 100) if gross_income > 0 else 0.0

    return TaxComputationResult(
        financial_year=financial_year,
        tax_regime=regime,
        gross_income=round(gross_income, 2),
        total_deductions=round(total_deductions, 2),
        taxable_income=round(taxable_income, 2),
        deduction_breakdown=deduction_summary,
        tax_before_cess=round(tax_before_cess, 2),
        education_cess=round(education_cess, 2),
        total_tax_liability=round(total_tax, 2),
        tds_already_paid=round(tds_paid, 2),
        net_tax_payable=round(net_tax_payable, 2),
        effective_tax_rate=round(effective_rate, 2),
        slabs_applied=slabs_applied,
    )


def generate_tax_recommendations(result: TaxComputationResult, classified: list) -> list[str]:
    """Generate actionable tax-saving recommendations."""
    recs = []
    regime = result.tax_regime
    ded = result.deduction_breakdown

    if regime == TaxRegime.NEW:
        if result.taxable_income > 7_00_000:
            recs.append(
                f"Consider switching to Old Regime — with 80C/80D deductions you may reduce "
                f"taxable income significantly."
            )
    else:
        remaining_80c = max(0, 150000 - ded.section_80c)
        if remaining_80c > 0:
            recs.append(
                f"You can still invest ₹{remaining_80c:,.0f} under Section 80C "
                f"(PPF, ELSS, LIC, NSC) to reduce taxable income."
            )
        remaining_80d = max(0, 25000 - ded.section_80d)
        if remaining_80d > 0:
            recs.append(
                f"Consider health insurance to claim up to ₹{remaining_80d:,.0f} more "
                f"under Section 80D."
            )

    if result.net_tax_payable > 10000:
        recs.append(
            f"Advance tax of ₹{result.net_tax_payable:,.0f} is due. "
            f"Pay in installments to avoid interest u/s 234B/234C."
        )

    if result.tds_already_paid > result.total_tax_liability:
        excess = result.tds_already_paid - result.total_tax_liability
        recs.append(
            f"You have excess TDS of ₹{excess:,.0f}. File ITR to claim refund."
        )

    if not recs:
        recs.append("Your tax planning looks efficient for this period.")

    return recs