import random
from .texts import BUYER_REPLICAS, BUYER_TYPES
from .pricing import real_value

BUYER_NAMES = ["Алексей", "Дмитрий", "Сергей", "Игорь", "Виталий", "Андрей", "Ольга", "Павел", "Николай", "Егор", "Максим", "Денис"]

def generate_offers(listing_price: int, car, user_reputation: int, promotion_level: int, listing_style: str,
                    rng: random.Random | None = None) -> list[dict]:
    rng = rng or random
    true_val = real_value(car)
    # кол-во предложений 1-4, зависит от цены vs рынка и продвижения
    ratio = listing_price / max(1, true_val)
    if ratio < 0.92:
        n = rng.randint(3, 4)
    elif ratio < 1.05:
        n = rng.randint(2, 3)
    elif ratio < 1.18:
        n = rng.randint(1, 2)
    else:
        n = 1
    n = min(4, n + (1 if promotion_level >= 2 else 0))
    if listing_style == "urgent":
        n = min(4, n + 1)
    offers = []
    for _ in range(n):
        btype = rng.choice(list(BUYER_TYPES.keys()))
        name = rng.choice(BUYER_NAMES)
        # покупатель ориентируется на честную цену с шумом и торгуется
        noise = rng.uniform(0.92, 1.05)
        base_offer = int(min(listing_price * rng.uniform(0.90, 1.0), true_val * noise))
        # репутация повышает доверие (+до 4%)
        base_offer = int(base_offer * (1 + (user_reputation - 10) * 0.0006))
        # придирчивость: если много известных дефектов — скидка
        known_left = len([d for d in (car.known_defects or []) if d not in (car.resolved_defects or [])])
        base_offer -= known_left * rng.randint(40, 120)
        base_offer = max(500, base_offer)
        traits = {
            "pickiness": rng.randint(20, 90),
            "haste": rng.randint(20, 95),
            "haggle": rng.randint(20, 90),
        }
        msg = rng.choice(BUYER_REPLICAS).format(price=f"{base_offer:,}".replace(",", " "))
        offers.append({"buyer_name": name, "buyer_type": btype, "offered_price": base_offer, "traits": traits, "message": msg})
    # сортируем по цене вниз
    offers.sort(key=lambda o: o["offered_price"], reverse=True)
    return offers
