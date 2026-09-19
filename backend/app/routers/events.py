from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..database import get_db
from ..deps import get_current_user
from ..models import User, GameEvent

router = APIRouter(prefix="/events", tags=["events"])

@router.get("")
def list_events(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    evs = db.query(GameEvent).filter(GameEvent.user_id == user.id).order_by(GameEvent.id.desc()).limit(20).all()
    return [{"id": e.id, "event_type": e.event_type, "title": e.title, "description": e.description,
             "resolved": e.resolved, "payload": e.payload or {}} for e in evs]

@router.post("/{event_id}/resolve")
def resolve(event_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    e = db.query(GameEvent).filter(GameEvent.id == event_id, GameEvent.user_id == user.id).first()
    if not e:
        raise HTTPException(404, "Событие не найдено")
    e.resolved = True
    db.commit()
    return {"ok": True}
