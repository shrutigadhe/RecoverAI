from app.policies.recovery_policy import RecoveryPolicyEngine


def test_policy_approval_standard_retry():
    engine = RecoveryPolicyEngine()
    res = engine.evaluate(
        recommended_action="RETRY",
        confidence=0.89,
        amount=3500.0,
        retry_count=0,
        payment_status="QUEUED"
    )
    assert res.approved is True
    assert res.rule_name == "ALL_POLICIES_PASSED"


def test_policy_rejection_max_retry_limit():
    engine = RecoveryPolicyEngine()
    res = engine.evaluate(
        recommended_action="RETRY",
        confidence=0.90,
        amount=2000.0,
        retry_count=1,  # MAX_AUTO_RETRY is 1
        payment_status="QUEUED"
    )
    assert res.approved is False
    assert res.rule_name == "MAX_RETRY_LIMIT"


def test_policy_rejection_high_value_amount():
    engine = RecoveryPolicyEngine()
    res = engine.evaluate(
        recommended_action="RETRY",
        confidence=0.95,
        amount=25000.0,  # Exceeds 5000.0 limit
        retry_count=0,
        payment_status="QUEUED"
    )
    assert res.approved is False
    assert res.rule_name == "MAX_AMOUNT_LIMIT"


def test_policy_rejection_low_confidence():
    engine = RecoveryPolicyEngine()
    res = engine.evaluate(
        recommended_action="RETRY",
        confidence=0.61,  # Below 0.80 threshold
        amount=3200.0,
        retry_count=0,
        payment_status="QUEUED"
    )
    assert res.approved is False
    assert res.rule_name == "MIN_CONFIDENCE_THRESHOLD"


def test_policy_duplicate_payment_protection():
    engine = RecoveryPolicyEngine()
    res = engine.evaluate(
        recommended_action="RETRY",
        confidence=0.95,
        amount=3500.0,
        retry_count=0,
        payment_status="RECOVERED"  # Already recovered
    )
    assert res.approved is False
    assert res.rule_name == "DUPLICATE_PAYMENT_PROTECTION"
