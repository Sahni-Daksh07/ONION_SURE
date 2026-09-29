"""
Inspection Management and Finalization Service
Smart India Hackathon 2026 - Problem Statement PS26031

Handles:
- Idempotent inspection registration
- Image metadata attachment
- Manual review override with audit trail
- Report finalization with verifiable QR hash
"""

import uuid
import hashlib
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
from datetime import datetime, timezone

from ..models import (
    Inspection,
    InspectionImage,
    GradeResult as DBGradeResult,
    ManualReview,
    Report,
    Lot,
)
from .audit_service import AuditService


class InspectionService:
    @staticmethod
    def create_inspection(
        db: Session,
        lot_id: str,
        inspector_id: str,
        inspection_code: Optional[str] = None,
        sample_size: int = 0,
    ) -> Inspection:
        """Creates or idempotently retrieves an inspection."""
        code = inspection_code or f"INSP-{uuid.uuid4().hex[:8].upper()}"

        existing = db.query(Inspection).filter(Inspection.inspection_code == code).first()
        if existing:
            return existing

        lot = db.query(Lot).filter(Lot.id == lot_id).first()
        if not lot:
            raise ValueError(f"Lot '{lot_id}' does not exist.")

        inspection = Inspection(
            inspection_code=code,
            lot_id=lot_id,
            inspector_id=inspector_id,
            sample_size=sample_size,
            status="CAPTURING",
        )
        db.add(inspection)
        db.flush()

        AuditService.log_event(
            db=db,
            actor_id=inspector_id,
            action="CREATE_INSPECTION",
            entity_type="Inspection",
            entity_id=inspection.id,
            new_values={"inspection_code": code, "lot_id": lot_id},
        )
        db.commit()
        db.refresh(inspection)
        return inspection

    @staticmethod
    def attach_image_metadata(
        db: Session,
        inspection_id: str,
        storage_key: str,
        filename: str,
        file_size_bytes: int,
        content_type: str = "image/jpeg",
        sha256_hash: Optional[str] = None,
        quality_status: str = "PASSED",
        blur_variance: Optional[float] = None,
        mean_brightness: Optional[float] = None,
        contrast_std: Optional[float] = None,
        quality_reasons: Optional[list] = None,
        calibration_detected: bool = False,
        pixels_per_mm: Optional[float] = None,
        calibration_method: Optional[str] = None,
    ) -> InspectionImage:
        """Attaches validated image metadata without storing binary in database."""
        image = InspectionImage(
            inspection_id=inspection_id,
            storage_key=storage_key,
            filename=filename,
            file_size_bytes=file_size_bytes,
            content_type=content_type,
            sha256_hash=sha256_hash,
            quality_status=quality_status,
            blur_variance=blur_variance,
            mean_brightness=mean_brightness,
            contrast_std=contrast_std,
            quality_reasons=quality_reasons or [],
            calibration_detected=calibration_detected,
            pixels_per_mm=pixels_per_mm,
            calibration_method=calibration_method,
        )
        db.add(image)
        db.commit()
        db.refresh(image)
        return image

    @staticmethod
    def apply_manual_review(
        db: Session,
        grade_result_id: str,
        reviewer_id: str,
        reviewed_grade: str,
        reason: str,
        comments: Optional[str] = None,
    ) -> ManualReview:
        """
        Applies a human review override:
        Preserves original AI grade and logs an immutable manual review record.
        """
        grade_result = db.query(DBGradeResult).filter(DBGradeResult.id == grade_result_id).first()
        if not grade_result:
            raise ValueError(f"GradeResult '{grade_result_id}' not found.")

        original_grade = grade_result.grade
        grade_result.grade = reviewed_grade
        grade_result.requires_review = False

        review = ManualReview(
            inspection_id=grade_result.inspection_id,
            grade_result_id=grade_result.id,
            reviewer_id=reviewer_id,
            original_grade=original_grade,
            reviewed_grade=reviewed_grade,
            reason=reason,
            comments=comments,
            status="APPROVED",
        )
        db.add(review)

        # Update decision trace
        trace = list(grade_result.decision_trace)
        trace.append({
            "step": len(trace) + 1,
            "check": "manual_review_override",
            "reviewer_id": reviewer_id,
            "original_grade": original_grade,
            "reviewed_grade": reviewed_grade,
            "reason": reason,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })
        grade_result.decision_trace = trace

        AuditService.log_event(
            db=db,
            actor_id=reviewer_id,
            action="MANUAL_GRADE_OVERRIDE",
            entity_type="GradeResult",
            entity_id=grade_result.id,
            old_values={"grade": original_grade},
            new_values={"grade": reviewed_grade, "reason": reason},
        )
        db.commit()
        db.refresh(review)
        return review

    @staticmethod
    def finalize_inspection(
        db: Session,
        inspection_id: str,
        actor_id: str,
    ) -> Report:
        """
        Finalizes inspection and generates tamper-evident Report with QR hash.
        """
        inspection = db.query(Inspection).filter(Inspection.id == inspection_id).first()
        if not inspection:
            raise ValueError(f"Inspection '{inspection_id}' not found.")

        # Check existing report
        existing_report = db.query(Report).filter(Report.inspection_id == inspection_id).first()
        if existing_report:
            return existing_report

        report_code = f"REP-{inspection.inspection_code}"
        
        # SHA256 verifiable hash of inspection code + decision + timestamp
        now = datetime.now(timezone.utc)
        raw_hash_str = f"{inspection.id}:{inspection.inspection_code}:{inspection.lot_decision}:{now.isoformat()}"
        qr_hash = hashlib.sha256(raw_hash_str.encode("utf-8")).hexdigest()

        summary_metrics = {
            "total_onions": inspection.total_onions_evaluated,
            "grade_a_percentage": inspection.grade_a_percentage,
            "urs_percentage": inspection.urs_percentage,
            "reject_percentage": inspection.reject_percentage,
            "lot_decision": inspection.lot_decision,
            "decision_reason": inspection.decision_reason,
            "finalized_at": now.isoformat(),
        }

        report = Report(
            report_code=report_code,
            inspection_id=inspection.id,
            qr_verification_hash=qr_hash,
            summary_metrics=summary_metrics,
            is_finalized=True,
            generated_at=now,
        )
        db.add(report)
        db.flush()

        inspection.status = "COMPLETED"
        inspection.finalized_at = now

        AuditService.log_event(
            db=db,
            actor_id=actor_id,
            action="FINALIZE_INSPECTION_REPORT",
            entity_type="Report",
            entity_id=report.id,
            new_values={"report_code": report_code, "qr_hash": qr_hash},
        )

        db.commit()
        db.refresh(report)
        return report
