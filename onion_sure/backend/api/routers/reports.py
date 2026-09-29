"""
Reports and Verification Router
Smart India Hackathon 2026 - Problem Statement PS26031

Endpoints:
- GET /reports           : List finalized reports with pagination
- GET /reports/{id}      : Retrieve specific report
- GET /reports/verify/{qr_hash} : Public verification endpoint for QR code certificate verification
"""

from datetime import datetime
from typing import List, Optional, Union
from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy.orm import Session

from ...database import get_db
from ...models.entities import Report, Inspection
from ...schemas.api_schemas import (
    ReportResponse,
    ReportVerifyResponse,
    PaginatedResponse,
)
from ...services.report_service import ReportService
from ...services.storage_service import image_storage_service

router = APIRouter(prefix="/reports", tags=["Reports & QR Verification"])


@router.get("", response_model=Union[PaginatedResponse[ReportResponse], List[ReportResponse]])
def list_reports(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    page: Optional[int] = Query(None, ge=1),
    page_size: Optional[int] = Query(None, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """Lists digital quality inspection reports with pagination."""
    query = db.query(Report)
    total = query.count()

    if page is not None:
        p_size = page_size or 20
        offset = (page - 1) * p_size
        items = query.order_by(Report.created_at.desc()).offset(offset).limit(p_size).all()
        total_pages = (total + p_size - 1) // p_size if total > 0 else 1
        return PaginatedResponse(
            items=items,
            total=total,
            page=page,
            page_size=p_size,
            total_pages=total_pages,
        )

    return query.order_by(Report.created_at.desc()).offset(skip).limit(limit).all()


@router.post("/generate/{inspection_id}", response_model=ReportResponse, status_code=status.HTTP_201_CREATED)
def generate_report_for_inspection(
    inspection_id: str,
    actor_id: str = "system",
    db: Session = Depends(get_db),
):
    """Generates a professional digital quality report with PDF and QR code for an inspection."""
    try:
        return ReportService.finalize_and_generate_report(
            db=db,
            inspection_id=inspection_id,
            actor_id=actor_id,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{report_id}", response_model=ReportResponse)
def get_report(report_id: str, db: Session = Depends(get_db)):
    """Retrieves report by ID or report_code."""
    report = db.query(Report).filter(
        (Report.id == report_id) | (Report.report_code == report_id)
    ).first()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    return report


@router.get("/{report_id}/pdf")
def download_report_pdf(report_id: str, db: Session = Depends(get_db)):
    """Downloads or views the official PDF quality report."""
    report = db.query(Report).filter(
        (Report.id == report_id) | (Report.report_code == report_id)
    ).first()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")

    pdf_bytes = None
    if report.pdf_storage_key:
        try:
            pdf_bytes = image_storage_service.get_file(report.pdf_storage_key)
        except Exception:
            pass

    if not pdf_bytes:
        # Generate dynamically if storage file was purged
        report_data = ReportService.aggregate_inspection_report_data(db, report.inspection_id)
        qr_bytes = ReportService.generate_qr_code_image(report_data["verification_url"])
        pdf_bytes = ReportService.generate_pdf_document(report_data, qr_bytes)

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f"inline; filename={report.report_code}.pdf",
        },
    )


@router.get("/{report_id}/qr")
def get_report_qr_image(report_id: str, db: Session = Depends(get_db)):
    """Retrieves the verification QR code PNG image for a report."""
    report = db.query(Report).filter(
        (Report.id == report_id) | (Report.report_code == report_id)
    ).first()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")

    metrics = report.summary_metrics or {}
    verification_url = metrics.get(
        "verification_url",
        f"https://onionsure.doca.gov.in/verify/{report.qr_verification_hash}",
    )
    qr_png = ReportService.generate_qr_code_image(verification_url)

    return Response(
        content=qr_png,
        media_type="image/png",
        headers={
            "Content-Disposition": f"inline; filename=qr_{report.report_code}.png",
        },
    )


@router.get("/verify/{qr_hash}", response_model=ReportVerifyResponse)
def verify_qr_certificate(qr_hash: str, db: Session = Depends(get_db)):
    """
    Public QR verification endpoint:
    Validates physical inspection certificate using SHA-256 cryptographic hash or verification ID.
    Privacy Rule: Does not expose sensitive personal information (phone, aadhaar, internal credentials).
    """
    verification = ReportService.verify_public_report(db, qr_hash)
    if not verification["is_valid"]:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Certificate hash not found or invalid",
        )

    # Fetch report to provide complete model fields
    report = db.query(Report).filter(
        (Report.qr_verification_hash == qr_hash)
        | (Report.report_code == qr_hash)
        | (Report.id == qr_hash)
    ).first()

    if not report:
        all_reps = db.query(Report).all()
        for r in all_reps:
            if isinstance(r.summary_metrics, dict) and r.summary_metrics.get("verification_id") == qr_hash:
                report = r
                break

    return ReportVerifyResponse(
        is_valid=verification["is_valid"],
        verification_status=verification["verification_status"],
        verification_id=verification.get("verification_id"),
        report_code=verification["report_code"],
        inspection_id=report.inspection_id if report else "INSP-VERIFIED",
        qr_verification_hash=report.qr_verification_hash if report else qr_hash,
        generated_at=report.generated_at if report else datetime.now(),
        summary_metrics=report.summary_metrics if report else {},
        lot_number=verification.get("lot_number"),
        lot_decision=verification.get("lot_decision"),
        grade_a_percentage=verification.get("grade_a_percentage"),
        urs_percentage=verification.get("urs_percentage"),
        reject_percentage=verification.get("reject_percentage"),
        average_diameter_mm=verification.get("average_diameter_mm"),
        model_version=verification.get("model_version"),
        policy_version=verification.get("policy_version"),
        verification_source="DoCA Official Verification Registry (SIH 2026 PS26031)",
    )
