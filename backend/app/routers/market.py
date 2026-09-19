import random
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..database import get_db
from ..deps import get_current_user
from ..models import User, Car, Transaction, GameEvent, DailyTask
from ..schemas import MarketResponse, MarketCarCard
from ..game.market import generate_market_cars
from ..game.pricing import liquidity_label, risk_hint
from ..game.texts import HIDDEN_DEFECTS, DAILY_TASK_TEMPLATES, RANDOM_EVENTS

router = APIRouter(prefix="/market", tags=["market"])
REFRESH_COST = 50

def _card(c: Car) -> MarketCarCard:
    label = HIDDEN_DEFECTS.get((c.visible_defects or [None])[0], {}).get("label", "") if c.visible_defects else ""
    short = c.description[:90]
    if label:
        short += f" Нюанс: {label.lower()}."
    return MarketCarCard(
        id=c.id, brand=c.brand, model=c.model, generation=c.generation, year=c.year,
        mileage=c.mileage, engine_type=c.engine_type, engine_volume=c.engine_volume,
        transmission=c.transmission, price=c.current_price,
        liquidity=liquidity_label(c.liquidity_score), liquidity_score=c.liquidity_score,
        urgent=c.urgency_score >= 70, risk_hint=risk_hint(c), image_seed=c.image_seed,
        color=c.color, short_description=short,
    )

def _ensure_tasks(db: Session, user: User):
    existing = db.query(DailyTask).filter(DailyTask.user_id == user.id, DailyTask.game_day == user.current_game_day).count()
    if existing == 0:
        rng = random.Random(user.id * 1000 + user.current_game_day)
        for t in rng.sample(DAILY_TASK_TEMPLATES, 3):
            db.add(DailyTask(user_id=user.id, task_type=t[0], title=t[1], target_value=t[2],
                             reward_type=t[3], reward_value=t[4], game_day=user.current_game_day))
        db.commit()

@router.get("", response_model=MarketResponse)
def get_market(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    cars = db.query(Car).filter(Car.owner_user_id == user.id, Car.status == "MARKET",
                                Car.market_day == user.current_game_day).order_by(Car.id).all()
    if not cars:
        cars = generate_market_cars(db, user, count=6)
        # случайное событие дня
        rng = random.Random(user.id * 7919 + user.current_game_day)
        if rng.random() < 0.6:
            ev = rng.choice(RANDOM_EVENTS)
            db.add(GameEvent(user_id=user.id, event_type=ev[0], title=ev[1], description=ev[2]))
            db.commit()
    _ensure_tasks(db, user)
    free = user.market_refreshes_today == 0
    return MarketResponse(game_day=user.current_game_day, cars=[_card(c) for c in cars],
                          refresh_cost=0 if free else REFRESH_COST, free_refresh_available=free)

@router.post("/refresh", response_model=MarketResponse)
def refresh_market(advance_day: bool = True, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """advance_day=true — следующий игровой день (бесплатно).
    advance_day=false — обновить объявления в том же дне (1-й раз бесплатно, далее 50 BYN)."""
    if advance_day:
        # старые объявления истекают
        db.query(Car).filter(Car.owner_user_id == user.id, Car.status == "MARKET").update({Car.status: "EXPIRED"})
        user.current_game_day += 1
        user.market_refreshes_today = 0
        db.commit()
        cars = generate_market_cars(db, user, count=6)
        rng = random.Random(user.id * 7919 + user.current_game_day)
        if rng.random() < 0.65:
            ev = rng.choice(RANDOM_EVENTS)
            db.add(GameEvent(user_id=user.id, event_type=ev[0], title=ev[1], description=ev[2]))
            db.commit()
        _ensure_tasks(db, user)
        return MarketResponse(game_day=user.current_game_day, cars=[_card(c) for c in cars],
                              refresh_cost=0, free_refresh_available=True)
    else:
        cost = 0 if user.market_refreshes_today == 0 else REFRESH_COST
        if user.balance < cost:
            raise HTTPException(400, "Не хватает BYN для обновления рынка")
        if cost:
            user.balance -= cost
            db.add(Transaction(user_id=user.id, type="REWARD", amount=-cost, balance_after=user.balance,
                               meta={"reason": "Обновление рынка"}))
        user.market_refreshes_today += 1
        # конкурент может забрать 1 хорошую машину
        cars = db.query(Car).filter(Car.owner_user_id == user.id, Car.status == "MARKET").all()
        rng = random.Random()
        if cars and rng.random() < 0.35:
            victim = rng.choice(cars)
            victim.status = "EXPIRED"
            db.add(GameEvent(user_id=user.id, event_type="competitor", title="Конкурент купил автомобиль",
                             description=f"Пока вы думали, {victim.brand} {victim.model} {victim.year} забрали."))
        # заменяем истёкшие новыми
        active = [c for c in cars if c.status == "MARKET"]
        need = max(0, 6 - len(active))
        if need:
            generate_market_cars(db, user, count=need)
        db.commit()
        cars = db.query(Car).filter(Car.owner_user_id == user.id, Car.status == "MARKET",
                                    Car.market_day == user.current_game_day).all()
        # если обновляли в тот же день — подтянем и новые (market_day тот же)
        if not cars:
            cars = generate_market_cars(db, user, count=6)
        return MarketResponse(game_day=user.current_game_day, cars=[_card(c) for c in cars],
                              refresh_cost=REFRESH_COST, free_refresh_available=False)
