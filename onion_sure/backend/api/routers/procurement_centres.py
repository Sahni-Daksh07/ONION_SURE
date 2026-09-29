"""
Procurement Centre Management Router
Smart India Hackathon 2026 - Problem Statement PS26031
"""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ...database import get_db
from ...models import ProcurementCentre
from ...schemas import ProcurementCentreCreate, ProcurementCentreResponse

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


@router.get("", response_model=List[ProcurementCentreResponse])
def list_procurement_centres(skip: int = 0, limit: int = 50, db: Session = Depends(get_db)):
    """Lists registered procurement centres."""
    return db.query(ProcurementCentre).offset(skip).limit(limit).all()
