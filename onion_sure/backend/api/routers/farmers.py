"""
Farmer Management Router
Smart India Hackathon 2026 - Problem Statement PS26031
"""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ...database import get_db
from ...models import Farmer
from ...schemas import FarmerCreate, FarmerResponse

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


@router.get("", response_model=List[FarmerResponse])
def list_farmers(skip: int = 0, limit: int = 50, db: Session = Depends(get_db)):
    """Lists registered farmers."""
    return db.query(Farmer).offset(skip).limit(limit).all()
