import logging
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from app.models import Merchant, Customer, Payment
from app.schemas import MerchantCreate, CustomerCreate, PaymentCreate

logger = logging.getLogger("recoverai.payment_service")


class PaymentService:
    @staticmethod
    def get_or_create_default_merchant(db: Session) -> Merchant:
        merchant = db.query(Merchant).filter_by(email="default@merchant.com").first()
        if not merchant:
            merchant = Merchant(
                name="RecoverAI Merchant Test",
                email="default@merchant.com"
            )
            db.add(merchant)
            db.commit()
            db.refresh(merchant)
        return merchant

    @staticmethod
    def create_merchant(db: Session, merchant_in: MerchantCreate) -> Merchant:
        merchant = Merchant(name=merchant_in.name, email=merchant_in.email)
        db.add(merchant)
        db.commit()
        db.refresh(merchant)
        return merchant

    @staticmethod
    def get_or_create_customer(db: Session, name: str, email: str, merchant_id: Optional[str] = None) -> Customer:
        if not merchant_id:
            merchant = PaymentService.get_or_create_default_merchant(db)
            merchant_id = merchant.id

        customer = db.query(Customer).filter_by(email=email, merchant_id=merchant_id).first()
        if not customer:
            customer = Customer(
                merchant_id=merchant_id,
                name=name,
                email=email,
                total_payments=0,
                successful_payments=0,
                failed_payments=0
            )
            db.add(customer)
            db.commit()
            db.refresh(customer)
        return customer

    @staticmethod
    def record_payment(db: Session, payment_in: PaymentCreate) -> Payment:
        customer = db.query(Customer).filter_by(id=payment_in.customer_id).first()
        if not customer:
            raise ValueError(f"Customer with ID {payment_in.customer_id} not found")

        # Update customer payment counts
        customer.total_payments += 1
        if payment_in.failure_reason:
            customer.failed_payments += 1
            initial_status = "QUEUED"
        else:
            customer.successful_payments += 1
            initial_status = "RECOVERED"

        payment = Payment(
            customer_id=payment_in.customer_id,
            razorpay_payment_id=payment_in.razorpay_payment_id,
            razorpay_order_id=payment_in.razorpay_order_id,
            amount=payment_in.amount,
            currency=payment_in.currency,
            status=initial_status,
            payment_method=payment_in.payment_method,
            failure_reason=payment_in.failure_reason,
            raw_metadata=payment_in.raw_metadata or {},
            is_demo=payment_in.is_demo
        )
        db.add(payment)
        db.commit()
        db.refresh(payment)

        logger.info(f"Recorded payment {payment.id} for customer {customer.email} (Status: {payment.status})")
        return payment

    @staticmethod
    def get_payment_by_id(db: Session, payment_id: str, merchant_id: Optional[str] = None) -> Optional[Payment]:
        query = db.query(Payment).join(Customer)
        if merchant_id:
            query = query.filter(Customer.merchant_id == merchant_id)
        return query.filter(Payment.id == payment_id).first()

    @staticmethod
    def get_payment_by_razorpay_id(db: Session, razorpay_payment_id: str) -> Optional[Payment]:
        return db.query(Payment).filter(Payment.razorpay_payment_id == razorpay_payment_id).first()

    @staticmethod
    def list_payments(db: Session, merchant_id: Optional[str] = None, skip: int = 0, limit: int = 100) -> List[Payment]:
        query = db.query(Payment).join(Customer)
        if merchant_id:
            query = query.filter(Customer.merchant_id == merchant_id)
        return query.order_by(Payment.created_at.desc()).offset(skip).limit(limit).all()
