"""
Lot Management Router
Smart India Hackathon 2026 - Problem Statement PS26031
"""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ...database import get_db
from ...models import Lot, Farmer, ProcurementCentre
from ...schemas import LotCreate, LotResponse

router = APIRouter(prefix="/lots", tags=["Lots"])


@router.post("", response_model=LotResponse, status_code=status.HTTP_201_CREATED)
def create_lot(lot_in: LotCreate, db: Session = Depends(get_db)):
    """Registers a new lot arriving at a procurement centre."""
    # Ensure farmer exists
    farmer = db.query(Farmer).filter(Farmer.id == lot_in.farmer_id).first()
    if not farmer:
        raise HTTPException(status_code=404, detail="Farmer not found")

    # Ensure procurement centre exists
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
    )
    db.add(lot)
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
