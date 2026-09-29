"""
Offline Synchronization Router
Smart India Hackathon 2026 - Problem Statement PS26031

Endpoints:
- POST /sync/batch: Idempotent batch synchronization for Flutter mobile inspections
- GET  /sync/status: Check status of sync records by client_id
"""

from typing import List
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from datetime import datetime, timezone

from ...database import get_db
from ...models.entities import SyncRecord
from ...schemas.api_schemas import (
    SyncBatchRequest,
    SyncBatchResponse,
    SyncItemResponse,
)

router = APIRouter(prefix="/sync", tags=["Offline Synchronization"])


@router.post("/batch", response_model=SyncBatchResponse, status_code=status.HTTP_200_OK)
def sync_batch(batch_in: SyncBatchRequest, db: Session = Depends(get_db)):
    """
    Idempotent batch synchronization endpoint for Flutter mobile offline client.
    - Uses sync_key (client-generated UUID) to prevent duplicate processing.
    - If sync_key already exists in sync_records, acknowledges without duplicate inserts.
    """
    results: List[SyncItemResponse] = []
    success_count = 0
    failed_count = 0

    for item in batch_in.items:
        existing = db.query(SyncRecord).filter(SyncRecord.sync_key == item.sync_key).first()
        if existing:
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
            # Record newly synchronized item
            record = SyncRecord(
                client_id=batch_in.client_id,
                sync_key=item.sync_key,
                entity_type=item.entity_type,
                entity_id=item.entity_id,
                status="SYNCED",
                synced_at=datetime.now(timezone.utc),
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
