"""Seed: проверяет соединение с БД и создаёт таблицы.
Рыночные авто генерируются персонально под каждого игрока при первом GET /api/market,
поэтому глобальный сид рынка не нужен. Здесь — только служебная проверка."""
from .database import engine
from .models import Base

def main():
    Base.metadata.create_all(bind=engine)
    print("DB ready. Market cars are generated per-user on first /api/market call.")

if __name__ == "__main__":
    main()
