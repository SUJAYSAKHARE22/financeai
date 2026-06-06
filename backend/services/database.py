import uuid
from datetime import datetime, timezone
from typing import List, Optional, Dict
from models.schemas import Transaction, Budget, Goal, TransactionCategory, TransactionType
from models.aica_schemas import LedgerEntry, JournalEntry, TaxpayerProfile


def _now() -> datetime:
    """Always return UTC naive datetime for consistency."""
    return datetime.utcnow()


def _normalize_dt(dt: Optional[datetime]) -> Optional[datetime]:
    """Strip timezone info to ensure all datetimes are offset-naive (UTC)."""
    if dt is None:
        return None
    if dt.tzinfo is not None:
        dt = dt.astimezone(timezone.utc).replace(tzinfo=None)
    return dt


class Database:
    def __init__(self):
        self.transactions: Dict[str, Transaction] = {}
        self.budgets: Dict[str, Budget] = {}
        self.goals: Dict[str, Goal] = {}
        self.ledger_entries: Dict[str, LedgerEntry] = {}
        self.journal_entries: Dict[str, JournalEntry] = {}
        self.tax_rules: Dict[str, dict] = {}
        self.tax_reports: Dict[str, dict] = {}
        self.taxpayer_profile: dict = {}
        self._seed_data()

    def _seed_data(self):
        # Database starts completely blank. No pre-seeded transactions, budgets, or goals.
        self.taxpayer_profile = TaxpayerProfile().model_dump()

    def _recalculate_budget_spent(self, budget: Budget):
        spent = 0.0
        for t in self.transactions.values():
            t_date = _normalize_dt(t.date)
            if (t.category == budget.category
                    and t.type == TransactionType.EXPENSE
                    and t_date is not None
                    and t_date.month == budget.month
                    and t_date.year == budget.year):
                spent += t.amount
        budget.spent = spent

    # ── Transactions ──────────────────────────────────────────────────────────

    def get_all_transactions(self) -> List[Transaction]:
        def _sort_key(t: Transaction):
            return _normalize_dt(t.date) or datetime.min

        return sorted(self.transactions.values(), key=_sort_key, reverse=True)

    def get_transaction(self, id: str) -> Optional[Transaction]:
        return self.transactions.get(id)

    def create_transaction(self, transaction: Transaction) -> Transaction:
        transaction.id = str(uuid.uuid4())
        transaction.created_at = _now()
        # Normalize incoming date to avoid future comparison errors
        transaction.date = _normalize_dt(transaction.date) or _now()
        self.transactions[transaction.id] = transaction
        for budget in self.budgets.values():
            if budget.category == transaction.category:
                self._recalculate_budget_spent(budget)
        return transaction

    def delete_transaction(self, id: str) -> bool:
        if id in self.transactions:
            del self.transactions[id]
            # Recalculate all budgets after deletion
            for budget in self.budgets.values():
                self._recalculate_budget_spent(budget)
            return True
        return False

    # ── Budgets ───────────────────────────────────────────────────────────────

    def get_all_budgets(self) -> List[Budget]:
        return list(self.budgets.values())

    def create_budget(self, budget: Budget) -> Budget:
        budget.id = str(uuid.uuid4())
        budget.created_at = _now()
        self._recalculate_budget_spent(budget)
        self.budgets[budget.id] = budget
        return budget

    def update_budget(self, id: str, limit: float) -> Optional[Budget]:
        if id in self.budgets:
            self.budgets[id].limit = limit
            return self.budgets[id]
        return None

    def delete_budget(self, id: str) -> bool:
        if id in self.budgets:
            del self.budgets[id]
            return True
        return False

    # ── Goals ─────────────────────────────────────────────────────────────────

    def get_all_goals(self) -> List[Goal]:
        def _sort_key(g: Goal):
            return _normalize_dt(g.created_at) or datetime.min

        return sorted(self.goals.values(), key=_sort_key, reverse=True)

    def create_goal(self, goal: Goal) -> Goal:
        goal.id = str(uuid.uuid4())
        goal.created_at = _now()
        if goal.deadline:
            goal.deadline = _normalize_dt(goal.deadline)
        self.goals[goal.id] = goal
        return goal

    def update_goal(self, id: str, current_amount: float) -> Optional[Goal]:
        if id in self.goals:
            self.goals[id].current_amount = current_amount
            return self.goals[id]
        return None

    def delete_goal(self, id: str) -> bool:
        if id in self.goals:
            del self.goals[id]
            return True
        return False

    # ── Analytics ─────────────────────────────────────────────────────────────

    def get_financial_summary(self) -> dict:
        now = _now()
        month_transactions = []
        for t in self.transactions.values():
            t_date = _normalize_dt(t.date)
            if t_date and t_date.month == now.month and t_date.year == now.year:
                month_transactions.append(t)

        total_income = sum(t.amount for t in month_transactions if t.type == TransactionType.INCOME)
        total_expense = sum(t.amount for t in month_transactions if t.type == TransactionType.EXPENSE)
        savings = total_income - total_expense

        category_spending: Dict[str, float] = {}
        for t in month_transactions:
            if t.type == TransactionType.EXPENSE:
                key = t.category.value if hasattr(t.category, 'value') else str(t.category)
                category_spending[key] = category_spending.get(key, 0.0) + t.amount

        return {
            "total_income": total_income,
            "total_expense": total_expense,
            "savings": savings,
            "savings_rate": round((savings / total_income * 100), 2) if total_income > 0 else 0.0,
            "category_spending": category_spending,
            "transaction_count": len(month_transactions),
        }

    def get_monthly_trends(self) -> List[dict]:
        from collections import defaultdict
        monthly: Dict[str, dict] = defaultdict(lambda: {"income": 0.0, "expense": 0.0})
        for t in self.transactions.values():
            t_date = _normalize_dt(t.date)
            if t_date:
                key = f"{t_date.year}-{t_date.month:02d}"
                if t.type == TransactionType.INCOME:
                    monthly[key]["income"] += t.amount
                else:
                    monthly[key]["expense"] += t.amount
        return [{"month": k, **v} for k, v in sorted(monthly.items())]

    # ── AI_CA Additions ───────────────────────────────────────────────────────
    def get_all_ledger_entries(self) -> List[LedgerEntry]:
        return list(self.ledger_entries.values())

    def save_ledger_entry(self, entry: LedgerEntry) -> LedgerEntry:
        if not entry.id:
            entry.id = str(uuid.uuid4())
        self.ledger_entries[entry.id] = entry
        return entry

    def get_all_journal_entries(self) -> List[JournalEntry]:
        return list(self.journal_entries.values())

    def save_journal_entry(self, entry: JournalEntry) -> JournalEntry:
        if not entry.id:
            entry.id = str(uuid.uuid4())
        self.journal_entries[entry.id] = entry
        return entry

    def get_taxpayer_profile(self) -> dict:
        if not self.taxpayer_profile:
            self.taxpayer_profile = TaxpayerProfile().model_dump()
        return self.taxpayer_profile

    def save_taxpayer_profile(self, profile: dict) -> dict:
        self.taxpayer_profile = profile
        return self.taxpayer_profile


db = Database()
