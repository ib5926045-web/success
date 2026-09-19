import random
from app.game.negotiation import negotiate_seller

def test_small_discount_accepted():
    rng = random.Random(42)
    ok = 0
    for _ in range(20):
        res, price, msg = negotiate_seller(5000, 4500, "adequate", 50, 10, 0, 4850, rng)
        assert price <= 5000 and msg
        if res == "ACCEPTED":
            ok += 1
    assert ok > 0  # скидка 3% обычно проходит

def test_below_minimum_counters():
    rng = random.Random(1)
    res, price, msg = negotiate_seller(5000, 4600, "confident", 10, 10, 0, 3000, rng)
    assert res in ("COUNTERED", "DECLINED")
    assert price >= 4600 or res == "DECLINED"
