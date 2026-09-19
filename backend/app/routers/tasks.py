from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..database import get_db
from ..deps import get_current_user
from ..models import User, DailyTask, Transaction
from ..game.pricing import add_xp

router = APIRouter(prefix="/tasks", tags=["tasks"])

@router.get("")
def list_tasks(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    tasks = db.query(DailyTask).filter(DailyTask.user_id == user.id, DailyTask.game_day == user.current_game_day).all()
    return [{"id": t.id, "task_type": t.task_type, "title": t.title, "target_value": t.target_value,
             "progress_value": t.progress_value, "reward_type": t.reward_type, "reward_value": t.reward_value,
             "status": t.status} for t in tasks]

@router.post("/{task_id}/claim")
def claim(task_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    t = db.query(DailyTask).filter(DailyTask.id == task_id, DailyTask.user_id == user.id).first()
    if not t:
        raise HTTPException(404, "Задание не найдено")
    if t.status == "CLAIMED":
        raise HTTPException(400, "Награда уже получена")
    if t.progress_value < t.target_value:
        raise HTTPException(400, "Задание ещё не выполнено")
    t.status = "CLAIMED"
    if t.reward_type == "xp":
        add_xp(user, t.reward_value)
    else:
        user.balance += t.reward_value
        db.add(Transaction(user_id=user.id, type="REWARD", amount=t.reward_value, balance_after=user.balance,
                           meta={"task": t.task_type}))
    db.commit()
    return {"ok": True, "balance": user.balance, "experience": user.experience, "level": user.level}
