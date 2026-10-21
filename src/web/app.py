"""
FastAPI Application Entrypoint for ShikshaSignal REST API
"""

from pathlib import Path
from typing import Optional
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from src.models.database import DatabaseManager
from src.engine.validator import DataValidator
from src.services.import_service import ImportService
from src.services.student_service import StudentService
from src.services.overview_service import OverviewService
from src.services.intervention_service import InterventionService
from src.config import DATABASE_PATH, SYNTHETIC_DIR
from src.web.routes import (
    health_router,
    import_router,
    overview_router,
    students_router,
    interventions_router,
    governance_router,
)


def create_app(
    db: Optional[DatabaseManager] = None,
    db_path: Optional[Path] = None,
    skill_catalog_path: Optional[Path] = None
) -> FastAPI:
    app = FastAPI(
        title="ShikshaSignal REST API",
        description=(
            "Decision support and learning-gap early-warning layer for foundational "
            "literacy and numeracy (Grades 1–3). Aligned with Techfest IIT Bombay Challenge 2026–27."
        ),
        version="0.3.0-phase3",
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json"
    )

    # Enable CORS for local web development
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Initialize validator and database
    catalog_path = skill_catalog_path or (SYNTHETIC_DIR / "skill_catalog.csv")
    validator = DataValidator(catalog_path)
    database = db or DatabaseManager(db_path or DATABASE_PATH)

    # Initialize Application Services
    import_service = ImportService(database, validator)
    student_service = StudentService(database, validator)
    overview_service = OverviewService(database, validator)
    intervention_service = InterventionService(database, validator)

    # Attach to application state for route dependency access
    app.state.db = database
    app.state.validator = validator
    app.state.import_service = import_service
    app.state.student_service = student_service
    app.state.overview_service = overview_service
    app.state.intervention_service = intervention_service

    # Include Routers
    app.include_router(health_router)
    app.include_router(import_router)
    app.include_router(overview_router)
    app.include_router(students_router)
    app.include_router(interventions_router)
    app.include_router(governance_router)

    # Mount built frontend dashboard if available
    frontend_dist = Path(__file__).resolve().parent.parent.parent / "frontend" / "dist"
    if frontend_dist.exists():
        from fastapi.staticfiles import StaticFiles
        app.mount("/", StaticFiles(directory=str(frontend_dist), html=True), name="frontend")

    # Global Exception Handler: Sanitize internal errors
    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        # Prevent leaking file-system paths or internal database stack traces
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "detail": "An internal server error occurred. Request could not be processed safely."
            }
        )

    return app


# Default app instance for uvicorn runner
app = create_app()
