"""
AI_CA Chat Service
Tax-aware conversational AI assistant using Groq.
"""
import os
import json
import logging
from models.aica_schemas import AICAhatRequest

logger = logging.getLogger(__name__)


def build_aica_system_prompt(tax_context: dict, financial_context: dict) -> str:
    return f"""You are AI-CA, an expert AI Chartered Accountant assistant specializing in Indian taxation and financial planning.

=== Client Financial Context ===
Monthly Income  : ₹{financial_context.get('total_income', 0):,.0f}
Monthly Expenses: ₹{financial_context.get('total_expense', 0):,.0f}
Net Savings     : ₹{financial_context.get('savings', 0):,.0f}
Savings Rate    : {financial_context.get('savings_rate', 0):.1f}%

=== Tax Context (Current FY) ===
Gross Income        : ₹{tax_context.get('gross_income', 0):,.0f}
Taxable Income      : ₹{tax_context.get('taxable_income', 0):,.0f}
Tax Regime          : {tax_context.get('tax_regime', 'new')}
Total Tax Liability : ₹{tax_context.get('total_tax_liability', 0):,.0f}
Net Tax Payable     : ₹{tax_context.get('net_tax_payable', 0):,.0f}
Deductions Used     :
  - 80C: ₹{tax_context.get('section_80c', 0):,.0f} (limit ₹1,50,000)
  - 80D: ₹{tax_context.get('section_80d', 0):,.0f} (limit ₹25,000)
  - Standard: ₹{tax_context.get('standard_deduction', 0):,.0f}

Deductible Expenses : ₹{tax_context.get('deductible_expenses', 0):,.0f}
================================

Your role:
- Answer Indian income tax questions with precision.
- Reference the client's actual financial data above.
- Cite relevant IT Act sections (80C, 80D, 87A, 44ADA etc.).
- Suggest legal tax saving strategies.
- Explain deductibility of specific expenses.
- Calculate estimated tax when asked.
- Always recommend consulting a qualified CA for final tax filing.
- Be concise, accurate, and use ₹ for all amounts.
- Do NOT give generic answers — personalize to the data above."""


def aica_chat(request: AICAhatRequest, tax_context: dict, financial_context: dict) -> dict:
    """Synchronous Groq chat call for AI-CA assistant."""
    api_key = os.environ.get("GROQ_API_KEY", "").strip()

    if not api_key:
        return _demo_tax_response(request.message, tax_context, financial_context)

    try:
        from groq import Groq, APIError
        client = Groq(api_key=api_key)

        system = build_aica_system_prompt(tax_context, financial_context)
        messages = [{"role": "system", "content": system}]
        for msg in request.conversation_history[-15:]:
            messages.append({"role": msg.role, "content": msg.content})
        messages.append({"role": "user", "content": request.message})

        completion = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=messages,
            temperature=0.3,    # lower temp for tax accuracy
            max_tokens=2048,
            stream=False,
        )
        return {
            "reply": completion.choices[0].message.content.strip(),
            "role": "assistant",
            "source": "ai"
        }

    except Exception as e:
        logger.error(f"AI-CA chat error: {e}")
        return _demo_tax_response(request.message, tax_context, financial_context)


def _demo_tax_response(message: str, tax_ctx: dict, fin_ctx: dict) -> dict:
    msg = message.lower()
    income = tax_ctx.get("gross_income", fin_ctx.get("total_income", 0))
    liability = tax_ctx.get("total_tax_liability", 0)
    taxable = tax_ctx.get("taxable_income", 0)
    sec_80c = tax_ctx.get("section_80c", 0)
    sec_80d = tax_ctx.get("section_80d", 0)
    deductible = tax_ctx.get("deductible_expenses", 0)

    if any(w in msg for w in ["save tax", "tax saving", "reduce tax", "save on tax"]):
        remaining_80c = max(0, 150000 - sec_80c)
        remaining_80d = max(0, 25000 - sec_80d)
        reply = f"""Here are your personalized tax-saving opportunities 💡

**Current Position:**
- Gross Income: ₹{income:,.0f}
- Current Tax Liability: ₹{liability:,.0f}

**Immediate Tax-Saving Actions:**

1. **Section 80C** (remaining: ₹{remaining_80c:,.0f})
   - Invest in PPF, ELSS, NSC, or LIC premium
   - Max limit: ₹1,50,000/year

2. **Section 80D** (remaining: ₹{remaining_80d:,.0f})
   - Buy/upgrade health insurance for self/family
   - Max limit: ₹25,000 (₹50,000 for senior citizens)

3. **HRA Exemption** — If paying rent, claim HRA deduction

4. **Section 44ADA** — If freelancer, 50% of gross receipts exempt

5. **NPS (80CCD(1B))** — Additional ₹50,000 deduction over 80C limit

*Always consult a qualified CA before filing your ITR.*"""

    elif any(w in msg for w in ["tax liability", "how much tax", "tax amount", "my tax"]):
        regime = tax_ctx.get("tax_regime", "new")
        reply = f"""**Your Estimated Tax Liability** 📊

Financial Year: 2024-25
Tax Regime: {regime.upper()}

| Item | Amount |
|------|--------|
| Gross Income | ₹{income:,.0f} |
| Total Deductions | ₹{tax_ctx.get('total_deductions', 0):,.0f} |
| Taxable Income | ₹{taxable:,.0f} |
| Tax (before cess) | ₹{tax_ctx.get('tax_before_cess', 0):,.0f} |
| Education Cess (4%) | ₹{tax_ctx.get('education_cess', 0):,.0f} |
| **Total Tax Liability** | **₹{liability:,.0f}** |
| TDS Already Paid | ₹{tax_ctx.get('tds_already_paid', 0):,.0f} |
| **Net Tax Payable** | **₹{tax_ctx.get('net_tax_payable', 0):,.0f}** |

*Effective Tax Rate: {tax_ctx.get('effective_tax_rate', 0):.1f}%*"""

    elif any(w in msg for w in ["deductible", "deduction", "which expense", "80c", "80d"]):
        reply = f"""**Your Deductible Expenses** 📋

Total Deductible Expenses Identified: **₹{deductible:,.0f}**

**Section 80C Investments:** ₹{sec_80c:,.0f} / ₹1,50,000
**Section 80D (Health Insurance):** ₹{sec_80d:,.0f} / ₹25,000

**Common Deductible Expenses Under Indian IT Act:**

| Section | Deduction | Limit |
|---------|-----------|-------|
| 80C | PPF, ELSS, LIC, NSC, Home Loan Principal | ₹1,50,000 |
| 80D | Health Insurance Premium | ₹25,000 |
| 80CCD(1B) | NPS Contribution | ₹50,000 |
| 24(b) | Home Loan Interest | ₹2,00,000 |
| 80E | Education Loan Interest | No limit |
| 80G | Charitable Donations | 50-100% |

*Note: Available deductions depend on your chosen tax regime.*"""

    elif any(w in msg for w in ["old regime", "new regime", "which regime", "better regime"]):
        reply = f"""**Old vs New Tax Regime Comparison** ⚖️

Based on your income of ₹{income:,.0f}/year:

**New Regime (Default FY 2024-25):**
- Standard deduction: ₹75,000
- No 80C/80D deductions
- Lower slab rates
- Rebate u/s 87A: Zero tax if income ≤ ₹7L

**Old Regime:**
- Standard deduction: ₹50,000
- Full 80C (₹1.5L), 80D (₹25K), HRA, LTA
- Higher slab rates but more deductions

**My Recommendation:**
{"Switch to Old Regime if your total deductions exceed ₹2.5L" if income > 1000000 else "New Regime is likely better — lower rates and simpler filing."}

*Run a detailed comparison with /ai-ca/tax-summary for both regimes.*"""

    else:
        reply = f"""Hello! I'm **AI-CA**, your AI Chartered Accountant. 🏛️

Your financial snapshot:
- 💵 Annual Income Tracked: ₹{income:,.0f}
- 💰 Estimated Tax Liability: ₹{liability:,.0f}
- 📋 Deductible Expenses: ₹{deductible:,.0f}
- 📊 Taxable Income: ₹{taxable:,.0f}

**I can help you with:**
- 🔢 Tax liability estimation (Old & New Regime)
- 💡 Tax-saving strategies (80C, 80D, NPS, HRA)
- 📊 P&L and financial statements
- 🧾 Deduction identification
- 📁 ITR preparation guidance
- 💼 Business vs personal expense separation

**Ask me things like:**
- "How much tax can I save?"
- "Which of my expenses are deductible?"
- "Compare old vs new tax regime for me"
- "Show my business expenses"
- "What is my advance tax liability?"

*Note: Add GROQ_API_KEY to .env for full AI-powered responses.*"""

    return {"reply": reply, "role": "assistant", "source": "demo"}
