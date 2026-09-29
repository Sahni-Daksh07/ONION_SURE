"""
Inspection and Grading Orchestration Router
Smart India Hackathon 2026 - Problem Statement PS26031

Connects mobile inspection workflow and deterministic grading engine to PostgreSQL.
"""

from typing import List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ...database import get_db
from ...models import Inspection, Report
from ...schemas import (
    InspectionCreate,
    InspectionResponse,
    ImageMetadataCreate,
    ImageMetadataResponse,
    PersistGradeResultRequest,
    GradeResultResponse,
    ManualReviewCreate,
    ManualReviewResponse,
    ReportResponse,
)
from ...services.inspection_service import InspectionService
from ...services.grading_persistence_service import GradingPersistenceService

router = APIRouter(prefix="/inspections", tags=["Inspections"])


@router.post("", response_model=InspectionResponse, status_code=status.HTTP_201_CREATED)
def create_inspection(insp_in: InspectionCreate, db: Session = Depends(get_db)):
    """Creates a new inspection record or returns existing matching code (idempotent)."""
    try:
        return InspectionService.create_inspection(
            db=db,
            lot_id=insp_in.lot_id,
            inspector_id=insp_in.inspector_id,
            inspection_code=insp_in.inspection_code,
            sample_size=insp_in.sample_size,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{inspection_id}", response_model=InspectionResponse)
def get_inspection(inspection_id: str, db: Session = Depends(get_db)):
    """Retrieves full inspection state including aggregated grade percentages."""
    inspection = db.query(Inspection).filter(Inspection.id == inspection_id).first()
    if not inspection:
        raise HTTPException(status_code=404, detail="Inspection not found")
    return inspection


@router.patch("/{inspection_id}/status", response_model=InspectionResponse)
def update_inspection_status(
    inspection_id: str,
    status: str,
    db: Session = Depends(get_db),
):
    """Updates inspection status (e.g. DRAFT, CAPTURING, PROCESSING, COMPLETED)."""
    inspection = db.query(Inspection).filter(Inspection.id == inspection_id).first()
    if not inspection:
        raise HTTPException(status_code=404, detail="Inspection not found")
    inspection.status = status
    db.commit()
    db.refresh(inspection)
    return inspection


@router.post("/{inspection_id}/images", response_model=ImageMetadataResponse, status_code=status.HTTP_201_CREATED)
def attach_inspection_image_metadata(
    inspection_id: str,
    img_in: ImageMetadataCreate,
    db: Session = Depends(get_db),
):
    """Stores validated image metadata without storing large binaries in PostgreSQL."""
    inspection = db.query(Inspection).filter(Inspection.id == inspection_id).first()
    if not inspection:
        raise HTTPException(status_code=404, detail="Inspection not found")

    return InspectionService.attach_image_metadata(
        db=db,
        inspection_id=inspection_id,
        storage_key=img_in.storage_key,
        filename=img_in.filename,
        file_size_bytes=img_in.file_size_bytes,
        content_type=img_in.content_type,
        sha256_hash=img_in.sha256_hash,
        quality_status=img_in.quality_status,
        blur_variance=img_in.blur_variance,
        mean_brightness=img_in.mean_brightness,
        contrast_std=img_in.contrast_std,
        quality_reasons=img_in.quality_reasons,
        calibration_detected=img_in.calibration_detected,
        pixels_per_mm=img_in.pixels_per_mm,
        calibration_method=img_in.calibration_method,
    )


@router.post("/{inspection_id}/grade", response_model=List[GradeResultResponse])
def evaluate_and_persist_grading(
    inspection_id: str,
    grade_req: PersistGradeResultRequest,
    db: Session = Depends(get_db),
):
    """
    Feeds structured observations into the deterministic grading engine,
    persisting detections, measurements, defect predictions, decision traces,
    and updating the inspection lot summary.
    """
    try:
        observations_dicts = [obs.model_dump() for obs in grade_req.observations]
        _, db_grade_results = GradingPersistenceService.evaluate_and_persist_inspection(
            db=db,
            inspection_id=inspection_id,
            observations_data=observations_dicts,
            policy_version_str=grade_req.policy_version,
            model_version_str=grade_req.model_version,
        )
        return db_grade_results
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{inspection_id}/manual-review", response_model=ManualReviewResponse)
def submit_manual_review(
    inspection_id: str,
    review_in: ManualReviewCreate,
    db: Session = Depends(get_db),
):
    """
    Submits an inspector/supervisor grade override:
    Records original vs new grade, reason, reviewer, and decision trace step.
    """
    try:
        return InspectionService.apply_manual_review(
            db=db,
            grade_result_id=review_in.grade_result_id,
            reviewer_id=review_in.reviewer_id,
            reviewed_grade=review_in.reviewed_grade,
            reason=review_in.reason,
            comments=review_in.comments,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{inspection_id}/finalize", response_model=ReportResponse)
def finalize_inspection_and_generate_report(
    inspection_id: str,
    actor_id: str = "system",
    db: Session = Depends(get_db),
):
    """Finalizes an inspection and generates the immutable digital quality report with QR hash."""
    try:
        return InspectionService.finalize_inspection(
            db=db,
            inspection_id=inspection_id,
            actor_id=actor_id,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
