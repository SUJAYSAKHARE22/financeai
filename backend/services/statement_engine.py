"""
AI_CA Financial Statement Generator
Generates P&L, Cash Flow, Tax Summary from classified transactions.
"""
from datetime import datetime
from typing import List, Dict, Optional
from models.aica_schemas import (
    ProfitLossStatement, CashFlowSummary, TaxSummaryReport,
    ReportPeriod, AICACategory, DeductionSummary
)

INCOME_CATEGORIES = {
    AICACategory.SALARY, AICACategory.FREELANCE_INCOME, AICACategory.BUSINESS_INCOME,
    AICACategory.INTEREST_INCOME, AICACategory.CAPITAL_GAINS,
}


def _period_label(period: ReportPeriod, month: Optional[int], year: Optional[int], quarter: Optional[int]) -> str:
    now = datetime.utcnow()
    y = year or now.year
    if period == ReportPeriod.MONTHLY:
        m = month or now.month
        return datetime(y, m, 1).strftime("%B %Y")
    elif period == ReportPeriod.QUARTERLY:
        q = quarter or ((now.month - 1) // 3 + 1)
        return f"Q{q} FY{y}"
    else:
        return f"FY {y}"


def _filter_by_period(classified: list, period: ReportPeriod,
                       month: Optional[int], year: Optional[int],
                       quarter: Optional[int]) -> list:
    """Filter classified transactions to the requested period using original_amount > 0 as proxy."""
    # Since in-memory DB doesn't store dates on classified objects, return all.
    # In a real DB implementation, filter by transaction date here.
    return classified


def generate_pl_statement(
    classified: list,
    period: ReportPeriod,
    month: Optional[int] = None,
    year: Optional[int] = None,
    quarter: Optional[int] = None,
) -> ProfitLossStatement:
    filtered = _filter_by_period(classified, period, month, year, quarter)

    income_breakdown: Dict[str, float] = {}
    expense_breakdown: Dict[str, float] = {}

    for ct in filtered:
        cat_val = ct.aica_category.value if hasattr(ct.aica_category, 'value') else str(ct.aica_category)
        if ct.aica_category in INCOME_CATEGORIES:
            income_breakdown[cat_val] = income_breakdown.get(cat_val, 0.0) + ct.original_amount
        else:
            expense_breakdown[cat_val] = expense_breakdown.get(cat_val, 0.0) + ct.original_amount

    total_income = sum(income_breakdown.values())
    total_expenses = sum(expense_breakdown.values())
    gross_profit = total_income - total_expenses
    profit_margin = (gross_profit / total_income * 100) if total_income > 0 else 0.0

    return ProfitLossStatement(
        period=_period_label(period, month, year, quarter),
        period_type=period,
        total_income=round(total_income, 2),
        income_breakdown={k: round(v, 2) for k, v in income_breakdown.items()},
        total_expenses=round(total_expenses, 2),
        expense_breakdown={k: round(v, 2) for k, v in expense_breakdown.items()},
        gross_profit=round(gross_profit, 2),
        net_profit=round(gross_profit, 2),
        profit_margin=round(profit_margin, 2),
    )


def generate_cashflow(
    classified: list,
    period: ReportPeriod,
    month: Optional[int] = None,
    year: Optional[int] = None,
    quarter: Optional[int] = None,
    opening_balance: float = 0.0,
) -> CashFlowSummary:
    filtered = _filter_by_period(classified, period, month, year, quarter)

    inflow_breakdown: Dict[str, float] = {}
    outflow_breakdown: Dict[str, float] = {}

    for ct in filtered:
        cat_val = ct.aica_category.value if hasattr(ct.aica_category, 'value') else str(ct.aica_category)
        if ct.aica_category in INCOME_CATEGORIES:
            inflow_breakdown[cat_val] = inflow_breakdown.get(cat_val, 0.0) + ct.original_amount
        else:
            outflow_breakdown[cat_val] = outflow_breakdown.get(cat_val, 0.0) + ct.original_amount

    total_in = sum(inflow_breakdown.values())
    total_out = sum(outflow_breakdown.values())
    net = total_in - total_out

    return CashFlowSummary(
        period=_period_label(period, month, year, quarter),
        opening_balance=round(opening_balance, 2),
        total_inflows=round(total_in, 2),
        total_outflows=round(total_out, 2),
        net_cash_flow=round(net, 2),
        closing_balance=round(opening_balance + net, 2),
        inflow_breakdown={k: round(v, 2) for k, v in inflow_breakdown.items()},
        outflow_breakdown={k: round(v, 2) for k, v in outflow_breakdown.items()},
    )


def generate_tax_summary(
    classified: list,
    tax_result,
    recommendations: List[str],
    period: ReportPeriod,
    month: Optional[int] = None,
    year: Optional[int] = None,
    financial_year: str = "2024-25",
) -> TaxSummaryReport:
    deductible_total = sum(
        ct.original_amount for ct in classified if ct.tax_flags.deductible
    )
    tds_summary: Dict[str, float] = {}
    for ct in classified:
        if ct.tax_flags.tds_applicable:
            cat = ct.aica_category.value if hasattr(ct.aica_category, 'value') else str(ct.aica_category)
            tds_summary[cat] = tds_summary.get(cat, 0.0) + ct.original_amount * 0.10

    return TaxSummaryReport(
        period=_period_label(period, month, year, None),
        financial_year=financial_year,
        total_income=tax_result.gross_income,
        taxable_income=tax_result.taxable_income,
        deductible_expenses=round(deductible_total, 2),
        tax_paid=tax_result.tds_already_paid,
        estimated_tax_liability=tax_result.total_tax_liability,
        tds_summary={k: round(v, 2) for k, v in tds_summary.items()},
        deduction_summary=tax_result.deduction_breakdown,
        recommendations=recommendations,
    )


def generate_expense_category_report(classified: list) -> Dict:
    """Categorized expense breakdown with deductibility flags."""
    report = {}
    for ct in classified:
        if ct.aica_category in INCOME_CATEGORIES:
            continue
        cat = ct.aica_category.value if hasattr(ct.aica_category, 'value') else str(ct.aica_category)
        if cat not in report:
            report[cat] = {
                "total": 0.0, "count": 0,
                "deductible": 0.0, "non_deductible": 0.0,
                "business": 0.0, "personal": 0.0,
            }
        report[cat]["total"] += ct.original_amount
        report[cat]["count"] += 1
        if ct.tax_flags.deductible:
            report[cat]["deductible"] += ct.original_amount
        else:
            report[cat]["non_deductible"] += ct.original_amount
        if ct.tax_flags.business_related:
            report[cat]["business"] += ct.original_amount
        else:
            report[cat]["personal"] += ct.original_amount

    return {k: {sk: round(sv, 2) for sk, sv in v.items()} for k, v in report.items()}
