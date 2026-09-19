from pydantic import BaseModel, Field
from typing import Any

class AuthRequest(BaseModel):
    initData: str = Field(default="", description="Telegram WebApp initData, либо 'dev' в dev-режиме")

class AuthResponse(BaseModel):
    token: str
    is_new: bool
    user: "MeResponse"

class MeResponse(BaseModel):
    id: int
    telegram_id: int
    username: str | None = None
    first_name: str | None = None
    photo_url: str | None = None
    balance: int
    reputation: int
    level: int
    experience: int
    current_game_day: int
    rating_opt_out: bool
    streak_days: int
    total_profit: int
    deals_count: int
    garage_limit: int
    level_name: str
    next_level_xp: int | None
    season_goal: int

class MarketCarCard(BaseModel):
    id: int
    brand: str
    model: str
    generation: str | None = None
    year: int
    mileage: int
    engine_type: str
    engine_volume: float
    transmission: str
    price: int
    liquidity: str
    liquidity_score: int
    urgent: bool
    risk_hint: str  # low|medium|high
    image_seed: int
    color: str
    short_description: str

class MarketResponse(BaseModel):
    game_day: int
    cars: list[MarketCarCard]
    refresh_cost: int
    free_refresh_available: bool

class CarDetail(BaseModel):
    id: int
    brand: str
    model: str
    generation: str | None
    year: int
    mileage: int
    engine_type: str
    engine_volume: float
    power_hp: int
    transmission: str
    drive_type: str
    color: str
    status: str
    price: int
    seller_price: int
    minimum_seller_price: int | None = None
    market_value_low: int
    market_value_high: int
    liquidity: str
    liquidity_score: int
    urgent: bool
    description: str
    visible_defects: list[str]
    known_defects: list[str]
    inspections_done: list[str]
    conditions: dict[str, int]
    seller_personality: str
    seller_personality_label: str
    owners_count: int
    image_seed: int
    purchase_price: int | None = None
    invested: int = 0
    photo_done: bool = False
    owned_days: int = 0

class InspectRequest(BaseModel):
    inspection_type: str  # body|docs|diagnostics|testdrive|full

class InspectResponse(BaseModel):
    result_text: str
    revealed: list[str]
    known_defects: list[str]
    balance: int
    price: int

class NegotiateRequest(BaseModel):
    discount_percent: float | None = None
    offer_price: int | None = None

class NegotiateResponse(BaseModel):
    result: str
    new_price: int
    message: str
    balance: int

class BuyResponse(BaseModel):
    car_id: int
    purchase_price: int
    balance: int
    experience: int
    level: int

class GarageCar(BaseModel):
    id: int
    brand: str
    model: str
    year: int
    mileage: int
    image_seed: int
    status: str
    purchase_price: int | None
    invested: int
    estimated_value: int
    potential_profit: int
    conditions: dict[str, int]
    known_defects: list[str]
    readiness: int
    owned_days: int
    listing_id: int | None = None

class RepairRequest(BaseModel):
    repair_type: str

class RepairResponse(BaseModel):
    result_text: str
    cost: int
    balance: int
    conditions: dict[str, int]
    resolved: list[str]

class PrepareRequest(BaseModel):
    action: str  # photo|ad

class ListRequest(BaseModel):
    listing_price: int
    listing_style: str = "honest"
    promotion_level: int = 0
    disclosed_defects: list[str] = []

class OfferOut(BaseModel):
    id: int
    buyer_name: str
    buyer_type: str
    offered_price: int
    status: str
    message: str

class ListingOut(BaseModel):
    id: int
    car_id: int
    car_title: str
    listing_price: int
    listing_style: str
    status: str
    offers: list[OfferOut]

class CounterRequest(BaseModel):
    price: int

class TxnOut(BaseModel):
    id: int
    type: str
    amount: int
    balance_after: int
    meta: dict[str, Any]
    created_at: str

class EventOut(BaseModel):
    id: int
    event_type: str
    title: str
    description: str
    resolved: bool
    payload: dict[str, Any]

class TaskOut(BaseModel):
    id: int
    task_type: str
    title: str
    target_value: int
    progress_value: int
    reward_type: str
    reward_value: int
    status: str

class LeaderRow(BaseModel):
    rank: int
    name: str
    level: int
    capital: int
    profit: int
    reputation: int
    is_me: bool = False

class AdvisorResponse(BaseModel):
    tips: list[str]
