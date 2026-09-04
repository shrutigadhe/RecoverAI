import json


def test_razorpay_failed_payment_webhook(client):
    payload = {
        "event": "payment.failed",
        "payload": {
            "payment": {
                "entity": {
                    "id": "pay_test_failed_999",
                    "order_id": "order_test_999",
                    "amount": 350000,
                    "currency": "INR",
                    "method": "upi",
                    "error_description": "Temporary bank server error",
                    "email": "rahul@test.com",
                    "contact": "Rahul Sharma"
                }
            }
        }
    }

    response = client.post(
        "/api/webhook/razorpay",
        content=json.dumps(payload),
        headers={"X-Razorpay-Signature": "demo_signature", "Content-Type": "application/json"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert "recovery_case_id" in data
