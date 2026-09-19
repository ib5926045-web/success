"""Сквозной игровой цикл: вход -> рынок -> осмотр -> торг -> покупка -> мойка/ремонт -> продажа."""
import uuid

def _auth(client):
    r = client.post("/api/auth/telegram", json={"initData": "dev"})
    assert r.status_code == 200, r.text
    return {"Authorization": f"Bearer {r.json()['token']}"}

def test_full_cycle(client):
    h = _auth(client)
    me = client.get("/api/me", headers=h).json()
    assert me["balance"] == 5000

    market = client.get("/api/market", headers=h).json()
    assert len(market["cars"]) >= 5
    car_id = min(market["cars"], key=lambda c: c["price"])["id"]

    det = client.get(f"/api/cars/{car_id}", headers=h).json()
    assert det["price"] > 0

    insp = client.post(f"/api/cars/{car_id}/inspect", headers=h, json={"inspection_type": "body"}).json()
    assert insp["balance"] == 5000 - 30, insp

    neg = client.post(f"/api/cars/{car_id}/negotiate-seller", headers=h, json={"discount_percent": 5}).json()
    assert neg["result"] in ("ACCEPTED", "COUNTERED", "DECLINED")

    # покупка с idempotency
    key = str(uuid.uuid4())
    r = client.post(f"/api/cars/{car_id}/buy", headers={**h, "X-Idempotency-Key": key})
    assert r.status_code == 200, r.text
    purchase = r.json()["purchase_price"]

    garage = client.get("/api/garage", headers=h).json()
    assert len(garage) == 1

    rep = client.post(f"/api/garage/{car_id}/repair", headers=h, json={"repair_type": "wash"}).json()
    assert rep["cost"] == 20

    prep = client.post(f"/api/garage/{car_id}/prepare", headers=h, json={"action": "photo"}).json()
    assert prep["ok"] is True

    lst = client.post(f"/api/garage/{car_id}/list", headers=h,
                      json={"listing_price": purchase + 800, "listing_style": "honest"}).json()
    assert lst["offers_count"] >= 1
    offer_id = lst["offers"][0]["id"]
    listing_id = lst["listing_id"]

    acc = client.post(f"/api/listings/{listing_id}/offers/{offer_id}/accept",
                      headers={**h, "X-Idempotency-Key": str(uuid.uuid4())}).json()
    assert acc["ok"] is True
    assert "profit" in acc and "balance" in acc

    hist = client.get("/api/deals/history", headers=h).json()
    assert any(t["type"] == "SALE" for t in hist)

def test_cannot_buy_twice(client):
    h = _auth(client)
    cars = client.get("/api/market", headers=h).json()["cars"]
    car_id = min(cars, key=lambda c: c["price"])["id"]
    r1 = client.post(f"/api/cars/{car_id}/buy", headers={**h, "X-Idempotency-Key": "k1"})
    assert r1.status_code == 200
    r2 = client.post(f"/api/cars/{car_id}/buy", headers={**h, "X-Idempotency-Key": "k2"})
    assert r2.status_code == 400

def test_cannot_overspend(client):
    h = _auth(client)
    cars = client.get("/api/market", headers=h).json()["cars"]
    # покупаем первую, затем пытаемся купить вторую дороже остатка или при полном гараже (L1 лимит=1)
    by_price = sorted(cars, key=lambda c: c["price"])
    c1 = by_price[0]["id"]
    assert client.post(f"/api/cars/{c1}/buy", headers=h).status_code == 200
    c2 = by_price[1]["id"]
    r = client.post(f"/api/cars/{c2}/buy", headers=h)
    assert r.status_code == 400  # гараж заполнен на 1 уровне
