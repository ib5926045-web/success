def _auth(client):
    r = client.post("/api/auth/telegram", json={"initData": "dev"})
    return {"Authorization": f"Bearer {r.json()['token']}"}

def _cheapest(client, h):
    cars = client.get("/api/market", headers=h).json()["cars"]
    return min(cars, key=lambda c: c["price"])["id"]

def test_repair_locked_by_level(client):
    h = _auth(client)
    car_id = _cheapest(client, h)
    assert client.post(f"/api/cars/{car_id}/buy", headers=h).status_code == 200
    r = client.post(f"/api/garage/{car_id}/repair", headers=h, json={"repair_type": "gearbox"})
    assert r.status_code == 403  # 4 уровень нужен

def test_repair_improves_and_costs(client):
    h = _auth(client)
    car_id = _cheapest(client, h)
    client.post(f"/api/cars/{car_id}/buy", headers=h)
    before = client.get("/api/me", headers=h).json()["balance"]
    r = client.post(f"/api/garage/{car_id}/repair", headers=h, json={"repair_type": "wash"})
    assert r.status_code == 200
    after = client.get("/api/me", headers=h).json()["balance"]
    assert after == before - 20

def test_counter_offer_flow(client):
    h = _auth(client)
    car_id = _cheapest(client, h)
    buy = client.post(f"/api/cars/{car_id}/buy", headers=h).json()
    assert "purchase_price" in buy, buy
    lst = client.post(f"/api/garage/{car_id}/list", headers=h,
                      json={"listing_price": buy["purchase_price"] + 500, "listing_style": "honest"}).json()
    offer = lst["offers"][-1]
    r = client.post(f"/api/listings/{lst['listing_id']}/offers/{offer['id']}/counter", headers=h,
                    json={"price": offer["offered_price"] + 100}).json()
    assert r["result"] in ("ACCEPTED", "COUNTERED")
