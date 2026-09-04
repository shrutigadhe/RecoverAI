from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import AuditLog
from app.schemas import AuditLogResponse

router = APIRouter(prefix="/audit-logs", tags=["Audit Logs"])


@router.get("", response_model=List[AuditLogResponse])
def get_audit_logs(
    event: Optional[str] = Query(None, description="Filter by event type"),
    actor: Optional[str] = Query(None, description="Filter by actor"),
    recovery_case_id: Optional[str] = Query(None, description="Filter by recovery case ID"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db)
):
    """Fetches searchable audit trail entries."""
    query = db.query(AuditLog)
    if event:
        query = query.filter(AuditLog.event == event)
    if actor:
        query = query.filter(AuditLog.actor == actor)
    if recovery_case_id:
        query = query.filter(AuditLog.recovery_case_id == recovery_case_id)
        
    return query.order_by(AuditLog.timestamp.desc()).offset(skip).limit(limit).all()
