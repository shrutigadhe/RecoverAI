import uuid
from datetime import datetime, timezone
from sqlalchemy import (
    Column, String, Integer, Float, DateTime, ForeignKey, Text, JSON, Index, Boolean
)
from sqlalchemy.orm import relationship
from app.database import Base


def generate_uuid():
    return str(uuid.uuid4())


def utc_now():
    return datetime.now(timezone.utc)


class Merchant(Base):
    __tablename__ = "merchants"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    name = Column(String(255), nullable=False)
    email = Column(String(255), nullable=False, unique=True, index=True)
    password_hash = Column(String(255), nullable=True)  # Argon2 password hash
    created_at = Column(DateTime(timezone=True), default=utc_now)

    # Relationships
    customers = relationship("Customer", back_populates="merchant", cascade="all, delete-orphan")


class Customer(Base):
    __tablename__ = "customers"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    merchant_id = Column(String(36), ForeignKey("merchants.id"), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    email = Column(String(255), nullable=False, index=True)
    total_payments = Column(Integer, default=0)
    successful_payments = Column(Integer, default=0)
    failed_payments = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), default=utc_now)

    # Relationships
    merchant = relationship("Merchant", back_populates="customers")
    payments = relationship("Payment", back_populates="customer", cascade="all, delete-orphan")

    @property
    def success_rate(self) -> float:
        if self.total_payments == 0:
            return 0.0
        return round(self.successful_payments / self.total_payments, 2)


class Payment(Base):
    __tablename__ = "payments"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    razorpay_payment_id = Column(String(255), index=True, nullable=True, unique=True)
    razorpay_order_id = Column(String(255), index=True, nullable=True)
    customer_id = Column(String(36), ForeignKey("customers.id"), nullable=False, index=True)
    amount = Column(Float, nullable=False)  # Stored in main currency units (e.g. ₹3500.0)
    currency = Column(String(10), default="INR")
    status = Column(String(50), nullable=False, default="QUEUED", index=True)
    payment_method = Column(String(50), nullable=False)  # UPI, Card, Netbanking, etc.
    failure_reason = Column(String(255), nullable=True)
    raw_metadata = Column(JSON, nullable=True)
    is_demo = Column(Boolean, default=False)  # Clearly flag simulated vs real Razorpay events
    created_at = Column(DateTime(timezone=True), default=utc_now, index=True)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)

    # Relationships
    customer = relationship("Customer", back_populates="payments")
    recovery_case = relationship("RecoveryCase", back_populates="payment", uselist=False, cascade="all, delete-orphan")


class RecoveryCase(Base):
    __tablename__ = "recovery_cases"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    payment_id = Column(String(36), ForeignKey("payments.id"), nullable=False, unique=True, index=True)
    recovery_score = Column(Float, nullable=False, default=0.0)
    diagnosis = Column(Text, nullable=True)
    recommended_action = Column(String(50), nullable=True)  # RETRY, REMINDER, ESCALATE, STOP
    confidence = Column(Float, nullable=False, default=0.0)
    status = Column(String(50), nullable=False, default="QUEUED", index=True)
    recovered_amount = Column(Float, default=0.0)
    escalation_reason = Column(Text, nullable=True)
    retry_count = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), default=utc_now, index=True)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)

    # Relationships
    payment = relationship("Payment", back_populates="recovery_case")
    actions = relationship("RecoveryAction", back_populates="recovery_case", cascade="all, delete-orphan")
    audit_logs = relationship("AuditLog", back_populates="recovery_case", cascade="all, delete-orphan")

    @property
    def customer(self):
        return self.payment.customer if self.payment else None


class RecoveryAction(Base):
    __tablename__ = "recovery_actions"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    recovery_case_id = Column(String(36), ForeignKey("recovery_cases.id"), nullable=False, index=True)
    action = Column(String(50), nullable=False)  # RETRY, REMINDER, ESCALATE, STOP
    status = Column(String(50), nullable=False, default="PENDING")  # PENDING, EXECUTING, SUCCESS, FAILED, REJECTED
    attempt_number = Column(Integer, default=1)
    result = Column(JSON, nullable=True)
    executed_at = Column(DateTime(timezone=True), default=utc_now)
    completed_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    recovery_case = relationship("RecoveryCase", back_populates="actions")


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    recovery_case_id = Column(String(36), ForeignKey("recovery_cases.id"), nullable=True, index=True)
    event = Column(String(100), nullable=False, index=True)  # e.g., PAYMENT_FAILED, AI_DIAGNOSIS, POLICY_APPROVED
    actor = Column(String(50), nullable=False)  # SYSTEM, AI_AGENT, POLICY_ENGINE, MERCHANT, WEBHOOK
    action = Column(String(100), nullable=False)
    reason = Column(Text, nullable=True)
    policy_result = Column(String(50), nullable=True)  # APPROVED, REJECTED, N/A
    metadata_info = Column("metadata", JSON, nullable=True)
    timestamp = Column(DateTime(timezone=True), default=utc_now, index=True)

    # Relationships
    recovery_case = relationship("RecoveryCase", back_populates="audit_logs")
