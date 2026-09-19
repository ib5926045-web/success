import random
from sqlalchemy.orm import Session
from ..models import Car, User
from .texts import HIDDEN_DEFECTS, SELLER_REPLICAS_EXTRA, PERSONALITIES

# 30 шаблонов: brand, model, generation, year_from, year_to, engine, volume, power, trans, drive, base_price, liquidity
TEMPLATES = [
    ("Volkswagen", "Passat", "B5", 1997, 2000, "бензин", 1.8, 125, "МКПП", "передний", 5200, 85),
    ("Volkswagen", "Passat", "B5+", 2001, 2005, "дизель", 1.9, 130, "МКПП", "передний", 6800, 88),
    ("Volkswagen", "Golf", "4", 1998, 2003, "бензин", 1.6, 101, "МКПП", "передний", 4900, 90),
    ("Audi", "A4", "B5", 1996, 2001, "бензин", 1.8, 125, "МКПП", "передний", 5400, 78),
    ("BMW", "3er", "E36", 1994, 1999, "бензин", 1.8, 115, "МКПП", "задний", 4300, 70),
    ("BMW", "3er", "E46", 1999, 2004, "бензин", 2.0, 143, "МКПП", "задний", 7200, 80),
    ("Opel", "Astra", "G", 1998, 2004, "бензин", 1.6, 101, "МКПП", "передний", 4200, 82),
    ("Opel", "Astra", "H", 2004, 2009, "бензин", 1.6, 105, "МКПП", "передний", 6500, 84),
    ("Opel", "Vectra", "C", 2002, 2007, "дизель", 1.9, 120, "МКПП", "передний", 6300, 72),
    ("Renault", "Megane", "2", 2003, 2008, "бензин", 1.6, 115, "МКПП", "передний", 5100, 78),
    ("Renault", "Laguna", "2", 2001, 2006, "дизель", 1.9, 120, "МКПП", "передний", 4800, 60),
    ("Peugeot", "307", "—", 2002, 2007, "бензин", 1.6, 109, "МКПП", "передний", 4400, 68),
    ("Peugeot", "406", "—", 1999, 2004, "бензин", 2.0, 136, "МКПП", "передний", 4100, 58),
    ("Ford", "Focus", "2", 2005, 2010, "бензин", 1.6, 100, "МКПП", "передний", 7500, 86),
    ("Ford", "Mondeo", "3", 2001, 2006, "дизель", 2.0, 130, "МКПП", "передний", 5600, 70),
    ("Ford", "Mondeo", "4", 2007, 2012, "дизель", 2.0, 140, "МКПП", "передний", 9800, 74),
    ("Skoda", "Octavia", "Tour", 1999, 2007, "бензин", 1.6, 102, "МКПП", "передний", 5800, 90),
    ("Skoda", "Octavia", "A5", 2004, 2010, "бензин", 1.6, 102, "МКПП", "передний", 8200, 92),
    ("Toyota", "Avensis", "2", 2003, 2008, "бензин", 1.8, 129, "МКПП", "передний", 7800, 80),
    ("Honda", "Civic", "7", 2001, 2005, "бензин", 1.6, 110, "МКПП", "передний", 6600, 76),
    ("Mazda", "3", "BK", 2003, 2008, "бензин", 1.6, 105, "МКПП", "передний", 6900, 82),
    ("Mercedes-Benz", "C", "W202", 1996, 2000, "бензин", 2.0, 136, "АКПП", "задний", 4700, 62),
    ("Mercedes-Benz", "C", "W203", 2000, 2006, "дизель", 2.2, 143, "АКПП", "задний", 7400, 68),
    ("Lada", "Priora", "—", 2008, 2014, "бензин", 1.6, 98, "МКПП", "передний", 3800, 75),
    ("Lada", "Vesta", "—", 2015, 2019, "бензин", 1.6, 106, "МКПП", "передний", 12500, 80),
    ("Geely", "Emgrand", "EC7", 2012, 2016, "бензин", 1.8, 126, "МКПП", "передний", 8900, 72),
    ("Kia", "Rio", "2", 2006, 2010, "бензин", 1.4, 97, "МКПП", "передний", 6200, 84),
    ("Hyundai", "Accent", "2", 2000, 2006, "бензин", 1.5, 102, "МКПП", "передний", 4500, 78),
    ("Nissan", "Almera", "N16", 2000, 2006, "бензин", 1.8, 114, "МКПП", "передний", 5200, 74),
    ("Chevrolet", "Lacetti", "—", 2004, 2010, "бензин", 1.6, 109, "МКПП", "передний", 5900, 76),
]

COLORS = ["серебристый", "чёрный", "синий", "красный", "зелёный", "белый", "серый", "бежевый"]

def _defects_for_personality(personality: str, rng: random.Random) -> tuple[list[str], list[str]]:
    keys = list(HIDDEN_DEFECTS.keys())
    # срочные/паника/перекупы — больше скрытых дефектов
    if personality in ("urgent", "panic"):
        n_hidden = rng.randint(2, 4)
    elif personality == "reseller":
        n_hidden = rng.randint(2, 3)
    elif personality == "elder":
        n_hidden = rng.randint(0, 2)
    else:
        n_hidden = rng.randint(1, 3)
    hidden = rng.sample(keys, min(n_hidden, len(keys)))
    # видимые — лёгкие косметические (часть hidden может быть видна)
    visible_pool = ["rust_arches", "repainted_door", "suspension_knock", "brake_vibration"]
    visible = [d for d in hidden if d in visible_pool and rng.random() < 0.5]
    if not visible and rng.random() < 0.4:
        visible = [rng.choice(visible_pool)]
    return hidden, visible

def generate_market_cars(db: Session, user: User, count: int = 6, rng: random.Random | None = None) -> list[Car]:
    rng = rng or random.Random()
    # фильтр по уровню: L1 — только дешёвые (base <= 6500), L4+ — доступ к дорогим
    if user.level <= 1:
        pool = [t for t in TEMPLATES if t[10] <= 7000]
    elif user.level <= 3:
        pool = [t for t in TEMPLATES if t[10] <= 10000]
    else:
        pool = TEMPLATES
    chosen = rng.sample(pool, min(count, len(pool)))
    # Новичкам гарантируем минимум 2 бюджетных варианта (иначе старт фрустрирует)
    if user.level <= 1:
        cheap = [t for t in pool if t[10] <= 5200]
        if len(cheap) >= 2:
            for t in rng.sample(cheap, 2):
                if t not in chosen:
                    chosen[rng.randrange(len(chosen))] = t
    cars: list[Car] = []
    personalities = list(PERSONALITIES.keys())
    budget_left = 2 if user.level <= 1 else 0
    for t in chosen:
        brand, model, gen, y0, y1, eng, vol, power, trans, drive, base, liq = t
        year = rng.randint(y0, y1)
        age = max(1, 2026 - year)
        mileage = rng.randint(120000, 120000 + age * 22000)
        if rng.random() < 0.2:
            mileage -= rng.randint(30000, 80000)  # «маленький пробег» — подозрительно
        personality = rng.choice(personalities)
        urgency = rng.randint(10, 100)
        if personality in ("urgent", "panic"):
            urgency = rng.randint(65, 100)
        # состояние узлов
        def cond():
            return max(25, min(95, rng.randint(45, 90) - (0 if personality == "elder" else rng.randint(0, 12))))
        body, eng_c, trans_c, susp, inter = cond(), cond(), cond(), cond(), cond()
        hidden, visible = _defects_for_personality(personality, rng)
        # базовая цена с поправкой на год и пробег
        base_val = int(base * (1 - (2026 - year) * 0.008) * (1 - max(0, mileage - 150000) / 1000000))
        base_val = max(2500, base_val)
        # цена продавца: наценка по характеру
        margin = {"urgent": -0.06, "confident": 0.12, "adequate": 0.05, "reseller": 0.10, "elder": 0.02, "panic": -0.10}[personality]
        seller_price = int(base_val * (1 + margin + rng.uniform(-0.03, 0.05)))
        max_disc = {"urgent": 0.15, "confident": 0.04, "adequate": 0.08, "reseller": 0.06, "elder": 0.07, "panic": 0.18}[personality]
        min_price = int(seller_price * (1 - max_disc))
        if budget_left > 0:
            # бюджетный вариант: цена в пределах стартового капитала
            seller_price = min(seller_price, 4650)
            min_price = min(min_price, int(seller_price * (1 - max_disc)))
            budget_left -= 1
        desc = rng.choice(SELLER_REPLICAS_EXTRA)
        car = Car(
            owner_user_id=user.id, status="MARKET",
            brand=brand, model=model, generation=gen, year=year, mileage=mileage,
            engine_type=eng, engine_volume=vol, power_hp=power, transmission=trans, drive_type=drive,
            color=rng.choice(COLORS),
            base_market_value=base_val, seller_price=seller_price, minimum_seller_price=min_price,
            current_price=seller_price,
            liquidity_score=max(10, min(99, liq + rng.randint(-12, 12))),
            body_condition=body, engine_condition=eng_c, transmission_condition=trans_c,
            suspension_condition=susp, interior_condition=inter, visual_appeal=rng.randint(35, 75),
            legal_risk_score=rng.randint(0, 35) + (20 if "ban_registration" in hidden or "pledge_bank" in hidden else 0),
            accident_risk_score=rng.randint(0, 35) + (25 if "accident_front" in hidden or "accident_rear" in hidden else 0),
            mileage_risk_score=rng.randint(0, 30) + (25 if "mileage_rolled" in hidden else 0),
            seller_personality=personality, urgency_score=urgency,
            owners_count=rng.randint(1, 5),
            visible_defects=visible, hidden_defects=hidden, known_defects=[], resolved_defects=[],
            description=f"{brand} {model} {year} г. {desc}",
            image_seed=rng.randint(1, 999999), market_day=user.current_game_day,
        )
        db.add(car)
        cars.append(car)
    db.commit()
    for c in cars:
        db.refresh(c)
    return cars
