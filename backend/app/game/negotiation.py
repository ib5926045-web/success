import random
from .texts import SELLER_REPLICAS_ACCEPT, SELLER_REPLICAS_COUNTER, SELLER_REPLICAS_DECLINE

# Характер -> максимальная скидка и сговорчивость
PERSONALITY_DEAL = {
    "urgent": {"max_disc": 0.15, "agree": 0.75},
    "confident": {"max_disc": 0.04, "agree": 0.25},
    "adequate": {"max_disc": 0.08, "agree": 0.55},
    "reseller": {"max_disc": 0.06, "agree": 0.4},
    "elder": {"max_disc": 0.07, "agree": 0.5},
    "panic": {"max_disc": 0.18, "agree": 0.7},
}

def negotiate_seller(price: int, min_price: int, personality: str, urgency: int,
                     reputation: int, defects_found: int, request_price: int, rng: random.Random | None = None) -> tuple[str, int, str]:
    """Возвращает (result, new_price, message). result: ACCEPTED|COUNTERED|DECLINED"""
    rng = rng or random
    deal = PERSONALITY_DEAL.get(personality, PERSONALITY_DEAL["adequate"])
    if request_price >= price:
        return "ACCEPTED", price, rng.choice(SELLER_REPLICAS_ACCEPT).format(price=f"{price:,}".replace(",", " "))
    discount = (price - request_price) / price
    # ниже минимальной цены продавец не пойдёт почти никогда
    if request_price < min_price:
        # 10% шанс что паникующий/urgent согласится чуть ниже минимума
        if personality in ("panic", "urgent") and rng.random() < 0.12:
            msg = rng.choice(SELLER_REPLICAS_ACCEPT).format(price=f"{request_price:,}".replace(",", " "))
            return "ACCEPTED", request_price, msg
        counter = max(min_price, int(price * (1 - deal["max_disc"])))
        msg = rng.choice(SELLER_REPLICAS_COUNTER).format(
            offer=f"{request_price:,}".replace(",", " "), price=f"{counter:,}".replace(",", " "))
        return "COUNTERED", counter, msg
    # вероятность согласия
    p = deal["agree"]
    p += (urgency - 50) * 0.004
    p += (reputation - 10) * 0.003
    p += defects_found * 0.06
    p -= max(0, discount - 0.03) * 4  # большие скидки режут шанс
    if rng.random() < p or discount <= 0.03:
        msg = rng.choice(SELLER_REPLICAS_ACCEPT).format(price=f"{request_price:,}".replace(",", " "))
        return "ACCEPTED", request_price, msg
    # встречное: середина между запросом и текущей, но не ниже минимума
    counter = max(min_price, int((request_price + price) / 2))
    if counter >= price - 5:
        msg = rng.choice(SELLER_REPLICAS_DECLINE)
        return "DECLINED", price, msg
    if discount > deal["max_disc"] + 0.05 and rng.random() < 0.4:
        msg = rng.choice(SELLER_REPLICAS_DECLINE)
        return "DECLINED", price, msg
    msg = rng.choice(SELLER_REPLICAS_COUNTER).format(
        offer=f"{request_price:,}".replace(",", " "), price=f"{counter:,}".replace(",", " "))
    return "COUNTERED", counter, msg
