"""
AcademicIQ — FastAPI application entry point.
Evidence-Driven Explainable Academic Intelligence Platform.
"""
from __future__ import annotations

from contextlib import asynccontextmanager

import structlog
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.core.exceptions import AcademicIQError
from app.core.logging import configure_logging
from app.core.middleware import RequestIDMiddleware, SecurityHeadersMiddleware

# Routers
from app.auth.router import router as auth_router
from app.students.router import router as students_router
from app.academics.router import router as academics_router
from app.results.router import router as results_router
from app.analytics.router import router as analytics_router
from app.profile.router import router as profile_router
from app.intelligence.router import router as intelligence_router
from app.evidence.router import router as evidence_router
from app.interventions.router import router as interventions_router
from app.simulation.router import router as simulation_router
from app.ai.router import router as ai_router
from app.reports.router import router as reports_router
from app.evaluation.router import router as evaluation_router
from app.users.router import router as users_router
from app.audit.router import router as audit_router
from app.notifications.router import router as notifications_router
from app.ml.router import router as ml_router

configure_logging(debug=settings.DEBUG)
logger = structlog.get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("startup", app=settings.APP_NAME, version=settings.APP_VERSION, env=settings.ENVIRONMENT)
    yield
    logger.info("shutdown", app=settings.APP_NAME)


app = FastAPI(
    title=settings.APP_NAME,
    description=(
        "Evidence-Driven Explainable Academic Intelligence and Early-Warning Platform "
        "for Longitudinal University Result Analytics"
    ),
    version=settings.APP_VERSION,
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
    lifespan=lifespan,
)

# ---------------------------------------------------------------------------
# Middleware (order matters: outer → inner)
# ---------------------------------------------------------------------------
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(RequestIDMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Exception handlers
# ---------------------------------------------------------------------------

@app.exception_handler(AcademicIQError)
async def academiciq_exception_handler(request: Request, exc: AcademicIQError):
    request_id = request.headers.get("X-Request-ID", "")
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "code": exc.error_code,
                "message": exc.message,
                "request_id": request_id,
            }
        },
    )


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    request_id = request.headers.get("X-Request-ID", "")
    logger.error("unhandled_exception", exc=str(exc), path=request.url.path, request_id=request_id)
    return JSONResponse(
        status_code=500,
        content={
            "error": {
                "code": "INTERNAL_ERROR",
                "message": "An unexpected error occurred",
                "request_id": request_id,
            }
        },
    )


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

API_PREFIX = "/api/v1"

app.include_router(auth_router, prefix=API_PREFIX)
app.include_router(students_router, prefix=API_PREFIX)
app.include_router(academics_router, prefix=API_PREFIX)
app.include_router(results_router, prefix=API_PREFIX)
app.include_router(analytics_router, prefix=API_PREFIX)
app.include_router(profile_router, prefix=API_PREFIX)
app.include_router(intelligence_router, prefix=API_PREFIX)
app.include_router(evidence_router, prefix=API_PREFIX)
app.include_router(interventions_router, prefix=API_PREFIX)
app.include_router(simulation_router, prefix=API_PREFIX)
app.include_router(ai_router, prefix=API_PREFIX)
app.include_router(reports_router, prefix=API_PREFIX)
app.include_router(evaluation_router, prefix=API_PREFIX)
app.include_router(users_router, prefix=API_PREFIX)
app.include_router(audit_router, prefix=API_PREFIX)
app.include_router(notifications_router, prefix=API_PREFIX)
app.include_router(ml_router, prefix=API_PREFIX)


# ---------------------------------------------------------------------------
# Health / Readiness
# ---------------------------------------------------------------------------

@app.get("/health", tags=["ops"])
async def health():
    return {"status": "ok", "app": settings.APP_NAME, "version": settings.APP_VERSION}


@app.get("/ready", tags=["ops"])
async def readiness():
    """Check DB connectivity."""
    from app.database.session import async_engine
    from sqlalchemy import text
    try:
        async with async_engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        return {"status": "ready"}
    except Exception as e:
        return JSONResponse(status_code=503, content={"status": "not_ready", "detail": str(e)})
