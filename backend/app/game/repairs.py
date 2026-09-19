import random

# repair_type -> (label, min_cost, max_cost, min_level, эффект)
REPAIR_CATALOG = {
    "wash": {"label": "Мойка", "min": 20, "max": 20, "level": 1},
    "chem": {"label": "Химчистка", "min": 80, "max": 180, "level": 2},
    "polish": {"label": "Полировка", "min": 120, "max": 300, "level": 2},
    "consumables": {"label": "Замена расходников", "min": 100, "max": 350, "level": 2},
    "suspension": {"label": "Ремонт подвески", "min": 150, "max": 900, "level": 2},
    "body": {"label": "Кузовной ремонт", "min": 200, "max": 2000, "level": 3},
    "engine": {"label": "Ремонт двигателя", "min": 300, "max": 2500, "level": 3},
    "gearbox": {"label": "Ремонт коробки", "min": 400, "max": 3000, "level": 4},
}

# какие дефекты чинит каждый ремонт
REPAIR_FIXES = {
    "wash": [],
    "chem": [],
    "polish": ["repainted_door"],
    "consumables": ["timing_worn"],
    "suspension": ["suspension_knock", "brake_vibration"],
    "body": ["rust_arches", "repainted_door", "accident_rear", "accident_front"],
    "engine": ["engine_oil_burn", "timing_worn", "turbo_wear"],
    "gearbox": ["gearbox_kick", "clutch_worn", "electronics_abs"],
}

def repair_cost(repair_type: str, car, rng: random.Random | None = None) -> int:
    rng = rng or random
    cat = REPAIR_CATALOG[repair_type]
    # стоимость масштабируется от цены машины
    scale = min(1.6, max(0.7, car.base_market_value / 6000))
    base = rng.randint(cat["min"], cat["max"])
    return max(cat["min"], int(base * scale))

def apply_repair(car, repair_type: str, rng: random.Random | None = None) -> tuple[str, list[str]]:
    """Применяет ремонт к объекту car (без коммита). Возвращает (текст, resolved)."""
    rng = rng or random
    label = REPAIR_CATALOG[repair_type]["label"]
    resolved: list[str] = []
    hidden = list(car.hidden_defects or [])
    res = list(car.resolved_defects or [])
    known = list(car.known_defects or [])
    for d in REPAIR_FIXES.get(repair_type, []):
        if d in hidden and d not in res:
            resolved.append(d)
            res.append(d)
            if d not in known:
                known.append(d)
    car.resolved_defects = res
    car.known_defects = known
    extra_note = ""
    # улучшение состояния
    if repair_type == "wash":
        car.visual_appeal = min(100, car.visual_appeal + rng.randint(8, 15))
        car.interior_condition = min(100, car.interior_condition + 2)
    elif repair_type == "chem":
        car.interior_condition = min(100, car.interior_condition + rng.randint(10, 20))
        car.visual_appeal = min(100, car.visual_appeal + 5)
    elif repair_type == "polish":
        car.visual_appeal = min(100, car.visual_appeal + rng.randint(10, 18))
        car.body_condition = min(100, car.body_condition + 5)
    elif repair_type == "consumables":
        car.engine_condition = min(100, car.engine_condition + rng.randint(5, 12))
    elif repair_type == "suspension":
        car.suspension_condition = min(100, car.suspension_condition + rng.randint(15, 30))
    elif repair_type == "body":
        car.body_condition = min(100, car.body_condition + rng.randint(15, 35))
        car.visual_appeal = min(100, car.visual_appeal + 8)
    elif repair_type == "engine":
        car.engine_condition = min(100, car.engine_condition + rng.randint(18, 35))
    elif repair_type == "gearbox":
        car.transmission_condition = min(100, car.transmission_condition + rng.randint(18, 35))
    # риск вскрытия дополнительной проблемы на крупных ремонтах
    if repair_type in ("engine", "gearbox", "body") and rng.random() < 0.18:
        from .texts import HIDDEN_DEFECTS
        candidates = [k for k in HIDDEN_DEFECTS if k not in hidden]
        if candidates:
            new_def = rng.choice(candidates)
            hidden.append(new_def)
            car.hidden_defects = hidden
            known.append(new_def)
            car.known_defects = known
            extra_note = f" При разборе мастер нашёл новую проблему: «{HIDDEN_DEFECTS[new_def]['label']}»."
    if resolved:
        from .texts import HIDDEN_DEFECTS
        names = ", ".join(HIDDEN_DEFECTS[d]["label"] for d in resolved if d in HIDDEN_DEFECTS)
        text = f"{label} выполнен. Устранено: {names}."
    else:
        text = f"{label} выполнен. Состояние улучшено."
    return text + extra_note, resolved
