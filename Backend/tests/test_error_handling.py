from unittest.mock import patch
from app.models import Merchant, Customer, Payment, RecoveryCase, AuditLog
from app.services.recovery_service import RecoveryService


def test_invalid_webhook_signature(client):
    with patch("app.config.settings.DEMO_MODE", False):
        with patch("app.config.settings.RAZORPAY_WEBHOOK_SECRET", "real_secret_123"):
            response = client.post(
                "/api/webhook/razorpay",
                content=b'{"event":"payment.failed"}',
                headers={"X-Razorpay-Signature": "invalid_sig_abc"}
            )
            assert response.status_code == 400
            assert "Invalid webhook signature" in response.json()["detail"]


def test_malformed_webhook_payload(client):
    response = client.post(
        "/api/webhook/razorpay",
        content=b'not_valid_json',
        headers={"X-Razorpay-Signature": "demo_signature"}
    )
    assert response.status_code == 400


def test_ai_error_handling_escalation(db_session):
    merchant = Merchant(name="Err Merchant", email="err@test.com")
    db_session.add(merchant)
    db_session.commit()

    customer = Customer(merchant_id=merchant.id, name="Err Cust", email="errcust@test.com")
    db_session.add(customer)
    db_session.commit()

    payment = Payment(customer_id=customer.id, amount=3500.0, payment_method="UPI", failure_reason="Temporary failure")
    db_session.add(payment)
    db_session.commit()

    case = RecoveryCase(payment_id=payment.id, status="QUEUED")
    db_session.add(case)
    db_session.commit()

    # Enable LLM mode & mock LLM constructor raising an exception
    with patch("app.config.settings.DEMO_MODE", False):
        with patch("app.config.settings.LLM_API_KEY", "mock_llm_key"):
            with patch("langchain_google_genai.ChatGoogleGenerativeAI", side_effect=Exception("LLM Timeout Connection Failed")):
                executed = RecoveryService.run_recovery_workflow(db_session, case.id)
                assert executed.status == "ESCALATED"

                # Verify AI_ERROR audit log entry was created
                audit_entry = db_session.query(AuditLog).filter_by(recovery_case_id=case.id, event="AI_ERROR").first()
                assert audit_entry is not None
                assert audit_entry.actor == "AI_AGENT"
