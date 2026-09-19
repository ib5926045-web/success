import random
from datetime import datetime
from fastapi import APIRouter, Depends, Header, HTTPException
from sqlalchemy.orm import Session
from ..database import get_db
from ..deps import get_current_user
from ..models import User, Car, Listing, Offer, Transaction, DailyTask
from ..schemas import CounterRequest, ListingOut, OfferOut
from ..game.pricing import add_xp
from ..game.texts import HIDDEN_DEFECTS, BUYER_REPLICAS

router = APIRouter(prefix="/listings", tags=["listings"])

def _get_listing(db: Session, user: User, listing_id: int) -> Listing:
    l = db.query(Listing).filter(Listing.id == listing_id, Listing.user_id == user.id).first()
    if not l:
        raise HTTPException(404, "Объявление не найдено")
    return l

@router.get("", response_model=list[ListingOut])
def my_listings(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    out: list[ListingOut] = []
    for l in db.query(Listing).filter(Listing.user_id == user.id).order_by(Listing.id.desc()).limit(20).all():
        car = db.get(Car, l.car_id)
        offers = [OfferOut(id=o.id, buyer_name=o.buyer_name, buyer_type=o.buyer_type,
                           offered_price=o.offered_price, status=o.status, message=o.message)
                  for o in db.query(Offer).filter(Offer.listing_id == l.id).order_by(Offer.offered_price.desc()).all()]
        out.append(ListingOut(id=l.id, car_id=l.car_id, car_title=f"{car.brand} {car.model} {car.year}" if car else "?",
                              listing_price=l.listing_price, listing_style=l.listing_style, status=l.status, offers=offers))
    return out

@router.post("/{listing_id}/offers/{offer_id}/accept")
def accept_offer(listing_id: int, offer_id: int, user: User = Depends(get_current_user),
                 db: Session = Depends(get_db), x_idempotency_key: str | None = Header(default=None)):
    if x_idempotency_key:
        dup = db.query(Transaction).filter(Transaction.user_id == user.id,
                                            Transaction.idempotency_key == x_idempotency_key).first()
        if dup:
            return {"ok": True, "deduped": True, "balance": user.balance}
    listing = _get_listing(db, user, listing_id)
    if listing.status != "ACTIVE":
        raise HTTPException(400, "Объявление уже закрыто")
    offer = db.query(Offer).filter(Offer.id == offer_id, Offer.listing_id == listing.id).first()
    if not offer or offer.status != "PENDING":
        raise HTTPException(400, "Предложение недоступно")
    car = db.get(Car, listing.car_id)
    if not car or car.status != "LISTED":
        raise HTTPException(400, "Машина уже продана")
    sale_price = offer.offered_price
    total_cost = (car.purchase_price or 0) + (car.invested or 0)
    profit = sale_price - total_cost
    # скрытие серьёзных дефектов: риск жалобы
    known = set(car.known_defects or []) - set(car.resolved_defects or [])
    disclosed = set(listing.disclosed_defects or [])
    hidden_serious = [d for d in known - disclosed if HIDDEN_DEFECTS.get(d, {}).get("severity", 1) >= 2]
    complaint = False
    rng = random.Random(offer.id * 101 + listing.id)
    if hidden_serious and rng.random() < 0.45:
        complaint = True
    for o in db.query(Offer).filter(Offer.listing_id == listing.id, Offer.status == "PENDING").all():
        o.status = "EXPIRED" if o.id != offer.id else "ACCEPTED"
    listing.status = "SOLD"
    listing.sold_at = datetime.utcnow()
    car.status = "SOLD"
    car.sale_price = sale_price
    user.balance += sale_price
    user.total_profit += profit
    user.deals_count += 1
    db.add(Transaction(user_id=user.id, type="SALE", amount=sale_price, balance_after=user.balance,
                       meta={"car_id": car.id, "profit": profit, "purchase": car.purchase_price,
                             "invested": car.invested, "complaint": complaint},
                       idempotency_key=x_idempotency_key))
    # опыт и репутация
    xp = 250 + max(0, min(800, profit // 3))
    if profit < 0:
        xp = 120
    leveled = add_xp(user, xp)
    if complaint:
        user.reputation = max(0, user.reputation - 8)
        rep_msg = "Покупатель обнаружил скрытый дефект и оставил жалобу. Репутация −8."
    elif profit > 0 and listing.listing_style == "honest":
        user.reputation = min(100, user.reputation + 3)
        rep_msg = "Честная сделка! Репутация +3."
    elif profit > 0:
        user.reputation = min(100, user.reputation + 1)
        rep_msg = "Сделка закрыта. Репутация +1."
    else:
        user.reputation = max(0, user.reputation - 1)
        rep_msg = "Продажа в убыток. Репутация −1."
    if leveled:
        rep_msg += f" Новый уровень: {user.level}!"
    for t in db.query(DailyTask).filter(DailyTask.user_id == user.id, DailyTask.game_day == user.current_game_day,
                                        DailyTask.status == "ACTIVE").all():
        if t.task_type == "profit_sale" and profit > 0:
            t.progress_value = min(t.target_value, t.progress_value + 1)
        if t.task_type == "profit100" and profit > 0:
            t.progress_value = min(t.target_value, t.progress_value + min(profit, t.target_value))
    db.commit()
    return {"ok": True, "sale_price": sale_price, "profit": profit, "balance": user.balance,
            "experience": user.experience, "level": user.level, "reputation": user.reputation,
            "message": rep_msg, "complaint": complaint}

@router.post("/{listing_id}/offers/{offer_id}/decline")
def decline_offer(listing_id: int, offer_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    listing = _get_listing(db, user, listing_id)
    offer = db.query(Offer).filter(Offer.id == offer_id, Offer.listing_id == listing.id).first()
    if not offer or offer.status != "PENDING":
        raise HTTPException(400, "Предложение недоступно")
    offer.status = "DECLINED"
    db.commit()
    return {"ok": True}

@router.post("/{listing_id}/offers/{offer_id}/counter")
def counter_offer(listing_id: int, offer_id: int, body: CounterRequest, user: User = Depends(get_current_user),
                  db: Session = Depends(get_db)):
    listing = _get_listing(db, user, listing_id)
    if listing.status != "ACTIVE":
        raise HTTPException(400, "Объявление закрыто")
    offer = db.query(Offer).filter(Offer.id == offer_id, Offer.listing_id == listing.id).first()
    if not offer or offer.status not in ("PENDING", "COUNTERED"):
        raise HTTPException(400, "Предложение недоступно")
    rng = random.Random()
    haggle = (offer.buyer_traits or {}).get("haggle", 50)
    gap = (body.price - offer.offered_price) / max(1, offer.offered_price)
    # покупатель соглашается если встречная близко (до ~4%) и он не любитель торга
    if gap <= 0.02 or (gap <= 0.05 and rng.random() < (100 - haggle) / 100 + 0.2):
        offer.offered_price = body.price
        offer.status = "PENDING"
        offer.message = f"Хорошо, согласен на {body.price:,} BYN. Оформляем?".replace(",", " ")
        db.commit()
        return {"result": "ACCEPTED", "price": body.price, "message": offer.message}
    # иначе двигается навстречу на половину разрыва
    new_price = int((offer.offered_price + body.price) / 2)
    new_price = min(new_price, listing.listing_price)
    offer.offered_price = new_price
    offer.status = "PENDING"
    offer.message = rng.choice(BUYER_REPLICAS).format(price=f"{new_price:,}".replace(",", " "))
    db.commit()
    return {"result": "COUNTERED", "price": new_price, "message": offer.message}
