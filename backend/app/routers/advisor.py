from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from ..database import get_db
from ..deps import get_current_user
from ..models import User, Car
from ..game.advisor import rule_tips

router = APIRouter(prefix="/advisor", tags=["advisor"])

@router.get("")
def advisor(car_id: int | None = None, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    car = None
    if car_id:
        car = db.query(Car).filter(Car.id == car_id, Car.owner_user_id == user.id).first()
    return {"tips": rule_tips(car, user)}
