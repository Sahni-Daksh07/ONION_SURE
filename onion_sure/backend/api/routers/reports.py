"""
Reports and Verification Router
Smart India Hackathon 2026 - Problem Statement PS26031

Endpoints:
- GET /reports           : List finalized reports with pagination
- GET /reports/{id}      : Retrieve specific report
- GET /reports/verify/{qr_hash} : Public verification endpoint for QR code certificate verification
"""

from typing import List, Optional, Union
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from ...database import get_db
from ...models.entities import Report, Inspection
from ...schemas.api_schemas import (
    ReportResponse,
    ReportVerifyResponse,
    PaginatedResponse,
)

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


@router.get("/{report_id}", response_model=ReportResponse)
def get_report(report_id: str, db: Session = Depends(get_db)):
    """Retrieves report by ID."""
    report = db.query(Report).filter(Report.id == report_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    return report


@router.get("/verify/{qr_hash}", response_model=ReportVerifyResponse)
def verify_qr_certificate(qr_hash: str, db: Session = Depends(get_db)):
    """
    Public QR verification endpoint:
    Validates physical inspection certificate using SHA-256 cryptographic hash.
    Does not expose sensitive internal credentials.
    """
    report = db.query(Report).filter(Report.qr_verification_hash == qr_hash).first()
    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Certificate hash not found or invalid",
        )

    return ReportVerifyResponse(
        is_valid=report.is_finalized,
        report_code=report.report_code,
        inspection_id=report.inspection_id,
        qr_verification_hash=report.qr_verification_hash,
        generated_at=report.generated_at,
        summary_metrics=report.summary_metrics,
        verification_source="DoCA Official Verification Registry (SIH 2026 PS26031)",
    )
