from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas import RecoveryCaseResponse, RecoveryCaseDetailResponse
from app.services.recovery_service import RecoveryService
from app.models import Merchant
from app.utils.security import get_current_merchant

router = APIRouter(prefix="/recovery", tags=["Recovery"])


@router.get("/cases", response_model=List[RecoveryCaseResponse])
def get_recovery_cases(
    status: Optional[str] = Query(None, description="Filter by status"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    current_merchant: Merchant = Depends(get_current_merchant),
    db: Session = Depends(get_db)
):
    """Lists all recovery cases for authenticated merchant."""
    return RecoveryService.list_cases(db, merchant_id=current_merchant.id, status=status, skip=skip, limit=limit)


@router.get("/cases/{case_id}", response_model=RecoveryCaseDetailResponse)
def get_recovery_case_details(
    case_id: str,
    current_merchant: Merchant = Depends(get_current_merchant),
    db: Session = Depends(get_db)
):
    """Fetches details for a recovery case owned by authenticated merchant."""
    case = RecoveryService.get_case(db, case_id, merchant_id=current_merchant.id)
    if not case:
        raise HTTPException(status_code=404, detail="Recovery case not found")
    return case


@router.post("/cases/{case_id}/run", response_model=RecoveryCaseResponse)
def run_recovery_pipeline(
    case_id: str,
    current_merchant: Merchant = Depends(get_current_merchant),
    db: Session = Depends(get_db)
):
    """Triggers recovery workflow for merchant's case."""
    case = RecoveryService.get_case(db, case_id, merchant_id=current_merchant.id)
    if not case:
        raise HTTPException(status_code=404, detail="Recovery case not found")
    try:
        return RecoveryService.run_recovery_workflow(db, case_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error executing recovery workflow: {str(e)}")


@router.post("/cases/{case_id}/approve", response_model=RecoveryCaseResponse)
def merchant_approve_case(
    case_id: str,
    notes: Optional[str] = Query(None, description="Merchant approval notes"),
    current_merchant: Merchant = Depends(get_current_merchant),
    db: Session = Depends(get_db)
):
    """Merchant manual approval for an escalated case."""
    case = RecoveryService.get_case(db, case_id, merchant_id=current_merchant.id)
    if not case:
        raise HTTPException(status_code=404, detail="Recovery case not found")
    return RecoveryService.approve_case(db, case_id, notes=notes)


@router.post("/cases/{case_id}/escalate", response_model=RecoveryCaseResponse)
def merchant_escalate_case(
    case_id: str,
    reason: str = Query("Merchant requested manual escalation"),
    current_merchant: Merchant = Depends(get_current_merchant),
    db: Session = Depends(get_db)
):
    """Merchant manual escalation."""
    case = RecoveryService.get_case(db, case_id, merchant_id=current_merchant.id)
    if not case:
        raise HTTPException(status_code=404, detail="Recovery case not found")
    return RecoveryService.escalate_case(db, case_id, reason=reason)
