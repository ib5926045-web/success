import hashlib
import hmac
import json
import time
from urllib.parse import parse_qsl
import jwt
from .config import get_settings

settings = get_settings()

def validate_telegram_init_data(init_data: str, bot_token: str, max_age_sec: int = 86400) -> dict:
    """Проверка подписи initData по официальной схеме Telegram.
    Raises ValueError если подпись неверна."""
    if not init_data:
        raise ValueError("empty initData")
    pairs = dict(parse_qsl(init_data, keep_blank_values=True))
    received_hash = pairs.pop("hash", None)
    if not received_hash:
        raise ValueError("missing hash")
    data_check_string = "\n".join(f"{k}={pairs[k]}" for k in sorted(pairs.keys()))
    secret_key = hmac.new(b"WebAppData", bot_token.encode(), hashlib.sha256).digest()
    calc_hash = hmac.new(secret_key, data_check_string.encode(), hashlib.sha256).hexdigest()
    if not hmac.compare_digest(calc_hash, received_hash):
        raise ValueError("invalid signature")
    # проверка давности
    try:
        auth_date = int(pairs.get("auth_date", "0"))
    except ValueError:
        raise ValueError("invalid auth_date")
    if auth_date and (time.time() - auth_date > max_age_sec):
        raise ValueError("initData expired")
    user = {}
    if "user" in pairs:
        try:
            user = json.loads(pairs["user"])
        except Exception:
            raise ValueError("invalid user json")
    return {"params": pairs, "user": user}

def create_access_token(user_id: int) -> str:
    payload = {"sub": str(user_id), "iat": int(time.time()), "exp": int(time.time()) + 60 * 60 * 24 * 30}
    return jwt.encode(payload, settings.SECRET_KEY, algorithm="HS256")

def decode_access_token(token: str) -> int:
    data = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
    return int(data["sub"])
