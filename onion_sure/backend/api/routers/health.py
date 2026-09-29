"""
Health Check Router
Smart India Hackathon 2026 - Problem Statement PS26031

Actively tests PostgreSQL connectivity via SELECT 1.
"""

from fastapi import APIRouter, Depends, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from datetime import datetime, timezone

from sqlalchemy import text
from ...database import get_db
from ...schemas import HealthResponse

router = APIRouter(tags=["Health"])


@router.get("/health", response_model=HealthResponse)
def get_system_health(db: Session = Depends(get_db)):
    """Verifies that API is running and tests active database connection."""
    now = datetime.now(timezone.utc)
    try:
        db.execute(text("SELECT 1"))
        dialect = db.get_bind().name if db.get_bind() is not None else "unknown"
        return HealthResponse(
            status="ok",
            database="connected",
            timestamp=now,
            version="1.0.0",
            details={"dialect": dialect},
        )
    except Exception as e:
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "status": "degraded",
                "database": "disconnected",
                "timestamp": now.isoformat(),
                "version": "1.0.0",
                "details": {"error": f"Database connection unavailable: {str(e)}"},
            },
        )
