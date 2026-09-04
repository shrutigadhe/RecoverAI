import logging
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List
from sqlalchemy.orm import Session
from app.models import RecoveryCase, Payment, Customer, RecoveryAction
from app.agent.graph import recovery_agent_graph
from app.utils.audit import AuditLogger
from app.services.razorpay_service import RazorpayService

logger = logging.getLogger("recoverai.recovery_service")


class RecoveryService:
    @staticmethod
    def get_case(db: Session, case_id: str, merchant_id: Optional[str] = None) -> Optional[RecoveryCase]:
        query = db.query(RecoveryCase).join(Payment).join(Customer)
        if merchant_id:
            query = query.filter(Customer.merchant_id == merchant_id)
        return query.filter(RecoveryCase.id == case_id).first()

    @staticmethod
    def list_cases(db: Session, merchant_id: Optional[str] = None, status: Optional[str] = None, skip: int = 0, limit: int = 100) -> List[RecoveryCase]:
        query = db.query(RecoveryCase).join(Payment).join(Customer)
        if merchant_id:
            query = query.filter(Customer.merchant_id == merchant_id)
        if status:
            query = query.filter(RecoveryCase.status == status)
        return query.order_by(RecoveryCase.created_at.desc()).offset(skip).limit(limit).all()

    @staticmethod
    def run_recovery_workflow(db: Session, case_id: str) -> RecoveryCase:
        """
        Executes the closed loop recovery workflow:
        LOAD -> DIAGNOSE -> DECIDE -> POLICY CHECK -> ACT -> VERIFY -> RECOVER -> AUDIT
        """
        case = db.query(RecoveryCase).filter(RecoveryCase.id == case_id).first()
        if not case:
            raise ValueError(f"Recovery case {case_id} not found")

        payment = case.payment
        customer = payment.customer

        # 1. Duplicate Charge / Idempotency Protection
        if payment.status in ["RECOVERED", "captured"]:
            case.status = "STOPPED"
            case.escalation_reason = "Payment already captured; duplicate charge prevented."
            db.commit()
            AuditLogger.log(
                db=db,
                event="STOPPED",
                actor="POLICY_ENGINE",
                action="PREVENT_DUPLICATE_CHARGE",
                recovery_case_id=case.id,
                reason="Payment was already captured. Halting recovery.",
                policy_result="REJECTED"
            )
            return case

        # Set status to ANALYZING
        case.status = "ANALYZING"
        db.commit()

        # 2. Build Agent Inputs
        customer_history = {
            "total_payments": customer.total_payments,
            "successful_payments": customer.successful_payments,
            "failed_payments": customer.failed_payments,
            "success_rate": customer.success_rate
        }

        initial_state = {
            "payment_id": payment.id,
            "amount": payment.amount,
            "payment_method": payment.payment_method,
            "failure_reason": payment.failure_reason,
            "retry_count": case.retry_count,
            "customer_history": customer_history,
            "diagnosis": None,
            "recovery_score": 0.0,
            "recommended_action": None,
            "confidence": 0.0,
            "reason": None,
            "policy_approved": False,
            "policy_rule": None,
            "policy_reason": None,
            "execution_result": None,
            "recovered_amount": 0.0,
            "final_status": "ANALYZING"
        }

        # 3. Execute LangGraph Workflow
        result_state = recovery_agent_graph.invoke(initial_state)

        # 4. Record AI Diagnosis or AI Error Audit Log
        if result_state.get("ai_error"):
            AuditLogger.log(
                db=db,
                event="AI_ERROR",
                actor="AI_AGENT",
                action="LLM_EXECUTION_FAILURE",
                recovery_case_id=case.id,
                reason=result_state.get("diagnosis") or "LLM execution failed or returned invalid output",
                policy_result="REJECTED"
            )
        else:
            AuditLogger.log(
                db=db,
                event="AI_DIAGNOSIS",
                actor="AI_AGENT",
                action="DIAGNOSE_FAILURE",
                recovery_case_id=case.id,
                reason=result_state.get("diagnosis"),
                metadata_info={
                    "score": result_state.get("recovery_score"),
                    "confidence": result_state.get("confidence")
                }
            )

        # 5. Record Proposed Action Audit Log
        AuditLogger.log(
            db=db,
            event="ACTION_PROPOSED",
            actor="AI_AGENT",
            action=result_state.get("recommended_action") or "UNKNOWN",
            recovery_case_id=case.id,
            reason=result_state.get("reason"),
            metadata_info={"confidence": result_state.get("confidence")}
        )

        # 6. Policy Audit Log
        policy_approved = result_state.get("policy_approved", False)
        policy_reason = result_state.get("policy_reason")
        AuditLogger.log(
            db=db,
            event="POLICY_APPROVED" if policy_approved else "POLICY_REJECTED",
            actor="POLICY_ENGINE",
            action=result_state.get("recommended_action") or "UNKNOWN",
            recovery_case_id=case.id,
            reason=policy_reason,
            policy_result="APPROVED" if policy_approved else "REJECTED"
        )

        # 7. Action Execution Record
        action_name = result_state.get("recommended_action") or "ESCALATE"
        exec_res = result_state.get("execution_result", {})
        action_rec = RecoveryAction(
            recovery_case_id=case.id,
            action=action_name,
            status="SUCCESS" if policy_approved else "REJECTED",
            attempt_number=case.retry_count + 1,
            result=exec_res,
            completed_at=datetime.now(timezone.utc)
        )
        db.add(action_rec)

        # If RETRY was executed, increment retry count
        if action_name == "RETRY" and policy_approved:
            case.retry_count += 1

        # 8. Update Recovery Case Status & Payment Status
        final_status = result_state.get("final_status", "ESCALATED")
        recovered_amt = result_state.get("recovered_amount", 0.0)

        case.recovery_score = result_state.get("recovery_score", 0.0)
        case.diagnosis = result_state.get("diagnosis")
        case.recommended_action = action_name
        case.confidence = result_state.get("confidence", 0.0)
        case.status = final_status
        case.recovered_amount = recovered_amt
        
        if not policy_approved:
            case.escalation_reason = f"Policy Rejected: {policy_reason}"
        elif final_status == "ESCALATED":
            case.escalation_reason = policy_reason or f"Escalated to merchant (Action: {action_name})"

        if final_status == "RECOVERED":
            payment.status = "RECOVERED"
            customer.successful_payments += 1
            AuditLogger.log(
                db=db,
                event="PAYMENT_RECOVERED",
                actor="SYSTEM",
                action="MARK_RECOVERED",
                recovery_case_id=case.id,
                reason=f"Successfully recovered ₹{recovered_amt:,.2f}",
                metadata_info={"amount": recovered_amt}
            )

        db.commit()
        db.refresh(case)
        return case

    @staticmethod
    def approve_case(db: Session, case_id: str, notes: Optional[str] = None) -> RecoveryCase:
        """
        Human-in-the-Loop manual merchant approval for escalated cases.
        """
        case = db.query(RecoveryCase).filter(RecoveryCase.id == case_id).first()
        if not case:
            raise ValueError(f"Case {case_id} not found")

        rzp_service = RazorpayService()
        res = rzp_service.retry_payment(
            razorpay_order_id=f"order_{case.payment_id[:8]}",
            amount=case.payment.amount
        )

        case.status = "RECOVERED" if res.get("success") else "FAILED"
        case.recovered_amount = case.payment.amount if res.get("success") else 0.0
        case.payment.status = "RECOVERED" if res.get("success") else "FAILED"

        AuditLogger.log(
            db=db,
            event="MERCHANT_APPROVED",
            actor="MERCHANT",
            action="MANUAL_RETRY_OVERRIDE",
            recovery_case_id=case.id,
            reason=notes or "Merchant manually approved recovery retry.",
            policy_result="APPROVED"
        )

        db.commit()
        db.refresh(case)
        return case

    @staticmethod
    def escalate_case(db: Session, case_id: str, reason: str) -> RecoveryCase:
        """
        Human-in-the-Loop explicit merchant escalation.
        """
        case = db.query(RecoveryCase).filter(RecoveryCase.id == case_id).first()
        if not case:
            raise ValueError(f"Case {case_id} not found")

        case.status = "ESCALATED"
        case.escalation_reason = reason

        AuditLogger.log(
            db=db,
            event="ESCALATED",
            actor="MERCHANT",
            action="MANUAL_ESCALATION",
            recovery_case_id=case.id,
            reason=reason
        )

        db.commit()
        db.refresh(case)
        return case
