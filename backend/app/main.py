import time
from collections import defaultdict
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from .config import get_settings
from .database import engine
from .models import Base
from .routers import auth, me, market, cars, garage, listings, deals, events, tasks, leaderboard, advisor, settings as settings_router

settings = get_settings()
app = FastAPI(title="Перекуп Симулятор API", version="1.0.0",
              description="Игровая экономика: рынок, торг, гараж, продажа. Все деньги считаются только на сервере.")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Простой in-memory rate limit (для production — Redis)
_hits: dict[str, list[float]] = defaultdict(list)
LIMITS = {"/api/auth": (20, 60), "/api/cars": (60, 60), "/api/market": (30, 60)}

@app.middleware("http")
async def ratelimit(request: Request, call_next):
    path = request.url.path
    for prefix, (limit, window) in LIMITS.items():
        if path.startswith(prefix):
            key = f"{prefix}:{request.client.host if request.client else '?'}"
            now = time.time()
            _hits[key] = [t for t in _hits[key] if now - t < window]
            if len(_hits[key]) >= limit:
                return JSONResponse({"detail": "Слишком много запросов. Подождите минуту."}, status_code=429)
            _hits[key].append(now)
    return await call_next(request)

@app.get("/api/health")
def health():
    return {"ok": True, "game": "perekup-simulator"}

app.include_router(auth.router, prefix="/api")
app.include_router(me.router, prefix="/api")
app.include_router(market.router, prefix="/api")
app.include_router(cars.router, prefix="/api")
app.include_router(garage.router, prefix="/api")
app.include_router(listings.router, prefix="/api")
app.include_router(deals.router, prefix="/api")
app.include_router(events.router, prefix="/api")
app.include_router(tasks.router, prefix="/api")
app.include_router(leaderboard.router, prefix="/api")
app.include_router(advisor.router, prefix="/api")
app.include_router(settings_router.router, prefix="/api")
