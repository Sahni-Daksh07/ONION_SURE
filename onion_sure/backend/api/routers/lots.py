"""
Lot Management Router
Smart India Hackathon 2026 - Problem Statement PS26031

Features:
- Registration and farmer/centre validation
- Retrieval by ID
- Filtering by farmer, procurement centre, status, variety
- Pagination and updates with audit logging
"""

from typing import List, Optional, Union
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from ...database import get_db
from ...models.entities import Lot, Farmer, ProcurementCentre
from ...schemas.api_schemas import LotCreate, LotUpdate, LotResponse, PaginatedResponse
from ...services.audit_service import AuditService

router = APIRouter(prefix="/lots", tags=["Lots"])


@router.post("", response_model=LotResponse, status_code=status.HTTP_201_CREATED)
def create_lot(lot_in: LotCreate, db: Session = Depends(get_db)):
    """Registers a new lot arriving at a procurement centre."""
    farmer = db.query(Farmer).filter(Farmer.id == lot_in.farmer_id).first()
    if not farmer:
        raise HTTPException(status_code=404, detail="Farmer not found")

    centre = db.query(ProcurementCentre).filter(ProcurementCentre.id == lot_in.procurement_centre_id).first()
    if not centre:
        raise HTTPException(status_code=404, detail="Procurement centre not found")

    existing = db.query(Lot).filter(Lot.lot_number == lot_in.lot_number).first()
    if existing:
        return existing

    lot = Lot(
        lot_number=lot_in.lot_number,
        farmer_id=lot_in.farmer_id,
        procurement_centre_id=lot_in.procurement_centre_id,
        variety=lot_in.variety,
        quantity_quintals=lot_in.quantity_quintals,
        bag_count=lot_in.bag_count,
        status="REGISTERED",
    )
    db.add(lot)
    db.flush()

    AuditService.log_event(
        db=db,
        action="LOT_REGISTERED",
        entity_type="Lot",
        entity_id=lot.id,
        new_values={"lot_number": lot.lot_number, "quantity_quintals": lot.quantity_quintals},
    )

    db.commit()
    db.refresh(lot)
    return lot


@router.get("/{lot_id}", response_model=LotResponse)
def get_lot(lot_id: str, db: Session = Depends(get_db)):
    """Retrieves lot details by ID."""
    lot = db.query(Lot).filter(Lot.id == lot_id).first()
    if not lot:
        raise HTTPException(status_code=404, detail="Lot not found")
    return lot


@router.patch("/{lot_id}", response_model=LotResponse)
def update_lot(
    lot_id: str,
    lot_update: LotUpdate,
    db: Session = Depends(get_db),
):
    """Updates lot details (status, bag count, quantity) with audit logging."""
    lot = db.query(Lot).filter(Lot.id == lot_id).first()
    if not lot:
        raise HTTPException(status_code=404, detail="Lot not found")

    old_values = {
        "status": lot.status,
        "quantity_quintals": lot.quantity_quintals,
        "bag_count": lot.bag_count,
        "variety": lot.variety,
    }

    update_data = lot_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(lot, field, value)

    AuditService.log_event(
        db=db,
        action="LOT_UPDATED",
        entity_type="Lot",
        entity_id=lot.id,
        old_values=old_values,
        new_values=update_data,
    )

    db.commit()
    db.refresh(lot)
    return lot


@router.get("", response_model=Union[PaginatedResponse[LotResponse], List[LotResponse]])
def list_lots(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    page: Optional[int] = Query(None, ge=1),
    page_size: Optional[int] = Query(None, ge=1, le=100),
    farmer_id: Optional[str] = None,
    procurement_centre_id: Optional[str] = None,
    status: Optional[str] = None,
    variety: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """Lists registered lots with filtering and pagination."""
    query = db.query(Lot)
    if farmer_id:
        query = query.filter(Lot.farmer_id == farmer_id)
    if procurement_centre_id:
        query = query.filter(Lot.procurement_centre_id == procurement_centre_id)
    if status:
        query = query.filter(Lot.status == status.upper())
    if variety:
        query = query.filter(Lot.variety.ilike(f"%{variety}%"))

    total = query.count()

    if page is not None:
        p_size = page_size or 20
        offset = (page - 1) * p_size
        items = query.order_by(Lot.created_at.desc()).offset(offset).limit(p_size).all()
        total_pages = (total + p_size - 1) // p_size if total > 0 else 1
        return PaginatedResponse(
            items=items,
            total=total,
            page=page,
            page_size=p_size,
            total_pages=total_pages,
        )

    return query.order_by(Lot.created_at.desc()).offset(skip).limit(limit).all()
