import uuid
from datetime import datetime, timezone
from typing import List, Optional, Dict
from models.schemas import Transaction, Budget, Goal, TransactionCategory, TransactionType


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
        self._seed_data()

    def _seed_data(self):
        now = _now()
        seed_transactions = [
            Transaction(id=str(uuid.uuid4()), title="Monthly Salary", amount=75000, type=TransactionType.INCOME, category=TransactionCategory.INCOME, date=datetime(now.year, now.month, 1)),
            Transaction(id=str(uuid.uuid4()), title="Freelance Project", amount=15000, type=TransactionType.INCOME, category=TransactionCategory.INCOME, date=datetime(now.year, now.month, 5)),
            Transaction(id=str(uuid.uuid4()), title="Grocery Shopping", amount=4500, type=TransactionType.EXPENSE, category=TransactionCategory.FOOD, date=datetime(now.year, now.month, 3)),
            Transaction(id=str(uuid.uuid4()), title="Restaurant Dinner", amount=1800, type=TransactionType.EXPENSE, category=TransactionCategory.FOOD, date=datetime(now.year, now.month, 7)),
            Transaction(id=str(uuid.uuid4()), title="Uber Rides", amount=1200, type=TransactionType.EXPENSE, category=TransactionCategory.TRANSPORT, date=datetime(now.year, now.month, 4)),
            Transaction(id=str(uuid.uuid4()), title="Amazon Shopping", amount=3500, type=TransactionType.EXPENSE, category=TransactionCategory.SHOPPING, date=datetime(now.year, now.month, 6)),
            Transaction(id=str(uuid.uuid4()), title="Netflix Subscription", amount=649, type=TransactionType.EXPENSE, category=TransactionCategory.ENTERTAINMENT, date=datetime(now.year, now.month, 1)),
            Transaction(id=str(uuid.uuid4()), title="Electricity Bill", amount=2200, type=TransactionType.EXPENSE, category=TransactionCategory.BILLS, date=datetime(now.year, now.month, 5)),
            Transaction(id=str(uuid.uuid4()), title="Internet Bill", amount=999, type=TransactionType.EXPENSE, category=TransactionCategory.BILLS, date=datetime(now.year, now.month, 5)),
            Transaction(id=str(uuid.uuid4()), title="Gym Membership", amount=1500, type=TransactionType.EXPENSE, category=TransactionCategory.HEALTH, date=datetime(now.year, now.month, 1)),
            Transaction(id=str(uuid.uuid4()), title="Online Course", amount=2999, type=TransactionType.EXPENSE, category=TransactionCategory.EDUCATION, date=datetime(now.year, now.month, 8)),
            Transaction(id=str(uuid.uuid4()), title="Mutual Fund SIP", amount=10000, type=TransactionType.EXPENSE, category=TransactionCategory.INVESTMENT, date=datetime(now.year, now.month, 3)),
            Transaction(id=str(uuid.uuid4()), title="Mobile Recharge", amount=299, type=TransactionType.EXPENSE, category=TransactionCategory.BILLS, date=datetime(now.year, now.month, 2)),
            Transaction(id=str(uuid.uuid4()), title="Coffee & Snacks", amount=800, type=TransactionType.EXPENSE, category=TransactionCategory.FOOD, date=datetime(now.year, now.month, 9)),
            Transaction(id=str(uuid.uuid4()), title="Movie Tickets", amount=600, type=TransactionType.EXPENSE, category=TransactionCategory.ENTERTAINMENT, date=datetime(now.year, now.month, 10)),
        ]
        for t in seed_transactions:
            t.created_at = _now()
            self.transactions[t.id] = t

        seed_budgets = [
            Budget(id=str(uuid.uuid4()), category=TransactionCategory.FOOD, limit=8000, month=now.month, year=now.year),
            Budget(id=str(uuid.uuid4()), category=TransactionCategory.TRANSPORT, limit=3000, month=now.month, year=now.year),
            Budget(id=str(uuid.uuid4()), category=TransactionCategory.SHOPPING, limit=5000, month=now.month, year=now.year),
            Budget(id=str(uuid.uuid4()), category=TransactionCategory.ENTERTAINMENT, limit=2000, month=now.month, year=now.year),
            Budget(id=str(uuid.uuid4()), category=TransactionCategory.BILLS, limit=5000, month=now.month, year=now.year),
        ]
        for b in seed_budgets:
            b.created_at = _now()
            self._recalculate_budget_spent(b)
            self.budgets[b.id] = b

        seed_goals = [
            Goal(id=str(uuid.uuid4()), title="Emergency Fund", target_amount=200000, current_amount=75000, description="6 months of expenses"),
            Goal(id=str(uuid.uuid4()), title="New Laptop", target_amount=80000, current_amount=35000, deadline=datetime(now.year, 12, 31), description="MacBook Pro"),
            Goal(id=str(uuid.uuid4()), title="Vacation - Goa Trip", target_amount=50000, current_amount=20000, deadline=datetime(now.year, 6, 30)),
        ]
        for g in seed_goals:
            g.created_at = _now()
            self.goals[g.id] = g

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


db = Database()
