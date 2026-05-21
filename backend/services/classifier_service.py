"""
AI_CA Classifier Service
Hybrid: rule engine first, LLM fallback for low-confidence items.
"""
import os
import json
import logging
from typing import List
from models.aica_schemas import (
    ClassifiedTransaction, AICACategory, TaxFlags, ClassifyResponse
)
from services.rule_engine import classify_by_rules

logger = logging.getLogger(__name__)

CONFIDENCE_THRESHOLD = 0.70   # below this → try LLM


def _build_llm_classification_prompt(transactions: list) -> str:
    items = "\n".join(
        f"{i+1}. title='{t.title}', amount=₹{t.amount}, category='{t.category}'"
        for i, t in enumerate(transactions)
    )
    return f"""You are an Indian CA (Chartered Accountant) and tax expert.
Classify each of the following financial transactions for Indian income tax purposes.

Transactions:
{items}

For each transaction return a JSON array with objects having these exact keys:
- index: (1-based integer)
- aica_category: one of [salary, freelance_income, business_income, interest_income, capital_gains, food, fuel, travel, office_expense, rent, entertainment, investment, tax_payment, utilities, medical, loan_payment, insurance, other]
- taxable: boolean
- deductible: boolean
- gst_applicable: boolean
- tds_applicable: boolean
- business_related: boolean
- section_80c: boolean
- section_80d: boolean
- confidence: float 0.0-1.0
- notes: brief explanation string

Return ONLY the JSON array, no markdown, no explanation."""


def _parse_llm_response(text: str, transactions: list) -> dict:
    """Parse LLM JSON response safely."""
    try:
        clean = text.strip()
        if clean.startswith("```"):
            clean = clean.split("```")[1]
            if clean.startswith("json"):
                clean = clean[4:]
        items = json.loads(clean.strip())
        return {item["index"]: item for item in items}
    except Exception as e:
        logger.warning(f"LLM response parse failed: {e}")
        return {}


def _llm_classify(transactions: list) -> dict:
    """Call Groq LLM to classify low-confidence transactions. Returns index->result map."""
    api_key = os.environ.get("GROQ_API_KEY", "").strip()
    if not api_key:
        return {}

    try:
        from groq import Groq
        client = Groq(api_key=api_key)
        prompt = _build_llm_classification_prompt(transactions)
        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {"role": "system", "content": "You are an Indian CA tax expert. Always respond with valid JSON only."},
                {"role": "user", "content": prompt},
            ],
            temperature=0.1,
            max_tokens=2048,
        )
        text = response.choices[0].message.content
        return _parse_llm_response(text, transactions)
    except Exception as e:
        logger.error(f"LLM classification error: {e}")
        return {}


def classify_transactions(transactions: list, use_ai: bool = True) -> ClassifyResponse:
    """
    Main classification pipeline.
    1. Rule engine for all transactions.
    2. LLM for low-confidence ones (if use_ai=True).
    """
    results: List[ClassifiedTransaction] = []
    low_confidence_batch = []
    low_confidence_indices = []

    # ── Step 1: Rule engine pass ───────────────────────────────────────────────
    for i, t in enumerate(transactions):
        cat, flags, confidence, source = classify_by_rules(
            t.title, t.amount,
            t.category.value if hasattr(t.category, 'value') else str(t.category)
        )
        results.append(ClassifiedTransaction(
            transaction_id=t.id or str(i),
            original_title=t.title,
            original_amount=t.amount,
            original_category=t.category.value if hasattr(t.category, 'value') else str(t.category),
            aica_category=cat,
            tax_flags=flags,
            confidence=confidence,
            classification_source=source,
        ))
        if confidence < CONFIDENCE_THRESHOLD:
            low_confidence_batch.append(t)
            low_confidence_indices.append(i)

    # ── Step 2: LLM enhancement for low-confidence items ─────────────────────
    ai_classified_count = 0
    if use_ai and low_confidence_batch:
        llm_results = _llm_classify(low_confidence_batch)
        for batch_pos, orig_idx in enumerate(low_confidence_indices):
            llm = llm_results.get(batch_pos + 1)
            if llm:
                try:
                    cat = AICACategory(llm["aica_category"])
                    flags = TaxFlags(
                        taxable=llm.get("taxable", True),
                        deductible=llm.get("deductible", False),
                        gst_applicable=llm.get("gst_applicable", False),
                        tds_applicable=llm.get("tds_applicable", False),
                        business_related=llm.get("business_related", False),
                        section_80c=llm.get("section_80c", False),
                        section_80d=llm.get("section_80d", False),
                        tax_category=llm["aica_category"],
                    )
                    results[orig_idx].aica_category = cat
                    results[orig_idx].tax_flags = flags
                    results[orig_idx].confidence = llm.get("confidence", 0.75)
                    results[orig_idx].classification_source = "ai"
                    results[orig_idx].notes = llm.get("notes")
                    ai_classified_count += 1
                except Exception as e:
                    logger.warning(f"LLM result parse error for item {batch_pos}: {e}")

    rule_classified = sum(1 for r in results if r.classification_source == "rule_engine")
    return ClassifyResponse(
        classified=results,
        total=len(results),
        ai_classified=ai_classified_count,
        rule_classified=rule_classified,
    )
