from fastapi import APIRouter, HTTPException, Query, Depends
from typing import List
from models.schemas import Goal, GoalCreate
from services.database import db
from services.auth import get_current_user_id

router = APIRouter()


@router.get("/", response_model=List[Goal])
def get_goals(user_id: str = Depends(get_current_user_id)):
    return db.get_all_goals(user_id)


@router.post("/", response_model=Goal)
def create_goal(data: GoalCreate, user_id: str = Depends(get_current_user_id)):
    goal = Goal(**data.model_dump())
    return db.create_goal(user_id, goal)


@router.put("/{goal_id}/progress", response_model=Goal)
def update_goal_progress(goal_id: str, current_amount: float = Query(..., ge=0), user_id: str = Depends(get_current_user_id)):
    goal = db.update_goal(user_id, goal_id, current_amount)
    if not goal:
        raise HTTPException(status_code=404, detail="Goal not found")
    return goal


@router.delete("/{goal_id}")
def delete_goal(goal_id: str, user_id: str = Depends(get_current_user_id)):
    if not db.delete_goal(user_id, goal_id):
        raise HTTPException(status_code=404, detail="Goal not found")
    return {"message": "Goal deleted"}
