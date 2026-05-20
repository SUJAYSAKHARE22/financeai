from fastapi import APIRouter, HTTPException, Query
from typing import List
from models.schemas import Goal, GoalCreate
from services.database import db

router = APIRouter()


@router.get("/", response_model=List[Goal])
def get_goals():
    return db.get_all_goals()


@router.post("/", response_model=Goal)
def create_goal(data: GoalCreate):
    goal = Goal(**data.model_dump())
    return db.create_goal(goal)


@router.put("/{goal_id}/progress", response_model=Goal)
def update_goal_progress(goal_id: str, current_amount: float = Query(..., ge=0)):
    goal = db.update_goal(goal_id, current_amount)
    if not goal:
        raise HTTPException(status_code=404, detail="Goal not found")
    return goal


@router.delete("/{goal_id}")
def delete_goal(goal_id: str):
    if not db.delete_goal(goal_id):
        raise HTTPException(status_code=404, detail="Goal not found")
    return {"message": "Goal deleted"}
