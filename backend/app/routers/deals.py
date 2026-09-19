from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from ..database import get_db
from ..deps import get_current_user
from ..models import User, Transaction

router = APIRouter(prefix="/deals", tags=["deals"])

@router.get("/history")
def history(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    txns = db.query(Transaction).filter(Transaction.user_id == user.id).order_by(Transaction.id.desc()).limit(50).all()
    return [{"id": t.id, "type": t.type, "amount": t.amount, "balance_after": t.balance_after,
             "meta": t.meta or {}, "created_at": t.created_at.isoformat() if t.created_at else ""} for t in txns]
