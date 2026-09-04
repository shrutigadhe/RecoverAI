import csv
import os
import logging
from typing import Dict, Any, List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas import EvaluationResultResponse
from app.agent.nodes import calculate_deterministic_recovery_score
from app.policies.recovery_policy import RecoveryPolicyEngine

logger = logging.getLogger("recoverai.evaluation")

router = APIRouter(prefix="/evaluation", tags=["Evaluation"])

CSV_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "..", "data", "synthetic_payments.csv")


@router.post("/run", response_model=EvaluationResultResponse)
def run_batch_evaluation(db: Session = Depends(get_db)):
    """
    Ultra-fast batch evaluation runner over synthetic_payments.csv (100 cases).
    Evaluates failure diagnosis, recovery scoring, and policy guardrails in-memory.
    Computes exact dynamic metrics without hitting database network timeouts.
    """
    if not os.path.exists(CSV_PATH):
        raise HTTPException(status_code=404, detail=f"Synthetic dataset not found at {CSV_PATH}")

    rows = []
    with open(CSV_PATH, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    if not rows:
        raise HTTPException(status_code=400, detail="Synthetic CSV file is empty")

    results: List[Dict[str, Any]] = []

    total_revenue_at_risk = 0.0
    total_recovered_revenue = 0.0
    recovery_attempts = 0
    successful_recoveries = 0
    escalations = 0
    policy_rejections = 0

    policy_engine = RecoveryPolicyEngine()

    for r in rows:
        amount = float(r.get("amount", 0.0))
        total_revenue_at_risk += amount

        succ_pay = int(r.get("successful_payments", 0))
        fail_pay = int(r.get("failed_payments", 0))
        total_pay = succ_pay + fail_pay
        success_rate = (succ_pay / total_pay) if total_pay > 0 else 0.0
        retry_count = int(r.get("previous_attempts", 0))

        # 1. Deterministic/AI Scoring
        rec_data = calculate_deterministic_recovery_score(
            amount=amount,
            failure_reason=r.get("failure_reason"),
            payment_method=r.get("payment_method", "UPI"),
            success_rate=success_rate,
            retry_count=retry_count
        )

        rec_action = rec_data.get("recommended_action", "ESCALATE")
        confidence = rec_data.get("confidence", 0.0)

        # 2. Policy Engine Guardrail Check
        policy_res = policy_engine.evaluate(
            recommended_action=rec_action,
            confidence=confidence,
            amount=amount,
            retry_count=retry_count,
            payment_status="QUEUED",
            failure_reason=r.get("failure_reason")
        )

        final_status = "ESCALATED"
        recovered_amt = 0.0

        if policy_res.approved:
            if rec_action == "RETRY":
                final_status = "RECOVERED"
                recovered_amt = amount
                successful_recoveries += 1
                total_recovered_revenue += amount
                recovery_attempts += 1
            elif rec_action == "REMINDER":
                final_status = "ACTION_EXECUTED"
            elif rec_action == "STOP":
                final_status = "STOPPED"
        else:
            final_status = "ESCALATED"
            escalations += 1
            policy_rejections += 1
            if rec_action == "RETRY":
                recovery_attempts += 1

        results.append({
            "payment_id": r.get("payment_id"),
            "amount": amount,
            "failure_reason": r.get("failure_reason"),
            "diagnosis": rec_data.get("diagnosis"),
            "recommended_action": rec_action,
            "confidence": confidence,
            "policy_approved": policy_res.approved,
            "final_status": final_status,
            "recovered_amount": recovered_amt
        })

    total_cases = len(rows)
    recovery_rate = (successful_recoveries / total_cases * 100.0) if total_cases > 0 else 0.0
    escalation_rate = (escalations / total_cases * 100.0) if total_cases > 0 else 0.0
    rejection_rate = (policy_rejections / total_cases * 100.0) if total_cases > 0 else 0.0

    return EvaluationResultResponse(
        total_cases=total_cases,
        total_revenue_at_risk=round(total_revenue_at_risk, 2),
        recovery_attempts=recovery_attempts,
        successful_recoveries=successful_recoveries,
        total_recovered_revenue=round(total_recovered_revenue, 2),
        recovery_rate_percentage=round(recovery_rate, 1),
        escalation_rate_percentage=round(escalation_rate, 1),
        policy_rejection_rate_percentage=round(rejection_rate, 1),
        cases=results
    )
