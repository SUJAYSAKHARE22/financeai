from fastapi import APIRouter, HTTPException
from typing import List
from models.schemas import Transaction, TransactionCreate
from services.database import db

router = APIRouter()


@router.get("/", response_model=List[Transaction])
def get_transactions():
    return db.get_all_transactions()


@router.get("/stats/monthly")
def get_monthly_stats():
    return db.get_financial_summary()


@router.get("/stats/trends")
def get_spending_trends():
    return db.get_monthly_trends()


@router.post("/", response_model=Transaction)
def create_transaction(data: TransactionCreate):
    transaction = Transaction(**data.model_dump())
    return db.create_transaction(transaction)


@router.delete("/{transaction_id}")
def delete_transaction(transaction_id: str):
    if not db.delete_transaction(transaction_id):
        raise HTTPException(status_code=404, detail="Transaction not found")
    return {"message": "Transaction deleted"}
