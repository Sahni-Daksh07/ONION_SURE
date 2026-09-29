"""
Farmer Management Router
Smart India Hackathon 2026 - Problem Statement PS26031

Features:
- Registration and duplicate code detection
- Retrieval by ID
- Pagination, search, and geographical filtering (district, state)
- Updates with audit logging
"""

from typing import List, Optional, Union
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from ...database import get_db
from ...models.entities import Farmer
from ...schemas.api_schemas import (
    FarmerCreate,
    FarmerUpdate,
    FarmerResponse,
    PaginatedResponse,
)
from ...services.audit_service import AuditService

router = APIRouter(prefix="/farmers", tags=["Farmers"])


@router.post("", response_model=FarmerResponse, status_code=status.HTTP_201_CREATED)
def create_farmer(farmer_in: FarmerCreate, db: Session = Depends(get_db)):
    """Registers a new farmer in the system."""
    existing = db.query(Farmer).filter(Farmer.farmer_code == farmer_in.farmer_code).first()
    if existing:
        return existing

    farmer = Farmer(
        farmer_code=farmer_in.farmer_code,
        name=farmer_in.name,
        phone=farmer_in.phone,
        village=farmer_in.village,
        district=farmer_in.district,
        state=farmer_in.state,
        aadhaar_masked=farmer_in.aadhaar_masked,
    )
    db.add(farmer)
    db.flush()

    AuditService.log_event(
        db=db,
        action="FARMER_REGISTERED",
        entity_type="Farmer",
        entity_id=farmer.id,
        new_values={"farmer_code": farmer.farmer_code, "name": farmer.name},
    )

    db.commit()
    db.refresh(farmer)
    return farmer


@router.get("/{farmer_id}", response_model=FarmerResponse)
def get_farmer(farmer_id: str, db: Session = Depends(get_db)):
    """Retrieves farmer details by ID."""
    farmer = db.query(Farmer).filter(Farmer.id == farmer_id).first()
    if not farmer:
        raise HTTPException(status_code=404, detail="Farmer not found")
    return farmer


@router.patch("/{farmer_id}", response_model=FarmerResponse)
def update_farmer(
    farmer_id: str,
    farmer_update: FarmerUpdate,
    db: Session = Depends(get_db),
):
    """Updates farmer profile information with audit trail."""
    farmer = db.query(Farmer).filter(Farmer.id == farmer_id).first()
    if not farmer:
        raise HTTPException(status_code=404, detail="Farmer not found")

    old_values = {
        "name": farmer.name,
        "phone": farmer.phone,
        "village": farmer.village,
        "district": farmer.district,
        "state": farmer.state,
    }

    update_data = farmer_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(farmer, field, value)

    AuditService.log_event(
        db=db,
        action="FARMER_UPDATED",
        entity_type="Farmer",
        entity_id=farmer.id,
        old_values=old_values,
        new_values=update_data,
    )

    db.commit()
    db.refresh(farmer)
    return farmer


@router.get("", response_model=Union[PaginatedResponse[FarmerResponse], List[FarmerResponse]])
def list_farmers(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    page: Optional[int] = Query(None, ge=1),
    page_size: Optional[int] = Query(None, ge=1, le=100),
    search: Optional[str] = None,
    district: Optional[str] = None,
    state: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """
    Lists registered farmers with optional search, district/state filtering,
    and pagination (supports either page/page_size or skip/limit).
    """
    query = db.query(Farmer)

    if search:
        query = query.filter(
            (Farmer.name.ilike(f"%{search}%"))
            | (Farmer.farmer_code.ilike(f"%{search}%"))
            | (Farmer.phone.ilike(f"%{search}%"))
        )
    if district:
        query = query.filter(Farmer.district.ilike(district))
    if state:
        query = query.filter(Farmer.state.ilike(state))

    total = query.count()

    if page is not None:
        p_size = page_size or 20
        offset = (page - 1) * p_size
        items = query.order_by(Farmer.created_at.desc()).offset(offset).limit(p_size).all()
        total_pages = (total + p_size - 1) // p_size if total > 0 else 1
        return PaginatedResponse(
            items=items,
            total=total,
            page=page,
            page_size=p_size,
            total_pages=total_pages,
        )

    return query.order_by(Farmer.created_at.desc()).offset(skip).limit(limit).all()
