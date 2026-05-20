from fastapi import APIRouter, HTTPException, Query
from typing import List
from models.schemas import Budget, BudgetCreate
from services.database import db

router = APIRouter()


@router.get("/", response_model=List[Budget])
def get_budgets():
    return db.get_all_budgets()


@router.post("/", response_model=Budget)
def create_budget(data: BudgetCreate):
    budget = Budget(**data.model_dump())
    return db.create_budget(budget)


@router.put("/{budget_id}", response_model=Budget)
def update_budget(budget_id: str, limit: float = Query(..., gt=0)):
    budget = db.update_budget(budget_id, limit)
    if not budget:
        raise HTTPException(status_code=404, detail="Budget not found")
    return budget


@router.delete("/{budget_id}")
def delete_budget(budget_id: str):
    if not db.delete_budget(budget_id):
        raise HTTPException(status_code=404, detail="Budget not found")
    return {"message": "Budget deleted"}
