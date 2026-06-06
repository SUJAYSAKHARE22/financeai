"""
AI_CA Router
All /api/ai-ca/* endpoints.
Does NOT modify any existing routers.
"""
import logging
from datetime import datetime
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import Response

from models.aica_schemas import (
    ClassifyRequest, ClassifyResponse, ReportRequest, ReportPeriod,
    ReportFormat, TaxRegime, AICAhatRequest, TaxpayerProfile, ITRFilingRequest,
)
from services.classifier_service import classify_transactions
from services.tax_engine import compute_tax, generate_tax_recommendations
from services.ledger_engine import generate_ledger_entries, generate_journal_entries, generate_account_summary
from services.statement_engine import (
    generate_pl_statement, generate_cashflow,
    generate_tax_summary, generate_expense_category_report,
)
from services.aica_chat_service import aica_chat
from services.report_generator import generate_pdf_report, generate_excel_report
from services.itr_generator import generate_itr_json, generate_itr1_pdf, generate_form16_pdf, generate_form26as_pdf

# Import existing DB — read-only usage, never modify existing data
from services.database import db

router = APIRouter()
logger = logging.getLogger(__name__)

# ── Shared helper ──────────────────────────────────────────────────────────────

def _get_classified(use_ai: bool = True):
    """Classify all transactions from existing DB."""
    transactions = db.get_all_transactions()
    if not transactions:
        return []
    response = classify_transactions(transactions, use_ai=use_ai)
    return response.classified


# ── 1. Classify ───────────────────────────────────────────────────────────────

@router.post("/classify", response_model=ClassifyResponse, summary="Classify transactions for tax")
def classify(request: ClassifyRequest):
    """
    Classify all (or selected) transactions using rule engine + optional AI.
    Returns enriched classification with tax flags.
    """
    all_transactions = db.get_all_transactions()
    if not all_transactions:
        return ClassifyResponse(classified=[], total=0, ai_classified=0, rule_classified=0)

    if request.transaction_ids:
        id_set = set(request.transaction_ids)
        filtered = [t for t in all_transactions if t.id in id_set]
    else:
        filtered = all_transactions

    return classify_transactions(filtered, use_ai=request.use_ai)


# ── 2. Tax Summary ────────────────────────────────────────────────────────────

@router.get("/tax-summary", summary="Get Indian income tax computation")
def tax_summary(
    regime: TaxRegime = Query(TaxRegime.NEW, description="old or new tax regime"),
    financial_year: str = Query("2024-25"),
    existing_tds: float = Query(0.0, description="TDS already deducted (₹)"),
):
    """
    Compute estimated Indian income tax liability based on all classified transactions.
    """
    classified = _get_classified(use_ai=False)   # rule engine only for speed
    if not classified:
        raise HTTPException(status_code=404, detail="No transactions found to compute tax")

    result = compute_tax(classified, regime, financial_year, existing_tds)
    recommendations = generate_tax_recommendations(result, classified)

    return {
        "tax_computation": result.model_dump(),
        "recommendations": recommendations,
        "classified_count": len(classified),
        "regime": regime,
        "financial_year": financial_year,
    }


# ── 3. Financial Statements ───────────────────────────────────────────────────

@router.get("/financial-statements", summary="Get P&L, Cash Flow, Expense Summary")
def financial_statements(
    period: ReportPeriod = Query(ReportPeriod.MONTHLY),
    month: int = Query(None, ge=1, le=12),
    year: int = Query(None, ge=2000),
    quarter: int = Query(None, ge=1, le=4),
    regime: TaxRegime = Query(TaxRegime.NEW),
    financial_year: str = Query("2024-25"),
):
    classified = _get_classified(use_ai=False)
    if not classified:
        raise HTTPException(status_code=404, detail="No transactions found")

    now = datetime.utcnow()
    pl = generate_pl_statement(classified, period, month, year, quarter)
    cf = generate_cashflow(classified, period, month, year, quarter)
    tax_result = compute_tax(classified, regime, financial_year)
    recs = generate_tax_recommendations(tax_result, classified)
    tax_sum = generate_tax_summary(classified, tax_result, recs, period, month, year, financial_year)
    expense_report = generate_expense_category_report(classified)

    return {
        "profit_loss": pl.model_dump(),
        "cash_flow": cf.model_dump(),
        "tax_summary": tax_sum.model_dump(),
        "expense_breakdown": expense_report,
        "period": period,
        "generated_at": now.isoformat(),
    }


# ── 4. Ledger ─────────────────────────────────────────────────────────────────

@router.get("/ledger", summary="Get accounting ledger entries")
def ledger():
    classified = _get_classified(use_ai=False)
    if not classified:
        raise HTTPException(status_code=404, detail="No transactions found")

    entries = generate_ledger_entries(classified)
    journals = generate_journal_entries(classified)
    account_summary = generate_account_summary(classified)

    db.ledger_entries.clear()
    for e in entries:
        db.save_ledger_entry(e)

    db.journal_entries.clear()
    for j in journals:
        db.save_journal_entry(j)

    return {
        "ledger_entries": [e.model_dump() for e in entries],
        "journal_entries": [j.model_dump() for j in journals],
        "account_summary": account_summary,
        "total_entries": len(entries),
    }


# ── 5. Reports (JSON / PDF / Excel) ───────────────────────────────────────────

@router.post("/reports", summary="Generate downloadable reports (JSON/PDF/Excel)")
def generate_report(request: ReportRequest):
    classified = _get_classified(use_ai=False)
    if not classified:
        raise HTTPException(status_code=404, detail="No transactions found")

    now = datetime.utcnow()
    regime = request.tax_regime
    fy = request.financial_year or "2024-25"

    # Build report data dict
    pl = generate_pl_statement(classified, request.period, request.month, request.year, request.quarter)
    cf = generate_cashflow(classified, request.period, request.month, request.year, request.quarter)
    tax_result = compute_tax(classified, regime, fy)
    recs = generate_tax_recommendations(tax_result, classified)
    tax_sum = generate_tax_summary(classified, tax_result, recs, request.period, request.month, request.year, fy)
    expense_report = generate_expense_category_report(classified)

    report_data = {
        "report_info": {
            "type": request.report_type,
            "period": request.period,
            "generated_at": now.isoformat(),
            "financial_year": fy,
            "tax_regime": regime,
        },
        "profit_loss": pl.model_dump(),
        "cash_flow": cf.model_dump(),
        "tax_summary": {
            "total_income": tax_sum.total_income,
            "taxable_income": tax_sum.taxable_income,
            "deductible_expenses": tax_sum.deductible_expenses,
            "tax_paid": tax_sum.tax_paid,
            "estimated_tax_liability": tax_sum.estimated_tax_liability,
        },
        "deductions": tax_result.deduction_breakdown.model_dump(),
        "expense_categories": expense_report,
        "recommendations": recs,
    }

    if request.format == ReportFormat.JSON:
        return report_data

    elif request.format == ReportFormat.PDF:
        try:
            pdf_bytes = generate_pdf_report(report_data, request.report_type)
            return Response(
                content=pdf_bytes,
                media_type="application/pdf",
                headers={"Content-Disposition": f"attachment; filename=financeai_report_{now.strftime('%Y%m%d')}.pdf"}
            )
        except Exception as e:
            logger.error(f"PDF generation failed: {e}")
            raise HTTPException(status_code=500, detail=f"PDF generation failed: {e}")

    elif request.format == ReportFormat.EXCEL:
        try:
            xlsx_bytes = generate_excel_report(report_data, request.report_type)
            return Response(
                content=xlsx_bytes,
                media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                headers={"Content-Disposition": f"attachment; filename=financeai_report_{now.strftime('%Y%m%d')}.xlsx"}
            )
        except Exception as e:
            logger.error(f"Excel generation failed: {e}")
            raise HTTPException(status_code=500, detail=f"Excel generation failed: {e}")


# ── 6. AI-CA Chat ─────────────────────────────────────────────────────────────

@router.post("/chat", summary="Chat with AI Chartered Accountant")
def aica_chat_endpoint(request: AICAhatRequest):
    classified = _get_classified(use_ai=False)
    fin_ctx = db.get_financial_summary()

    # Build tax context for prompt
    if classified:
        from models.aica_schemas import TaxRegime as TR
        tax_result = compute_tax(classified, TR.NEW, "2024-25")
        deductible = sum(ct.original_amount for ct in classified if ct.tax_flags.deductible)
        tax_ctx = {
            "gross_income": tax_result.gross_income,
            "taxable_income": tax_result.taxable_income,
            "tax_regime": tax_result.tax_regime,
            "total_tax_liability": tax_result.total_tax_liability,
            "net_tax_payable": tax_result.net_tax_payable,
            "tds_already_paid": tax_result.tds_already_paid,
            "tax_before_cess": tax_result.tax_before_cess,
            "education_cess": tax_result.education_cess,
            "total_deductions": tax_result.total_deductions,
            "effective_tax_rate": tax_result.effective_tax_rate,
            "section_80c": tax_result.deduction_breakdown.section_80c,
            "section_80d": tax_result.deduction_breakdown.section_80d,
            "standard_deduction": tax_result.deduction_breakdown.standard_deduction,
            "deductible_expenses": deductible,
        }
    else:
        tax_ctx = {}

    return aica_chat(request, tax_ctx, fin_ctx)


# ── 7. Overview / Dashboard data ─────────────────────────────────────────────

@router.get("/overview", summary="AI-CA dashboard overview")
def overview(regime: TaxRegime = Query(TaxRegime.NEW)):
    classified = _get_classified(use_ai=False)
    fin_ctx = db.get_financial_summary()

    if not classified:
        return {
            "message": "No transactions to analyze. Add transactions first.",
            "financial_summary": fin_ctx,
        }

    tax_result = compute_tax(classified, regime, "2024-25")
    recs = generate_tax_recommendations(tax_result, classified)
    expense_report = generate_expense_category_report(classified)

    deductible_total = sum(ct.original_amount for ct in classified if ct.tax_flags.deductible)
    business_total = sum(ct.original_amount for ct in classified if ct.tax_flags.business_related)
    gst_total = sum(ct.original_amount for ct in classified if ct.tax_flags.gst_applicable)

    category_counts = {}
    for ct in classified:
        cat = ct.aica_category.value if hasattr(ct.aica_category, 'value') else str(ct.aica_category)
        category_counts[cat] = category_counts.get(cat, 0) + 1

    return {
        "financial_summary": fin_ctx,
        "tax_snapshot": {
            "regime": regime,
            "gross_income": tax_result.gross_income,
            "taxable_income": tax_result.taxable_income,
            "total_tax_liability": tax_result.total_tax_liability,
            "net_tax_payable": tax_result.net_tax_payable,
            "effective_tax_rate": tax_result.effective_tax_rate,
        },
        "deduction_snapshot": tax_result.deduction_breakdown.model_dump(),
        "expense_flags": {
            "deductible_total": round(deductible_total, 2),
            "business_related_total": round(business_total, 2),
            "gst_applicable_total": round(gst_total, 2),
        },
        "category_distribution": category_counts,
        "top_expense_categories": dict(
            sorted(expense_report.items(), key=lambda x: x[1]["total"], reverse=True)[:5]
        ),
        "recommendations": recs[:3],
        "classified_transactions": len(classified),
    }


# ── 8. E-Filing & Documents ───────────────────────────────────────────────────

@router.get("/profile", summary="Get taxpayer profile details")
def get_profile():
    return db.get_taxpayer_profile()


@router.post("/profile", summary="Update taxpayer profile details")
def update_profile(profile: TaxpayerProfile):
    return db.save_taxpayer_profile(profile.model_dump())


@router.post("/itr/json", summary="Generate ready-to-file ITR portal JSON")
def get_itr_json_route(request: ITRFilingRequest):
    classified = _get_classified(use_ai=False)
    tax_result = compute_tax(classified, request.tax_regime, request.financial_year)
    itr_json = generate_itr_json(request.profile, tax_result.model_dump(), classified)
    return itr_json


@router.post("/itr/pdf", summary="Generate filled ITR-1 Sahaj PDF Form")
def get_itr_pdf_route(request: ITRFilingRequest):
    try:
        classified = _get_classified(use_ai=False)
        tax_result = compute_tax(classified, request.tax_regime, request.financial_year)
        pdf_bytes = generate_itr1_pdf(request.profile, tax_result.model_dump(), classified)
        now = datetime.utcnow()
        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename=itr1_sahaj_{now.strftime('%Y%m%d')}.pdf"}
        )
    except Exception as e:
        logger.error(f"Failed to generate ITR PDF: {e}")
        raise HTTPException(status_code=500, detail=f"ITR PDF generation failed: {e}")


@router.post("/document/form16", summary="Generate Form 16 Tax Summary PDF")
def get_form16_route(request: ITRFilingRequest):
    try:
        classified = _get_classified(use_ai=False)
        tax_result = compute_tax(classified, request.tax_regime, request.financial_year)
        pdf_bytes = generate_form16_pdf(request.profile, tax_result.model_dump(), classified)
        now = datetime.utcnow()
        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename=form16_salary_{now.strftime('%Y%m%d')}.pdf"}
        )
    except Exception as e:
        logger.error(f"Failed to generate Form 16: {e}")
        raise HTTPException(status_code=500, detail=f"Form 16 PDF generation failed: {e}")


@router.post("/document/form26as", summary="Generate Form 26AS TDS Credit Statement PDF")
def get_form26as_route(request: ITRFilingRequest):
    try:
        classified = _get_classified(use_ai=False)
        tax_result = compute_tax(classified, request.tax_regime, request.financial_year)
        pdf_bytes = generate_form26as_pdf(request.profile, tax_result.model_dump(), classified)
        now = datetime.utcnow()
        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename=form26as_credit_{now.strftime('%Y%m%d')}.pdf"}
        )
    except Exception as e:
        logger.error(f"Failed to generate Form 26AS: {e}")
        raise HTTPException(status_code=500, detail=f"Form 26AS PDF generation failed: {e}")
