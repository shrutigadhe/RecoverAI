import logging
from typing import Dict, Any, Optional
from app.config import settings
from app.schemas import AIRecommendationSchema
from app.agent.state import RecoveryAgentState
from app.agent.prompts import SYSTEM_RECOVERY_PROMPT
from app.policies.recovery_policy import RecoveryPolicyEngine
from app.services.razorpay_service import RazorpayService

logger = logging.getLogger("recoverai.agent_nodes")


def calculate_deterministic_recovery_score(
    amount: float,
    failure_reason: Optional[str],
    payment_method: str,
    success_rate: float,
    retry_count: int
) -> Dict[str, Any]:
    """
    Transparent explainable recovery scoring algorithm used in demo mode or when LLM is unconfigured.
    """
    reason_str = (failure_reason or "").lower()

    # Base score derived from customer history
    score = 0.5 + (success_rate * 0.3)

    # Category adjustment
    if any(k in reason_str for k in ["temporary", "bank", "network", "timeout"]):
        score += 0.20
        diagnosis = "Temporary banking or network communication error"
        recommended_action = "RETRY"
    elif any(k in reason_str for k in ["insufficient", "declined", "funds"]):
        score -= 0.10
        diagnosis = "Customer card or bank account insufficient funds"
        recommended_action = "REMINDER"
    elif any(k in reason_str for k in ["expired", "invalid card"]):
        score -= 0.25
        diagnosis = "Card details expired or invalid authentication method"
        recommended_action = "REMINDER"
    elif "unknown" in reason_str or not failure_reason:
        score -= 0.15
        diagnosis = "Unknown payment gateway failure reason"
        recommended_action = "ESCALATE"
    else:
        diagnosis = f"Payment failure due to {failure_reason}"
        recommended_action = "RETRY" if success_rate >= 0.7 else "REMINDER"

    # Retry penalty
    if retry_count > 0:
        score -= 0.30 * retry_count
        if retry_count >= settings.MAX_AUTO_RETRY and recommended_action == "RETRY":
            recommended_action = "ESCALATE"

    # Amount weighting
    if amount > settings.MAX_AUTO_RECOVERY_AMOUNT:
        recommended_action = "ESCALATE"

    score = max(0.0, min(1.0, round(score, 2)))
    confidence = max(0.60, min(0.95, round(0.70 + (success_rate * 0.2), 2)))

    if "unknown" in reason_str:
        confidence = 0.61  # Low confidence for unknown failure to test escalation

    return {
        "diagnosis": diagnosis,
        "recovery_score": score,
        "recommended_action": recommended_action,
        "confidence": confidence,
        "reason": f"Customer has {success_rate:.0%} payment success rate. Failure: '{failure_reason}'. Retry count: {retry_count}."
    }


def diagnose_and_score_node(state: RecoveryAgentState) -> Dict[str, Any]:
    """
    LLM + LangGraph node for failure diagnosis and recovery recommendation.
    Invokes LLM structured output when API key is set.
    On LLM failure, timeout, or malformed JSON, safely falls back to ESCALATE & logs AI_ERROR.
    """
    customer_hist = state.get("customer_history", {})
    success_rate = customer_hist.get("success_rate", 0.0)
    total_payments = customer_hist.get("total_payments", 0)
    successful_payments = customer_hist.get("successful_payments", 0)
    failed_payments = customer_hist.get("failed_payments", 0)

    llm_api_key = settings.LLM_API_KEY
    recommendation = None
    ai_error_flag = False

    if llm_api_key and not settings.DEMO_MODE:
        try:
            if settings.LLM_PROVIDER.lower() == "gemini":
                from langchain_google_genai import ChatGoogleGenerativeAI
                llm = ChatGoogleGenerativeAI(
                    model="gemini-1.5-flash",
                    google_api_key=llm_api_key,
                    temperature=0.1
                )
                structured_llm = llm.with_structured_output(AIRecommendationSchema)
                formatted_prompt = SYSTEM_RECOVERY_PROMPT.format(
                    payment_id=state.get("payment_id"),
                    amount=state.get("amount"),
                    payment_method=state.get("payment_method"),
                    failure_reason=state.get("failure_reason"),
                    retry_count=state.get("retry_count"),
                    total_payments=total_payments,
                    successful_payments=successful_payments,
                    failed_payments=failed_payments,
                    success_rate=success_rate
                )
                result = structured_llm.invoke(formatted_prompt)
                recommendation = result.model_dump()
        except Exception as e:
            logger.error(f"LLM Provider execution error/timeout: {e}")
            ai_error_flag = True
            recommendation = {
                "diagnosis": f"LLM Execution Error: {str(e)}",
                "recovery_score": 0.0,
                "recommended_action": "ESCALATE",
                "confidence": 0.0,
                "reason": f"AI provider error or malformed response: {str(e)}"
            }

    if not recommendation:
        recommendation = calculate_deterministic_recovery_score(
            amount=state.get("amount", 0.0),
            failure_reason=state.get("failure_reason"),
            payment_method=state.get("payment_method", "card"),
            success_rate=success_rate,
            retry_count=state.get("retry_count", 0)
        )

    # Validate output schema strictly
    valid_actions = ["RETRY", "REMINDER", "ESCALATE", "STOP"]
    if recommendation.get("recommended_action") not in valid_actions:
        recommendation["recommended_action"] = "ESCALATE"
        recommendation["confidence"] = 0.0

    return {
        "diagnosis": recommendation.get("diagnosis"),
        "recovery_score": recommendation.get("recovery_score", 0.0),
        "recommended_action": recommendation.get("recommended_action"),
        "confidence": recommendation.get("confidence", 0.0),
        "reason": recommendation.get("reason"),
        "ai_error": ai_error_flag
    }


def policy_check_node(state: RecoveryAgentState) -> Dict[str, Any]:
    """
    Evaluates AI proposed recommendation against Policy / Guardrail Engine.
    AI recommendations MUST pass through this deterministic policy engine.
    """
    engine = RecoveryPolicyEngine()
    policy_res = engine.evaluate(
        recommended_action=state.get("recommended_action"),
        confidence=state.get("confidence", 0.0),
        amount=state.get("amount", 0.0),
        retry_count=state.get("retry_count", 0),
        payment_status=state.get("final_status", "QUEUED"),
        failure_reason=state.get("failure_reason")
    )

    return {
        "policy_approved": policy_res.approved,
        "policy_rule": policy_res.rule_name,
        "policy_reason": policy_res.reason
    }


def execute_action_node(state: RecoveryAgentState) -> Dict[str, Any]:
    """
    Executes bounded recovery action if policy approved, otherwise escalates case.
    """
    approved = state.get("policy_approved", False)
    action = state.get("recommended_action")
    amount = state.get("amount", 0.0)

    if not approved:
        # Policy rejected action -> Escalate case to merchant
        return {
            "execution_result": {
                "status": "policy_rejected",
                "action": action,
                "reason": state.get("policy_reason")
            },
            "final_status": "ESCALATED",
            "recovered_amount": 0.0
        }

    if action == "RETRY":
        rzp_service = RazorpayService()
        res = rzp_service.retry_payment(
            razorpay_order_id=f"order_{state.get('payment_id')[:8]}",
            amount=amount
        )
        return {
            "execution_result": res,
            "final_status": "RECOVERED" if res.get("success") else "FAILED",
            "recovered_amount": amount if res.get("success") else 0.0
        }

    elif action == "REMINDER":
        reminder_msg = (
            f"Hi customer, your payment of ₹{amount:,.2f} could not be completed "
            f"due to a temporary issue. Please complete your payment here: "
            f"https://pay.recoverai.demo/retry/{state.get('payment_id')[:8]}"
        )
        return {
            "execution_result": {
                "status": "reminder_sent",
                "message": reminder_msg
            },
            "final_status": "ACTION_EXECUTED",
            "recovered_amount": 0.0
        }

    elif action == "STOP":
        return {
            "execution_result": {"status": "stopped", "reason": state.get("policy_reason")},
            "final_status": "STOPPED",
            "recovered_amount": 0.0
        }

    # Default ESCALATE
    return {
        "execution_result": {"status": "escalated_to_merchant"},
        "final_status": "ESCALATED",
        "recovered_amount": 0.0
    }
