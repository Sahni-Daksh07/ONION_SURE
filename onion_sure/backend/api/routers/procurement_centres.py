"""
Procurement Centre Management Router
Smart India Hackathon 2026 - Problem Statement PS26031

Features:
- Registration and uniqueness check
- Retrieval by ID
- Pagination and geographic filtering (district, state)
"""

from typing import List, Optional, Union
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from ...database import get_db
from ...models.entities import ProcurementCentre
from ...schemas.api_schemas import (
    ProcurementCentreCreate,
    ProcurementCentreResponse,
    PaginatedResponse,
)

router = APIRouter(prefix="/procurement-centres", tags=["Procurement Centres"])


@router.post("", response_model=ProcurementCentreResponse, status_code=status.HTTP_201_CREATED)
def create_procurement_centre(pc_in: ProcurementCentreCreate, db: Session = Depends(get_db)):
    """Registers a new procurement centre."""
    existing = db.query(ProcurementCentre).filter(ProcurementCentre.centre_code == pc_in.centre_code).first()
    if existing:
        return existing

    centre = ProcurementCentre(
        centre_code=pc_in.centre_code,
        name=pc_in.name,
        district=pc_in.district,
        state=pc_in.state,
    )
    db.add(centre)
    db.commit()
    db.refresh(centre)
    return centre


@router.get("/{centre_id}", response_model=ProcurementCentreResponse)
def get_procurement_centre(centre_id: str, db: Session = Depends(get_db)):
    """Retrieves procurement centre details by ID."""
    centre = db.query(ProcurementCentre).filter(ProcurementCentre.id == centre_id).first()
    if not centre:
        raise HTTPException(status_code=404, detail="Procurement centre not found")
    return centre


@router.get("", response_model=Union[PaginatedResponse[ProcurementCentreResponse], List[ProcurementCentreResponse]])
def list_procurement_centres(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    page: Optional[int] = Query(None, ge=1),
    page_size: Optional[int] = Query(None, ge=1, le=100),
    district: Optional[str] = None,
    state: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """Lists registered procurement centres with optional filters and pagination."""
    query = db.query(ProcurementCentre)
    if district:
        query = query.filter(ProcurementCentre.district.ilike(district))
    if state:
        query = query.filter(ProcurementCentre.state.ilike(state))

    total = query.count()

    if page is not None:
        p_size = page_size or 20
        offset = (page - 1) * p_size
        items = query.order_by(ProcurementCentre.created_at.desc()).offset(offset).limit(p_size).all()
        total_pages = (total + p_size - 1) // p_size if total > 0 else 1
        return PaginatedResponse(
            items=items,
            total=total,
            page=page,
            page_size=p_size,
            total_pages=total_pages,
        )

    return query.order_by(ProcurementCentre.created_at.desc()).offset(skip).limit(limit).all()
