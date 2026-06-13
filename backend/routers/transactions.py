from fastapi import APIRouter, HTTPException, Depends
from typing import List
from models.schemas import Transaction, TransactionCreate
from services.database import db
from services.auth import get_current_user_id

router = APIRouter()


@router.get("/", response_model=List[Transaction])
def get_transactions(user_id: str = Depends(get_current_user_id)):
    return db.get_all_transactions(user_id)


@router.get("/stats/monthly")
def get_monthly_stats(user_id: str = Depends(get_current_user_id)):
    return db.get_financial_summary(user_id)


@router.get("/stats/trends")
def get_spending_trends(user_id: str = Depends(get_current_user_id)):
    return db.get_monthly_trends(user_id)


@router.post("/", response_model=Transaction)
def create_transaction(data: TransactionCreate, user_id: str = Depends(get_current_user_id)):
    transaction = Transaction(**data.model_dump())
    return db.create_transaction(user_id, transaction)


@router.delete("/{transaction_id}")
def delete_transaction(transaction_id: str, user_id: str = Depends(get_current_user_id)):
    if not db.delete_transaction(user_id, transaction_id):
        raise HTTPException(status_code=404, detail="Transaction not found")
    return {"message": "Transaction deleted"}
