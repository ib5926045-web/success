import random
from fastapi import APIRouter, Depends, Header, HTTPException
from sqlalchemy.orm import Session
from ..database import get_db
from ..deps import get_current_user
from ..models import User, Car, CarInspection, Transaction, Negotiation, DailyTask
from ..schemas import CarDetail, InspectRequest, InspectResponse, NegotiateRequest, NegotiateResponse, BuyResponse
from ..game.pricing import market_range, liquidity_label, garage_limit, add_xp, real_value
from ..game.negotiation import negotiate_seller
from ..game.texts import HIDDEN_DEFECTS, PERSONALITIES

router = APIRouter(prefix="/cars", tags=["cars"])

INSPECTION_PRICES = {"body": 30, "docs": 40, "diagnostics": 50, "testdrive": 30, "full": 120}
INSPECTION_LABELS = {"body": "Осмотр кузова", "docs": "Проверка документов", "diagnostics": "Компьютерная диагностика",
                     "testdrive": "Тест-драйв", "full": "Комплексная проверка"}

def _get_market_car(db: Session, user: User, car_id: int) -> Car:
    car = db.query(Car).filter(Car.id == car_id, Car.owner_user_id == user.id, Car.status == "MARKET").first()
    if not car:
        raise HTTPException(404, "Объявление не найдено или уже недоступно")
    if car.market_day != user.current_game_day:
        car.status = "EXPIRED"
        db.commit()
        raise HTTPException(410, "Срок объявления истёк")
    return car

def _detail(db: Session, car: Car) -> CarDetail:
    low, high = market_range(car)
    insp = db.query(CarInspection.inspection_type).filter(CarInspection.car_id == car.id).all()
    known_labels = [HIDDEN_DEFECTS[d]["label"] for d in (car.known_defects or []) if d in HIDDEN_DEFECTS]
    vis_labels = [HIDDEN_DEFECTS[d]["label"] for d in (car.visible_defects or []) if d in HIDDEN_DEFECTS]
    return CarDetail(
        id=car.id, brand=car.brand, model=car.model, generation=car.generation, year=car.year,
        mileage=car.mileage, engine_type=car.engine_type, engine_volume=car.engine_volume,
        power_hp=car.power_hp, transmission=car.transmission, drive_type=car.drive_type, color=car.color,
        status=car.status, price=car.current_price, seller_price=car.seller_price,
        market_value_low=low, market_value_high=high,
        liquidity=liquidity_label(car.liquidity_score), liquidity_score=car.liquidity_score,
        urgent=car.urgency_score >= 70, description=car.description,
        visible_defects=vis_labels, known_defects=known_labels,
        inspections_done=[i[0] for i in insp],
        conditions={"body": car.body_condition, "engine": car.engine_condition,
                    "gearbox": car.transmission_condition, "suspension": car.suspension_condition,
                    "interior": car.interior_condition},
        seller_personality=car.seller_personality,
        seller_personality_label=PERSONALITIES.get(car.seller_personality, car.seller_personality),
        owners_count=car.owners_count, image_seed=car.image_seed,
    )

@router.get("/{car_id}", response_model=CarDetail)
def car_detail(car_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    car = _get_market_car(db, user, car_id)
    return _detail(db, car)

@router.post("/{car_id}/inspect", response_model=InspectResponse)
def inspect_car(car_id: int, body: InspectRequest, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    car = _get_market_car(db, user, car_id)
    itype = body.inspection_type
    if itype not in INSPECTION_PRICES:
        raise HTTPException(400, "Неизвестный тип проверки")
    price = INSPECTION_PRICES[itype]
    if user.balance < price:
        raise HTTPException(400, "Не хватает BYN для проверки")
    rng = random.Random()
    hidden = [d for d in (car.hidden_defects or []) if d not in (car.resolved_defects or [])]
    known = set(car.known_defects or [])
    # какие дефекты может раскрыть проверка
    if itype == "full":
        targets = hidden
        p = 0.75
    else:
        targets = [d for d in hidden if HIDDEN_DEFECTS.get(d, {}).get("check") == itype]
        p = 0.85
    revealed: list[str] = []
    for d in targets:
        if d not in known and rng.random() < p:
            revealed.append(d)
            known.add(d)
    car.known_defects = sorted(known)
    user.balance -= price
    car.invested += 0  # проверки до покупки в invested не входят (учитываются в статистике отдельно)
    if revealed:
        names = ", ".join(HIDDEN_DEFECTS[d]["label"] for d in revealed)
        text = f"{INSPECTION_LABELS[itype]}: выявлено — {names}."
    else:
        # честный «ничего не нашли» либо «всё чисто по этому направлению»
        text = f"{INSPECTION_LABELS[itype]}: явных проблем не выявлено. Это не гарантирует их отсутствие."
        if itype == "body" and car.body_condition >= 80:
            text += " Кузов выглядит ухоженно."
    db.add(CarInspection(car_id=car.id, user_id=user.id, inspection_type=itype, price=price,
                         result_text=text, revealed_defects=revealed))
    db.add(Transaction(user_id=user.id, type="INSPECTION", amount=-price, balance_after=user.balance,
                       meta={"car_id": car.id, "inspection": itype}))
    # прогресс заданий
    for t in db.query(DailyTask).filter(DailyTask.user_id == user.id, DailyTask.game_day == user.current_game_day,
                                        DailyTask.status == "ACTIVE").all():
        if t.task_type == "inspect" or (t.task_type == "diagnose" and itype in ("diagnostics", "full")):
            t.progress_value = min(t.target_value, t.progress_value + 1)
    db.commit()
    known_labels = [HIDDEN_DEFECTS[d]["label"] for d in car.known_defects if d in HIDDEN_DEFECTS]
    return InspectResponse(result_text=text, revealed=[HIDDEN_DEFECTS[d]["label"] for d in revealed],
                           known_defects=known_labels, balance=user.balance, price=price)

@router.post("/{car_id}/negotiate-seller", response_model=NegotiateResponse)
def negotiate(car_id: int, body: NegotiateRequest, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    car = _get_market_car(db, user, car_id)
    if body.offer_price:
        req = body.offer_price
    elif body.discount_percent:
        req = int(car.current_price * (1 - body.discount_percent / 100))
    else:
        raise HTTPException(400, "Укажите discount_percent или offer_price")
    req = max(500, req)
    defects_found = len(car.known_defects or [])
    result, new_price, msg = negotiate_seller(car.current_price, car.minimum_seller_price, car.seller_personality,
                                              car.urgency_score, user.reputation, defects_found, req)
    if result in ("ACCEPTED", "COUNTERED"):
        car.current_price = new_price
    db.add(Negotiation(car_id=car.id, user_id=user.id, side="SELLER", initial_price=car.seller_price,
                       offered_price=req, result=result,
                       dialogue=[{"you": req, "seller": msg, "price": new_price}]))
    if result == "ACCEPTED":
        for t in db.query(DailyTask).filter(DailyTask.user_id == user.id, DailyTask.game_day == user.current_game_day,
                                            DailyTask.status == "ACTIVE", DailyTask.task_type == "haggle").all():
            t.progress_value = min(t.target_value, t.progress_value + 1)
    db.commit()
    return NegotiateResponse(result=result, new_price=new_price, message=msg, balance=user.balance)

@router.post("/{car_id}/buy", response_model=BuyResponse)
def buy_car(car_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db),
            x_idempotency_key: str | None = Header(default=None)):
    # idempotency
    if x_idempotency_key:
        dup = db.query(Transaction).filter(Transaction.user_id == user.id,
                                            Transaction.idempotency_key == x_idempotency_key).first()
        if dup:
            car = db.query(Car).filter(Car.id == car_id).first()
            return BuyResponse(car_id=car_id, purchase_price=car.purchase_price or car.current_price,
                               balance=user.balance, experience=user.experience, level=user.level)
    car = db.query(Car).filter(Car.id == car_id, Car.owner_user_id == user.id).first()
    if not car or car.status != "MARKET":
        raise HTTPException(400, "Автомобиль уже продан или недоступен")
    if car.market_day != user.current_game_day:
        car.status = "EXPIRED"
        db.commit()
        raise HTTPException(410, "Срок объявления истёк")
    garage_count = db.query(Car).filter(Car.owner_user_id == user.id, Car.status.in_(["OWNED", "LISTED"])).count()
    if garage_count >= garage_limit(user.level):
        raise HTTPException(400, f"Гараж заполнен ({garage_count}/{garage_limit(user.level)}). Повысьте уровень.")
    price = car.current_price
    if user.balance < price:
        raise HTTPException(400, "Не хватает BYN для покупки")
    user.balance -= price
    car.status = "OWNED"
    car.purchase_price = price
    car.owned_since_day = user.current_game_day
    car.invested = 0
    db.add(Transaction(user_id=user.id, type="BUY", amount=-price, balance_after=user.balance,
                       meta={"car_id": car.id, "title": f"{car.brand} {car.model} {car.year}"},
                       idempotency_key=x_idempotency_key))
    leveled = add_xp(user, 120)
    if leveled:
        user.reputation = min(100, user.reputation + 2)
    db.commit()
    return BuyResponse(car_id=car.id, purchase_price=price, balance=user.balance,
                       experience=user.experience, level=user.level)

@router.post("/{car_id}/skip")
def skip_car(car_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    car = db.query(Car).filter(Car.id == car_id, Car.owner_user_id == user.id, Car.status == "MARKET").first()
    if not car:
        raise HTTPException(404, "Объявление не найдено")
    car.status = "EXPIRED"
    db.commit()
    return {"ok": True}
