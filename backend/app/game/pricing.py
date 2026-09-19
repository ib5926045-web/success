"""Серверные расчёты цен. Клиенту никогда не доверяем."""
from __future__ import annotations

def avg_condition(car) -> float:
    vals = [car.body_condition, car.engine_condition, car.transmission_condition, car.suspension_condition, car.interior_condition]
    return sum(vals) / len(vals)

def real_value(car) -> int:
    """Честная стоимость с учётом состояния и скрытых дефектов (серверная тайна)."""
    base = car.base_market_value
    cond = avg_condition(car) / 100  # 0..1
    # состояние даёт множитель 0.55..1.05
    mult = 0.55 + cond * 0.5
    val = base * mult
    # скрытые дефекты снижают цену
    from .texts import HIDDEN_DEFECTS
    for d in (car.hidden_defects or []):
        if d in HIDDEN_DEFECTS and d not in (car.resolved_defects or []):
            val -= HIDDEN_DEFECTS[d]["cost"] * 0.9
    # ликвидность влияет на реализуемость, не на честную цену — лёгкая поправка
    val *= 1 + (car.liquidity_score - 50) * 0.0008
    return max(500, int(val))

def estimated_value(car) -> int:
    """Оценка для гаража: учитывает известные дефекты и вложения частично."""
    base = car.base_market_value
    cond = avg_condition(car) / 100
    mult = 0.55 + cond * 0.5
    val = base * mult
    from .texts import HIDDEN_DEFECTS
    known = set(car.known_defects or []) | set(car.visible_defects or [])
    for d in known:
        if d in HIDDEN_DEFECTS and d not in (car.resolved_defects or []):
            val -= HIDDEN_DEFECTS[d]["cost"] * 0.9
    # вложения возвращаются частично (60%) через состояние, но визуал добавляет
    val += car.visual_appeal * 2
    if car.photo_done:
        val += 80
    return max(400, int(val))

def market_range(car) -> tuple[int, int]:
    """Диапазон рыночной стоимости с погрешностью для карточки (не раскрывает правду)."""
    est = real_value(car)
    # погрешность ±8%, смещённая вверх для интриги
    low = int(est * 0.90)
    high = int(est * 1.10)
    return low, high

def liquidity_label(score: int) -> str:
    if score >= 70:
        return "Высокая"
    if score >= 40:
        return "Средняя"
    return "Низкая"

def risk_hint(car) -> str:
    risk = (car.legal_risk_score + car.accident_risk_score + car.mileage_risk_score) / 3
    hidden = len([d for d in (car.hidden_defects or []) if d not in (car.resolved_defects or [])])
    score = risk + hidden * 8
    if score < 25:
        return "low"
    if score < 55:
        return "medium"
    return "high"

def add_xp(user, amount: int) -> bool:
    """Начисляет опыт, возвращает True если уровень вырос."""
    from .texts import LEVELS, level_for_xp
    user.experience += amount
    new_level = level_for_xp(user.experience)["level"]
    if new_level > user.level:
        user.level = new_level
        return True
    return False

def garage_limit(level: int) -> int:
    from .texts import LEVELS
    for lv in LEVELS:
        if lv["level"] == level:
            return lv["garage"]
    return 1
