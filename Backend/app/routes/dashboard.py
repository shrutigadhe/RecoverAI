from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.database import get_db
from app.models import Payment, RecoveryCase, AuditLog
from app.schemas import DashboardMetricsResponse

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


@router.get("/metrics", response_model=DashboardMetricsResponse)
def get_dashboard_metrics(db: Session = Depends(get_db)):
    """Fetches real-time dashboard analytics metrics."""

    # 1. Revenue at Risk
    total_at_risk = db.query(func.coalesce(func.sum(Payment.amount), 0.0)).filter(
        Payment.failure_reason.isnot(None)
    ).scalar()

    # 2. Revenue Recovered
    total_recovered = db.query(func.coalesce(func.sum(RecoveryCase.recovered_amount), 0.0)).scalar()

    # 3. Recovery Rate %
    recovery_rate = (total_recovered / total_at_risk * 100.0) if total_at_risk > 0 else 0.0

    # 4. Total Failed Payments Count
    total_failed = db.query(Payment).filter(Payment.failure_reason.isnot(None)).count()

    # 5. Recovery Attempts Count
    total_attempts = db.query(RecoveryCase).filter(
        RecoveryCase.status.in_(["ACTION_EXECUTED", "RECOVERED", "ACTION_PROPOSED"])
    ).count()

    # 6. Escalated Cases Count
    total_escalated = db.query(RecoveryCase).filter(RecoveryCase.status == "ESCALATED").count()

    # 7. Policy Rejections / Blocked Count
    total_blocked = db.query(AuditLog).filter(AuditLog.policy_result == "REJECTED").count()

    # 8. Recent 5 cases
    recent_cases = db.query(RecoveryCase).order_by(RecoveryCase.created_at.desc()).limit(5).all()

    return DashboardMetricsResponse(
        total_revenue_at_risk=round(total_at_risk, 2),
        total_revenue_recovered=round(total_recovered, 2),
        recovery_rate_percentage=round(recovery_rate, 1),
        total_failed_payments=total_failed,
        total_recovery_attempts=total_attempts,
        total_escalated_cases=total_escalated,
        total_blocked_attempts=total_blocked,
        recent_cases=recent_cases
    )
