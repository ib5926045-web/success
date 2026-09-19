import random
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..database import get_db
from ..deps import get_current_user
from ..models import User, Car, CarRepair, Transaction, Listing, Offer, DailyTask
from ..schemas import GarageCar, RepairRequest, RepairResponse, PrepareRequest, ListRequest, CarDetail
from ..game.pricing import estimated_value, liquidity_label, market_range
from ..game.repairs import REPAIR_CATALOG, repair_cost, apply_repair
from ..game.offers import generate_offers
from ..game.texts import HIDDEN_DEFECTS, PERSONALITIES

router = APIRouter(prefix="/garage", tags=["garage"])

def _readiness(car: Car) -> int:
    cond = (car.body_condition + car.engine_condition + car.transmission_condition + car.suspension_condition + car.interior_condition) / 5
    score = cond * 0.6 + car.visual_appeal * 0.25 + (15 if car.photo_done else 0)
    return max(0, min(100, int(score)))

def _out(db: Session, car: Car, user: User) -> GarageCar:
    est = estimated_value(car)
    total = (car.purchase_price or 0) + (car.invested or 0)
    listing = db.query(Listing).filter(Listing.car_id == car.id, Listing.status == "ACTIVE").first()
    return GarageCar(
        id=car.id, brand=car.brand, model=car.model, year=car.year, mileage=car.mileage,
        image_seed=car.image_seed, status=car.status, purchase_price=car.purchase_price,
        invested=car.invested or 0, estimated_value=est, potential_profit=est - total,
        conditions={"body": car.body_condition, "engine": car.engine_condition,
                    "gearbox": car.transmission_condition, "suspension": car.suspension_condition,
                    "interior": car.interior_condition},
        known_defects=[HIDDEN_DEFECTS[d]["label"] for d in (car.known_defects or []) if d in HIDDEN_DEFECTS],
        readiness=_readiness(car), owned_days=user.current_game_day - (car.owned_since_day or user.current_game_day),
        listing_id=listing.id if listing else None,
    )

def _owned(db: Session, user: User, car_id: int) -> Car:
    car = db.query(Car).filter(Car.id == car_id, Car.owner_user_id == user.id,
                               Car.status.in_(["OWNED", "LISTED"])).first()
    if not car:
        raise HTTPException(404, "Машина не найдена в гараже")
    return car

@router.get("", response_model=list[GarageCar])
def garage(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    cars = db.query(Car).filter(Car.owner_user_id == user.id, Car.status.in_(["OWNED", "LISTED"])).order_by(Car.id).all()
    return [_out(db, c, user) for c in cars]

@router.get("/{car_id}")
def garage_car(car_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    car = _owned(db, user, car_id)
    low, high = market_range(car)
    listing = db.query(Listing).filter(Listing.car_id == car.id, Listing.status == "ACTIVE").first()
    offers = []
    if listing:
        offers = [{"id": o.id, "buyer_name": o.buyer_name, "buyer_type": o.buyer_type,
                   "offered_price": o.offered_price, "status": o.status, "message": o.message}
                  for o in db.query(Offer).filter(Offer.listing_id == listing.id).order_by(Offer.offered_price.desc()).all()]
    return {
        "car": _out(db, car, user),
        "market_value_low": low, "market_value_high": high,
        "liquidity": liquidity_label(car.liquidity_score),
        "description": car.description,
        "repairs": [{"type": k, "label": v["label"], "min": v["min"], "max": v["max"],
                     "level": v["level"], "locked": user.level < v["level"]} for k, v in REPAIR_CATALOG.items()],
        "listing": {"id": listing.id, "price": listing.listing_price, "style": listing.listing_style,
                    "promotion": listing.promotion_level} if listing else None,
        "offers": offers,
        "photo_done": car.photo_done,
    }

@router.post("/{car_id}/repair", response_model=RepairResponse)
def repair(car_id: int, body: RepairRequest, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    car = _owned(db, user, car_id)
    if car.status == "LISTED":
        raise HTTPException(400, "Снимите машину с продажи перед ремонтом")
    rtype = body.repair_type
    if rtype not in REPAIR_CATALOG:
        raise HTTPException(400, "Неизвестный тип ремонта")
    if user.level < REPAIR_CATALOG[rtype]["level"]:
        raise HTTPException(403, f"Нужно достичь уровня {REPAIR_CATALOG[rtype]['level']}")
    cost = repair_cost(rtype, car)
    if user.balance < cost:
        raise HTTPException(400, "Не хватает BYN на ремонт")
    rng = random.Random()
    text, resolved = apply_repair(car, rtype, rng)
    user.balance -= cost
    car.invested = (car.invested or 0) + cost
    db.add(CarRepair(car_id=car.id, user_id=user.id, repair_type=rtype, cost=cost,
                     result_text=text, resolved_defects=resolved))
    db.add(Transaction(user_id=user.id, type="REPAIR", amount=-cost, balance_after=user.balance,
                       meta={"car_id": car.id, "repair": rtype}))
    for t in db.query(DailyTask).filter(DailyTask.user_id == user.id, DailyTask.game_day == user.current_game_day,
                                        DailyTask.status == "ACTIVE").all():
        if t.task_type == "repair" or (t.task_type == "wash" and rtype == "wash"):
            t.progress_value = min(t.target_value, t.progress_value + 1)
    db.commit()
    return RepairResponse(result_text=text, cost=cost, balance=user.balance,
                          conditions={"body": car.body_condition, "engine": car.engine_condition,
                                      "gearbox": car.transmission_condition,
                                      "suspension": car.suspension_condition,
                                      "interior": car.interior_condition},
                          resolved=[HIDDEN_DEFECTS[d]["label"] for d in resolved if d in HIDDEN_DEFECTS])

@router.post("/{car_id}/prepare")
def prepare(car_id: int, body: PrepareRequest, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    car = _owned(db, user, car_id)
    if body.action == "photo":
        car.photo_done = True
        car.visual_appeal = min(100, car.visual_appeal + 5)
        db.commit()
        return {"ok": True, "message": "Фотосессия готова! Объявление будет привлекательнее."}
    elif body.action == "ad":
        for t in db.query(DailyTask).filter(DailyTask.user_id == user.id, DailyTask.game_day == user.current_game_day,
                                            DailyTask.status == "ACTIVE", DailyTask.task_type == "honest_ad").all():
            t.progress_value = min(t.target_value, t.progress_value + 1)
        db.commit()
        return {"ok": True, "message": "Честное описание подготовлено. Покупатели будут доверять больше."}
    raise HTTPException(400, "Неизвестное действие")

PROMO_COSTS = [0, 60, 150]

@router.post("/{car_id}/list")
def list_car(car_id: int, body: ListRequest, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    car = _owned(db, user, car_id)
    if car.status == "LISTED":
        raise HTTPException(400, "Машина уже выставлена на продажу")
    if body.listing_price < 500:
        raise HTTPException(400, "Цена слишком низкая")
    promo = max(0, min(2, body.promotion_level))
    cost = PROMO_COSTS[promo]
    if user.balance < cost:
        raise HTTPException(400, "Не хватает BYN на продвижение")
    if cost:
        user.balance -= cost
        db.add(Transaction(user_id=user.id, type="ADVERTISING", amount=-cost, balance_after=user.balance,
                           meta={"car_id": car.id}))
    car.status = "LISTED"
    listing = Listing(car_id=car.id, user_id=user.id, listing_price=body.listing_price,
                      listing_style=body.listing_style, promotion_level=promo,
                      disclosed_defects=body.disclosed_defects or [])
    db.add(listing)
    db.commit()
    db.refresh(listing)
    rng = random.Random(listing.id * 31 + car.id)
    for o in generate_offers(body.listing_price, car, user.reputation, promo, body.listing_style, rng):
        db.add(Offer(listing_id=listing.id, buyer_name=o["buyer_name"], buyer_type=o["buyer_type"],
                     offered_price=o["offered_price"], buyer_traits=o["traits"], message=o["message"]))
    for t in db.query(DailyTask).filter(DailyTask.user_id == user.id, DailyTask.game_day == user.current_game_day,
                                        DailyTask.status == "ACTIVE").all():
        if t.task_type == "list" or (t.task_type == "honest_ad" and body.listing_style == "honest"):
            t.progress_value = min(t.target_value, t.progress_value + 1)
    db.commit()
    offers = db.query(Offer).filter(Offer.listing_id == listing.id).all()
    return {"listing_id": listing.id, "offers_count": len(offers),
            "offers": [{"id": o.id, "buyer_name": o.buyer_name, "offered_price": o.offered_price, "message": o.message} for o in offers]}

@router.post("/{car_id}/unlist")
def unlist(car_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    car = _owned(db, user, car_id)
    listing = db.query(Listing).filter(Listing.car_id == car.id, Listing.status == "ACTIVE").first()
    if not listing:
        raise HTTPException(400, "Машина не выставлена на продажу")
    listing.status = "CANCELLED"
    car.status = "OWNED"
    db.commit()
    return {"ok": True}
