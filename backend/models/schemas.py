from pydantic import BaseModel, field_validator
from typing import Optional, List
from datetime import datetime, timezone
from enum import Enum


def _strip_tz(v) -> Optional[datetime]:
    if v is None:
        return None
    if isinstance(v, str):
        # Parse ISO string first, then strip tz
        try:
            v = datetime.fromisoformat(v.replace("Z", "+00:00"))
        except ValueError:
            return None
    if isinstance(v, datetime):
        if v.tzinfo is not None:
            return v.astimezone(timezone.utc).replace(tzinfo=None)
        return v
    return None


class TransactionCategory(str, Enum):
    FOOD = "Food & Dining"
    TRANSPORT = "Transportation"
    SHOPPING = "Shopping"
    ENTERTAINMENT = "Entertainment"
    BILLS = "Bills & Utilities"
    HEALTH = "Health & Medical"
    EDUCATION = "Education"
    TRAVEL = "Travel"
    INCOME = "Income"
    INVESTMENT = "Investment"
    OTHER = "Other"


class TransactionType(str, Enum):
    INCOME = "income"
    EXPENSE = "expense"


class Transaction(BaseModel):
    model_config = {"use_enum_values": True}

    id: Optional[str] = None
    title: str
    amount: float
    type: TransactionType
    category: TransactionCategory
    date: datetime
    notes: Optional[str] = None
    created_at: Optional[datetime] = None

    @field_validator("date", "created_at", mode="before")
    @classmethod
    def normalize_datetime(cls, v):
        return _strip_tz(v) if v is not None else v


class Budget(BaseModel):
    model_config = {"use_enum_values": True}

    id: Optional[str] = None
    category: TransactionCategory
    limit: float
    spent: float = 0.0
    month: int
    year: int
    created_at: Optional[datetime] = None

    @field_validator("created_at", mode="before")
    @classmethod
    def normalize_datetime(cls, v):
        return _strip_tz(v) if v is not None else v


class Goal(BaseModel):
    model_config = {"use_enum_values": True}

    id: Optional[str] = None
    title: str
    target_amount: float
    current_amount: float = 0.0
    deadline: Optional[datetime] = None
    description: Optional[str] = None
    created_at: Optional[datetime] = None

    @field_validator("deadline", "created_at", mode="before")
    @classmethod
    def normalize_datetime(cls, v):
        return _strip_tz(v) if v is not None else v


class ChatMessage(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    message: str
    conversation_history: Optional[List[ChatMessage]] = []


class TransactionCreate(BaseModel):
    title: str
    amount: float
    type: TransactionType
    category: TransactionCategory
    date: datetime
    notes: Optional[str] = None

    @field_validator("date", mode="before")
    @classmethod
    def normalize_datetime(cls, v):
        return _strip_tz(v) if v is not None else v


class BudgetCreate(BaseModel):
    category: TransactionCategory
    limit: float
    month: int
    year: int


class GoalCreate(BaseModel):
    title: str
    target_amount: float
    current_amount: float = 0.0
    deadline: Optional[datetime] = None
    description: Optional[str] = None

    @field_validator("deadline", mode="before")
    @classmethod
    def normalize_datetime(cls, v):
        return _strip_tz(v) if v is not None else v