def test_create_order(client):
    response = client.post("/api/payments/create-order?amount=3500.0&customer_name=Rahul&customer_email=rahul@example.com")
    assert response.status_code == 200
    data = response.json()
    assert "order" in data
    assert data["customer"]["name"] == "Rahul"


def test_list_and_get_payments(client):
    # Create order first
    client.post("/api/payments/create-order?amount=2000.0&customer_name=Priya&customer_email=priya@example.com")
    
    response = client.get("/api/payments")
    assert response.status_code == 200
    payments = response.json()
    assert isinstance(payments, list)
