from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from ..database import get_db
from ..deps import get_current_user
from ..models import User, Car, Listing
from ..schemas import MeResponse
from ..config import get_settings
from ..game.texts import level_for_xp, next_level_xp
from ..game.pricing import garage_limit, estimated_value

router = APIRouter(tags=["me"])
settings = get_settings()

def _me(user: User) -> MeResponse:
    return MeResponse(
        id=user.id, telegram_id=user.telegram_id, username=user.username, first_name=user.first_name,
        photo_url=user.photo_url, balance=user.balance, reputation=user.reputation, level=user.level,
        experience=user.experience, current_game_day=user.current_game_day, rating_opt_out=user.rating_opt_out,
        streak_days=user.streak_days, total_profit=user.total_profit, deals_count=user.deals_count,
        garage_limit=garage_limit(user.level), level_name=level_for_xp(user.experience)["name"],
        next_level_xp=next_level_xp(user.experience), season_goal=settings.SEASON_GOAL,
    )

@router.get("/me", response_model=MeResponse)
def me(user: User = Depends(get_current_user)):
    return _me(user)

@router.get("/me/dashboard")
def dashboard(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    garage = db.query(Car).filter(Car.owner_user_id == user.id, Car.status.in_(["OWNED", "LISTED"])).all()
    garage_value = sum(estimated_value(c) for c in garage)
    capital = user.balance + garage_value
    active_listings = db.query(Listing).filter(Listing.user_id == user.id, Listing.status == "ACTIVE").count()
    return {
        "user": _me(user),
        "capital": capital,
        "garage_value": garage_value,
        "garage_count": len(garage),
        "active_listings": active_listings,
        "season_goal": settings.SEASON_GOAL,
        "goal_progress": min(100, round(capital / settings.SEASON_GOAL * 100)),
    }
