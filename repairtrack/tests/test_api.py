def test_health(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_create_and_read_order(client, order_payload):
    created = client.post("/orders", json=order_payload)
    assert created.status_code == 201
    body = created.json()
    assert body["receipt_number"] == "RT-000001"
    assert body["status"] == "accepted"
    assert len(body["retrieval_code"]) >= 20

    order = client.get(f"/orders/{body['id']}").json()
    assert order["serial_number"] == order_payload["serial_number"]
    assert order["accessories"] == order_payload["accessories"]
    assert [e["new_status"] for e in order["events"]] == ["accepted"]
    # Код получения и его хеш не возвращаются в карточке заказа.
    assert "retrieval_code" not in order
    assert "retrieval_code_hash" not in order


def test_create_order_rejects_invalid_input(client, order_payload):
    order_payload["serial_number"] = ""
    response = client.post("/orders", json=order_payload)
    assert response.status_code == 422
    assert client.get("/orders/1").status_code == 404


def test_public_status_with_valid_code(client, order_payload):
    created = client.post("/orders", json=order_payload).json()
    response = client.post(
        "/public/status",
        json={
            "receipt_number": created["receipt_number"],
            "retrieval_code": created["retrieval_code"],
        },
    )
    assert response.status_code == 200
    assert response.json() == {"status": "accepted", "total_cost": None}


def test_public_status_same_refusal_for_wrong_code_and_unknown_receipt(client, order_payload):
    created = client.post("/orders", json=order_payload).json()
    wrong_code = client.post(
        "/public/status",
        json={"receipt_number": created["receipt_number"], "retrieval_code": "wrong"},
    )
    unknown_receipt = client.post(
        "/public/status",
        json={"receipt_number": "RT-999999", "retrieval_code": "wrong"},
    )
    assert wrong_code.status_code == unknown_receipt.status_code == 404
    assert wrong_code.json() == unknown_receipt.json()
