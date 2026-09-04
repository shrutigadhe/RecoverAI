import logging
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
from app.models import AuditLog

logger = logging.getLogger("recoverai.audit")


class AuditLogger:
    @staticmethod
    def log(
        db: Session,
        event: str,
        actor: str,
        action: str,
        recovery_case_id: Optional[str] = None,
        reason: Optional[str] = None,
        policy_result: Optional[str] = None,
        metadata_info: Optional[Dict[str, Any]] = None
    ) -> AuditLog:
        """
        Appends an immutable audit log entry.
        """
        audit = AuditLog(
            recovery_case_id=recovery_case_id,
            event=event,
            actor=actor,
            action=action,
            reason=reason,
            policy_result=policy_result,
            metadata_info=metadata_info or {}
        )
        db.add(audit)
        db.commit()
        db.refresh(audit)
        logger.info(f"AUDIT LOG [{event}] by {actor}: {action} (Policy: {policy_result})")
        return audit
