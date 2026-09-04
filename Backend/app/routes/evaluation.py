import csv
import os
import logging
from typing import Dict, Any, List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas import EvaluationResultResponse
from app.services.payment_service import PaymentService
from app.schemas import PaymentCreate
from app.models import RecoveryCase, Payment, Customer
from app.services.recovery_service import RecoveryService

logger = logging.getLogger("recoverai.evaluation")

router = APIRouter(prefix="/evaluation", tags=["Evaluation"])

CSV_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "..", "data", "synthetic_payments.csv")


@router.post("/run", response_model=EvaluationResultResponse)
def run_batch_evaluation(db: Session = Depends(get_db)):
    """
    Runs batch evaluation over synthetic_payments.csv (100 cases).
    Calculates exact dynamic metrics from test execution results.
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

    for r in rows:
        amount = float(r.get("amount", 0.0))
        total_revenue_at_risk += amount

        # Get or create customer with exact synthetic history
        customer = PaymentService.get_or_create_customer(
            db=db,
            name=f"Customer {r.get('customer_id')}",
            email=f"{r.get('customer_id')}@synthetic.com"
        )
        customer.total_payments = int(r.get("successful_payments", 0)) + int(r.get("failed_payments", 0))
        customer.successful_payments = int(r.get("successful_payments", 0))
        customer.failed_payments = int(r.get("failed_payments", 0))
        db.commit()

        # Create payment record
        payment = Payment(
            customer_id=customer.id,
            razorpay_payment_id=f"pay_{r.get('payment_id')}",
            razorpay_order_id=f"order_{r.get('payment_id')}",
            amount=amount,
            currency="INR",
            status="QUEUED",
            payment_method=r.get("payment_method", "UPI"),
            failure_reason=r.get("failure_reason"),
            is_demo=True
        )
        db.add(payment)
        db.commit()
        db.refresh(payment)

        # Create recovery case
        case = RecoveryCase(
            payment_id=payment.id,
            retry_count=int(r.get("previous_attempts", 0)),
            status="QUEUED",
            recovery_score=0.0,
            confidence=0.0
        )
        db.add(case)
        db.commit()
        db.refresh(case)

        # Run closed-loop recovery workflow
        executed_case = RecoveryService.run_recovery_workflow(db, case.id)

        # Increment metrics
        if executed_case.recommended_action == "RETRY":
            recovery_attempts += 1

        if executed_case.status == "RECOVERED":
            successful_recoveries += 1
            total_recovered_revenue += executed_case.recovered_amount
        elif executed_case.status == "ESCALATED":
            escalations += 1

        if executed_case.escalation_reason and "Policy Rejected" in executed_case.escalation_reason:
            policy_rejections += 1

        results.append({
            "payment_id": r.get("payment_id"),
            "amount": amount,
            "failure_reason": r.get("failure_reason"),
            "diagnosis": executed_case.diagnosis,
            "recommended_action": executed_case.recommended_action,
            "confidence": executed_case.confidence,
            "policy_approved": executed_case.status != "ESCALATED" or not ("Policy Rejected" in (executed_case.escalation_reason or "")),
            "final_status": executed_case.status,
            "recovered_amount": executed_case.recovered_amount
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
