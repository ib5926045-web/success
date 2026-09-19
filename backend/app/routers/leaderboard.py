from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from ..database import get_db
from ..deps import get_current_user
from ..models import User, Car
from ..game.pricing import estimated_value

router = APIRouter(prefix="/leaderboard", tags=["leaderboard"])

@router.get("")
def board(sort: str = "capital", user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    users = db.query(User).filter(User.rating_opt_out == False).all()  # noqa
    rows = []
    for u in users:
        garage = db.query(Car).filter(Car.owner_user_id == u.id, Car.status.in_(["OWNED", "LISTED"])).all()
        gv = sum(estimated_value(c) for c in garage)
        rows.append({"id": u.id, "name": u.first_name or u.username or f"Игрок {u.id}",
                     "level": u.level, "capital": u.balance + gv, "profit": u.total_profit,
                     "reputation": u.reputation, "deals": u.deals_count})
    key = {"capital": "capital", "profit": "profit", "reputation": "reputation", "deals": "deals"}.get(sort, "capital")
    rows.sort(key=lambda r: r[key], reverse=True)
    out = []
    my_rank = None
    for i, r in enumerate(rows[:50], 1):
        is_me = r["id"] == user.id
        if is_me:
            my_rank = i
        out.append({"rank": i, "name": r["name"], "level": r["level"], "capital": r["capital"],
                    "profit": r["profit"], "reputation": r["reputation"], "is_me": is_me})
    return {"rows": out, "my_rank": my_rank, "sort": key}
