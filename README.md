# 🚗 Перекуп Симулятор — Telegram Mini App

Русскоязычная экономическая игра про покупку, проверку, ремонт и перепродажу подержанных авто.
Старт: **5 000 BYN**. Цель сезона: **50 000 BYN**. Валюта виртуальная, реальных денег/ставок/казино нет.

## Дерево проекта

```
.
├── frontend/                 # React + TS + Vite + Tailwind + Zustand + Telegram SDK
│   ├── Dockerfile
│   ├── src/
│   │   ├── App.tsx           # роутинг + Telegram init + auth
│   │   ├── telegram.ts       # WebApp API: ready/expand/haptic/back/mainbutton
│   │   ├── api.ts            # REST-клиент
│   │   ├── store.ts          # Zustand: профиль игрока
│   │   ├── components/       # TopBar, BottomNav, CarVisual, ConditionBar
│   │   └── pages/            # Market, CarDetails, Garage, GarageCar, Deals, Leaderboard, Profile
├── backend/                  # FastAPI + SQLAlchemy 2.0 + Alembic + PostgreSQL
│   ├── Dockerfile
│   ├── alembic/              # миграции (0001_initial)
│   ├── app/
│   │   ├── main.py           # FastAPI + CORS + rate limit
│   │   ├── security.py       # проверка Telegram initData (HMAC) + JWT
│   │   ├── game/             # pricing, negotiation, market, repairs, offers, advisor, texts
│   │   ├── routers/          # auth, me, market, cars, garage, listings, deals, events, tasks, leaderboard, advisor, settings
│   │   └── seed.py
│   └── tests/                # pytest: цены, торг, покупка, ремонт, продажа, initData, сквозной цикл
├── nginx/nginx.conf          # reverse proxy: / → frontend, /api → backend
├── docs/
│   ├── DEPLOY_UBUNTU_24_04.md
│   └── TELEGRAM_SETUP.md
├── docker-compose.yml
├── .env.example
└── README.md
```

## Архитектура

- **Frontend** — мобильная тёмная тема, 5 вкладок (Рынок/Гараж/Сделки/Рейтинг/Профиль). Telegram SDK: `ready/expand`, `initData`, тема, `BackButton`, `HapticFeedback`, `MainButton` на покупке.
- **Backend** — REST API (`/api/*`, Swagger на `/docs`). Авторизация: проверка подписи `initData` токеном бота → JWT на 30 дней. **Все деньги, цены, скидки, дефекты считаются только на сервере.**
- **БД** — PostgreSQL в Docker, SQLite для локальной разработки. Операции покупки/продажи атомарны + `Idempotency-Key`.
- **Режимы**: `TELEGRAM_DEV_MODE=true` — тестовый вход (`initData="dev"`); `false` — только реальный Telegram.

## Быстрый запуск через Docker (одна команда)

```bash
cp .env.example .env
nano .env   # TELEGRAM_DEV_MODE=true для локалки
docker compose up -d --build
curl http://localhost/api/health
```

- Игра: http://localhost/
- API docs: http://localhost/docs (через nginx) или http://localhost:8000/docs напрямую
- Остановка: `docker compose down` · Логи: `docker compose logs -f backend`

## Локальная разработка (без Docker)

Backend:

```bash
cd backend
python3.12 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
export DATABASE_URL="sqlite:///./dev.db" TELEGRAM_DEV_MODE=true SECRET_KEY=dev_secret_key_32_chars_min__
alembic upgrade head
python -m app.seed
uvicorn app.main:app --reload --port 8000
```

Frontend:

```bash
cd frontend
npm install
echo "VITE_API_URL=http://localhost:8000/api" > .env.local
npm run dev   # http://localhost:5173
```

Тесты:

```bash
cd backend
python -m pytest -q
```

## Игровой цикл (как играть)

1. **Рынок** — 6 объявлений на день. «След. день» бесплатно, обновление в тот же день — 50 BYN.
2. **Карточка авто** — диапазон рыночной цены, проверки (кузов 30 / документы 40 / диагностика 50 / тест-драйв 30 / комплекс 120 BYN).
3. **Торг** — −3/−5/−8% или своя цена. Зависит от характера продавца, срочности, репутации и найденных дефектов.
4. **Покупка** — деньги списываются на сервере, авто едет в гараж (+120 XP).
5. **Гараж** — мойка, химчистка, ремонты (уровень открывает новые), фото, объявление.
6. **Продажа** — цена/стиль/продвижение → 1–4 предложения покупателей → принять/встречная/отказ.
7. **Профиль** — капитал vs цель 50 000, задания дня, события, «поделиться результатом».

Уровни: 1 Новичок (1 место) → 2 (1 000 XP, 2 места) → 3 (3 000 XP, 3 места) → 4 (8 000 XP, 5 мест) → 5 Автодилер (20 000 XP, 8 мест).

## API (кратко)

| Метод | Путь | Описание |
|---|---|---|
| POST | /api/auth/telegram | вход по initData → JWT |
| GET | /api/me, /api/me/dashboard | профиль, капитал |
| GET/POST | /api/market, /api/market/refresh | рынок, смена дня |
| GET | /api/cars/{id} | карточка (без скрытых дефектов) |
| POST | /api/cars/{id}/inspect | проверка (30–120 BYN) |
| POST | /api/cars/{id}/negotiate-seller | торг |
| POST | /api/cars/{id}/buy | покупка (Idempotency-Key) |
| GET/POST | /api/garage… | гараж, ремонт, подготовка, продажа |
| POST | /api/listings/{lid}/offers/{oid}/accept·decline·counter | сделки |
| GET | /api/deals/history | история операций |
| GET | /api/events, /api/tasks, /api/leaderboard, /api/advisor | события, задания, рейтинг, советы |
| PATCH | /api/settings | приватность рейтинга |

Полная спецификация: `/docs` (OpenAPI/Swagger).

## Безопасность

- Подпись `initData` проверяется HMAC-SHA256 (`WebAppData` + токен бота), `auth_date` не старше 24 ч.
- Клиентские цены/баланс игнорируются; баланс не уходит в минус (проверка + транзакции).
- `Idempotency-Key` на покупку/продажу, rate limit на auth/market/cars, CORS по allowlist.
- Секреты только в `.env` (см. `.env.example`), токен бота и `DATABASE_URL` не коммитятся.

## Деплой

- **Ubuntu 24.04 + Docker + HTTPS**: см. [docs/DEPLOY_UBUNTU_24_04.md](docs/DEPLOY_UBUNTU_24_04.md)
- **BotFather + Mini App URL**: см. [docs/TELEGRAM_SETUP.md](docs/TELEGRAM_SETUP.md)

## Дисклеймер

Учебная игра. Все автомобили сгенерированы из шаблонов, совпадения случайны. Реальные VIN/номера/объявления не используются.
