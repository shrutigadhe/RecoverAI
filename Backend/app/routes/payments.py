from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas import PaymentResponse, PaymentCreate
from app.services.payment_service import PaymentService
from app.services.razorpay_service import RazorpayService
from app.models import Merchant
from app.utils.security import get_current_merchant

router = APIRouter(prefix="/payments", tags=["Payments"])


@router.post("/create-order")
def create_payment_order(
    amount: float = Query(..., description="Amount in INR (e.g. 3500.0)"),
    currency: str = Query("INR"),
    customer_name: str = Query("Test Customer"),
    customer_email: str = Query("test@example.com"),
    current_merchant: Merchant = Depends(get_current_merchant),
    db: Session = Depends(get_db)
):
    """
    Creates a Razorpay Test Mode order attached to the authenticated merchant.
    """
    customer = PaymentService.get_or_create_customer(
        db=db,
        name=customer_name,
        email=customer_email,
        merchant_id=current_merchant.id
    )

    rzp_service = RazorpayService()
    order_data = rzp_service.create_order(
        amount=amount,
        currency=currency,
        receipt=f"receipt_{customer.id[:8]}"
    )

    return {
        "order": order_data,
        "customer": {
            "id": customer.id,
            "name": customer.name,
            "email": customer.email,
            "merchant_id": current_merchant.id
        },
        "key_id": rzp_service.key_id
    }


@router.get("", response_model=List[PaymentResponse])
def get_all_payments(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    current_merchant: Merchant = Depends(get_current_merchant),
    db: Session = Depends(get_db)
):
    """Returns list of recorded payments for authenticated merchant only."""
    return PaymentService.list_payments(db, merchant_id=current_merchant.id, skip=skip, limit=limit)


@router.get("/{payment_id}", response_model=PaymentResponse)
def get_payment_details(
    payment_id: str,
    current_merchant: Merchant = Depends(get_current_merchant),
    db: Session = Depends(get_db)
):
    """Fetches details for a specific payment owned by current merchant."""
    payment = PaymentService.get_payment_by_id(db, payment_id, merchant_id=current_merchant.id)
    if not payment:
        raise HTTPException(status_code=404, detail="Payment record not found")
    return payment
