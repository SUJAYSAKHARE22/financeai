from fastapi import APIRouter
from services.database import db

router = APIRouter()


@router.get("/summary")
def get_dashboard_summary():
    summary = db.get_financial_summary()
    budgets = db.get_all_budgets()
    goals = db.get_all_goals()
    recent_transactions = db.get_all_transactions()[:5]

    budget_health = []
    for b in budgets:
        pct = (b.spent / b.limit * 100) if b.limit > 0 else 0.0
        budget_health.append({
            "category": b.category,
            "limit": b.limit,
            "spent": b.spent,
            "remaining": max(b.limit - b.spent, 0),
            "percentage": round(pct, 1),
            "status": "danger" if pct >= 90 else "warning" if pct >= 70 else "good",
        })

    goal_progress = []
    for g in goals:
        pct = (g.current_amount / g.target_amount * 100) if g.target_amount > 0 else 0.0
        goal_progress.append({
            "id": g.id,
            "title": g.title,
            "target": g.target_amount,
            "current": g.current_amount,
            "remaining": max(g.target_amount - g.current_amount, 0),
            "percentage": round(pct, 1),
            "completed": pct >= 100,
        })

    alerts = []
    for b in budgets:
        pct = (b.spent / b.limit * 100) if b.limit > 0 else 0.0
        if pct >= 100:
            alerts.append({"type": "danger", "message": f"Budget for {b.category} is exceeded ({pct:.0f}% used)"})
        elif pct >= 90:
            alerts.append({"type": "danger", "message": f"Budget for {b.category} is almost exhausted ({pct:.0f}% used)"})
        elif pct >= 75:
            alerts.append({"type": "warning", "message": f"Budget for {b.category} is at {pct:.0f}%"})

    return {
        "summary": summary,
        "budget_health": budget_health,
        "goal_progress": goal_progress,
        "recent_transactions": [t.model_dump() for t in recent_transactions],
        "alerts": alerts,
    }
