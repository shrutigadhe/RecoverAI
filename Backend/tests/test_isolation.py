from app.models import Customer, Payment, RecoveryCase
from app.services.payment_service import PaymentService


def test_merchant_data_isolation(client, db_session):
    # 1. Register Merchant A
    res_a = client.post("/api/auth/register", json={
        "name": "Merchant Alpha",
        "email": "alpha@merchant.com",
        "password": "Password123!"
    })
    token_a = res_a.json()["access_token"]
    merchant_a_id = res_a.json()["merchant"]["id"]

    # 2. Register Merchant B
    res_b = client.post("/api/auth/register", json={
        "name": "Merchant Beta",
        "email": "beta@merchant.com",
        "password": "Password123!"
    })
    token_b = res_b.json()["access_token"]

    # 3. Create customer and payment for Merchant A
    customer_a = PaymentService.get_or_create_customer(
        db=db_session,
        name="Customer A",
        email="cust_a@example.com",
        merchant_id=merchant_a_id
    )

    payment_a = Payment(
        customer_id=customer_a.id,
        amount=3500.0,
        currency="INR",
        status="QUEUED",
        payment_method="UPI",
        failure_reason="Temporary failure"
    )
    db_session.add(payment_a)
    db_session.commit()

    case_a = RecoveryCase(
        payment_id=payment_a.id,
        status="QUEUED"
    )
    db_session.add(case_a)
    db_session.commit()

    # 4. Merchant A fetches their own payment & recovery case -> 200 OK
    res_a_payment = client.get(
        f"/api/payments/{payment_a.id}",
        headers={"Authorization": f"Bearer {token_a}"}
    )
    assert res_a_payment.status_code == 200

    res_a_case = client.get(
        f"/api/recovery/cases/{case_a.id}",
        headers={"Authorization": f"Bearer {token_a}"}
    )
    assert res_a_case.status_code == 200

    # 5. Merchant B attempts to fetch Merchant A's payment & case -> 404 Not Found (Data Isolation)
    res_b_payment = client.get(
        f"/api/payments/{payment_a.id}",
        headers={"Authorization": f"Bearer {token_b}"}
    )
    assert res_b_payment.status_code == 404

    res_b_case = client.get(
        f"/api/recovery/cases/{case_a.id}",
        headers={"Authorization": f"Bearer {token_b}"}
    )
    assert res_b_case.status_code == 404
