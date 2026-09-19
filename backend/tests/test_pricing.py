from types import SimpleNamespace
from app.game.pricing import real_value, estimated_value, market_range, add_xp, garage_limit

def _car(**kw):
    d = dict(base_market_value=6000, body_condition=70, engine_condition=70,
             transmission_condition=70, suspension_condition=70, interior_condition=70,
             hidden_defects=[], resolved_defects=[], known_defects=[], visible_defects=[],
             liquidity_score=50, visual_appeal=50, photo_done=False, invested=0)
    d.update(kw)
    return SimpleNamespace(**d)

def test_real_value_state_effect():
    good = _car(body_condition=90, engine_condition=90, transmission_condition=90,
                suspension_condition=90, interior_condition=90)
    bad = _car(body_condition=30, engine_condition=30, transmission_condition=30,
               suspension_condition=30, interior_condition=30)
    assert real_value(good) > real_value(bad)

def test_hidden_defects_lower_value():
    clean = _car()
    broken = _car(hidden_defects=["gearbox_kick", "accident_front"])
    assert real_value(broken) < real_value(clean)

def test_market_range_order():
    low, high = market_range(_car())
    assert low < high and low > 0

def test_add_xp_levelup():
    u = SimpleNamespace(experience=950, level=1)
    assert add_xp(u, 100) is True
    assert u.level == 2

def test_garage_limit():
    assert garage_limit(1) == 1 and garage_limit(5) == 8
