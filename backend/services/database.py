import uuid
import sqlite3
import os
from contextlib import contextmanager
from datetime import datetime, timezone
from typing import List, Optional, Dict
from models.schemas import Transaction, Budget, Goal, TransactionCategory, TransactionType
from models.aica_schemas import LedgerEntry, JournalEntry, TaxpayerProfile

DB_FILE = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "financeai.db"))

@contextmanager
def get_db_conn():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()

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

def parse_dt(val: Optional[str]) -> Optional[datetime]:
    if not val:
        return None
    try:
        return datetime.fromisoformat(val)
    except Exception:
        return None

class Database:
    def __init__(self):
        self.init_db()

    def init_db(self):
        with get_db_conn() as conn:
            conn.execute("PRAGMA foreign_keys = ON;")
            # Create users table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id TEXT PRIMARY KEY,
                    username TEXT UNIQUE NOT NULL,
                    password_hash TEXT NOT NULL,
                    created_at TEXT NOT NULL
                )
            """)
            # Create sessions table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS sessions (
                    token TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    expires_at TEXT NOT NULL,
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
                )
            """)
            # Create transactions table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS transactions (
                    id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    title TEXT NOT NULL,
                    amount REAL NOT NULL,
                    type TEXT NOT NULL,
                    category TEXT NOT NULL,
                    date TEXT NOT NULL,
                    notes TEXT,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
                )
            """)
            # Create budgets table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS budgets (
                    id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    category TEXT NOT NULL,
                    limit_val REAL NOT NULL,
                    spent REAL NOT NULL DEFAULT 0.0,
                    month INTEGER NOT NULL,
                    year INTEGER NOT NULL,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
                )
            """)
            # Create goals table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS goals (
                    id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    title TEXT NOT NULL,
                    target_amount REAL NOT NULL,
                    current_amount REAL NOT NULL DEFAULT 0.0,
                    deadline TEXT,
                    description TEXT,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
                )
            """)
            # Create ledger_entries table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS ledger_entries (
                    id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    date TEXT NOT NULL,
                    description TEXT NOT NULL,
                    account TEXT NOT NULL,
                    debit REAL NOT NULL DEFAULT 0.0,
                    credit REAL NOT NULL DEFAULT 0.0,
                    balance REAL NOT NULL DEFAULT 0.0,
                    transaction_id TEXT,
                    aica_category TEXT NOT NULL,
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
                )
            """)
            # Create journal_entries table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS journal_entries (
                    id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    date TEXT NOT NULL,
                    narration TEXT NOT NULL,
                    debit_account TEXT NOT NULL,
                    credit_account TEXT NOT NULL,
                    amount REAL NOT NULL,
                    transaction_id TEXT,
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
                )
            """)
            # Create taxpayer_profiles table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS taxpayer_profiles (
                    user_id TEXT PRIMARY KEY,
                    first_name TEXT DEFAULT '',
                    middle_name TEXT DEFAULT '',
                    last_name TEXT DEFAULT '',
                    pan TEXT DEFAULT '',
                    aadhaar_no TEXT DEFAULT '',
                    dob TEXT DEFAULT '',
                    email TEXT DEFAULT '',
                    mobile TEXT DEFAULT '',
                    address_flat TEXT DEFAULT '',
                    address_premises TEXT DEFAULT '',
                    address_road TEXT DEFAULT '',
                    address_area TEXT DEFAULT '',
                    address_city TEXT DEFAULT '',
                    address_state TEXT DEFAULT '',
                    address_pin TEXT DEFAULT '',
                    employer_type TEXT DEFAULT 'OTHERS',
                    bank_name TEXT DEFAULT '',
                    bank_account_no TEXT DEFAULT '',
                    bank_ifsc TEXT DEFAULT '',
                    bank_refund_eligible INTEGER DEFAULT 0,
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
                )
            """)

    def _recalculate_budget_spent(self, conn, user_id: str, category: str, month: int, year: int) -> float:
        month_str = f"{month:02d}"
        cursor = conn.execute("""
            SELECT SUM(amount) FROM transactions
            WHERE user_id = ? AND category = ? AND type = 'expense'
              AND strftime('%m', date) = ? AND strftime('%Y', date) = ?
        """, (user_id, category, month_str, str(year)))
        row = cursor.fetchone()
        return row[0] if row[0] is not None else 0.0

    # ── Users & Sessions ──────────────────────────────────────────────────────

    def create_user(self, username: str, password_hash: str) -> dict:
        user_id = str(uuid.uuid4())
        created_at = _now().isoformat()
        with get_db_conn() as conn:
            conn.execute("""
                INSERT INTO users (id, username, password_hash, created_at)
                VALUES (?, ?, ?, ?)
            """, (user_id, username, password_hash, created_at))
        return {"id": user_id, "username": username}

    def get_user_by_username(self, username: str) -> Optional[dict]:
        with get_db_conn() as conn:
            cursor = conn.execute("SELECT * FROM users WHERE username = ?", (username,))
            row = cursor.fetchone()
            return dict(row) if row else None

    def create_session(self, user_id: str, token: str, expires_at: datetime) -> None:
        with get_db_conn() as conn:
            conn.execute("""
                INSERT INTO sessions (token, user_id, expires_at)
                VALUES (?, ?, ?)
            """, (token, user_id, expires_at.isoformat()))

    def get_user_id_by_token(self, token: str) -> Optional[str]:
        with get_db_conn() as conn:
            cursor = conn.execute("""
                SELECT user_id, expires_at FROM sessions WHERE token = ?
            """, (token,))
            row = cursor.fetchone()
            if row:
                expires_at = datetime.fromisoformat(row["expires_at"])
                if expires_at > _now():
                    return row["user_id"]
                else:
                    conn.execute("DELETE FROM sessions WHERE token = ?", (token,))
        return None

    def delete_session(self, token: str) -> None:
        with get_db_conn() as conn:
            conn.execute("DELETE FROM sessions WHERE token = ?", (token,))

    # ── Transactions ──────────────────────────────────────────────────────────

    def get_all_transactions(self, user_id: str) -> List[Transaction]:
        with get_db_conn() as conn:
            cursor = conn.execute("""
                SELECT * FROM transactions WHERE user_id = ?
                ORDER BY datetime(date) DESC
            """, (user_id,))
            rows = cursor.fetchall()
            txs = []
            for r in rows:
                txs.append(Transaction(
                    id=r["id"],
                    title=r["title"],
                    amount=r["amount"],
                    type=r["type"],
                    category=r["category"],
                    date=datetime.fromisoformat(r["date"]),
                    notes=r["notes"],
                    created_at=datetime.fromisoformat(r["created_at"])
                ))
            return txs

    def get_transaction(self, user_id: str, id: str) -> Optional[Transaction]:
        with get_db_conn() as conn:
            cursor = conn.execute("SELECT * FROM transactions WHERE user_id = ? AND id = ?", (user_id, id))
            r = cursor.fetchone()
            if r:
                return Transaction(
                    id=r["id"],
                    title=r["title"],
                    amount=r["amount"],
                    type=r["type"],
                    category=r["category"],
                    date=datetime.fromisoformat(r["date"]),
                    notes=r["notes"],
                    created_at=datetime.fromisoformat(r["created_at"])
                )
        return None

    def create_transaction(self, user_id: str, transaction: Transaction) -> Transaction:
        transaction.id = str(uuid.uuid4())
        transaction.created_at = _now()
        transaction.date = _normalize_dt(transaction.date) or _now()
        with get_db_conn() as conn:
            conn.execute("""
                INSERT INTO transactions (id, user_id, title, amount, type, category, date, notes, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                transaction.id,
                user_id,
                transaction.title,
                transaction.amount,
                transaction.type,
                transaction.category,
                transaction.date.isoformat(),
                transaction.notes,
                transaction.created_at.isoformat()
            ))
        return transaction

    def delete_transaction(self, user_id: str, id: str) -> bool:
        with get_db_conn() as conn:
            cursor = conn.execute("DELETE FROM transactions WHERE user_id = ? AND id = ?", (user_id, id))
            return cursor.rowcount > 0

    # ── Budgets ───────────────────────────────────────────────────────────────

    def get_all_budgets(self, user_id: str) -> List[Budget]:
        with get_db_conn() as conn:
            cursor = conn.execute("SELECT * FROM budgets WHERE user_id = ?", (user_id,))
            rows = cursor.fetchall()
            budgets = []
            for r in rows:
                spent = self._recalculate_budget_spent(conn, user_id, r["category"], r["month"], r["year"])
                budgets.append(Budget(
                    id=r["id"],
                    category=r["category"],
                    limit=r["limit_val"],
                    spent=spent,
                    month=r["month"],
                    year=r["year"],
                    created_at=datetime.fromisoformat(r["created_at"])
                ))
            return budgets

    def create_budget(self, user_id: str, budget: Budget) -> Budget:
        budget.id = str(uuid.uuid4())
        budget.created_at = _now()
        with get_db_conn() as conn:
            cursor = conn.execute("""
                SELECT id FROM budgets WHERE user_id = ? AND category = ? AND month = ? AND year = ?
            """, (user_id, budget.category, budget.month, budget.year))
            existing = cursor.fetchone()
            if existing:
                conn.execute("""
                    UPDATE budgets SET limit_val = ? WHERE id = ?
                """, (budget.limit, existing["id"]))
                budget.id = existing["id"]
            else:
                conn.execute("""
                    INSERT INTO budgets (id, user_id, category, limit_val, spent, month, year, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    budget.id,
                    user_id,
                    budget.category,
                    budget.limit,
                    0.0,
                    budget.month,
                    budget.year,
                    budget.created_at.isoformat()
                ))
            spent = self._recalculate_budget_spent(conn, user_id, budget.category, budget.month, budget.year)
            budget.spent = spent
        return budget

    def update_budget(self, user_id: str, id: str, limit: float) -> Optional[Budget]:
        with get_db_conn() as conn:
            conn.execute("UPDATE budgets SET limit_val = ? WHERE user_id = ? AND id = ?", (limit, user_id, id))
            cursor = conn.execute("SELECT * FROM budgets WHERE user_id = ? AND id = ?", (user_id, id))
            r = cursor.fetchone()
            if r:
                spent = self._recalculate_budget_spent(conn, user_id, r["category"], r["month"], r["year"])
                return Budget(
                    id=r["id"],
                    category=r["category"],
                    limit=r["limit_val"],
                    spent=spent,
                    month=r["month"],
                    year=r["year"],
                    created_at=datetime.fromisoformat(r["created_at"])
                )
        return None

    def delete_budget(self, user_id: str, id: str) -> bool:
        with get_db_conn() as conn:
            cursor = conn.execute("DELETE FROM budgets WHERE user_id = ? AND id = ?", (user_id, id))
            return cursor.rowcount > 0

    # ── Goals ─────────────────────────────────────────────────────────────────

    def get_all_goals(self, user_id: str) -> List[Goal]:
        with get_db_conn() as conn:
            cursor = conn.execute("""
                SELECT * FROM goals WHERE user_id = ?
                ORDER BY datetime(created_at) DESC
            """, (user_id,))
            rows = cursor.fetchall()
            goals = []
            for r in rows:
                goals.append(Goal(
                    id=r["id"],
                    title=r["title"],
                    target_amount=r["target_amount"],
                    current_amount=r["current_amount"],
                    deadline=parse_dt(r["deadline"]),
                    description=r["description"],
                    created_at=parse_dt(r["created_at"])
                ))
            return goals

    def create_goal(self, user_id: str, goal: Goal) -> Goal:
        goal.id = str(uuid.uuid4())
        goal.created_at = _now()
        if goal.deadline:
            goal.deadline = _normalize_dt(goal.deadline)
        with get_db_conn() as conn:
            conn.execute("""
                INSERT INTO goals (id, user_id, title, target_amount, current_amount, deadline, description, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                goal.id,
                user_id,
                goal.title,
                goal.target_amount,
                goal.current_amount,
                goal.deadline.isoformat() if goal.deadline else None,
                goal.description,
                goal.created_at.isoformat()
            ))
        return goal

    def update_goal(self, user_id: str, id: str, current_amount: float) -> Optional[Goal]:
        with get_db_conn() as conn:
            conn.execute("UPDATE goals SET current_amount = ? WHERE user_id = ? AND id = ?", (current_amount, user_id, id))
            cursor = conn.execute("SELECT * FROM goals WHERE user_id = ? AND id = ?", (user_id, id))
            r = cursor.fetchone()
            if r:
                return Goal(
                    id=r["id"],
                    title=r["title"],
                    target_amount=r["target_amount"],
                    current_amount=r["current_amount"],
                    deadline=parse_dt(r["deadline"]),
                    description=r["description"],
                    created_at=parse_dt(r["created_at"])
                )
        return None

    def delete_goal(self, user_id: str, id: str) -> bool:
        with get_db_conn() as conn:
            cursor = conn.execute("DELETE FROM goals WHERE user_id = ? AND id = ?", (user_id, id))
            return cursor.rowcount > 0

    # ── Analytics ─────────────────────────────────────────────────────────────

    def get_financial_summary(self, user_id: str) -> dict:
        now = _now()
        with get_db_conn() as conn:
            cursor = conn.execute("SELECT * FROM transactions WHERE user_id = ?", (user_id,))
            rows = cursor.fetchall()
            
            month_transactions = []
            for r in rows:
                t_date = parse_dt(r["date"])
                if t_date and t_date.month == now.month and t_date.year == now.year:
                    month_transactions.append(Transaction(
                        id=r["id"],
                        title=r["title"],
                        amount=r["amount"],
                        type=r["type"],
                        category=r["category"],
                        date=t_date,
                        notes=r["notes"],
                        created_at=parse_dt(r["created_at"])
                    ))

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

    def get_monthly_trends(self, user_id: str) -> List[dict]:
        from collections import defaultdict
        monthly: Dict[str, dict] = defaultdict(lambda: {"income": 0.0, "expense": 0.0})
        with get_db_conn() as conn:
            cursor = conn.execute("SELECT * FROM transactions WHERE user_id = ?", (user_id,))
            rows = cursor.fetchall()
            for r in rows:
                t_date = parse_dt(r["date"])
                if t_date:
                    key = f"{t_date.year}-{t_date.month:02d}"
                    if r["type"] == TransactionType.INCOME:
                        monthly[key]["income"] += r["amount"]
                    else:
                        monthly[key]["expense"] += r["amount"]
            return [{"month": k, **v} for k, v in sorted(monthly.items())]

    # ── AI_CA Additions ───────────────────────────────────────────────────────

    def get_all_ledger_entries(self, user_id: str) -> List[LedgerEntry]:
        with get_db_conn() as conn:
            cursor = conn.execute("SELECT * FROM ledger_entries WHERE user_id = ?", (user_id,))
            rows = cursor.fetchall()
            return [LedgerEntry(
                id=r["id"],
                date=datetime.fromisoformat(r["date"]),
                description=r["description"],
                account=r["account"],
                debit=r["debit"],
                credit=r["credit"],
                balance=r["balance"],
                transaction_id=r["transaction_id"],
                aica_category=r["aica_category"]
            ) for r in rows]

    def save_ledger_entry(self, user_id: str, entry: LedgerEntry) -> LedgerEntry:
        if not entry.id:
            entry.id = str(uuid.uuid4())
        with get_db_conn() as conn:
            conn.execute("""
                INSERT OR REPLACE INTO ledger_entries (id, user_id, date, description, account, debit, credit, balance, transaction_id, aica_category)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                entry.id,
                user_id,
                entry.date.isoformat(),
                entry.description,
                entry.account,
                entry.debit,
                entry.credit,
                entry.balance,
                entry.transaction_id,
                entry.aica_category
            ))
        return entry

    def clear_ledger_entries(self, user_id: str):
        with get_db_conn() as conn:
            conn.execute("DELETE FROM ledger_entries WHERE user_id = ?", (user_id,))

    def get_all_journal_entries(self, user_id: str) -> List[JournalEntry]:
        with get_db_conn() as conn:
            cursor = conn.execute("SELECT * FROM journal_entries WHERE user_id = ?", (user_id,))
            rows = cursor.fetchall()
            return [JournalEntry(
                id=r["id"],
                date=datetime.fromisoformat(r["date"]),
                narration=r["narration"],
                debit_account=r["debit_account"],
                credit_account=r["credit_account"],
                amount=r["amount"],
                transaction_id=r["transaction_id"]
            ) for r in rows]

    def save_journal_entry(self, user_id: str, entry: JournalEntry) -> JournalEntry:
        if not entry.id:
            entry.id = str(uuid.uuid4())
        with get_db_conn() as conn:
            conn.execute("""
                INSERT OR REPLACE INTO journal_entries (id, user_id, date, narration, debit_account, credit_account, amount, transaction_id)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                entry.id,
                user_id,
                entry.date.isoformat(),
                entry.narration,
                entry.debit_account,
                entry.credit_account,
                entry.amount,
                entry.transaction_id
            ))
        return entry

    def clear_journal_entries(self, user_id: str):
        with get_db_conn() as conn:
            conn.execute("DELETE FROM journal_entries WHERE user_id = ?", (user_id,))

    def get_taxpayer_profile(self, user_id: str) -> dict:
        with get_db_conn() as conn:
            cursor = conn.execute("SELECT * FROM taxpayer_profiles WHERE user_id = ?", (user_id,))
            row = cursor.fetchone()
            if row:
                d = dict(row)
                d.pop("user_id", None)
                d["bank_refund_eligible"] = bool(d["bank_refund_eligible"])
                return d
            else:
                profile_dict = TaxpayerProfile().model_dump()
                self.save_taxpayer_profile(user_id, profile_dict)
                return profile_dict

    def save_taxpayer_profile(self, user_id: str, profile: dict) -> dict:
        with get_db_conn() as conn:
            conn.execute("""
                INSERT OR REPLACE INTO taxpayer_profiles (
                    user_id, first_name, middle_name, last_name, pan, aadhaar_no, dob, email, mobile,
                    address_flat, address_premises, address_road, address_area, address_city,
                    address_state, address_pin, employer_type, bank_name, bank_account_no, bank_ifsc, bank_refund_eligible
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                user_id,
                profile.get("first_name", ""),
                profile.get("middle_name", ""),
                profile.get("last_name", ""),
                profile.get("pan", ""),
                profile.get("aadhaar_no", ""),
                profile.get("dob", ""),
                profile.get("email", ""),
                profile.get("mobile", ""),
                profile.get("address_flat", ""),
                profile.get("address_premises", ""),
                profile.get("address_road", ""),
                profile.get("address_area", ""),
                profile.get("address_city", ""),
                profile.get("address_state", ""),
                profile.get("address_pin", ""),
                profile.get("employer_type", "OTHERS"),
                profile.get("bank_name", ""),
                profile.get("bank_account_no", ""),
                profile.get("bank_ifsc", ""),
                1 if profile.get("bank_refund_eligible", False) else 0
            ))
        return profile

db = Database()
