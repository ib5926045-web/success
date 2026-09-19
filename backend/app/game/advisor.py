import random
from .texts import ADVISOR_TIPS
from .pricing import real_value, estimated_value

def rule_tips(car=None, user=None) -> list[str]:
    tips: list[str] = []
    if car is not None:
        rv = real_value(car)
        if car.status == "MARKET":
            if car.current_price < rv * 0.95:
                tips.append(f"Цена {car.current_price:,} BYN ниже честной оценки (~{rv:,} BYN). Проверьте кузов и документы — возможно, в машине подвох.".replace(",", " "))
            elif car.current_price > rv * 1.12:
                tips.append(f"Цена {car.current_price:,} BYN выше честной оценки (~{rv:,} BYN). Торгуйтесь или ищите другой вариант.".replace(",", " "))
            else:
                tips.append("Цена близка к честной оценке. Решение зависит от скрытых дефектов — начните с осмотра кузова за 30 BYN.")
            if car.liquidity_score < 40:
                tips.append("Низкая ликвидность: такую машину можно продавать долго. Требуйте скидку за риск.")
        else:
            est = estimated_value(car)
            total = (car.purchase_price or 0) + (car.invested or 0)
            tips.append(f"Вложено {total:,} BYN, оценка сейчас ~{est:,} BYN.".replace(",", " "))
            if not car.photo_done:
                tips.append("Сделайте фото перед продажей: это бесплатно и ускоряет сделку.")
            if car.visual_appeal < 60:
                tips.append("После полировки и химчистки вероятность быстрой продажи вырастет.")
    tips.append(random.choice(ADVISOR_TIPS))
    return tips[:4]
