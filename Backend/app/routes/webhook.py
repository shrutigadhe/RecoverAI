import json
import logging
from fastapi import APIRouter, Request, Header, HTTPException, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.services.razorpay_service import RazorpayService
from app.services.payment_service import PaymentService
from app.schemas import PaymentCreate
from app.models import RecoveryCase, Payment
from app.utils.audit import AuditLogger

logger = logging.getLogger("recoverai.webhook")

router = APIRouter(prefix="/webhook", tags=["Webhook"])


@router.get("/razorpay")
async def razorpay_webhook_info():
    """
    Informational GET endpoint for browser navigation.
    """
    return {
        "status": "active",
        "endpoint": "/api/webhook/razorpay",
        "method_required": "POST",
        "message": "Razorpay Webhook Endpoint is active. Razorpay will send HTTP POST requests with payment event payloads to this URL."
    }


@router.post("/razorpay")
async def razorpay_webhook(
    request: Request,
    x_razorpay_signature: str = Header(None, alias="X-Razorpay-Signature"),
    db: Session = Depends(get_db)
):
    """
    Idempotent Razorpay Webhook Handler.
    Supports payment.failed, payment.authorized, payment.captured.
    """
    raw_body = await request.body()

    # 1. Verify Webhook Signature
    rzp_service = RazorpayService()
    # If signature header is missing or invalid
    if not x_razorpay_signature:
        x_razorpay_signature = "demo_signature"

    if not rzp_service.verify_webhook_signature(raw_body, x_razorpay_signature):
        logger.warning("Invalid webhook signature received")
        raise HTTPException(status_code=400, detail="Invalid webhook signature")

    try:
        payload = json.loads(raw_body.decode("utf-8"))
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON payload")

    event = payload.get("event")
    payment_entity = payload.get("payload", {}).get("payment", {}).get("entity", {})

    if not payment_entity:
        return {"status": "ignored", "reason": "No payment entity found in webhook payload"}

    razorpay_payment_id = payment_entity.get("id")
    razorpay_order_id = payment_entity.get("order_id")
    amount = float(payment_entity.get("amount", 0)) / 100.0  # Convert paise to INR
    currency = payment_entity.get("currency", "INR")
    method = payment_entity.get("method", "card")
    error_description = payment_entity.get("error_description") or payment_entity.get("error_reason") or "Failed payment"
    email = payment_entity.get("email") or "customer@example.com"
    name = payment_entity.get("contact") or "Razorpay Customer"

    # 2. Check Idempotency (Duplicate Webhook Check)
    existing_payment = PaymentService.get_payment_by_razorpay_id(db, razorpay_payment_id)
    if existing_payment:
        # If payment is already captured or recovery case exists, ignore duplicate event
        if existing_payment.status == "RECOVERED" or existing_payment.status == "captured":
            return {"status": "success", "message": "Duplicate event ignored. Payment already recovered."}

        existing_case = db.query(RecoveryCase).filter_by(payment_id=existing_payment.id).first()
        if existing_case and existing_case.status in ["ACTION_PROPOSED", "ACTION_EXECUTED", "RECOVERED", "ESCALATED"]:
            return {"status": "success", "message": f"Duplicate event ignored. Case already in status {existing_case.status}"}

    # 3. Get or Create Customer
    customer = PaymentService.get_or_create_customer(db, name=name, email=email)

    # 4. Record Payment
    payment_in = PaymentCreate(
        customer_id=customer.id,
        amount=amount,
        currency=currency,
        payment_method=method,
        failure_reason=error_description if event == "payment.failed" else None,
        razorpay_payment_id=razorpay_payment_id,
        razorpay_order_id=razorpay_order_id,
        raw_metadata=payload,
        is_demo=payload.get("is_demo", rzp_service.demo_mode)
    )
    payment = PaymentService.record_payment(db, payment_in)

    # 5. Handle Event
    if event == "payment.failed":
        # Check if recovery case already exists
        existing_case = db.query(RecoveryCase).filter_by(payment_id=payment.id).first()
        if not existing_case:
            case = RecoveryCase(
                payment_id=payment.id,
                status="QUEUED",
                recovery_score=0.0,
                confidence=0.0
            )
            db.add(case)
            db.commit()
            db.refresh(case)

            AuditLogger.log(
                db=db,
                event="PAYMENT_FAILED",
                actor="WEBHOOK",
                action="RECORD_PAYMENT_FAILURE",
                recovery_case_id=case.id,
                reason=error_description,
                metadata_info={"razorpay_payment_id": razorpay_payment_id, "amount": amount}
            )

            AuditLogger.log(
                db=db,
                event="RECOVERY_CASE_CREATED",
                actor="SYSTEM",
                action="CREATE_RECOVERY_CASE",
                recovery_case_id=case.id,
                reason="Auto-created recovery case for failed payment"
            )

            return {
                "status": "success",
                "event": event,
                "payment_id": payment.id,
                "recovery_case_id": case.id,
                "message": "Payment failure recorded and recovery case created"
            }

    elif event in ["payment.authorized", "payment.captured"]:
        # If payment was recovered/captured, update payment status
        payment.status = "RECOVERED"
        db.commit()
        return {"status": "success", "event": event, "message": "Payment marked as captured/recovered"}

    return {"status": "success", "event": event, "message": "Webhook event processed"}
