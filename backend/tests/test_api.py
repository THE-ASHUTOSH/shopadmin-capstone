def add(client, **kw):
    product = {"name": "Mouse", "sku": "MS-1", "category": "Electronics", "price": 499, "stock": 20}
    product.update(kw)
    return client.post("/api/products", json=product)


def test_health(client):
    assert client.get("/health").json() == {"status": "ok"}
    assert client.get("/ready").status_code == 200


def test_create_and_get(client):
    res = add(client)
    assert res.status_code == 201
    pid = res.json()["id"]
    assert client.get(f"/api/products/{pid}").json()["sku"] == "MS-1"


def test_bad_input(client):
    assert add(client, price=-5).status_code == 422
    assert add(client, name="").status_code == 422


def test_duplicate_sku(client):
    add(client)
    assert add(client, name="Other").status_code == 409


def test_list_and_filter(client):
    add(client)
    add(client, name="T-shirt", sku="TS-1", category="Clothing")
    assert len(client.get("/api/products").json()) == 2
    assert [p["sku"] for p in client.get("/api/products?category=Clothing").json()] == ["TS-1"]
    assert [p["sku"] for p in client.get("/api/products?q=mou").json()] == ["MS-1"]


def test_update(client):
    pid = add(client).json()["id"]
    res = client.put(f"/api/products/{pid}", json={"stock": 3})
    assert res.json()["stock"] == 3
    assert res.json()["name"] == "Mouse"


def test_delete(client):
    pid = add(client).json()["id"]
    assert client.delete(f"/api/products/{pid}").status_code == 204
    assert client.get(f"/api/products/{pid}").status_code == 404
    assert client.delete(f"/api/products/{pid}").status_code == 404


def test_stats(client):
    add(client, price=100, stock=5)
    add(client, sku="KB-1", price=200, stock=10, category="Accessories")
    assert client.get("/api/products/stats").json() == {
        "total": 2, "low_stock": 1, "categories": 2, "inventory_value": 2500.0
    }


def test_metrics(client):
    client.get("/health")
    assert "http_requests_total" in client.get("/metrics").text
