"""
Offline Synchronization Router
Smart India Hackathon 2026 - Problem Statement PS26031

Endpoints:
- POST /sync/batch: Idempotent batch synchronization for Flutter mobile inspections
- GET  /sync/status/{client_id}: Check status of sync records by client_id
"""

from typing import List, Dict, Any
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from datetime import datetime, timezone
import uuid

from ...database import get_db
from ...models.entities import (
    SyncRecord,
    Farmer,
    Lot,
    Inspection,
    InspectionImage,
    GradeResult,
    User,
)
from ...schemas.api_schemas import (
    SyncBatchRequest,
    SyncBatchResponse,
    SyncItemResponse,
)
from ...services.audit_service import AuditService

router = APIRouter(prefix="/sync", tags=["Offline Synchronization"])


@router.post("/batch", response_model=SyncBatchResponse, status_code=status.HTTP_200_OK)
def sync_batch(batch_in: SyncBatchRequest, db: Session = Depends(get_db)):
    """
    Idempotent batch synchronization endpoint for Flutter mobile offline client.
    - Uses sync_key (client-generated UUID) to prevent duplicate processing.
    - If sync_key already exists in sync_records, acknowledges without duplicate inserts.
    - Automatically materializes offline entities into database without duplication.
    """
    results: List[SyncItemResponse] = []
    success_count = 0
    failed_count = 0

    for item in batch_in.items:
        existing = db.query(SyncRecord).filter(SyncRecord.sync_key == item.sync_key).first()
        if existing:
            # Idempotent response: return existing record without duplicate insertion
            results.append(
                SyncItemResponse(
                    sync_key=existing.sync_key,
                    entity_type=existing.entity_type,
                    entity_id=existing.entity_id,
                    status=existing.status,
                    synced_at=existing.synced_at,
                    error_details=existing.error_details,
                )
            )
            success_count += 1
            continue

        try:
            now = datetime.now(timezone.utc)
            payload = item.payload or {}

            with db.begin_nested():
                # Materialize entity if not yet present
                if item.entity_type == "Farmer":
                    f_existing = db.query(Farmer).filter(
                        (Farmer.id == item.entity_id) | (Farmer.farmer_code == payload.get("farmer_code"))
                    ).first()
                    if not f_existing:
                        farmer = Farmer(
                            id=item.entity_id,
                            farmer_code=payload.get("farmer_code", f"FARM-SYNC-{item.entity_id[:6].upper()}"),
                            name=payload.get("name") or payload.get("full_name", "Offline Farmer"),
                            phone=payload.get("phone") or payload.get("phone_number", "9999900000"),
                            village=payload.get("village", "Niphad"),
                            district=payload.get("district", "Nashik"),
                            state=payload.get("state", "Maharashtra"),
                            aadhaar_masked=payload.get("aadhaar_masked"),
                        )
                        db.add(farmer)
                        db.flush()

                elif item.entity_type == "Lot":
                    lot_existing = db.query(Lot).filter(
                        (Lot.id == item.entity_id) | (Lot.lot_number == payload.get("lot_number")) | (Lot.lot_number == payload.get("lot_code"))
                    ).first()
                    if not lot_existing:
                        lot = Lot(
                            id=item.entity_id,
                            lot_number=payload.get("lot_number") or payload.get("lot_code", f"LOT-SYNC-{item.entity_id[:6].upper()}"),
                            farmer_id=payload.get("farmer_id"),
                            procurement_centre_id=payload.get("procurement_centre_id"),
                            variety=payload.get("variety", "Red"),
                            quantity_quintals=float(payload.get("quantity_quintals", 10.0)),
                            bag_count=int(payload.get("bag_count") or payload.get("number_of_bags", 20)),
                            status=payload.get("status", "REGISTERED"),
                        )
                        db.add(lot)
                        db.flush()

                elif item.entity_type == "Inspection":
                    insp_existing = db.query(Inspection).filter(
                        (Inspection.id == item.entity_id) | (Inspection.inspection_code == payload.get("inspection_code"))
                    ).first()
                    if not insp_existing and payload.get("lot_id"):
                        insp_user_id = payload.get("inspector_id")
                        if not insp_user_id:
                            first_u = db.query(User).first()
                            insp_user_id = first_u.id if first_u else None

                        if insp_user_id:
                            insp = Inspection(
                                id=item.entity_id,
                                inspection_code=payload.get("inspection_code", f"INSP-SYNC-{item.entity_id[:6].upper()}"),
                                lot_id=payload.get("lot_id"),
                                inspector_id=insp_user_id,
                                sample_size=int(payload.get("sample_size") or payload.get("sample_size_count", 50)),
                                status=payload.get("status", "CAPTURING"),
                                total_onions_evaluated=int(payload.get("total_onions_evaluated", 0)),
                                grade_a_count=int(payload.get("grade_a_count", 0)),
                                grade_a_percentage=float(payload.get("grade_a_percentage", 0.0)),
                                urs_count=int(payload.get("urs_count", 0)),
                                urs_percentage=float(payload.get("urs_percentage", 0.0)),
                                reject_count=int(payload.get("reject_count", 0)),
                                reject_percentage=float(payload.get("reject_percentage", 0.0)),
                                manual_review_count=int(payload.get("manual_review_count", 0)),
                                lot_decision=payload.get("lot_decision"),
                                decision_reason=payload.get("decision_reason") or payload.get("notes"),
                            )
                            db.add(insp)
                            db.flush()

                elif item.entity_type in ("Image", "InspectionImage"):
                    img_existing = db.query(InspectionImage).filter(InspectionImage.id == item.entity_id).first()
                    if not img_existing and payload.get("inspection_id"):
                        img = InspectionImage(
                            id=item.entity_id,
                            inspection_id=payload.get("inspection_id"),
                            storage_key=payload.get("storage_key") or payload.get("file_path", f"offline_sync/{item.entity_id}.jpg"),
                            filename=payload.get("filename") or payload.get("file_name", "offline_tray.jpg"),
                            content_type=payload.get("content_type") or payload.get("mime_type", "image/jpeg"),
                            file_size_bytes=int(payload.get("file_size_bytes", 1024)),
                            sha256_hash=payload.get("sha256_hash") or payload.get("checksum_sha256"),
                            quality_status=payload.get("quality_status", "PASSED"),
                            blur_variance=float(payload.get("blur_variance", 150.0)) if payload.get("blur_variance") else None,
                            mean_brightness=float(payload.get("mean_brightness", 130.0)) if payload.get("mean_brightness") else None,
                            calibration_detected=bool(payload.get("calibration_detected", True)),
                            pixels_per_mm=float(payload.get("pixels_per_mm", 5.2)) if payload.get("pixels_per_mm") else None,
                            calibration_method=payload.get("calibration_method", "ARUCO_4X4_50"),
                            captured_at=now,
                        )
                        db.add(img)
                        db.flush()

                elif item.entity_type == "GradeResult":
                    target_insp_id = payload.get("inspection_id")
                    if target_insp_id:
                        insp = db.query(Inspection).filter_by(id=target_insp_id).first()
                        if insp:
                            if payload.get("grade"):
                                insp.lot_decision = f"ACCEPT_{payload.get('grade')}" if "ACCEPT" not in payload.get("grade") else payload.get("grade")
                            if payload.get("grade_a_percentage") is not None:
                                insp.grade_a_percentage = float(payload.get("grade_a_percentage"))
                            if payload.get("urs_percentage") is not None:
                                insp.urs_percentage = float(payload.get("urs_percentage"))
                            if payload.get("reject_percentage") is not None:
                                insp.reject_percentage = float(payload.get("reject_percentage"))
                            if payload.get("reason_code"):
                                insp.decision_reason = payload.get("explanation") or payload.get("reason_code")
                            db.flush()

                # Record newly synchronized item
                record = SyncRecord(
                    client_id=batch_in.client_id,
                    sync_key=item.sync_key,
                    entity_type=item.entity_type,
                    entity_id=item.entity_id,
                    status="SYNCED",
                    synced_at=now,
                )
                db.add(record)
                db.flush()

                results.append(
                    SyncItemResponse(
                        sync_key=record.sync_key,
                        entity_type=record.entity_type,
                        entity_id=record.entity_id,
                        status=record.status,
                        synced_at=record.synced_at,
                    )
                )
                success_count += 1
        except Exception as e:
            failed_count += 1
            results.append(
                SyncItemResponse(
                    sync_key=item.sync_key,
                    entity_type=item.entity_type,
                    entity_id=item.entity_id,
                    status="FAILED",
                    synced_at=datetime.now(timezone.utc),
                    error_details=str(e),
                )
            )

    db.commit()

    return SyncBatchResponse(
        client_id=batch_in.client_id,
        processed_count=len(batch_in.items),
        success_count=success_count,
        failed_count=failed_count,
        results=results,
    )


@router.get("/status/{client_id}", response_model=List[SyncItemResponse])
def get_client_sync_records(client_id: str, db: Session = Depends(get_db)):
    """Retrieves all synchronization records for a given mobile device client ID."""
    return db.query(SyncRecord).filter(SyncRecord.client_id == client_id).all()
