from sqlalchemy import BigInteger, Boolean, DateTime, ForeignKey, Integer, String, Text, JSON, func
from sqlalchemy.orm import Mapped, mapped_column
from .database import Base
from datetime import datetime

class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    telegram_id: Mapped[int] = mapped_column(BigInteger, unique=True, nullable=False, index=True)
    username: Mapped[str | None] = mapped_column(String(64), nullable=True)
    first_name: Mapped[str | None] = mapped_column(String(128), nullable=True)
    photo_url: Mapped[str | None] = mapped_column(String(512), nullable=True)
    balance: Mapped[int] = mapped_column(Integer, default=5000)
    reputation: Mapped[int] = mapped_column(Integer, default=10)
    level: Mapped[int] = mapped_column(Integer, default=1)
    experience: Mapped[int] = mapped_column(Integer, default=0)
    current_game_day: Mapped[int] = mapped_column(Integer, default=1)
    market_refreshes_today: Mapped[int] = mapped_column(Integer, default=0)
    rating_opt_out: Mapped[bool] = mapped_column(Boolean, default=False)
    streak_days: Mapped[int] = mapped_column(Integer, default=1)
    last_login_day: Mapped[int] = mapped_column(Integer, default=1)
    total_profit: Mapped[int] = mapped_column(Integer, default=0)
    deals_count: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())

class Car(Base):
    __tablename__ = "cars"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    owner_user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True, index=True)
    status: Mapped[str] = mapped_column(String(16), default="MARKET", index=True)
    brand: Mapped[str] = mapped_column(String(64))
    model: Mapped[str] = mapped_column(String(64))
    generation: Mapped[str | None] = mapped_column(String(64), nullable=True)
    year: Mapped[int] = mapped_column(Integer)
    mileage: Mapped[int] = mapped_column(Integer)
    engine_type: Mapped[str] = mapped_column(String(32))
    engine_volume: Mapped[float] = mapped_column()
    power_hp: Mapped[int] = mapped_column(Integer, default=100)
    transmission: Mapped[str] = mapped_column(String(32))
    drive_type: Mapped[str] = mapped_column(String(16))
    color: Mapped[str] = mapped_column(String(32))
    base_market_value: Mapped[int] = mapped_column(Integer)
    seller_price: Mapped[int] = mapped_column(Integer)
    minimum_seller_price: Mapped[int] = mapped_column(Integer)
    current_price: Mapped[int] = mapped_column(Integer)
    purchase_price: Mapped[int | None] = mapped_column(Integer, nullable=True)
    sale_price: Mapped[int | None] = mapped_column(Integer, nullable=True)
    invested: Mapped[int] = mapped_column(Integer, default=0)
    liquidity_score: Mapped[int] = mapped_column(Integer, default=50)
    body_condition: Mapped[int] = mapped_column(Integer, default=70)
    engine_condition: Mapped[int] = mapped_column(Integer, default=70)
    transmission_condition: Mapped[int] = mapped_column(Integer, default=70)
    suspension_condition: Mapped[int] = mapped_column(Integer, default=70)
    interior_condition: Mapped[int] = mapped_column(Integer, default=70)
    visual_appeal: Mapped[int] = mapped_column(Integer, default=50)
    legal_risk_score: Mapped[int] = mapped_column(Integer, default=10)
    accident_risk_score: Mapped[int] = mapped_column(Integer, default=10)
    mileage_risk_score: Mapped[int] = mapped_column(Integer, default=10)
    seller_personality: Mapped[str] = mapped_column(String(32), default="adequate")
    urgency_score: Mapped[int] = mapped_column(Integer, default=50)
    owners_count: Mapped[int] = mapped_column(Integer, default=2)
    visible_defects: Mapped[list] = mapped_column(JSON, default=list)
    hidden_defects: Mapped[list] = mapped_column(JSON, default=list)
    known_defects: Mapped[list] = mapped_column(JSON, default=list)
    resolved_defects: Mapped[list] = mapped_column(JSON, default=list)
    description: Mapped[str] = mapped_column(Text, default="")
    image_seed: Mapped[int] = mapped_column(Integer, default=1)
    market_day: Mapped[int] = mapped_column(Integer, default=1)
    owned_since_day: Mapped[int | None] = mapped_column(Integer, nullable=True)
    photo_done: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())

class CarInspection(Base):
    __tablename__ = "car_inspections"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    car_id: Mapped[int] = mapped_column(ForeignKey("cars.id"), index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    inspection_type: Mapped[str] = mapped_column(String(32))
    price: Mapped[int] = mapped_column(Integer)
    result_text: Mapped[str] = mapped_column(Text, default="")
    revealed_defects: Mapped[list] = mapped_column(JSON, default=list)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

class CarRepair(Base):
    __tablename__ = "car_repairs"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    car_id: Mapped[int] = mapped_column(ForeignKey("cars.id"), index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    repair_type: Mapped[str] = mapped_column(String(32))
    cost: Mapped[int] = mapped_column(Integer)
    result_text: Mapped[str] = mapped_column(Text, default="")
    resolved_defects: Mapped[list] = mapped_column(JSON, default=list)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

class Negotiation(Base):
    __tablename__ = "negotiations"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    car_id: Mapped[int] = mapped_column(ForeignKey("cars.id"))
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    side: Mapped[str] = mapped_column(String(16))
    initial_price: Mapped[int] = mapped_column(Integer)
    offered_price: Mapped[int] = mapped_column(Integer)
    result: Mapped[str] = mapped_column(String(16))
    dialogue: Mapped[list] = mapped_column(JSON, default=list)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

class Listing(Base):
    __tablename__ = "listings"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    car_id: Mapped[int] = mapped_column(ForeignKey("cars.id"), unique=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    listing_price: Mapped[int] = mapped_column(Integer)
    listing_style: Mapped[str] = mapped_column(String(32))
    promotion_level: Mapped[int] = mapped_column(Integer, default=0)
    disclosed_defects: Mapped[list] = mapped_column(JSON, default=list)
    status: Mapped[str] = mapped_column(String(16), default="ACTIVE")
    listed_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    sold_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

class Offer(Base):
    __tablename__ = "offers"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    listing_id: Mapped[int] = mapped_column(ForeignKey("listings.id"), index=True)
    buyer_name: Mapped[str] = mapped_column(String(64))
    buyer_type: Mapped[str] = mapped_column(String(32))
    offered_price: Mapped[int] = mapped_column(Integer)
    status: Mapped[str] = mapped_column(String(16), default="PENDING")
    buyer_traits: Mapped[dict] = mapped_column(JSON, default=dict)
    message: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())

class Transaction(Base):
    __tablename__ = "transactions"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    type: Mapped[str] = mapped_column(String(32))
    amount: Mapped[int] = mapped_column(Integer)
    balance_after: Mapped[int] = mapped_column(Integer)
    meta: Mapped[dict] = mapped_column(JSON, default=dict)
    idempotency_key: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

class GameEvent(Base):
    __tablename__ = "game_events"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    event_type: Mapped[str] = mapped_column(String(32))
    title: Mapped[str] = mapped_column(String(128))
    description: Mapped[str] = mapped_column(Text, default="")
    payload: Mapped[dict] = mapped_column(JSON, default=dict)
    resolved: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

class DailyTask(Base):
    __tablename__ = "daily_tasks"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    task_type: Mapped[str] = mapped_column(String(32))
    title: Mapped[str] = mapped_column(String(128))
    target_value: Mapped[int] = mapped_column(Integer, default=1)
    progress_value: Mapped[int] = mapped_column(Integer, default=0)
    reward_type: Mapped[str] = mapped_column(String(16), default="xp")
    reward_value: Mapped[int] = mapped_column(Integer, default=100)
    status: Mapped[str] = mapped_column(String(16), default="ACTIVE")
    game_day: Mapped[int] = mapped_column(Integer, default=1)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
