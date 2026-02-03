from sqlalchemy.orm import Session

from app.models.audit_log import AuditLog


class AuditService:
    @staticmethod
    def log_action(
        db: Session,
        user_id: int,
        action: str,
        document_id: int | None = None,
        details: str | None = None,
    ) -> AuditLog:
        """Create an audit log entry."""
        audit_log = AuditLog(
            user_id=user_id,
            action=action,
            document_id=document_id,
            details=details,
        )
        db.add(audit_log)
        db.commit()
        db.refresh(audit_log)
        return audit_log
