"""
FastAPI Backend Application Entrypoint
Smart India Hackathon 2026 - Problem Statement PS26031

AI-based Onion Quality Assessment and Deterministic Grading Platform
"""

import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import settings
from .database import check_database_connection
from .api.routers import health, farmers, procurement_centres, lots, inspections

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("onion_sure")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Verify database connection
    logger.info(f"Starting {settings.APP_NAME} v{settings.APP_VERSION}")
    db_ok = check_database_connection()
    if db_ok:
        logger.info("Database connection verified successfully.")
    else:
        logger.warning(
            "Database connection could not be established on startup. "
            "Ensure PostgreSQL is running via 'docker compose up -d' or DATABASE_URL is configured."
        )
    yield
    # Shutdown
    logger.info("Shutting down application...")


app = FastAPI(
    title="ONION_SURE API",
    description="AI-Based Onion Quality Assessment & Deterministic Grading Backend (SIH 2026 PS26031)",
    version=settings.APP_VERSION,
    lifespan=lifespan,
)

# CORS Middleware (permitting Flutter mobile app & web dashboard access)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register Routers
app.include_router(health.router)
app.include_router(farmers.router, prefix=settings.API_V1_PREFIX)
app.include_router(procurement_centres.router, prefix=settings.API_V1_PREFIX)
app.include_router(lots.router, prefix=settings.API_V1_PREFIX)
app.include_router(inspections.router, prefix=settings.API_V1_PREFIX)


@app.get("/")
def root_info():
    return {
        "project": "ONION_SURE",
        "competition": "Smart India Hackathon 2026",
        "problem_statement": "PS26031",
        "version": settings.APP_VERSION,
        "docs_url": "/docs",
        "health_check": "/health",
    }
