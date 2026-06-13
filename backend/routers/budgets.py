from fastapi import APIRouter, HTTPException, Query, Depends
from typing import List
from models.schemas import Budget, BudgetCreate
from services.database import db
from services.auth import get_current_user_id

router = APIRouter()


@router.get("/", response_model=List[Budget])
def get_budgets(user_id: str = Depends(get_current_user_id)):
    return db.get_all_budgets(user_id)


@router.post("/", response_model=Budget)
def create_budget(data: BudgetCreate, user_id: str = Depends(get_current_user_id)):
    budget = Budget(**data.model_dump())
    return db.create_budget(user_id, budget)


@router.put("/{budget_id}", response_model=Budget)
def update_budget(budget_id: str, limit: float = Query(..., gt=0), user_id: str = Depends(get_current_user_id)):
    budget = db.update_budget(user_id, budget_id, limit)
    if not budget:
        raise HTTPException(status_code=404, detail="Budget not found")
    return budget


@router.delete("/{budget_id}")
def delete_budget(budget_id: str, user_id: str = Depends(get_current_user_id)):
    if not db.delete_budget(user_id, budget_id):
        raise HTTPException(status_code=404, detail="Budget not found")
    return {"message": "Budget deleted"}
