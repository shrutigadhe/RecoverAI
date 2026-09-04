from app.models import Merchant, Customer, Payment, RecoveryCase
from app.services.recovery_service import RecoveryService


def test_scenario_1_successful_recovery(db_session):
    merchant = Merchant(name="Merchant 1", email="m1@test.com")
    db_session.add(merchant)
    db_session.commit()

    customer = Customer(
        merchant_id=merchant.id,
        name="Rahul Sharma",
        email="rahul@test.com",
        total_payments=15,
        successful_payments=14,
        failed_payments=1
    )
    db_session.add(customer)
    db_session.commit()

    payment = Payment(
        customer_id=customer.id,
        amount=3500.0,
        currency="INR",
        status="QUEUED",
        payment_method="UPI",
        failure_reason="Temporary bank error",
        is_demo=True
    )
    db_session.add(payment)
    db_session.commit()

    case = RecoveryCase(
        payment_id=payment.id,
        retry_count=0,
        status="QUEUED"
    )
    db_session.add(case)
    db_session.commit()

    executed = RecoveryService.run_recovery_workflow(db_session, case.id)
    assert executed.status == "RECOVERED"
    assert executed.recovered_amount == 3500.0
    assert executed.recommended_action == "RETRY"


def test_scenario_2_retry_blocked(db_session):
    merchant = Merchant(name="Merchant 2", email="m2@test.com")
    db_session.add(merchant)
    db_session.commit()

    customer = Customer(merchant_id=merchant.id, name="Test Cust", email="c2@test.com", total_payments=5, successful_payments=4)
    db_session.add(customer)
    db_session.commit()

    payment = Payment(customer_id=customer.id, amount=2000.0, payment_method="UPI", failure_reason="Temporary failure")
    db_session.add(payment)
    db_session.commit()

    case = RecoveryCase(payment_id=payment.id, retry_count=1, status="QUEUED")  # Retry count already 1
    db_session.add(case)
    db_session.commit()

    executed = RecoveryService.run_recovery_workflow(db_session, case.id)
    assert executed.status == "ESCALATED"
    assert executed.escalation_reason is not None


def test_scenario_3_low_confidence(db_session):
    merchant = Merchant(name="Merchant 3", email="m3@test.com")
    db_session.add(merchant)
    db_session.commit()

    customer = Customer(merchant_id=merchant.id, name="Test Cust 3", email="c3@test.com", total_payments=2, successful_payments=1)
    db_session.add(customer)
    db_session.commit()

    payment = Payment(customer_id=customer.id, amount=3200.0, payment_method="Netbanking", failure_reason="Unknown error code 99")
    db_session.add(payment)
    db_session.commit()

    case = RecoveryCase(payment_id=payment.id, retry_count=0, status="QUEUED")
    db_session.add(case)
    db_session.commit()

    executed = RecoveryService.run_recovery_workflow(db_session, case.id)
    assert executed.status == "ESCALATED"
    assert executed.escalation_reason is not None


def test_scenario_4_high_value_payment(db_session):
    merchant = Merchant(name="Merchant 4", email="m4@test.com")
    db_session.add(merchant)
    db_session.commit()

    customer = Customer(merchant_id=merchant.id, name="Enterprise Cust", email="ent@test.com", total_payments=10, successful_payments=10)
    db_session.add(customer)
    db_session.commit()

    payment = Payment(customer_id=customer.id, amount=25000.0, payment_method="Card", failure_reason="Temporary bank error")
    db_session.add(payment)
    db_session.commit()

    case = RecoveryCase(payment_id=payment.id, retry_count=0, status="QUEUED")
    db_session.add(case)
    db_session.commit()

    executed = RecoveryService.run_recovery_workflow(db_session, case.id)
    assert executed.status == "ESCALATED"
    assert executed.escalation_reason is not None


def test_scenario_5_already_successful(db_session):
    merchant = Merchant(name="Merchant 5", email="m5@test.com")
    db_session.add(merchant)
    db_session.commit()

    customer = Customer(merchant_id=merchant.id, name="Cust 5", email="c5@test.com")
    db_session.add(customer)
    db_session.commit()

    payment = Payment(customer_id=customer.id, amount=3500.0, payment_method="UPI", status="RECOVERED")
    db_session.add(payment)
    db_session.commit()

    case = RecoveryCase(payment_id=payment.id, status="QUEUED")
    db_session.add(case)
    db_session.commit()

    executed = RecoveryService.run_recovery_workflow(db_session, case.id)
    assert executed.status == "STOPPED"
    assert executed.recovered_amount == 0.0
