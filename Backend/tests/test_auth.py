from app.models import Merchant
from app.utils.security import verify_password


def test_register_merchant_argon2(client, db_session):
    payload = {
        "name": "Acme Fintech Corp",
        "email": "owner@acme.com",
        "password": "SecurePassword123!"
    }
    response = client.post("/api/auth/register", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["merchant"]["email"] == "owner@acme.com"

    # Verify password in DB is Argon2 hashed, not plaintext or simple hashlib
    merchant = db_session.query(Merchant).filter_by(email="owner@acme.com").first()
    assert merchant is not None
    assert merchant.password_hash.startswith("$argon2")
    assert verify_password("SecurePassword123!", merchant.password_hash) is True
    assert verify_password("WrongPassword", merchant.password_hash) is False


def test_login_merchant_argon2(client):
    # Register first
    client.post("/api/auth/register", json={
        "name": "Beta Merchant",
        "email": "beta@merchant.com",
        "password": "Password123!"
    })

    # Success login
    res = client.post("/api/auth/login", json={
        "email": "beta@merchant.com",
        "password": "Password123!"
    })
    assert res.status_code == 200
    assert "access_token" in res.json()

    # Invalid login
    bad_res = client.post("/api/auth/login", json={
        "email": "beta@merchant.com",
        "password": "WrongPassword"
    })
    assert bad_res.status_code == 401


def test_get_current_merchant_me(client):
    reg_res = client.post("/api/auth/register", json={
        "name": "Gamma Corp",
        "email": "gamma@corp.com",
        "password": "Password123!"
    })
    token = reg_res.json()["access_token"]

    me_res = client.get(
        "/api/auth/me",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert me_res.status_code == 200
    assert me_res.json()["email"] == "gamma@corp.com"
