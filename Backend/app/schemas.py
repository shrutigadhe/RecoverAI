from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, ConfigDict, Field, EmailStr


# Auth Schemas
class RegisterRequest(BaseModel):
    name: str = Field(..., min_length=2)
    email: str = Field(..., description="Merchant email address")
    password: str = Field(..., min_length=6, description="Merchant password")


class LoginRequest(BaseModel):
    email: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    merchant: Dict[str, Any]


# Merchant Schemas
class MerchantBase(BaseModel):
    name: str
    email: str


class MerchantCreate(MerchantBase):
    password: Optional[str] = None


class MerchantResponse(MerchantBase):
    id: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# Customer Schemas
class CustomerBase(BaseModel):
    name: str
    email: str


class CustomerCreate(CustomerBase):
    merchant_id: str


class CustomerResponse(CustomerBase):
    id: str
    merchant_id: str
    total_payments: int
    successful_payments: int
    failed_payments: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# Payment Schemas
class PaymentCreate(BaseModel):
    customer_id: str
    amount: float
    currency: str = "INR"
    payment_method: str  # UPI, Card, Netbanking, etc.
    failure_reason: Optional[str] = None
    razorpay_payment_id: Optional[str] = None
    razorpay_order_id: Optional[str] = None
    raw_metadata: Optional[Dict[str, Any]] = None
    is_demo: bool = False


class PaymentResponse(BaseModel):
    id: str
    customer_id: str
    razorpay_payment_id: Optional[str] = None
    razorpay_order_id: Optional[str] = None
    amount: float
    currency: str
    status: str
    payment_method: str
    failure_reason: Optional[str] = None
    is_demo: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# AI Structured Output Schema
class AIRecommendationSchema(BaseModel):
    diagnosis: str = Field(..., description="Root cause diagnosis of the payment failure")
    recovery_score: float = Field(..., ge=0.0, le=1.0, description="Calculated recovery score between 0 and 1")
    recommended_action: str = Field(..., description="Recommended action: RETRY, REMINDER, ESCALATE, STOP")
    confidence: float = Field(..., ge=0.0, le=1.0, description="AI confidence level between 0 and 1")
    reason: str = Field(..., description="Detailed explanation for the recommended recovery action")


# Policy Evaluation Result Schema
class PolicyEvaluationResult(BaseModel):
    approved: bool
    rule_name: str
    reason: str
    metadata: Optional[Dict[str, Any]] = None


# Recovery Action Schema
class RecoveryActionResponse(BaseModel):
    id: str
    recovery_case_id: str
    action: str
    status: str
    attempt_number: int
    result: Optional[Dict[str, Any]] = None
    executed_at: datetime
    completed_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


# Recovery Case Schemas
class RecoveryCaseResponse(BaseModel):
    id: str
    payment_id: str
    recovery_score: float
    diagnosis: Optional[str] = None
    recommended_action: Optional[str] = None
    confidence: float
    status: str
    recovered_amount: float
    escalation_reason: Optional[str] = None
    retry_count: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class RecoveryCaseDetailResponse(RecoveryCaseResponse):
    payment: PaymentResponse
    customer: CustomerResponse
    actions: List[RecoveryActionResponse] = []

    model_config = ConfigDict(from_attributes=True)


# Audit Log Schema
class AuditLogResponse(BaseModel):
    id: str
    recovery_case_id: Optional[str] = None
    event: str
    actor: str
    action: str
    reason: Optional[str] = None
    policy_result: Optional[str] = None
    metadata_info: Optional[Dict[str, Any]] = Field(None, alias="metadata_info")
    timestamp: datetime

    model_config = ConfigDict(from_attributes=True)


# Dashboard Metrics Schema
class DashboardMetricsResponse(BaseModel):
    total_revenue_at_risk: float
    total_revenue_recovered: float
    recovery_rate_percentage: float
    total_failed_payments: int
    total_recovery_attempts: int
    total_escalated_cases: int
    total_blocked_attempts: int
    recent_cases: List[RecoveryCaseResponse] = []


# Batch Evaluation Schema
class EvaluationResultResponse(BaseModel):
    total_cases: int
    total_revenue_at_risk: float
    recovery_attempts: int
    successful_recoveries: int
    total_recovered_revenue: float
    recovery_rate_percentage: float
    escalation_rate_percentage: float
    policy_rejection_rate_percentage: float
    cases: List[Dict[str, Any]] = []
