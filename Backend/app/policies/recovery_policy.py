import logging
from typing import Dict, Any, Optional
from app.config import settings
from app.schemas import PolicyEvaluationResult

logger = logging.getLogger("recoverai.policy_engine")


class RecoveryPolicyEngine:
    """
    Deterministic Guardrail Engine.
    The AI recommends actions. The Policy Engine decides whether the action is allowed.
    """

    def __init__(
        self,
        max_auto_retry: Optional[int] = None,
        max_auto_recovery_amount: Optional[float] = None,
        min_ai_confidence: Optional[float] = None
    ):
        self.max_auto_retry = max_auto_retry or settings.MAX_AUTO_RETRY
        self.max_auto_recovery_amount = max_auto_recovery_amount or settings.MAX_AUTO_RECOVERY_AMOUNT
        self.min_ai_confidence = min_ai_confidence or settings.MIN_AI_CONFIDENCE

    def evaluate(
        self,
        recommended_action: str,
        confidence: float,
        amount: float,
        retry_count: int,
        payment_status: str,
        failure_reason: Optional[str] = None
    ) -> PolicyEvaluationResult:
        """
        Evaluates a proposed recovery action against deterministic business policies.
        """
        action = (recommended_action or "").upper().strip()

        # Rule 1: Payment already successful / captured -> Prevent duplicate charge
        if payment_status in ["RECOVERED", "CAPTURED", "SUCCESS", "captured"]:
            return PolicyEvaluationResult(
                approved=False,
                rule_name="DUPLICATE_PAYMENT_PROTECTION",
                reason="Payment is already captured; duplicate charge prevented."
            )

        # Rule 2: Allowed action validation
        allowed_actions = ["RETRY", "REMINDER", "ESCALATE", "STOP"]
        if action not in allowed_actions:
            return PolicyEvaluationResult(
                approved=False,
                rule_name="INVALID_ACTION_SCHEMA",
                reason=f"Action '{recommended_action}' is not a valid allowed action."
            )

        # Explicit ESCALATE or STOP recommendation by AI
        if action == "ESCALATE":
            return PolicyEvaluationResult(
                approved=True,
                rule_name="PASS_THROUGH_ESCALATE",
                reason="AI recommended escalation to merchant; policy permits human intervention."
            )

        if action == "STOP":
            return PolicyEvaluationResult(
                approved=True,
                rule_name="PASS_THROUGH_STOP",
                reason="AI recommended stopping further recovery attempts."
            )

        # Rule 3: Check AI Confidence threshold
        if confidence < self.min_ai_confidence:
            return PolicyEvaluationResult(
                approved=False,
                rule_name="MIN_CONFIDENCE_THRESHOLD",
                reason=f"AI confidence ({confidence * 100:.1f}%) is below minimum threshold ({self.min_ai_confidence * 100:.1f}%)."
            )

        # Specific rules for RETRY action
        if action == "RETRY":
            # Rule 4: Maximum Retry Limit
            if retry_count >= self.max_auto_retry:
                return PolicyEvaluationResult(
                    approved=False,
                    rule_name="MAX_RETRY_LIMIT",
                    reason=f"Maximum automatic retry limit ({self.max_auto_retry}) has already been reached."
                )

            # Rule 5: High Value Payment Amount Restriction
            if amount > self.max_auto_recovery_amount:
                return PolicyEvaluationResult(
                    approved=False,
                    rule_name="MAX_AMOUNT_LIMIT",
                    reason=f"Payment amount (₹{amount:,.2f}) exceeds maximum automatic recovery limit (₹{self.max_auto_recovery_amount:,.2f})."
                )

        # Specific rules for REMINDER action
        if action == "REMINDER":
            # Allow reminder if confidence is sufficient
            return PolicyEvaluationResult(
                approved=True,
                rule_name="ALLOW_REMINDER",
                reason="Reminder message generation approved by policy engine."
            )

        # All checks passed for RETRY
        return PolicyEvaluationResult(
            approved=True,
            rule_name="ALL_POLICIES_PASSED",
            reason="Action approved: payment amount below threshold, retry limit valid, high AI confidence."
        )
