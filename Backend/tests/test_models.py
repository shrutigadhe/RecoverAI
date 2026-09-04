from app.models import Merchant, Customer, Payment, RecoveryCase, RecoveryAction, AuditLog


def test_create_merchant_and_customer(db_session):
    merchant = Merchant(name="Acme SaaS Inc", email="admin@acme.com")
    db_session.add(merchant)
    db_session.commit()
    db_session.refresh(merchant)

    assert merchant.id is not None
    assert merchant.name == "Acme SaaS Inc"

    customer = Customer(
        merchant_id=merchant.id,
        name="Rahul Sharma",
        email="rahul@example.com",
        total_payments=10,
        successful_payments=9,
        failed_payments=1
    )
    db_session.add(customer)
    db_session.commit()
    db_session.refresh(customer)

    assert customer.id is not None
    assert customer.merchant_id == merchant.id
    assert customer.success_rate == 0.90


def test_create_payment_and_recovery_case(db_session):
    merchant = Merchant(name="Test Merchant", email="test@merchant.com")
    db_session.add(merchant)
    db_session.commit()

    customer = Customer(
        merchant_id=merchant.id,
        name="Priya Shah",
        email="priya@example.com"
    )
    db_session.add(customer)
    db_session.commit()

    payment = Payment(
        customer_id=customer.id,
        razorpay_payment_id="pay_test_12345",
        razorpay_order_id="order_test_12345",
        amount=3500.0,
        currency="INR",
        status="QUEUED",
        payment_method="UPI",
        failure_reason="Temporary bank error",
        raw_metadata={"gateway": "HDFC"},
        is_demo=True
    )
    db_session.add(payment)
    db_session.commit()
    db_session.refresh(payment)

    assert payment.id is not None
    assert payment.amount == 3500.0
    assert payment.is_demo is True

    recovery_case = RecoveryCase(
        payment_id=payment.id,
        recovery_score=0.91,
        diagnosis="Temporary bank/network failure",
        recommended_action="RETRY",
        confidence=0.89,
        status="ACTION_PROPOSED",
        recovered_amount=0.0
    )
    db_session.add(recovery_case)
    db_session.commit()
    db_session.refresh(recovery_case)

    assert recovery_case.id is not None
    assert recovery_case.payment_id == payment.id
    assert recovery_case.recovery_score == 0.91

    action = RecoveryAction(
        recovery_case_id=recovery_case.id,
        action="RETRY",
        status="SUCCESS",
        attempt_number=1,
        result={"status": "captured", "amount": 3500.0}
    )
    db_session.add(action)
    db_session.commit()

    audit = AuditLog(
        recovery_case_id=recovery_case.id,
        event="RETRY_EXECUTED",
        actor="POLICY_ENGINE",
        action="RETRY",
        reason="Policy approved retry for payment under limit",
        policy_result="APPROVED",
        metadata_info={"amount": 3500.0}
    )
    db_session.add(audit)
    db_session.commit()

    # Query back and verify relationships
    fetched_case = db_session.query(RecoveryCase).filter_by(id=recovery_case.id).first()
    assert fetched_case is not None
    assert fetched_case.payment.amount == 3500.0
    assert len(fetched_case.actions) == 1
    assert fetched_case.actions[0].action == "RETRY"
    assert len(fetched_case.audit_logs) == 1
    assert fetched_case.audit_logs[0].event == "RETRY_EXECUTED"
