from typing import TypedDict, Optional, Dict, Any


class RecoveryAgentState(TypedDict):
    payment_id: str
    amount: float
    payment_method: str
    failure_reason: Optional[str]
    retry_count: int
    customer_history: Dict[str, Any]

    # AI Diagnosis & Recommendation Output
    diagnosis: Optional[str]
    recovery_score: float
    recommended_action: Optional[str]
    confidence: float
    reason: Optional[str]
    ai_error: Optional[bool]

    # Policy & Execution
    policy_approved: bool
    policy_rule: Optional[str]
    policy_reason: Optional[str]
    execution_result: Optional[Dict[str, Any]]
    recovered_amount: float
    final_status: str
