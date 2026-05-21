"""
AI_CA Ledger Engine
Generates double-entry accounting ledger and journal entries from classified transactions.
"""
import uuid
from datetime import datetime
from typing import List, Dict, Tuple
from models.aica_schemas import LedgerEntry, JournalEntry, AICACategory

# ── Account mapping ────────────────────────────────────────────────────────────
# Maps aica_category -> (debit_account, credit_account)

ACCOUNT_MAP: Dict[str, Tuple[str, str]] = {
    AICACategory.SALARY:           ("Bank Account",        "Salary Income"),
    AICACategory.FREELANCE_INCOME: ("Bank Account",        "Freelance Income"),
    AICACategory.BUSINESS_INCOME:  ("Bank Account",        "Business Revenue"),
    AICACategory.INTEREST_INCOME:  ("Bank Account",        "Interest Income"),
    AICACategory.CAPITAL_GAINS:    ("Bank Account",        "Capital Gains"),
    AICACategory.FOOD:             ("Food Expense",        "Bank Account"),
    AICACategory.FUEL:             ("Fuel Expense",        "Bank Account"),
    AICACategory.TRAVEL:           ("Travel Expense",      "Bank Account"),
    AICACategory.OFFICE_EXPENSE:   ("Office Expense",      "Bank Account"),
    AICACategory.RENT:             ("Rent Expense",        "Bank Account"),
    AICACategory.ENTERTAINMENT:    ("Entertainment Expense","Bank Account"),
    AICACategory.INVESTMENT:       ("Investment Account",  "Bank Account"),
    AICACategory.TAX_PAYMENT:      ("Tax Paid",            "Bank Account"),
    AICACategory.UTILITIES:        ("Utilities Expense",   "Bank Account"),
    AICACategory.MEDICAL:          ("Medical Expense",     "Bank Account"),
    AICACategory.LOAN_PAYMENT:     ("Loan Repayment",      "Bank Account"),
    AICACategory.INSURANCE:        ("Insurance Premium",   "Bank Account"),
    AICACategory.OTHER:            ("Miscellaneous Expense","Bank Account"),
}

INCOME_CATEGORIES = {
    AICACategory.SALARY, AICACategory.FREELANCE_INCOME, AICACategory.BUSINESS_INCOME,
    AICACategory.INTEREST_INCOME, AICACategory.CAPITAL_GAINS,
}


def generate_ledger_entries(classified_transactions: list) -> List[LedgerEntry]:
    """Generate ledger entries from classified transactions."""
    entries: List[LedgerEntry] = []
    running_balance = 0.0

    for ct in sorted(classified_transactions, key=lambda x: x.original_amount, reverse=False):
        is_income = ct.aica_category in INCOME_CATEGORIES
        debit = ct.original_amount if is_income else 0.0
        credit = 0.0 if is_income else ct.original_amount
        running_balance += debit - credit

        entries.append(LedgerEntry(
            id=str(uuid.uuid4()),
            date=datetime.utcnow(),
            description=ct.original_title,
            account="Bank Account",
            debit=round(debit, 2),
            credit=round(credit, 2),
            balance=round(running_balance, 2),
            transaction_id=ct.transaction_id,
            aica_category=ct.aica_category.value if hasattr(ct.aica_category, 'value') else str(ct.aica_category),
        ))

    return entries


def generate_journal_entries(classified_transactions: list) -> List[JournalEntry]:
    """Generate double-entry journal entries."""
    entries: List[JournalEntry] = []

    for ct in classified_transactions:
        cat = ct.aica_category
        debit_acc, credit_acc = ACCOUNT_MAP.get(cat, ("Miscellaneous Expense", "Bank Account"))

        entries.append(JournalEntry(
            id=str(uuid.uuid4()),
            date=datetime.utcnow(),
            narration=f"{ct.original_title} — {cat.value if hasattr(cat, 'value') else cat}",
            debit_account=debit_acc,
            credit_account=credit_acc,
            amount=round(ct.original_amount, 2),
            transaction_id=ct.transaction_id,
        ))

    return entries


def generate_account_summary(classified_transactions: list) -> Dict[str, Dict]:
    """Summarize debits/credits per account."""
    accounts: Dict[str, Dict] = {}

    for ct in classified_transactions:
        cat = ct.aica_category
        debit_acc, credit_acc = ACCOUNT_MAP.get(cat, ("Miscellaneous Expense", "Bank Account"))
        amt = ct.original_amount

        for acc, side in [(debit_acc, "debit"), (credit_acc, "credit")]:
            if acc not in accounts:
                accounts[acc] = {"debit": 0.0, "credit": 0.0, "net": 0.0, "entries": 0}
            accounts[acc][side] += amt
            accounts[acc]["entries"] += 1

    for acc in accounts:
        accounts[acc]["net"] = round(accounts[acc]["debit"] - accounts[acc]["credit"], 2)
        accounts[acc]["debit"] = round(accounts[acc]["debit"], 2)
        accounts[acc]["credit"] = round(accounts[acc]["credit"], 2)

    return accounts
