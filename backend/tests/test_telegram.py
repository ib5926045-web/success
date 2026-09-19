import hashlib
import hmac
import time
import urllib.parse
import pytest
from app.security import validate_telegram_init_data

def _make_init_data(bot_token: str, user_id: int = 123):
    params = {
        "auth_date": str(int(time.time())),
        "query_id": "AAE",
        "user": '{"id": %d, "first_name": "Test"}' % user_id,
    }
    dcs = "\n".join(f"{k}={params[k]}" for k in sorted(params))
    secret = hmac.new(b"WebAppData", bot_token.encode(), hashlib.sha256).digest()
    h = hmac.new(secret, dcs.encode(), hashlib.sha256).hexdigest()
    params["hash"] = h
    return urllib.parse.urlencode(params)

def test_valid_signature():
    tok = "123:ABC"
    data = _make_init_data(tok)
    res = validate_telegram_init_data(data, tok)
    assert res["user"]["id"] == 123

def test_tampered_fails():
    tok = "123:ABC"
    data = _make_init_data(tok) + "&extra=1"
    # подмена: меняем user без пересчёта hash
    bad = data.replace("Test", "Hacker")
    with pytest.raises(ValueError):
        validate_telegram_init_data(bad, tok)
