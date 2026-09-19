from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import User, Transaction
from ..schemas import AuthRequest, AuthResponse, MeResponse
from ..security import validate_telegram_init_data, create_access_token
from ..config import get_settings
from ..game.texts import level_for_xp, next_level_xp
from ..game.pricing import garage_limit

router = APIRouter(prefix="/auth", tags=["auth"])
settings = get_settings()

def _me(user: User) -> MeResponse:
    lv = level_for_xp(user.experience)
    return MeResponse(
        id=user.id, telegram_id=user.telegram_id, username=user.username, first_name=user.first_name,
        photo_url=user.photo_url, balance=user.balance, reputation=user.reputation, level=user.level,
        experience=user.experience, current_game_day=user.current_game_day, rating_opt_out=user.rating_opt_out,
        streak_days=user.streak_days, total_profit=user.total_profit, deals_count=user.deals_count,
        garage_limit=garage_limit(user.level), level_name=lv["name"], next_level_xp=next_level_xp(user.experience),
        season_goal=settings.SEASON_GOAL,
    )

@router.post("/telegram", response_model=AuthResponse)
def telegram_auth(body: AuthRequest, db: Session = Depends(get_db)):
    init_data = body.initData or ""
    # dev-режим
    if settings.TELEGRAM_DEV_MODE and init_data.strip() in ("dev", "test", ""):
        tg_id, username, first_name, photo = 999001, "dev_driver", "Тестовый Водитель", None
    else:
        if not settings.TELEGRAM_BOT_TOKEN:
            raise HTTPException(500, "TELEGRAM_BOT_TOKEN не настроен")
        try:
            res = validate_telegram_init_data(init_data, settings.TELEGRAM_BOT_TOKEN)
        except ValueError as e:
            raise HTTPException(401, f"Неверная подпись Telegram: {e}")
        u = res["user"] or {}
        tg_id = int(u.get("id", 0))
        if not tg_id:
            raise HTTPException(401, "Некорректные данные Telegram")
        username = u.get("username")
        first_name = u.get("first_name")
        photo = u.get("photo_url")
    user = db.query(User).filter(User.telegram_id == tg_id).first()
    is_new = False
    if not user:
        is_new = True
        user = User(telegram_id=tg_id, username=username, first_name=first_name, photo_url=photo,
                    balance=settings.START_BALANCE)
        db.add(user)
        db.commit()
        db.refresh(user)
        db.add(Transaction(user_id=user.id, type="START_BONUS", amount=settings.START_BALANCE,
                           balance_after=user.balance, meta={"reason": "Стартовый капитал сезона"}))
        db.commit()
    else:
        # обновим профиль из Telegram
        if username:
            user.username = username
        if first_name:
            user.first_name = first_name
        if photo:
            user.photo_url = photo
        db.commit()
    token = create_access_token(user.id)
    return AuthResponse(token=token, is_new=is_new, user=_me(user))
