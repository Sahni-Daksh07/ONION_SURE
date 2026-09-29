"""
Audit Logging Service
Smart India Hackathon 2026 - Problem Statement PS26031

Records tamper-evident audit logs for critical inspection and grading operations.
"""

from typing import Optional, Dict, Any
from sqlalchemy.orm import Session

from ..models import AuditLog


class AuditService:
    @staticmethod
    def log_event(
        db: Session,
        action: str,
        entity_type: str,
        entity_id: str,
        actor_id: Optional[str] = None,
        old_values: Optional[Dict[str, Any]] = None,
        new_values: Optional[Dict[str, Any]] = None,
        ip_address: Optional[str] = None,
        correlation_id: Optional[str] = None,
    ) -> AuditLog:
        audit_entry = AuditLog(
            actor_id=actor_id,
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            old_values=old_values,
            new_values=new_values,
            ip_address=ip_address,
            correlation_id=correlation_id,
        )
        db.add(audit_entry)
        return audit_entry
